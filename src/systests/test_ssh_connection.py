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
from attacks.ssh import BREACHSSHClient, SSHTarget
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
class TestBREACHSSHConnection:
    def test_connection_client(self, timeout_counter):
        ssh_target = SSHTarget(hostname="192.168.56.101", port=22, username="ssh", password="breach")
        ssh_client = BREACHSSHClient(ssh_target)
        command = "ipconfig"
        list_printer = ListPrinter()

        try_until_counter_reached(
            lambda: ssh_client.exec_command_on_target(command, list_printer),
            timeout_counter,
            exception=(TimeoutError, ConnectionResetError, SSHException, socket.error))

    def test_connection_internet_router(self, timeout_counter):
        ssh_target = SSHTarget(hostname="192.168.56.30", port=222, username="root", password="breach")
        ssh_client = BREACHSSHClient(ssh_target)
        command = "ipconfig"
        list_printer = ListPrinter()

        try_until_counter_reached(
            lambda: ssh_client.exec_command_on_target(command, list_printer),
            timeout_counter,
            exception=(TimeoutError, ConnectionResetError, SSHException, socket.error))

