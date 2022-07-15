#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pytest

from userbehavior.browsing.tests.mocks import MockBrowser, MockBrowsingProfile


@pytest.fixture()
def mb():
    return MockBrowser()


class TestMockBrowser:
    def test_init(self, mb: MockBrowser):
        pass

    def test_open(self, mb: MockBrowser):
        mb.open()
        assert mb.current_url() == "about:blank"

    def test_close(self, mb: MockBrowser):
        mb.close()

    def test_reset(self, mb: MockBrowser):
        mb.reset()

    def test_load_url(self, mb: MockBrowser):
        url = "someurl"
        mb.load(url)
        assert mb.current_url() == url

    def test_current_links(self, mb: MockBrowser):
        assert isinstance(mb.current_links(), list)
        assert mb.current_links()

    def test_search(self, mb: MockBrowser):
        assert isinstance(mb.search("some_term"), list)
        assert mb.search("some_term")


class TestMockBrowsingProfile:
    def test_websites_and_search_terms(self):
        mbp = MockBrowsingProfile()
        assert mbp.websites is not None
        assert mbp.search_terms is not None

    @pytest.mark.parametrize(
        "name, value", [
            ("Session Duration", 1 / 6),
            ("Session Pause", 1 / (60 * 3)),
            ("Stay Time", 4),
            ("Search", True)
        ])
    def test_default_browsing_distributions(self, name, value):
        mbp = MockBrowsingProfile()
        assert mbp.get_value(name) == value
