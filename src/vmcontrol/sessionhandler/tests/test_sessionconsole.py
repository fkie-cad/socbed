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


from unittest.mock import Mock

import pytest

from vmcontrol.sessionhandler import SessionConsole


class MockSessionHandler:
    def __init__(self):
        self.start_session = Mock()
        self.close_session = Mock()
        self.vmmc = Mock()


@pytest.fixture()
def sc():
    return SessionConsole(MockSessionHandler())


class TestTBFVMControlShell:
    def test_start_session(self, sc: SessionConsole):
        sc.do_start_session("")
        assert sc.session_handler.start_session.called

    def test_close_session(self, sc: SessionConsole):
        sc.do_close_session("")
        assert sc.session_handler.close_session.called
