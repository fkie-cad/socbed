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


import pytest

from vmcontrol.sessionhandler import SessionHandler
from vmcontrol.vmmcontroller import VBoxController

pytestmark = pytest.mark.systest


class TestSessionStartClose:
    def test_start_and_close_session(self):
        self.init_session()
        self.assert_session_not_running()
        self.start_session()
        self.assert_session_running()
        self.close_session()
        self.assert_session_not_running()

    def init_session(self):
        self.session = SessionHandler(VBoxController())
        self.servers = self.session.config.server_vms
        self.client = self.session.config.client_vm
        num_clones = self.session.config.number_of_clones
        self.client_clones = ["{}Clone{}".format(self.client, i + 1) for i in range(num_clones)]

    def assert_session_not_running(self):
        assert self.no_client_clone_exists()
        assert self.no_server_running()

    def start_session(self):
        self.session.start_session()

    def assert_session_running(self):
        assert self.all_client_clones_exist()
        assert self.all_servers_running()

    def close_session(self):
        self.session.close_session()

    def no_client_clone_exists(self):
        vms = self.session.vmmc.get_vms()
        return set(vms).isdisjoint(set(self.client_clones))

    def no_server_running(self):
        return not any([self.session.vmmc.is_running(server) for server in self.servers])

    def all_client_clones_exist(self):
        vms = self.session.vmmc.get_vms()
        return set(self.client_clones).issubset(set(vms))

    def all_servers_running(self):
        return all([self.session.vmmc.is_running(server) for server in self.servers])
