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

import time

import pytest
from paramiko import SSHException
import socket

from attacks.printer import ListPrinter
from attacks.ssh import SSHTarget, BREACHSSHClient
from systests.helpers import try_until_counter_reached
from vmcontrol.sessionhandler import SessionHandler
from vmcontrol.vmmcontroller import VBoxController

MAX_RUNTIME = 10 * 60  # Ten minutes
pytestmark = pytest.mark.systest


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
class TestClientManagementIPs:
    client_ids = [1, 2, 3]

    class DummyException(Exception):
        pass

    @pytest.mark.parametrize("client_id", client_ids, ids=lambda x: "Client {}".format(x))
    def test_client_management_ip(self, client_id, timeout_counter):
        command = "ipconfig /all"
        success_indicator = \
            "   Physical Address. . . . . . . . . : 00-50-56-00-{num_clients}-{client_id}\r".format(
                num_clients="{:02X}".format(len(self.client_ids)),
                client_id="{:02X}".format(client_id))
        try_until_counter_reached(
            lambda: self.exec_command_and_get_output_list(client_id, command, timeout_counter),
            timeout_counter,
            exception=self.DummyException,
            assertion_func=lambda x: (success_indicator in x))

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
