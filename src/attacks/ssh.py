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


import copy
import re
from types import SimpleNamespace

import paramiko
from attacks.util import print_command

class SSHTarget(SimpleNamespace):
    name = ""
    hostname = ""
    port = 22
    username = "root"
    password = "breach"


class SSHTargets(SimpleNamespace):
    attacker = SSHTarget(name="Attacker", hostname="192.168.56.31")
    company_router = SSHTarget(name="Company Router", hostname="192.168.56.10", port=222)
    dmz_server = SSHTarget(name="DMZ Server", hostname="192.168.56.20")
    log_server = SSHTarget(name="Log Server", hostname="192.168.56.12")
    internal_server = SSHTarget(name="Internal Server", hostname="192.168.56.11")
    internet_router = SSHTarget(name="Internet Router", hostname="192.168.56.30", port=222)
    client_1 = SSHTarget(name="Client 1", hostname="192.168.56.101", username="ssh")


class BREACHSSHClient(paramiko.SSHClient):
    default_target = SSHTargets.attacker
    channel_timeout = 300
    connect_timeout = 60
    stdin = None

    def __init__(self, target=None):
        super().__init__()
        self.target = target or copy.deepcopy(self.default_target)
        self._configure()

    def _configure(self):
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def exec_command_on_target(self, command, printer):
        self.connect_to_target()
        print_command(command)
        command = self.wrap_command(command)
        stdin, stdout, stderr = self.exec_command(command, timeout=self.channel_timeout, get_pty=True)
        self.stdin = stdin
        self.print_output(stdout, printer)
        self.print_output(stderr, printer)
        self.close()

    def exec_commands_on_target(self, commands, printer):
        self.connect_to_target()
        for command in commands:
            print_command(command)
            command = self.wrap_command(command)
            stdin, stdout, stderr = self.exec_command(command, timeout=self.channel_timeout, get_pty=True)
            self.stdin = stdin
            self.print_output(stdout, printer)
            self.print_output(stderr, printer)
        self.close()

    def connect_to_target(self):
        target = self.target
        super().connect(target.hostname, target.port, target.username, target.password,
                        look_for_keys=False, allow_agent=False, timeout=self.connect_timeout,
                        banner_timeout=self.connect_timeout, auth_timeout=self.connect_timeout)

    def set_envs(self, command):
        if "windows" in self._transport.remote_version.lower():
            return command
        if command.startswith("sudo"):
            return command.replace("sudo", f"sudo {self.env_str}")
        return f"{self.env_str} {command}"

    def _get_grc_string(self) -> str:
        if not self.exec_command("which grc", timeout=2)[0].channel.recv_exit_status():
            return "grc --colour=on"
        return ""

    def wrap_command(self, command: str) -> str:
        if "windows" in self._transport.remote_version.lower():
            return command

        env_str: str = "PYTHONUNBUFFERED=1"
        command_prefix: list[str] = [env_str, self._get_grc_string()]

        command_prefix_str = " ".join(x for x in command_prefix if x)

        if command.startswith("sudo"):
            return command.replace("sudo", f"sudo {command_prefix_str}")
        return f"{command_prefix_str} {command}"


    def print_output(self, msg_file, printer):
        if "windows" in self._transport.remote_version.lower():
            self.print_windows_output(msg_file, printer)
        else:
            while not msg_file.channel.exit_status_ready() or msg_file.channel.recv_ready():
                try:
                    printer.print(msg_file.read(1).decode())
                except UnicodeDecodeError:
                    pass

    @staticmethod
    def print_windows_output(msg_file, printer):
        # Removes certain ANSI escape codes (J, m, H) to prevent the printed console output from being malformed
        ansi_escape = re.compile(r'\x1b\[(?:[0-?]*[JmH])')
        while not msg_file.channel.exit_status_ready() or msg_file.channel.recv_ready():
            printer.print(ansi_escape.sub("", msg_file.readline()))

    @staticmethod
    def write_lines(stdin, lines):
        for line in lines:
            stdin.write(line + "\n")
