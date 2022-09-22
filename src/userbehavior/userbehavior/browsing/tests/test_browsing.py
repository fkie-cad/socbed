#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
from unittest.mock import Mock

import pytest

from userbehavior.browsing.browser import NullBrowser
from userbehavior.browsing.browsing import Browsing, Session, Routine, BrowsingConfig, BrowserConfig
from userbehavior.browsing.browsingprofile import BrowsingProfileConfig
from userbehavior.browsing.tests.mocks import MockBrowser, MockBrowsingProfile, ExceptionRaisingRoutine, \
    ExceptionRaisingBrowser
from userbehavior.misc.util import Factory


class TestBrowsingConfig:
    def test_from_dict(self):
        d = {'profile': {'seed': 42, 'websites': ['UniqueSite']},
             'browser': {'implementation': 'NullBrowser'}}
        bc = BrowsingConfig.from_dict(d)
        assert bc.profile_config.seed == 42
        assert bc.profile_config.websites == ['UniqueSite']
        assert bc.browser_config.implementation == NullBrowser


class TestBrowserConfig:
    def test_implementations(self):
        known_implementations = ["NullBrowser", "FirefoxBrowser"]
        for impl in known_implementations:
            assert impl in BrowserConfig.implementations


class TestBrowsing:
    @pytest.fixture()
    def browsing(self):
        bf = Factory(implementation=MockBrowser)
        mbp = MockBrowsingProfile()
        b = Browsing(browsing_profile=mbp, browser_factory=bf)
        return b

    def test_browsing_runs_in_fast(self, browsing: Browsing):
        browsing._take_timeout = lambda *args: None
        browsing._session_factory.create = Mock()
        browsing.session_limit = 10
        browsing.run()
        assert browsing._session_factory.create.call_count == 10

    def test_create_from_config(self):
        profile_config = BrowsingProfileConfig()
        profile_config.websites = ["MySite"]
        browser_config = BrowserConfig(implementation=MockBrowser, some_key="value")
        config = BrowsingConfig(profile_config=profile_config, browser_config=browser_config)
        b = Browsing.from_config(config)
        assert isinstance(b, Browsing)
        assert b.browser_factory.implementation == MockBrowser
        assert b.browser_factory.kwargs["some_key"] == "value"
        assert b.browsing_profile.websites == ["MySite"]


class TestSession:
    @pytest.fixture()
    def session(self):
        bf = Factory(implementation=MockBrowser)
        mbp = MockBrowsingProfile()
        session = Session(browser_factory=bf, browsing_profile=mbp)
        return session

    def test_duration_from_browsing_profile(self, session: Session):
        session._init_duration()
        assert session.duration == session.browsing_profile.get_value("Session Duration") * 60

    def test_init_without_opening_browser(self, session: Session):
        assert session._browser is None

    def test_opens_browser(self, session: Session):
        session._open_browser()
        assert session._browser is not None

    def test_run_fast_with_exceptions_everywhere(self, session: Session):
        session._routine_factory.implementation = ExceptionRaisingRoutine
        session.browser_factory.implementation = ExceptionRaisingBrowser
        session.browsing_profile.get_value = lambda dist: 1 / 600 if dist == "Session Duration" else None
        session._take_timeout = Mock()
        session.run()


class TestRoutine:
    @pytest.fixture()
    def routine(self):
        return Routine(browser=MockBrowser(), browsing_profile=MockBrowsingProfile())

    def test_stay_on_page(self, routine: Routine):
        routine.browsing_profile.add_mock_distribution("Stay Time", 0.5)
        begin = time.time()
        routine._stay_on_page()
        end = time.time()
        assert routine.browsing_profile.mock_distribution_called("Stay Time")
        assert end - begin >= 0.5
        assert end - begin <= 0.7

    def test_follow_random_link_in_current_domain(self, routine: Routine):
        routine.browsing_profile.add_mock_distribution("Stay Time", 0.5)
        routine._follow_random_link_in_current_domain()
        assert routine._browser.current_url() in routine._browser.current_links_results

    def test_load_known_website(self, routine: Routine):
        routine.browsing_profile.add_mock_distribution("Stay Time", 0.5)
        routine._load_known_website()
        assert routine._browser.current_url() in routine.browsing_profile.websites

    def test_search(self, routine: Routine):
        term = "TestTerm"
        routine.browsing_profile.search_terms = [term]
        routine._search()
        assert routine.browsing_profile.get_random_choice.called
        assert routine._browser.last_search_term == term

    def test_ignore_no_search_results(self, routine: Routine):
        term = "TestTerm"
        routine.browsing_profile.search_terms = [term]
        routine._browser.search = lambda _: list()
        current_url = routine._browser.current_url
        routine._search()
        assert routine._browser.current_url == current_url
