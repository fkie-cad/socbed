#!/usr/bin/python3
# -*- coding: utf-8 -*-

from userbehavior.mailing.helpers import get_urls_in_text, get_urls_in_html


class TestUrlsInText:
    def test_result_is_list(self):
        res = get_urls_in_text("")
        assert isinstance(res, list)

    def test_no_url(self):
        text = "Dies ist eine Textnachricht ohne eine URL"
        assert len(get_urls_in_text(text)) == 0

    def test_one_url(self):
        text = "Hier ist eine Nachricht mit http://www.google.de als URL"
        assert get_urls_in_text(text)[0] == "http://www.google.de"

    def test_url_without_protocol(self):
        text = "Der Link zu heise.de . Klick drauf!"
        assert get_urls_in_text(text)[0] == "http://heise.de"


class TestUrlsInHtml:
    def test_no_url(self):
        html = "<body><p>This is just a plain paragraph without links</p></body>"
        assert len(get_urls_in_html(html)) == 0

    def test_a_href(self):
        html = "<body><a href=\"http://some.de/here.html\">This is a link</a></body>"
        assert get_urls_in_html(html)[0] == "http://some.de/here.html"

    def test_a_href_single_quotes(self):
        html = "<body><a href='http://some.de/here.html'>This is a link</a></body>"
        assert get_urls_in_html(html)[0] == "http://some.de/here.html"

    def test_a_href_without_protocol(self):
        html = "<body><a href='some.de/here.html'>This is a link</a></body>"
        assert get_urls_in_html(html)[0] == "http://some.de/here.html"

    def test_no_url_outside_a_tag(self):
        html = "<body>http://heise.de is a url but should not match</body>"
        assert get_urls_in_html(html) == []

    def test_uppercase_tags_and_protocol(self):
        html = "<body><A HREF=\"HTTP://some.de/here.HTML\">This is a link</a></body>"
        assert get_urls_in_html(html)[0] == "http://some.de/here.HTML"

    def test_uppercase_url(self):
        html = "<body><A HREF=\"http://172.18.1.1/Bank-Of-Scotland/index.htm\">This is a link</a></body>"
        assert get_urls_in_html(html)[0] == "http://172.18.1.1/Bank-Of-Scotland/index.htm"
