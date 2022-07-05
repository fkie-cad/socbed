#!/usr/bin/env python3

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


"""
This script configures the client machine for the BREACH framework.
"""

import argparse
import datetime
import logging
import os
import re
import socket
import time
from collections import namedtuple
from subprocess import PIPE, run, CalledProcessError

logger = logging.getLogger(__name__)


class ISOFormatter(logging.Formatter):
    _tz_fix = re.compile(r"([+-]\d{2})(\d{2})$")

    def format(self, record):
        self._add_isotime_to_record(record)
        return super().format(record)

    @classmethod
    def _add_isotime_to_record(cls, record):
        isotime = datetime.datetime.fromtimestamp(record.created).isoformat()
        tz = cls._tz_fix.match(time.strftime("%z"))
        if time.timezone and tz:
            offset_hrs, offset_min = tz.groups()
            isotime += "{0}:{1}".format(offset_hrs, offset_min)
        else:
            isotime += "Z"
        record.__dict__["isotime"] = isotime


def setup_logging():
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename="init_tbf_client.log")
    fmt = "%(isotime)s %(name)s %(levelname)s %(message)s"
    handler.setFormatter(fmt=ISOFormatter(fmt=fmt))
    logger.addHandler(hdlr=handler)


class Main:
    client_dir = "C:\\BREACH"
    management_ip_trunc = "192.168.56."
    powershell_logfile = "powershell_stdout.log"

    def __init__(self):
        self.args = None
        self.client_id = None
        self.management_if = None
        self.management_ip = None

    def parse_args(self, argv=None):
        logger.debug("Parse arguments")
        parser = argparse.ArgumentParser(
            description="Sets the management IP and runs the userbehavior according to TBF.")
        args = parser.parse_args(argv)
        return args

    def run(self, argv=None):
        logger.info("Initalization script for client started!")
        self.args = self.parse_args(argv=argv)
        self.get_network_parameters()
        if self.is_configured_faulty():
            self.leave_domain()
            self.reset_auto_logon()
            self.do_first_setup_phase()
        elif self.management_ip_is_wrong():
            self.restart()
        elif self.is_first_setup_phase_required():
            self.do_first_setup_phase()
        elif self.is_second_setup_phase_required():
            self.do_second_setup_phase()

    def get_network_parameters(self):
        self.management_if = self.get_management_interface()
        self.client_id = self.management_if.mac % 0x100
        self.management_ip = self.management_ip_trunc + str(100 + self.client_id)

    def is_configured_faulty(self):
        return not socket.gethostname() == "CLIENT" and not socket.gethostname().endswith(str(self.client_id))

    def management_ip_is_wrong(self):
        if socket.gethostname() == "CLIENT":
            return False
        if "Duplicate" in self.get_ipconfig():
            logger.info("Duplicate IP detected - restarting since other clones should have fixed their wrong IP"
                    .format(if_name=self.management_if.name, ip=self.management_ip))
            return True

    def is_first_setup_phase_required(self):
        return os.environ["USERNAME"] == "setup" and os.environ["COMPUTERNAME"] == "CLIENT"

    def do_first_setup_phase(self):
        self.set_management_ip()
        self.set_computer_name()

    def is_second_setup_phase_required(self):
        return os.environ["USERNAME"] == "setup" and os.environ["COMPUTERNAME"] != "CLIENT"

    def do_second_setup_phase(self):
        self.set_auto_logon()
        self.join_domain()

    def set_management_ip(self):
        logger.info("Setting Management IP in '{if_name}' to {ip}"
                    .format(if_name=self.management_if.name, ip=self.management_ip))
        powershell_script = [
            "$cmd_man_ip = \"netsh.exe interface ip set address name='{if_name}' static {ip}\""
                .format(if_name=self.management_if.name, ip=self.management_ip),
            "Start-Process powershell.exe -Wait -ArgumentList $cmd_man_ip -Verb RunAs"] 
        self.powershell_execute(powershell_script)

    def set_computer_name(self):
        logger.info("Setting computer name - will reboot if successful")
        powershell_script = [
            "$new_name = 'CLIENT{}'".format(self.client_id),
            "Rename-Computer -NewName $new_name -Restart -Force"]
        self.powershell_execute(powershell_script)

    def set_auto_logon(self):
        logger.info("Setting automatic logon")
        powershell_script = [
            "$reg_path = 'HKLM:\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon'",
            "Set-ItemProperty -Path $reg_path -Name 'AutoAdminLogon' -Value '1'",
            "Set-ItemProperty -Path $reg_path -Name 'DefaultDomainName' -Value 'BREACH'",
            "Set-ItemProperty -Path $reg_path -Name 'DefaultPassword' -Value 'breach'",
            "Set-ItemProperty -Path $reg_path -Name 'DefaultUserName' -Value 'client{}'".format(
                self.client_id)]
        self.powershell_execute(powershell_script)


    def reset_auto_logon(self):
        logger.info("Resetting automatic logon")
        powershell_script = [
            "$reg_path = 'HKLM:\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon'",
            "Set-ItemProperty -Path $reg_path -Name 'AutoAdminLogon' -Value '1'",
            "Remove-ItemProperty -Path $reg_path -Name 'DefaultDomainName'",
            "Set-ItemProperty -Path $reg_path -Name 'DefaultPassword' -Value 'breach'",
            "Set-ItemProperty -Path $reg_path -Name 'DefaultUserName' -Value 'setup'"]
        self.powershell_execute(powershell_script)

    def join_domain(self):
        logger.info("Joining domain - will reboot if successful")
        powershell_script = [
            "$admin_secpwd = ConvertTo-SecureString 'breach' -AsPlainText -Force",
            "$credential = New-Object -TypeName System.Management.Automation.PSCredential "
            "-ArgumentList 'BREACH\\Administrator', $admin_secpwd",
            "Add-Computer -Credential $credential -DomainName 'BREACH' -Restart -Force"]
        self.powershell_execute(powershell_script)

    def leave_domain(self):
        logger.info("Leaving domain - will not reboot if successful")
        powershell_script = [
            "$admin_secpwd = ConvertTo-SecureString 'breach' -AsPlainText -Force",
            "$credential = New-Object -TypeName System.Management.Automation.PSCredential "
            "-ArgumentList 'BREACH\\Administrator', $admin_secpwd",
            "Remove-Computer -Credential $credential -Force"]
        self.powershell_execute(powershell_script)

    def restart(self):
        powershell_script = [
            "Restart-Computer"]
        self.powershell_execute(powershell_script)

    def get_management_interface(self):
        interfaces = self.get_interfaces()
        for interface in interfaces:
            if (interface.mac % 0x10000) // 0x100 > 0:
                return interface
        else:
            raise Exception("Could not find management interface in interfaces")

    def get_interfaces(self):
        regex = re.compile(
            r"(Ethernet adapter )(?P<ifname>[^\:]*):\n\n[\s\S]*?"
            r"(Physical Address[. :]*)(?P<MAC>([0-9A-F]{2}[:-]){5}([0-9A-F]{2}))[\s\S]*?"
            r"(IPv4 Address[. :]*)(?P<IP>((\d{1,3}.){3}\d{1,3}))[\s\S]*?\n")
        matches = [match for match in regex.finditer(self.get_ipconfig())]
        interfaces = [
            NetworkInterface(
                name=m.group("ifname"),
                mac=int(m.group("MAC").replace("-", ""), 16),
                ip=m.group("IP"))
            for m in matches]
        return interfaces

    def get_ipconfig(self):
        return self.execute(["ipconfig", "/all"])

    def powershell_execute(self, powershell_script):
        script = "; ".join(powershell_script)
        success = False
        while not success:
            try:
                self.execute(["powershell", script])
                success = True
            except CalledProcessError as e:
                logger.error("CalledProcessError, see {} for details".format(self.powershell_logfile))
                with open(self.powershell_logfile, "a") as f:
                    f.write(script + "\n\n" + e.stdout + "\n\n")
                time.sleep(1)

    @staticmethod
    def execute(call_vector):
        return run(
            call_vector, stdout=PIPE, universal_newlines=True,
            timeout=300, check=True).stdout


NetworkInterface = namedtuple("NetworkInterface", ["name", "mac", "ip"])

if __name__ == '__main__':
    setup_logging()
    Main().run()
