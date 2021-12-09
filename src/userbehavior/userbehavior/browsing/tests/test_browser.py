#!/usr/bin/python3
# -*- coding: utf-8 -*-
from userbehavior.browsing.browser import Browser, NullBrowser


class TestNullBrowser:
    def test_init(self):
        isinstance(NullBrowser(), Browser)

    def test_stubbed_methods(self):
        b = NullBrowser()
        b.open()
        b.close()
        b.reset()
        b.search(None)
        b.load(None)
        assert b.current_url() == ""
        assert b.current_links() == []

