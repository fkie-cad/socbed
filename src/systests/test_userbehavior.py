# Copyright 2016-2022 Fraunhofer FKIE
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
import re
import socket
import time
from http.client import HTTPConnection
from collections import namedtuple
from paramiko import SSHException

import pytest

from attacks.printer import ListPrinter
from attacks.ssh import BREACHSSHClient, SSHTarget, SSHTargets
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
    client_ids = [1, 2, 3]
    log_server = SSHTargets.log_server

    def test_browsing(self, timeout_counter):
        elasticsearch_query_values = namedtuple(
            "elasticsearch_query_values", "value search_keyword timestamp_key")
        called_website = "www.general-anzeiger-bonn.de"
        es_query = elasticsearch_query_values(called_website, "dns.question.name", "@timestamp")
        self.check_remote_log_format(es_query, timeout_counter)

    def check_remote_log_format(self, es_query, timeout_counter):
        try_until_counter_reached(
            lambda: self.query_elasticsearch(es_query),
            timeout_counter,
            exception=(IndexError, OSError, KeyError),
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

    def query_elasticsearch(self, es_query):
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        conn = HTTPConnection(f"{self.log_server.hostname}:9200")
        search_query = json.dumps(
            {"query": {"constant_score": {"filter": {"term": {
                es_query.search_keyword: es_query.value}}}}})
        conn.request(
                method="POST", url="/_search", body=str(search_query), headers=headers)
        return str(conn.getresponse().read(), 'utf-8')

    def check_elasticsearch_response(self, response, es_query):
        print(response)
        timestamp = json.loads(response)["hits"]["hits"][0]["_source"][es_query.timestamp_key]
        return self.is_iso8601_timestamp(timestamp)

    @pytest.mark.parametrize("client_id", client_ids, ids=lambda x: "Client {}".format(x))
    def test_client_userbehavior_is_running(self, client_id, timeout_counter):
        command = "powershell -c \"Get-WmiObject Win32_process\""
        success_indicator = "CommandLine                : python C:\\BREACH\\userbehavior\\run.py\r\n"
        try_until_counter_reached(
            lambda: self.exec_command_and_get_output_list(client_id, command, timeout_counter),
            timeout_counter,
            assertion_func=lambda x: (success_indicator in x)
        )

    def exec_command_and_get_output_list(self, client_id, command, timeout_counter):
        client_ip = "192.168.56.{}".format(100 + client_id)
        client = SSHTarget(hostname=client_ip, username="ssh")
        ssh_client = BREACHSSHClient(target=client)
        list_printer = ListPrinter()
        try_until_counter_reached(
            lambda: ssh_client.exec_command_on_target(command, list_printer),
            timeout_counter,
            exception=(TimeoutError, ConnectionResetError, SSHException, socket.error))
        return list_printer.printed
