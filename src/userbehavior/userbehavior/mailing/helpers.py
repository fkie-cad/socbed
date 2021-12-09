#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import re
import subprocess
import sys

logger = logging.getLogger(__name__)


def get_urls_in_text(text):
    # regex for urls
    regex = re.compile("((?P<protocol>https?://)?(([\da-z.-]+)\.([a-z\.]{2,6})([/\w.-]*)*/?))")
    urls = list()
    for match in regex.finditer(text):
        if match.group("protocol") is None:
            urls.append("http://" + match.group())
        else:
            urls.append(match.group())

    return urls


def get_urls_in_html(html):
    # regex for hrefs in a-tags
    regex = re.compile("<[aA] [^>]*(href|HREF)=['\"](?P<href>[^'\"]*)['\"]")
    urls = list()
    for match in regex.finditer(html):
        url = match.group("href")
        if url.startswith("HTTP:") or url.startswith("HTTPS:"):
            protocol, rest = url.split(":", maxsplit=1)
            url = ":".join([protocol.lower(), rest])
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "http://" + url
        urls.append(url)
    return urls


def open_file(file):
    """ Lets os open file with standard program. Works for Linux and Windows."""

    logger.debug("Make OS open " + str(file))
    if sys.platform.startswith("linux"):
        subprocess.call(["xdg-open", file])
    elif sys.platform.startswith("win"):
        os.startfile(file)
    else:
        print("No Execution: Could not guess OS...")


def open_url(url):
    """ Lets os open url with standard browser. Works for Linux and Windows. """

    logger.debug("Make OS Browser open " + str(url))
    if sys.platform.startswith("linux"):
        subprocess.call(["xdg-open", url])
    elif sys.platform.startswith("win"):
        os.startfile(url)
    else:
        print("No Execution: Could not guess OS...")
