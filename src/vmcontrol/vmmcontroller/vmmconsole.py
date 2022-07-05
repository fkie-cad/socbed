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


import cmd
import shlex
from contextlib import suppress

from vmcontrol.vmmcontroller.vmmcontroller import VMMController, VMMControllerException


class VMMConsole(cmd.Cmd):
    # intro = ""
    prompt = 'VMMConsole> '

    def __init__(self, vmm_controller: VMMController):
        super().__init__()
        self.vmmc = vmm_controller

    def do_get_vms(self, arg):
        with print_suppress(VMMControllerException):
            print(self.vmmc.get_vms())

    def do_start(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            self.vmmc.start(vm=args[0])

    def do_poweroff(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            self.vmmc.poweroff(vm=args[0])

    def do_delete(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            self.vmmc.delete(vm=args[0])

    def do_is_running(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            print(self.vmmc.is_running(vm=args[0]))

    def do_get_macs(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            print(self.vmmc.get_macs(vm=args[0]))

    def do_get_mac(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            if len(args) > 1:
                print(self.vmmc.get_mac(vm=args[0], if_id=int(args[1])))
            else:
                print(self.vmmc.get_mac(vm=args[0]))

    def do_set_mac(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            if len(args) > 2:
                self.vmmc.set_mac(vm=args[0], mac=int(args[1]), if_id=int(args[2]))
            else:
                self.vmmc.set_mac(vm=args[0], mac=int(args[1]))

    def do_get_snapshots(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            print(self.vmmc.get_snapshots(vm=args[0]))

    def do_create_snapshot(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            self.vmmc.create_snapshot(vm=args[0], snapshot=args[1])

    def do_delete_snapshot(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            self.vmmc.delete_snapshot(vm=args[0], snapshot=args[1])

    def do_restore_snapshot(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            self.vmmc.restore_snapshot(vm=args[0], snapshot=args[1])

    def do_clone(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            self.vmmc.clone(vm=args[0], snapshot=args[1], clone=args[2])

    def do_set_credentials(self, arg):
        args = Parser().parse(arg)
        with print_suppress(VMMControllerException):
            self.vmmc.set_credentials(vm=args[0], user=args[1], password=args[2], domain=args[3])

    def do_exit(self, arg):
        return True


class print_suppress(suppress):
    def __exit__(self, exctype, excinst, exctb):
        exception_is_suppressed = super().__exit__(exctype, excinst, exctb)
        if exception_is_suppressed:
            print("*** {type}: {e}\n".format(type=exctype.__name__, e=excinst))
        return exception_is_suppressed


class Parser:
    def parse(self, arg_string):
        return shlex.split(arg_string)
