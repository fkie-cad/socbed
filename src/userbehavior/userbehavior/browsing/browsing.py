#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import time
from types import SimpleNamespace

from userbehavior.misc.util import Factory

from userbehavior.browsing.browser import BrowserException, NullBrowser
from userbehavior.browsing.browsingprofile import BrowsingProfile, BrowsingProfileConfig
from userbehavior.browsing.firefoxbrowser import FirefoxBrowser

logger = logging.getLogger(__name__)


class BrowsingConfig:
    def __init__(self, profile_config, browser_config):
        self.profile_config = profile_config
        self.browser_config = browser_config

    @classmethod
    def from_dict(cls, d):
        profile_config = BrowsingProfileConfig(**d['profile'])
        browser_config = BrowserConfig.from_str_dict(**d['browser'])
        return BrowsingConfig(profile_config, browser_config)


class BrowserConfig(SimpleNamespace):
    implementations = {
        'NullBrowser': NullBrowser,
        'FirefoxBrowser': FirefoxBrowser}

    def __init__(self, implementation=None, **kwargs):
        self.implementation = implementation or NullBrowser
        super().__init__(**kwargs)

    @classmethod
    def from_str_dict(cls, implementation=None, **kwargs):
        parsed_implementation = cls.implementations[implementation]
        return cls(implementation=parsed_implementation, **kwargs)


class Browsing:
    def __init__(self, browsing_profile=None, browser_factory=None):
        self.browser_factory = browser_factory or self.default_browser_factory()
        self.browsing_profile = browsing_profile or self.default_browsing_profile()
        self.session_limit = None
        self._session_factory = self.default_session_factory()

    @classmethod
    def from_config(cls, config: BrowsingConfig):
        kwargs = config.browser_config.__dict__.copy()
        implementation = kwargs.pop("implementation")
        bf = Factory(implementation=implementation, kwargs=kwargs)
        bp = BrowsingProfile(config=config.profile_config)
        return cls(browser_factory=bf, browsing_profile=bp)

    @staticmethod
    def default_browser_factory():
        return Factory(implementation=NullBrowser)

    @staticmethod
    def default_browsing_profile():
        return BrowsingProfile()

    def default_session_factory(self):
        session_factory = Factory(
            implementation=Session,
            kwargs={
                "browser_factory": self.browser_factory,
                "browsing_profile": self.browsing_profile})
        return session_factory

    def run(self):
        logger.info("Started Browsing")
        self._loop_sessions()
        logger.info("Ended Browsing")

    def _loop_sessions(self):
        count_down = self.session_limit
        while (count_down is None) or count_down > 0:
            self._run_new_session()
            self._timeout_until_next_session()
            if count_down:
                count_down -= 1

    def _timeout_until_next_session(self):
        pause_hrs = self.browsing_profile.get_value("Session Pause")  # in hours
        logger.info("Next Session in {hrs} hours.".format(hrs=pause_hrs))
        self._take_timeout(pause_hrs * 3600)

    def _run_new_session(self):
        self._session_factory.create().run()

    @staticmethod
    def _take_timeout(seconds=1):
        logger.debug("Timeout: {secs} seconds".format(secs=seconds))
        time.sleep(seconds)


class Session:
    def __init__(self, browser_factory, browsing_profile):
        self.browser_factory = browser_factory
        self.browsing_profile = browsing_profile
        self._browser = None
        self._routine_factory = self.default_routine_factory()

    def default_routine_factory(self):
        routine_factory = Factory(
            Routine, kwargs={
                "browser": self._browser,
                "browsing_profile": self.browsing_profile})
        return routine_factory

    def _init_duration(self):
        self.start_time = time.time()
        self.duration = self.browsing_profile.get_value("Session Duration") * 60
        self.end_time = self.start_time + self.duration

    def run(self):
        self._init_duration()
        info = "Starttime: {start}, Endtime: {end}, Duration: {dur} seconds.".format(
            start=time.ctime(self.start_time), end=time.ctime(self.end_time), dur=self.duration)
        logger.info("Started Session: {info}".format(info=info))
        while not self._has_ended():
            try:
                self._try_run_session()
            except BrowserException as e:
                logger.info("Could not run session: {e}".format(e=str(e)))
                self._take_timeout(1)
        logger.info("Session ended")

    def _try_run_session(self):
        self._open_browser()
        self._loop_routines_until_session_ends()
        self._close_browser()

    def _open_browser(self):
        self._browser = self.browser_factory.create()
        self._routine_factory.kwargs["browser"] = self._browser
        self._browser.open()

    def _close_browser(self):
        self._browser.close()

    def _loop_routines_until_session_ends(self):
        while not self._has_ended():
            self._try_to_run_routine()

    def _has_ended(self):
        return time.time() > self.end_time

    def _try_to_run_routine(self):
        try:
            self._routine_factory.create().run()
        except BrowserException as e:
            logger.info("Exception in Routine: {e}".format(e=str(e)))
            try:
                self._browser.reset()
            except BrowserException as e:
                logger.info("Could not reset browser: {e}".format(e=str(e)))
                pass

    @staticmethod
    def _take_timeout(seconds=1):
        logger.debug("Timeout: {secs} seconds".format(secs=seconds))
        time.sleep(seconds)


class Routine:
    def __init__(self, browser, browsing_profile):
        self.browsing_profile = browsing_profile
        self._browser = browser

    def run(self):
        self._search_or_load_known_website()
        self._follow_random_links_in_current_domain(self.browsing_profile.get_randint(5))

    def _search_or_load_known_website(self):
        if self.browsing_profile.get_value("Search"):
            self._search()
        else:
            self._load_known_website()
        self._stay_on_page()

    def _search(self):
        search_term = self.browsing_profile.get_random_choice(self.browsing_profile.search_terms)
        logger.info("Search for {search_term}".format(search_term=search_term))
        results = self._browser.search(search_term)
        if results:
            self._browser.load(self.browsing_profile.get_random_choice(results))

    def _load_known_website(self):
        website = self.browsing_profile.get_random_choice(self.browsing_profile.websites)
        logger.info("Load known website {url}".format(url=website))
        self._browser.load(website)

    def _follow_random_links_in_current_domain(self, n=1):
        for i in range(n):
            self._follow_random_link_in_current_domain()

    def _follow_random_link_in_current_domain(self):
        logger.info("Try to follow a random link in current domain")
        links = self._browser.current_links()
        if links:
            rnd_link = self.browsing_profile.get_random_choice(links)
            self._browser.load(rnd_link)
            self._stay_on_page()

    def _stay_on_page(self):
        rnd_secs = self.browsing_profile.get_value("Stay Time")
        logger.info("Staying: Staying on page for {secs} seconds.".format(secs=rnd_secs))
        self._take_timeout(rnd_secs)

    @staticmethod
    def _take_timeout(seconds=1):
        logger.debug("Timeout: {secs} seconds".format(secs=seconds))
        time.sleep(seconds)


class BrowsingException(Exception):
    pass
