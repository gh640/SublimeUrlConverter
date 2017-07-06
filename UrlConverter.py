# coding: utf-8

"""Converts selected URLs to links with fetched page titles.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests

import sublime
import sublime_plugin

__version__ = '0.2.0'
__author__ = "Goto Hayato"
__copyright__ = 'Copyright 2017, Goto Hayato'
__license__ = 'MIT'


class TitleFetcher:
    """Webpage title fetcher with multithreading.
    """

    def fetch(self, urls):
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = (executor.submit(self.fetch_title, url) for url in urls)

            for f in as_completed(futures):
                results.append(f.result())

        return dict(results)

    @staticmethod
    def fetch_title(url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.head.title.text
        except Exception as e:
            title = False

        return (url, title)


class BaseUrlConverter:
    """Common abstract url converter.
    """

    REPL_TEMPLATE = ''

    def run(self, edit):
        region_and_urls = self.get_selected_urls()
        urls = self.extract_unique_urls(region_and_urls)
        url_titles_dict = self.fetch_titles(urls)
        region_and_repls = self.combine_region_links(region_and_urls, url_titles_dict)

        self.replace_regions(edit, region_and_repls)
        sublime.status_message('UrlConverter: urls are converted successfully.')

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
        fetcher = TitleFetcher()
        return fetcher.fetch(urls)

        return fetcher.results

    def combine_region_links(self, region_and_urls, url_titles_dict):
        region_and_repls = []
        for region, url in region_and_urls:
            if url_titles_dict[url]:
                repl = self.REPL_TEMPLATE.format(url=url, title=url_titles_dict[url])
            else:
                repl = False

            region_and_repls.append((region, repl))

        return region_and_repls

    def replace_regions(self, edit, region_and_repls):
        # Replace regions from the last to avoid misselection.
        for region, repl in sorted(region_and_repls, key=lambda x: x[0], reverse=True):
            if repl:
                self.view.replace(edit, region, repl)


class UrlConverterConvertToHtml(BaseUrlConverter, sublime_plugin.TextCommand):
    """Html url converter command.
    """

    REPL_TEMPLATE = '<a href="{url}">{title}</a>'


class UrlConverterConvertToMarkdown(BaseUrlConverter, sublime_plugin.TextCommand):
    """Markdown url converter command.
    """

    REPL_TEMPLATE = '[{title}]({url})'
