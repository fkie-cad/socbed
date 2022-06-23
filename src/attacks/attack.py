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


import re
import socket
from contextlib import contextmanager
from types import SimpleNamespace
from signal import SIGINT, default_int_handler, signal

import paramiko
from attacks.printer import Printer, ListPrinter, MultiPrinter
from attacks.ssh import BREACHSSHClient


class AttackInfo(SimpleNamespace):
    name = "<attack_info>"
    description = "<attack_description>"


class AttackOptions(SimpleNamespace):
    def __init__(self, **kwargs):
        self._set_options_to_none()
        self._set_defaults()
        super().__init__(**kwargs)

    def _set_options_to_none(self):
        default_options = dict.fromkeys(self._options(), None)
        self.__dict__.update(default_options)

    @classmethod
    def _options(cls):
        return [att for att in dir(cls) if not att.startswith("_")]

    def _set_defaults(self):
        pass


class AttackException(Exception):
    pass


class Attack:
    info = AttackInfo()
    options_class = AttackOptions
    printer_class = Printer
    ssh_client_class = BREACHSSHClient

    def __init__(self, options=None, printer=None, ssh_client=None):
        self.options = options or self.options_class()
        self.printer = printer or self.printer_class()
        self.ssh_client = ssh_client or self.ssh_client_class()

    def print(self, msg):
        self.printer.print(msg)

    def run(self):
        raise NotImplementedError()

    @contextmanager
    def wrap_ssh_exceptions(self):
        signal(SIGINT, self.interrupt_handler)
        try:
            yield
        except socket.timeout:
            print(f"Timeout after {self.ssh_client.channel_timeout}s")
            self.interrupt_handler(None, None)
        except (paramiko.SSHException, socket.error) as err:
            self.interrupt_handler(None, None)
            raise AttackException(err) from err
        finally:
            signal(SIGINT, default_int_handler)

    def exec_command_on_target(self, command):
        with self.wrap_ssh_exceptions():
            self.ssh_client.exec_command_on_target(command, self.printer)

    def exec_commands_on_target(self, commands):
        with self.wrap_ssh_exceptions():
            self.ssh_client.exec_commands_on_target(commands, self.printer)

    def connect_to_target(self):
        with self.wrap_ssh_exceptions():
            self.ssh_client.connect_to_target()

    def interrupt_handler(self, _signum, _frame):
        if hasattr(self, "handler"):
            print("\rStopping...")
            self.handler.shutdown()
        elif hasattr(self.ssh_client, "stdin"):
            print("\rStopping...")
            self.ssh_client.stdin.channel.send("\x03")
        else:
            print("Can not cancel command")


    @contextmanager
    def check_printed(self, indicator):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        lp = ListPrinter()
        old_printer = self.printer
        self.printer = MultiPrinter(printers=[lp, old_printer])
        yield
        self.printer = old_printer
        if not any(indicator in ansi_escape.sub("", line) for line in "".join(lp.printed).split("\n")):
            raise AttackException(
                "Attack failed: Indicator \"{}\" not found in output".format(indicator))
