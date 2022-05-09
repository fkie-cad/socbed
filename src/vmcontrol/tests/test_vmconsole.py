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
from unittest.mock import Mock

import pytest

from vmcontrol.vmconsole import Main


class MainForTesting(Main):
    vmmc_classes = {name: Mock() for name, _ in Main.vmmc_classes.items()}
    parse_json_file = Mock(return_value=dict())


class TestMain:
    def test_init(self):
        MainForTesting([])

    def test_set_session_config(self):
        m = MainForTesting(["-f", "some_file"])
        m.parse_json_file = Mock(return_value={"client_vm": "SpecialClient"})
        m.set_session_config()
        assert m.session_config.client_vm == "SpecialClient"

    def test_set_session_state_file(self):
        m = MainForTesting(["-s", "my_state_file"])
        m.set_session_state_file()
        assert m.session_state_file == "my_state_file"

    @pytest.mark.parametrize("vmm", ["VMWare", "VirtualBox", "Remote"])
    def test_set_vmm_controller(self, vmm):
        m = MainForTesting(["--vmm-config", "some_file"])
        m.parse_json_file = Mock(return_value={"vmm": vmm})
        m.set_vmm_controller()
        assert m.vmmc_classes[vmm].called
