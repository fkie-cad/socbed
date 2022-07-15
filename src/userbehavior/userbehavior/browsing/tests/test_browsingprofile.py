#!/usr/bin/python3
# -*- coding: utf-8 -*-
from userbehavior.browsing.browsingprofile import BrowsingProfile, SimpleBrowsingProfile, BrowsingProfileConfig


class TestBrowsingProfile:
    def test_init(self):
        BrowsingProfile()

    def test_distributions(self):
        bp = BrowsingProfile()
        dists = ["Session Duration", "Session Pause", "Stay Time", "Search"]
        for dist in dists:
            bp.get_value(dist)

    def test_default_websites_search_terms(self):
        bp = BrowsingProfile()
        assert bp.websites == bp.default_config().websites
        assert bp.search_terms == bp.default_config().search_terms

    def test_update_websites_search_terms(self):
        config = BrowsingProfileConfig(websites=["one", "two"], search_terms=["three", "four"])
        bp = BrowsingProfile(config=config)
        assert bp.websites == ["one", "two"]
        assert bp.search_terms == ["three", "four"]


class TestSimpleBrowsingProfile:
    def test_init(self):
        SimpleBrowsingProfile()

    def test_simple_distributions(self):
        sbp = SimpleBrowsingProfile(session_duration=1, session_pause=2, stay_time=3)
        assert sbp.get_value("Session Duration") == 1
        assert sbp.get_value("Session Pause") == 2
        assert sbp.get_value("Stay Time") == 3
