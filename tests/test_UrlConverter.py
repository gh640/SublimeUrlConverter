"""Tests functions and classes in UrlConverter.py.
"""

import sys
import unittest
from unittest import mock

import requests
import sublime

UrlConverter = sys.modules['UrlConverter.UrlConverter']


class TestViewMixin:
    def setUp(self):
        self.view = sublime.active_window().new_file()

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            window = self.view.window()
            window.focus_view(self.view)
            window.run_command('close_file')


class TestTitleFetcher(TestViewMixin, unittest.TestCase):
    @mock.patch.object(requests, 'get')
    def test_fetch(self, get):
        title_set = 'Sample title'
        urls = ['https://example1.com', 'https://example2.com']
        fake_response = get.return_value
        fake_response.text = '<!DOCTYPE html><html><head><title>{}</title></head></html>'.format(
            title_set
        )

        results = UrlConverter.TitleFetcher().fetch(urls)
        self.assertIsInstance(results, dict)
        for url in urls:
            self.assertIn(url, results)
            self.assertEqual(results[url], title_set)

    @mock.patch.object(requests, 'get')
    def test_fetch_title(self, get):
        title_set = 'Sample title'
        url_orig = 'https://example.com'
        fake_response = get.return_value
        fake_response.text = '<!DOCTYPE html><html><head><title>{}</title></head></html>'.format(
            title_set
        )

        url, title = UrlConverter.TitleFetcher.fetch_title(url_orig)
        self.assertEqual(url_orig, url)
        self.assertEqual(title_set, title)

    @mock.patch.object(requests, 'get')
    def test_fetch_title__with_surrounding_spaces(self, get):
        title_set = '\n Sample title  \n\n'
        url_orig = 'https://example.com'
        fake_response = get.return_value
        fake_response.text = '<!DOCTYPE html><html><head><title>{}</title></head></html>'.format(
            title_set
        )

        url, title = UrlConverter.TitleFetcher.fetch_title(url_orig)
        self.assertEqual(url_orig, url)
        self.assertEqual(title_set.strip(), title)

    @mock.patch.object(requests, 'get')
    def test_fetch_title__error(self, get):
        url_orig = 'https://example.com'
        get.side_effect = Exception('A random exception occurred.')

        url, title = UrlConverter.TitleFetcher.fetch_title(url_orig)
        self.assertEqual(url_orig, url)
        self.assertFalse(title)
