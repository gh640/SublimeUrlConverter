# coding: utf-8

"""Converts selected URLs to links with fetched page titles.
"""

import html
import logging
from concurrent.futures import TimeoutError, ThreadPoolExecutor, as_completed
from math import floor
from urllib.parse import urlparse
from urllib.request import urlopen

import requests
from bs4 import BeautifulSoup

import sublime
import sublime_plugin

__version__ = '0.6.0'
__author__ = "Goto Hayato"
__copyright__ = 'Copyright 2022, Goto Hayato'
__license__ = 'MIT'

try:
    SUBLIME_MAJOR_VERSION = floor(int(sublime.version()) / 1000)
except Exception:
    SUBLIME_MAJOR_VERSION = 3
SETTINGS_NAME = 'UrlConverter.sublime-settings'

logger = logging.getLogger('UrlConverter')


class TitleFetcher:
    """Webpage title fetcher with multithreading."""

    def __init__(self, sublime_major_version):
        self._sublime_major_version = sublime_major_version

    def fetch(self, urls):
        settings = sublime.load_settings(SETTINGS_NAME)
        timeout = settings.get('timeout', 10)

        if type(timeout) not in (int, float):
            logger.error('`timeout` must be an int or float.')
            return {}

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = (executor.submit(self.fetch_title, url) for url in urls)
            try:
                results.extend(
                    f.result() for f in as_completed(futures, timeout=timeout)
                )
            except TimeoutError as e:
                logger.error('Page title fetching timed out.')
                return {}

        return dict(results)

    def fetch_title(self, url):
        try:
            html = self._fetch_html(url)
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.head.title.text.strip()
        except Exception as e:
            title = False
            logger.error('Failed to fetch an HTML title of a URL: {}.'.format(str(e)))

        return (url, title)

    def _fetch_html(self, url):
        if self._sublime_major_version == 4:
            return self._fetch_html_v4(url)
        elif self._sublime_major_version == 3:
            return self._fetch_html_v3(url)
        else:
            raise ValueError(
                'Unsupported Sublime Text version: {}'.format(
                    self._sublime_major_version
                )
            )

    def _fetch_html_v4(cls, url):
        response = urlopen(url)
        return response.read().decode()

    def _fetch_html_v3(cls, url):
        response = requests.get(url)
        return response.text


class BaseUrlConverter:
    """Common abstract url converter."""

    REPL_TEMPLATE = ''

    def run(self, edit):
        region_and_urls = self.get_selected_urls()
        region_and_repls = self.prepare_region_and_repls(region_and_urls)

        self.replace_regions(edit, region_and_repls)
        sublime.status_message('UrlConverter: urls are converted successfully.')

    def prepare_region_and_repls(self, region_and_urls):
        urls = self.extract_unique_urls(region_and_urls)
        url_titles_dict = self.fetch_titles(urls)
        return self.combine_region_links(region_and_urls, url_titles_dict)

    def get_selected_urls(self):
        region_and_urls = []
        for region in self.view.sel():
            url = self.view.substr(region).strip()
            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https"):
                continue

            region_and_urls.append((region, url))

        return region_and_urls

    def extract_unique_urls(self, region_and_urls):
        return set(url for region, url in region_and_urls)

    def fetch_titles(self, urls):
        fetcher = TitleFetcher(SUBLIME_MAJOR_VERSION)
        return fetcher.fetch(urls)

    def combine_region_links(self, region_and_urls, url_titles_dict):
        region_and_repls = []
        for region, url in region_and_urls:
            if url_titles_dict.get(url):
                repl = self.REPL_TEMPLATE.format(url=url, title=url_titles_dict[url])
                region_and_repls.append((region, repl))

        return region_and_repls

    def replace_regions(self, edit, region_and_repls):
        # Replace regions from the last to avoid misselection.
        for region, repl in sorted(region_and_repls, key=lambda x: x[0], reverse=True):
            if repl:
                self.view.replace(edit, region, repl)


class UrlConverterConvertToHtml(BaseUrlConverter, sublime_plugin.TextCommand):
    """Html url converter command."""

    REPL_TEMPLATE = '<a href="{url}">{title}</a>'

    def combine_region_links(self, region_and_urls, url_titles_dict):
        """Override to escape the url in html `href`."""
        region_and_repls = []
        for region, url in region_and_urls:
            if url_titles_dict.get(url):
                repl = self.REPL_TEMPLATE.format(
                    url=html.escape(url), title=url_titles_dict[url]
                )
                region_and_repls.append((region, repl))

        return region_and_repls


class UrlConverterConvertToMarkdown(BaseUrlConverter, sublime_plugin.TextCommand):
    """Markdown url converter command."""

    REPL_TEMPLATE = '[{title}]({url})'


class UrlConverterConvertToRestructuredtext(
    BaseUrlConverter, sublime_plugin.TextCommand
):
    """RestructuredText url converter command."""

    REPL_TEMPLATE = '`{title} <{url}>`_'


class UrlConverterConvertToPath(BaseUrlConverter, sublime_plugin.TextCommand):
    """Path url converter command."""

    def prepare_region_and_repls(self, region_and_urls):
        converter = self.extract_path_of_url
        return ((region, converter(url)) for region, url in region_and_urls)

    def extract_path_of_url(self, url):
        parsed = urlparse(url)
        return ''.join(parsed[2:])


class UrlConverterConvertToCustom(BaseUrlConverter, sublime_plugin.TextCommand):
    """Custom-format url converter command."""

    def run(self, edit, template=None):
        if template:
            self.REPL_TEMPLATE = template
        else:
            settings = sublime.load_settings(SETTINGS_NAME)
            self.REPL_TEMPLATE = settings.get('fallback_template', '{title}\n{url}')

        super().run(edit)
