#!/usr/bin/env python3

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


import argparse
import json
import logging
import os
from tempfile import gettempdir

from vmcontrol.sessionhandler import SessionHandler, SessionConsole, \
    SessionConfig
from vmcontrol.vmmcontroller import ESXiServer, LoggingVMWareController, LoggingVBoxController, \
    LoggingRemoteVMMController


def setup_logging(level):
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


class Main:
    session_config_class = SessionConfig
    session_state_file = os.path.join(gettempdir(), "sessionstate")
    vmmc_classes = {
        "VirtualBox": LoggingVBoxController,
        "VMWare": LoggingVMWareController,
        "Remote": LoggingRemoteVMMController}
    vmm_config = {"vmm": "VirtualBox"}

    def __init__(self, argv=None):
        self.args = parse_args(argv=argv)
        self.session_config = None
        self.vmm_controller = None
        self.session_handler = None
        self.console = None

    def run(self):
        setup_logging(level=logging.DEBUG if self.args.verbose else logging.INFO)
        self.set_session_config()
        self.set_session_state_file()
        self.set_vmm_controller()
        self.set_session_handler()
        self.set_console()
        if not self.args.command:
            self.console.cmdloop()
        else:
            self.console.onecmd(self.args.command)

    def set_session_config(self):
        if self.args.config_file:
            config_dict = self.parse_json_file(self.args.config_file)
            self.session_config = self.session_config_class(**config_dict)
        else:
            self.session_config = self.session_config_class()

    def set_session_state_file(self):
        if self.args.session_state_file:
            self.session_state_file = self.args.session_state_file

    def set_vmm_controller(self):
        if self.args.vmm_config_file:
            self.vmm_config = self.parse_json_file(self.args.vmm_config_file)
        config = self.vmm_config.copy()
        vmm = config.pop("vmm")
        if vmm == "VirtualBox":
            self.vmm_controller = self.vmmc_classes["VirtualBox"]()
        elif vmm == "VMWare":
            esxi = ESXiServer(**config)
            self.vmm_controller = self.vmmc_classes["VMWare"](esxi_server=esxi)
        elif vmm == "Remote":
            self.vmm_controller = self.vmmc_classes["Remote"](**config)
        else:
            raise Exception("VMM {} not implemented".format(vmm))

    def set_session_handler(self):
        self.session_handler = SessionHandler(
            self.vmm_controller, self.session_config, self.session_state_file)

    def set_console(self):
        self.console = SessionConsole(session_handler=self.session_handler)
        self.console.prompt = "vmconsole > "

    @staticmethod
    def parse_json_file(file):
        with open(file) as f:
            d = json.load(f)
        return d


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="The VMConsole")
    parser.add_argument(
        "-c", dest="command", default=None,
        help="execute command")
    parser.add_argument(
        "-v", dest="verbose", action="store_const", const=True, default=False,
        help="verbose output")
    parser.add_argument(
        "-f", "--session-config", dest="config_file", default=None,
        help="Use custom SessionConfig. Only works for fresh session.")
    parser.add_argument(
        "-s", "--session-state-file", dest="session_state_file", default=None,
        help="Use custom session state file")
    parser.add_argument(
        "-m", "--vmm-config", dest="vmm_config_file", default=None,
        help="Use a VMM config file.")
    args = parser.parse_args(args=argv)
    return args


def main(argv=None):
    Main(argv=argv).run()


if __name__ == '__main__':
    main()
