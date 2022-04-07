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

from attacks import AttackException
from attacks.attack_flashdrive_exfiltration import FlashdriveExfiltrationAttack
from attacks.ssh import SSHTarget


@pytest.fixture()
def attack():
    FlashdriveExfiltrationAttack.ssh_client_class = Mock
    attack = FlashdriveExfiltrationAttack()
    attack.ssh_client.target = SSHTarget()
    return attack


class TestFlashdriveExfiltrationAttack:
    def test_set_target(self, attack: FlashdriveExfiltrationAttack):
        attack._set_target()
        assert attack.ssh_client.target.hostname == "192.168.56.101"
        assert attack.ssh_client.target.username == "ssh"
        assert attack.ssh_client.target.password == "breach"
        assert attack.ssh_client.target.port == 22

    def test_raise_exception_bad_output(self, attack: FlashdriveExfiltrationAttack):
        attack.exec_commands_on_target = lambda _: attack.printer.print("Bad output")
        with pytest.raises(AttackException):
            attack.run()

    def test_no_exception_good_output(self, attack: FlashdriveExfiltrationAttack):
        indicator = "File(s) copied"
        attack.exec_commands_on_target = lambda _: attack.printer.print(indicator)
        attack.run()
