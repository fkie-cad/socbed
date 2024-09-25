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


from unittest.mock import Mock, patch

import pytest
from attacks import AttackException
from attacks.attack_take_screenshot import TakeScreenshotAttack
from attacks.ssh import SSHTarget


@pytest.fixture()
def attack():
    TakeScreenshotAttack.ssh_client_class = Mock
    attack = TakeScreenshotAttack()
    attack.ssh_client.target = SSHTarget()
    return attack

class TestTakeScreenshotAttack:
    def test_info(self):
        assert TakeScreenshotAttack.info.name == "c2_take_screenshot"

    def test_prepare_attack(self, attack: TakeScreenshotAttack):
        attack.exec_command_on_target = Mock()
        attack._prepare_attack()
        attack.exec_command_on_target.assert_called_with("cd /root; mkdir -p loot; cd loot; rm -f screenshot.jpeg")
    
    @patch('time.sleep', return_value=None)
    def test_respond(self, mock_sleep, attack: TakeScreenshotAttack):
        attack._collect_files = Mock()
        attack.handler = Mock()
        
        attack._respond("test")
        assert not attack._collect_files.called
        assert not attack.handler.shutdown.called
        
        attack._respond("Meterpreter session 1 opened bla bla")
        assert attack._collect_files.called

        attack._respond("Backgrounding session bla bla")
        assert attack.handler.shutdown.called
        attack.handler.shutdown.reset_mock()

        attack._respond("Exploit completed, but no session was created bla bla")
        assert attack.handler.shutdown.called

    def test_collect_files(self, attack: TakeScreenshotAttack):
        attack.handler = Mock()
        attack.screenshot_file = "fancy_screenshot.jpeg"
        attack.handler.stdin = "some stdin"

        attack._collect_files()
        attack.ssh_client.write_lines.assert_called_with("some stdin", ["screenshot -p fancy_screenshot.jpeg", "background"])