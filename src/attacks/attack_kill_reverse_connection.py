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


from attacks import Attack, AttackInfo, AttackOptions


class KillReverseConnectionAttackOptions(AttackOptions):
    host = "Client management IP address"

    def _set_defaults(self):
        self.host = "192.168.56.101"


class KillReverseConnectionAttack(Attack):
    info = AttackInfo(
        name="disinfect_client",
        description="Kills exploited Adobe Reader and Firefox instances")
    options_class = KillReverseConnectionAttackOptions

    def run(self):
        self._set_target()
        self._reset_reverse_connection()

    def _set_target(self):
        self.ssh_client.target.hostname = self.options.host
        self.ssh_client.target.username = "ssh"

    def _reset_reverse_connection(self):
    	things_to_kill = [
    		"plugin-container.exe",
    		"firefox.exe",
    		"meterpreter_bin_tcp.exe",
    		"%%Bank-of-Nuthington.exe",
    		]
    	for process in things_to_kill:
    		cmd = (
    			'cmd /c "wmic process where '
            	f'\"Description like \'{process}\'\" call terminate" '
            	'&& echo Successful wmic execution\"')
    		with self.check_printed("Successful wmic execution"):
    			self.exec_command_on_target(cmd)
