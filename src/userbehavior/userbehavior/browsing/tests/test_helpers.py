#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pytest

from userbehavior.browsing.helpers import get_domain_name, url_in_domain


@pytest.fixture(params=[None, 42, 3.14, [], {}])
def no_str(request):
    return request.param


class TestGetDomainName:
    @pytest.mark.parametrize(
        "url, res", [
            ("http://www.google.de", "www.google.de"),
            ("maps.google.de", "maps.google.de"),
            ("here.there.com/this/is/some/text.html", "here.there.com"),
            ("http://sub.domain.org/with/some/folders", "sub.domain.org"),
            ("ftp://this.should/work/too.jpg", "this.should"),
            ("some_protocol://example.com/some_sir/file.exe", "example.com")
        ]
    )
    def test_basic_examples(self, url, res):
        assert get_domain_name(url) == res

    @pytest.mark.parametrize(
        "url", [
            "http://",
            "",
            "/some/folder/",
            "/some.file",
            "/somefolder/somefile.txt"
        ]
    )
    def test_return_empty(self, url):
        assert get_domain_name(url) == ""

    def test_raise_error_if_not_string(self, no_str):
        with pytest.raises(TypeError) as e:
            get_domain_name(no_str)
        assert type(no_str).__name__ in str(e.value)

    def test_zero_depth(self):
        url = "this.is.a.domain.with.many.sub.domains.de"
        assert get_domain_name(url, depth=0) == ""

    def test_positive_depth(self):
        url = "this.is.a.domain.with.many.sub.domains.de"
        for i in range(1, len(url.split("."))):
            assert len(get_domain_name(url, depth=i).split(".")) == i

    def test_depth_domain(self):
        url = "this.is.a.domain.with.many.sub.domains.de"
        for i in range(1, len(url.split("."))):
            assert get_domain_name(url, depth=i) == \
                   ".".join(url.split(".")[-i:])


class TestUrlInDomain:
    def test_raise_error_if_domain_not_string(self, no_str):
        with pytest.raises(TypeError) as e:
            url_in_domain("", no_str)
        assert type(no_str).__name__ in str(e.value)

    def test_raise_error_if_url_not_string(self, no_str):
        with pytest.raises(TypeError) as e:
            url_in_domain(no_str, "")
        assert type(no_str).__name__ in str(e.value)

    @pytest.mark.parametrize(
        "url", [
            "http://www.google.de",
            "/navigation/index.html",
            "here.html",
        ]
    )
    def test_empty_domain(self, url):
        assert url_in_domain(url, "")

    def test_empty_url_and_domain(self):
        assert not url_in_domain("", "")

    @pytest.mark.parametrize(
        "dirfile", [
            "/just",
            "/just/index.html",
            "/index.html",
            "./index.html",
            "../../index.html"
        ]
    )
    def test_url_is_just_directory_or_file(self, dirfile):
        assert url_in_domain(dirfile, "google.de")

    @pytest.mark.parametrize(
        "url, dom", [
            ("http://maps.google.de/", "google.de"),
            ("http://maps.google.de/", "http://google.de"),
            ("security.heise.de", "heise.de"),
            ("facebook.de", "de"),
            ("google.de", "google.de"),
            ("http://www.google.de/index.html", "http://google.de"),
            ("http://maps.google.de/directory/file.html", "maps.google.de"),
            ("maps.google.de", "http://google.de")
        ]
    )
    def test_positive_examples(self, url, dom):
        assert url_in_domain(url, dom)

    @pytest.mark.parametrize(
        "url, dom", [
            ("maps.google.de", "www.google.de"),
            ("http://www.facebook.de/dir/file.html", "files.facebook.de"),
            ("google.de", "maps.google.de"),
            ("http://domain.com/files/index.html", "sub.domain.com"),
            ("de", "com")
        ]
    )
    def test_negative_examples(self, url, dom):
        assert not url_in_domain(url, dom)

    @pytest.mark.parametrize(
        "url, dom, depth", [
            ("maps.google.de", "www.google.de", 2),
            ("http://www.facebook.de/dir/file.html", "files.facebook.de", 2),
            ("google.de", "maps.google.de", 1),
            ("http://domain.com/files/index.html", "sub.domain.com", 0),
            ("de", "com", 0)
        ]
    )
    def test_positive_depth_examples(self, url, dom, depth):
        assert url_in_domain(url, dom, compare_depth=depth)

    @pytest.mark.parametrize(
        "url, dom, depth", [
            ("maps.google.de", "www.google.de", 3),
            ("http://www.facebook.de/dir/file.html", "files.facebook.de", 4),
            ("google.de", "maps.google.de", 3),
            ("http://domain.com/files/index.html", "sub.domain.com", 3),
            ("de", "com", 1)
        ]
    )
    def test_negative_depth_examples(self, url, dom, depth):
        assert not url_in_domain(url, dom, compare_depth=depth)
