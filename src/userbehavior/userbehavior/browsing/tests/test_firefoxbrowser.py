#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
from types import SimpleNamespace

import pytest
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException

from userbehavior.browsing.firefoxbrowser import FirefoxBrowser, SeleniumException


class DriverStub:
    def __init__(self):
        self.current_tag_elements = None
        self.current_id_element = None
        self.current_url = ""

    def find_elements_by_tag_name(self, tag_name):
        return self.current_tag_elements

    def find_element_by_id(self, id):
        return self.current_id_element

    def get(self, url):
        pass

    def quit(self):
        pass


class WebElementStub:
    pass


def raise_(exception):
    raise exception


@pytest.fixture()
def fx_browser():
    fx_browser = FirefoxBrowser()
    fx_browser._driver = DriverStub()
    return fx_browser


class TestFirefoxBrowser:
    def test_exception_in_current_links(self, fx_browser: FirefoxBrowser):
        a = SimpleNamespace()
        a.text = "Some Stub Text"
        a.get_attribute = lambda key: raise_(StaleElementReferenceException())
        fx_browser._driver.current_tag_elements = [a]
        assert fx_browser.current_links(same_domain=False) == []

    def test_no_mailto_urls_in_current_links(self, fx_browser: FirefoxBrowser):
        mailto_element = WebElementStub()
        mailto_element.text = "Some mailto url"
        mailto_element.get_attribute = lambda _: "mailto:some@domain.de"
        http_element = WebElementStub()
        http_element.text = "Some http url"
        http_element.get_attribute = lambda _: "http://some.domain.de"
        fx_browser._driver.current_tag_elements = [mailto_element, http_element]
        links = fx_browser.current_links()
        assert links == [http_element.get_attribute("href")]

    def test_raise_proper_exception_if_driver_does_not_init(self, fx_browser: FirefoxBrowser):
        fx_browser._create_driver = lambda: raise_(WebDriverException)
        with pytest.raises(SeleniumException) as e:
            fx_browser._init_driver()
        assert "WebDriver" in str(e)

    def test_exception_in_send_keys(self, fx_browser: FirefoxBrowser):
        web_element = WebElementStub()
        web_element.send_keys = lambda keys: raise_(StaleElementReferenceException)
        fx_browser._driver.current_id_element = web_element
        with pytest.raises(SeleniumException):
            fx_browser.search("some term")


class SeleniumIntegration:
    def assert_some_actions(self, fx: FirefoxBrowser):
        fx.open()
        fx.load("http://google.de")
        assert "google" in fx.current_url()
        results = fx.search("FKIE")
        assert any("fkie" in result for result in results)
        fx.close()


#@pytest.mark.integration
#@pytest.mark.skipif(not sys.platform == "linux", reason="linux test is skipped")
#class TestLinuxSeleniumIntegration(SeleniumIntegration):
#    @pytest.mark.parametrize("version", ["linux_33"])
#    def test_firefox_versions(self, version):
#        binary = os.path.join(os.path.dirname(__file__), "fx", version, "firefox")
#        fx = FirefoxBrowser(firefox_binary=binary)
#        self.assert_some_actions(fx)


#@pytest.mark.integration
#@pytest.mark.skipif(not sys.platform.startswith("win"), reason="windows test is skipped")
#class TestWindowsSystemSeleniumIntegration(SeleniumIntegration):
#    def test_system_firefox(self):
#        fx = FirefoxBrowser()
#        self.assert_some_actions(fx)
