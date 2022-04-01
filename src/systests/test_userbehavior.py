# Copyright 2016-2021 Fraunhofer FKIE
#
# This file is part of SOCBED.
#
# SOCBED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SOCBED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SOCBED. If not, see <http://www.gnu.org/licenses/>.

import json
import os
import re
import time
from http.client import HTTPConnection, CannotSendRequest
from collections import namedtuple

import pytest
import requests

from attacks.ssh import SSHTargets
from systests.helpers import try_until_counter_reached
from vmcontrol.sessionhandler import SessionHandler
from vmcontrol.vmmcontroller import VBoxController

MAX_RUNTIME = 10 * 60  # Ten minutes
pytestmark = [pytest.mark.systest]


@pytest.fixture(scope="module")
def session():
    sh = SessionHandler(VBoxController())
    sh.start_session()
    yield
    sh.close_session()


@pytest.fixture(scope="module")
def timeout_counter():
    return time.perf_counter() + MAX_RUNTIME


@pytest.mark.usefixtures("session", "timeout_counter")
class TestUserbehavior:
    log_server = SSHTargets.log_server

    def test_browsing(self, timeout_counter):
        elasticsearch_query_values = namedtuple(
            "elasticsearch_query_values", "value search_keyword timestamp_key")
        called_website = "www.general-anzeiger-bonn.de"
        es_query = elasticsearch_query_values(called_website, "dns.question.name", "@timestamp")
        self.check_remote_log_format(es_query, timeout_counter)

    def check_remote_log_format(self, es_query, timeout_counter):
        try_until_counter_reached(
            lambda: self.query_elasticsearch(es_query, timeout_counter),
            timeout_counter,
            exception=IndexError,
            assertion_func=lambda x: self.check_elasticsearch_response(x, es_query))

    def is_iso8601_timestamp(self, timestamp):
        iso8601_a = re.compile(
            r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d.\d\d\d\d\d\d[+-]\d\d:\d\d")
        iso8601_b = re.compile(
            r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d.\d\d\dZ")
        return (iso8601_a.match(timestamp) is not None
                or iso8601_b.match(timestamp) is not None)

    def test_is_iso8601_timestamp(self):
        valid_timestamps = [
            "2017-06-01T15:45:15.495964+02:00"
            "2021-02-13T05:50:01.109Z"]
        invalid_timestamps = [
            "May 31 16:03:00",
            "May",
            ""]
        assert all(
            self.is_iso8601_timestamp(valid_timestamp)
            for valid_timestamp in valid_timestamps)
        assert not any(
            self.is_iso8601_timestamp(invalid_timestamp)
            for invalid_timestamp in invalid_timestamps)

    def query_elasticsearch(self, es_query, timeout_counter, conn=-1):
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        try_until_counter_reached(
            lambda: self.check_elastic_status(),
            timeout_counter,
            assertion_func=lambda response: b"\"status\":\"yellow\"" in response.content
        )
        conn = HTTPConnection(f"{self.log_server.hostname}:9200")
        search_query = json.dumps(
            {"query": {"constant_score": {"filter": {"term": {
                es_query.search_keyword: es_query.value}}}}})
        try_until_counter_reached(
            lambda: conn.request(
                method="POST", url="/_search", body=str(search_query), headers=headers),
            timeout_counter,
            exception=(TimeoutError, ConnectionRefusedError, CannotSendRequest))
        return str(conn.getresponse().read(), 'utf-8')

    def check_elasticsearch_response(self, response, es_query):
        print(response)
        timestamp = json.loads(response)["hits"]["hits"][0]["_source"][es_query.timestamp_key]
        return self.is_iso8601_timestamp(timestamp)

    def check_elastic_status(self):
        response = requests.get(f"http://{self.log_server.hostname}:9200/_cluster/health")
        return response
