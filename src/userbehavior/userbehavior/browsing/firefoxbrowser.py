#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os.path
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, \
    StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

from userbehavior.browsing.browser import BrowserException, Browser
from userbehavior.browsing.helpers import url_in_domain

logger = logging.getLogger(__name__)


class FirefoxBrowser(Browser):
    def __init__(self, firefox_binary=None, firefox_profile=None):
        self.firefox_binary = firefox_binary
        self.custom_firefox_profile = firefox_profile
        self._driver = None

    def __del__(self):
        self._close_driver()

    @staticmethod
    def default_firefox_profile():
        fp = webdriver.FirefoxProfile()
        # Adding noscript extension to webdriver.
        # This generally blocks javascript execution on webpages.
        # At the moment it is necessary to prevent the driver from
        # getting stuck on an print dialog (window.print).
        fp.add_extension(
            os.path.join(os.path.dirname(__file__), "firefox_extensions/noscript.xpi"))
        # prevent noscript page to load on startup
        fp.set_preference("noscript.firstRunRedirection", False)
        # add whitepages
        fp.set_preference("capability.policy.maonoscript.sites", "google.de")
        return fp

    def open(self):
        self._init_driver()

    def close(self):
        self._close_driver()

    def reset(self):
        self._close_driver()
        self._init_driver()

    def _init_driver(self):
        try:
            self._create_driver()
        except WebDriverException as e:
            raise SeleniumException("Could not create WebDriver: {e}".format(e=e))
        self._set_driver_attributes()

    def _create_driver(self):
        cap = webdriver.DesiredCapabilities.FIREFOX.copy()
        cap["marionette"] = False
        self._driver = webdriver.Firefox(
            firefox_profile=self.custom_firefox_profile or self.default_firefox_profile(),
            firefox_binary=FirefoxBinary(self.firefox_binary),
            capabilities=cap)

    def _set_driver_attributes(self):
        self._driver.implicitly_wait(1)
        self._driver.set_page_load_timeout(5)

    def _close_driver(self):
        if self._driver:
            self._driver.quit()
            self._driver = None

    def current_url(self):
        return self._driver.current_url

    def current_links(self, same_domain=True):
        a_elements = self._current_tag_elements("a")
        current_url = self._driver.current_url

        def _is_good_a_element(a):
            return len(a.text) >= 4 and a.get_attribute("href") is not None

        try:
            urls = [a.get_attribute("href") for a in a_elements if _is_good_a_element(a)]
        except StaleElementReferenceException:
            urls = list()

        def _is_good_url(url):
            return all([
                not url.startswith("mailto"),
                (not same_domain) or url_in_domain(url, current_url, compare_depth=2)])

        good_urls = [url for url in urls if _is_good_url(url)]
        return good_urls

    def _current_tag_elements(self, tag_name):
        try:
            return self._driver.find_elements_by_tag_name(tag_name)
        except NoSuchElementException:
            logger.debug("No {tag}-tag elements found".format(tag=tag_name))
            return list()

    def _current_id_element(self, id):
        try:
            return self._driver.find_element_by_id(id)
        except NoSuchElementException:
            raise SeleniumException("No {id}-id element found".format(id=id))

    def _current_class_elements(self, class_name):
        try:
            return self._driver.find_elements_by_class_name(class_name)
        except NoSuchElementException:
            logger.debug("No {class_}-class elements found".format(class_=class_name))

    def search(self, search_term):
        logger.info("Search: " + search_term)
        engine = "http://www.google.de"
        search_box_id = "lst-ib"
        search_result_class = "g"
        self._try_to_load(engine)
        search_box = self._current_id_element(search_box_id)
        self._try_send_keys(search_box, search_term + Keys.RETURN)
        time.sleep(3)
        class_results = self._current_class_elements(search_result_class)

        def has_a_tag_and_href(element):
            try:
                return element.find_element_by_tag_name("a").get_attribute("href") is not None
            except NoSuchElementException:
                return False

        url_results = [
            result.find_element_by_tag_name("a").get_attribute("href")
            for result in class_results
            if has_a_tag_and_href(result)]
        return url_results

    def _try_send_keys(self, web_element, keys):
        try:
            web_element.send_keys(keys)
        except StaleElementReferenceException:
            raise SeleniumException("Could not send keys to web element")

    def load(self, url):
        logger.info("Loading url: " + url)
        self._try_to_load(url)

    def _try_to_load(self, url):
        try:
            self._driver.get(url)
        except TimeoutException as e:
            logger.info("Loading url: Timeout - try to abort loading")
            try:
                self._driver.find_element_by_tag_name("html") \
                    .send_keys(Keys.ESCAPE)
            except WebDriverException as e:
                raise BrowserException(
                    "WebDriverException: " + (e.msg or "No message"))
        except WebDriverException as e:
            raise BrowserException(
                "WebDriverException: " + (e.msg or "No message"))
        except:
            raise BrowserException()


class SeleniumException(BrowserException):
    pass
