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
from attacks.attack_set_autostart import SetAutostartAttack
from attacks.ssh import SSHTarget


@pytest.fixture()
def attack():
    SetAutostartAttack.ssh_client_class = Mock
    attack = SetAutostartAttack()
    attack.ssh_client.target = SSHTarget()
    return attack


class TestSetAutostartAttack:
    def test_info(self):
        assert SetAutostartAttack.info.name == "misc_set_autostart"

    def test_set_target(self, attack: SetAutostartAttack):
        attack._set_target()
        assert attack.ssh_client.target.hostname == "192.168.56.101"
        assert attack.ssh_client.target.username == "ssh"
        assert attack.ssh_client.target.password == "breach"
        assert attack.ssh_client.target.port == 22

    def test_raise_exception_bad_output(self, attack: SetAutostartAttack):
        attack.exec_commands_on_target = lambda _: attack.printer.print("Failure.")
        with pytest.raises(AttackException):
            attack.run()

    def test_autostart_command(self, attack: SetAutostartAttack):
        command = (
            "REG ADD HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run "
            "/v \"Meterpreter Bind TCP\" /t REG_SZ /d \"meterpreter_bind_tcp.exe\" /f")
        assert attack._autostart_command() == command

    def test_no_exception_good_output(self, attack: SetAutostartAttack):
        indicator = "The operation completed successfully."
        attack.exec_commands_on_target = lambda _: attack.printer.print(indicator)
        attack.run()
