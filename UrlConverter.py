# coding: utf-8

"""Converts selected URLs to links with fetched page titles.
"""

import time
from threading import Thread
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests

import sublime
import sublime_plugin


class TitleFetchThread(Thread):
    """Thread for fetching a html page title.
    """

    def __init__(self, url):
        self.url = url
        super().__init__()

    def run(self):
        try:
            response = requests.get(self.url)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.head.title.text
        except Exception as e:
            title = False

        self.title = title


class BaseUrlConverter(sublime_plugin.TextCommand):
    """Common abstract url converter.
    """

    REPL_TEMPLATE = ''

    def run(self, edit):
        title_fetch_threads = self.fetch_title_with_treads()
        region_and_repls = self.extract_links(title_fetch_threads)
        self.replace_regions(edit, region_and_repls)
        sublime.status_message('UrlConverter: urls are converted successfully.')

    def fetch_title_with_treads(self):
        title_fetch_threads = []
        for region in reversed(self.view.sel()):
            url = self.view.substr(region).strip()
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https"):
                fetcher = TitleFetchThread(url)
                fetcher.start()
                title_fetch_threads.append((region, fetcher))

        while True:
            completed = True
            for region, fetcher in title_fetch_threads:
                if fetcher.is_alive():
                    completed = False
            if completed:
                break
            time.sleep(0.1)

        return title_fetch_threads

    def extract_links(self, title_fetch_threads):
        return ((s, self.REPL_TEMPLATE.format(f)) if f.title else (s, f.url)
                for s, f in title_fetch_threads)

    def replace_regions(self, edit, region_and_repls):
        for region, repl in region_and_repls:
            if repl:
                self.view.replace(edit, region, repl)


class UrlConverterConvertToHtml(BaseUrlConverter):
    """Html Url converter command.
    """

    REPL_TEMPLATE = '<a href="{0.url}">{0.title}</a>'


class UrlConverterConvertToMarkdown(BaseUrlConverter):
    """Html Url converter command.
    """

    REPL_TEMPLATE = '[{0.title}]({0.url})'
