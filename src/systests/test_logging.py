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
import re
import time
import uuid
from http.client import HTTPConnection, CannotSendRequest
from collections import namedtuple

import pytest
from paramiko import SSHException
import socket

from attacks.printer import ListPrinter
from attacks.ssh import BREACHSSHClient, SSHTargets
from systests.helpers import try_until_counter_reached
from vmcontrol.sessionhandler import SessionHandler
from vmcontrol.vmmcontroller import VBoxController

MAX_RUNTIME = 10 * 60  # Ten minutes
pytestmark = [pytest.mark.systest, pytest.mark.longtest]

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
class TestLogging:
    machines = [
        SSHTargets.internet_router,
        SSHTargets.attacker,
        SSHTargets.company_router,
        SSHTargets.log_server,
        SSHTargets.internal_server,
        SSHTargets.dmz_server,
        SSHTargets.client_1]
    forwarding_machines = [
        SSHTargets.company_router,
        SSHTargets.internal_server,
        SSHTargets.dmz_server,
        SSHTargets.client_1]
    windows_machines = [
        SSHTargets.client_1]
    packetbeat_machines = [
        SSHTargets.company_router]
    log_server = SSHTargets.log_server

    @pytest.mark.parametrize("machine", machines, ids=lambda m: m.name)
    def test_local_and_remote_logging(self, machine, timeout_counter):
        elasticsearch_query_values = namedtuple(
            "elasticsearch_query_values", "token search_keyword timestamp_key")
        if machine in self.windows_machines:
            es_query = elasticsearch_query_values(self.unique_token(), "message", "@timestamp")
            self.generate_windows_log(machine, es_query.token, timeout_counter)
        else:
            es_query = elasticsearch_query_values(self.unique_token(), "message", "timestamp")
            self.generate_linux_log(machine, es_query.token, timeout_counter)
            self.check_local_log_format(machine, es_query.token, timeout_counter)
        if machine in self.forwarding_machines:
            self.check_remote_log_format(es_query, timeout_counter)
        if machine in self.packetbeat_machines:
            es_query = elasticsearch_query_values(self.unique_token(), "resource", "@timestamp")
            self.generate_linux_packet_log(machine, es_query.token, timeout_counter)
            self.check_remote_log_format(es_query, timeout_counter)

    def unique_token(self):
        return str(uuid.uuid4()).replace("-", "")

    def generate_windows_log(self, machine, token, timeout_counter):
        command = f"powershell -command \"echo {token}\""
        self.exec_command_and_get_output_list(machine, command, timeout_counter)

    def generate_linux_log(self, machine, token, timeout_counter):
        command = f"logger {token}"
        self.exec_command_and_get_output_list(machine, command, timeout_counter)

    def generate_linux_packet_log(self, machine, token, timeout_counter):
        command = f"ping {token}"
        self.exec_command_and_get_output_list(machine, command, timeout_counter)

    def check_local_log_format(self, machine, token, timeout_counter):
        command = f"grep --text {token} /var/log/syslog"
        try_until_counter_reached(
            lambda: self.exec_command_and_get_output_list(machine, command, timeout_counter),
            timeout_counter,
            assertion_func=lambda x: self.is_iso8601_timestamp(x[0].split()[0]))

    def check_remote_log_format(self, es_query, timeout_counter):
        try_until_counter_reached(
            lambda: self.query_elasticsearch(es_query, timeout_counter),
            timeout_counter,
            exception=IndexError,
            assertion_func=lambda x: self.check_elasticsearch_response(x, es_query))

    def exec_command_and_get_output_list(self, machine, command, timeout_counter):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        try_until_counter_reached(
            lambda: ssh_client.exec_command_on_target(command, list_printer),
            timeout_counter,
            exception=(TimeoutError, ConnectionResetError, SSHException, socket.error))
        return list_printer.printed

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

    def query_elasticsearch(self, es_query, timeout_counter):
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        conn = HTTPConnection(f"{self.log_server.hostname}:9200")
        search_query = json.dumps(
            {"query": {"constant_score": {"filter": {"term": {
                es_query.search_keyword: es_query.token}}}}})
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
