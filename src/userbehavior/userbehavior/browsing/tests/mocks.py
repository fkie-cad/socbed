#!/usr/bin/python3
# -*- coding: utf-8 -*-
from userbehavior.browsing.browser import Browser, BrowserException
from userbehavior.browsing.browsing import Routine
from userbehavior.profile.tests.mocks import MockProfile


class MockBrowser(Browser):
    def __init__(self):
        self.last_search_term = None
        self.current_url_field = None
        self.current_links_results = ["link_url1", "link_url2", "link_url3"]
        self.search_results = ["result1", "result2", "result3"]

    def open(self):
        self.current_url_field = "about:blank"

    def close(self):
        pass

    def reset(self):
        pass

    def load(self, url):
        self.current_url_field = url

    def current_url(self):
        return self.current_url_field

    def current_links(self, same_domain=True):
        return self.current_links_results

    def search(self, search_term):
        self.last_search_term = search_term
        return self.search_results


class ExceptionRaisingBrowser(Browser):
    def current_url(self):
        raise BrowserException()

    def reset(self):
        raise BrowserException()

    def current_links(self, same_domain=True):
        raise BrowserException()

    def search(self, search_term):
        raise BrowserException()

    def open(self):
        raise BrowserException()

    def load(self, url):
        raise BrowserException()

    def close(self):
        raise BrowserException()


class ExceptionRaisingRoutine(Routine):
    def run(self):
        raise BrowserException()


class MockBrowsingProfile(MockProfile):
    def __init__(self):
        MockProfile.__init__(self)
        self.init_mock_attributes()
        self.init_mock_distributions()

    def init_mock_attributes(self):
        self.websites = ["http://www.google.de", "http://www.heise.de/"]
        self.search_terms = ["Hallo Welt", "Katzenvideos"]

    def init_mock_distributions(self):
        self.add_mock_distribution("Session Duration", 1 / 6)
        self.add_mock_distribution("Session Pause", 1 / (60 * 3))
        self.add_mock_distribution("Stay Time", 4)
        self.add_mock_distribution("Search", True)
