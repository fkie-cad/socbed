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


class FlashdriveExfiltrationAttackOptions(AttackOptions):
    rhost = "Target client host or IP address"
    rdir = "Directory on target host"

    def _set_defaults(self):
        self.rhost = "192.168.56.101"
        self.rdir = "C:\\BREACH\\important-files"


class FlashdriveExfiltrationAttack(Attack):
    info = AttackInfo(
        name="misc_exfiltration",
        description="Copies files from a client to a removable drive")
    options_class = FlashdriveExfiltrationAttackOptions

    def run(self):
        self._set_target()
        with self.check_printed("File(s) copied"):
            self.exec_commands_on_target(self._copy_files_to_flashdrive_commands())

    def _set_target(self):
        self.ssh_client.target.hostname = self.options.rhost
        self.ssh_client.target.username = "ssh"

    def _copy_files_to_flashdrive_commands(self):
        return [
            "imdisk -a -s 64M -m L: -p \"/fs:ntfs /q /y\"",
            "xcopy /E \"{dir}\" L:".format(dir=self.options.rdir),
            "imdisk -D -m L:"]
