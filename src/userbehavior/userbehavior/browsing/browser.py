#!/usr/bin/python3
# -*- coding: utf-8 -*-


class Browser:
    def open(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def current_url(self):
        raise NotImplementedError()

    def current_links(self, same_domain=True):
        raise NotImplementedError()

    def search(self, search_term):
        raise NotImplementedError()

    def load(self, url):
        raise NotImplementedError()


class BrowserException(Exception):
    pass


class NullBrowser(Browser):
    def search(self, search_term):
        pass

    def open(self):
        pass

    def load(self, url):
        pass

    def close(self):
        pass

    def reset(self):
        pass

    def current_url(self):
        return ""

    def current_links(self, same_domain=True):
        return []
