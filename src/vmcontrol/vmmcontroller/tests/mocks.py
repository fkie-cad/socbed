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


from vmcontrol.vmmcontroller import VMMController, VMMControllerException


def mock_print_decorator():
    def wrap(method):
        def printing_method(*args, **kwargs):
            self = args[0]
            if self.printing:
                method_name = str(method.__name__)[6:]
                print("called \"{method_name}\" with {args} and {kwargs}"
                      .format(method_name=method_name, args=args[1:], kwargs=kwargs))
            return method(*args, **kwargs)

        return printing_method

    return wrap


class VM:
    mac_count = 0

    def __init__(self, name):
        self.name = name or ""
        self.snapshots = list()
        self.macs = [
            int("0080123456AA", 16) + self.mac_count,
            int("00801BB456AA", 16) + self.mac_count
        ]
        VM.mac_count += 1


class MockVMMController(VMMController):
    def __init__(self, printing=False):
        self.printing = printing
        self.vms = [VM("VM"), VM("VM_One"), VM("VM_Two")]
        self.running_vms = set()

    def _get_vm_by_name(self, name):
        for vm in self.vms:
            if vm.name == name:
                return vm
        return None

    @mock_print_decorator()
    def get_vms(self):
        return [vm.name for vm in self.vms]

    @mock_print_decorator()
    def is_running(self, vm):
        vm_obj = self._get_vm_by_name(vm)
        return vm_obj in self.running_vms

    @mock_print_decorator()
    def start(self, vm):
        vm_obj = self._get_vm_by_name(vm)
        if vm_obj not in self.running_vms:
            self.running_vms.add(vm_obj)
        else:
            raise VMMControllerException()

    @mock_print_decorator()
    def poweroff(self, vm):
        vm_obj = self._get_vm_by_name(vm)
        try:
            self.running_vms.remove(vm_obj)
        except KeyError:
            raise VMMControllerException()

    @mock_print_decorator()
    def delete(self, vm):
        vm_obj = self._get_vm_by_name(vm)
        self.vms.remove(vm_obj)

    @mock_print_decorator()
    def get_snapshots(self, vm):
        vm_obj = self._get_vm_by_name(vm)
        return vm_obj.snapshots

    @mock_print_decorator()
    def create_snapshot(self, vm, snapshot):
        vm_obj = self._get_vm_by_name(vm)
        vm_obj.snapshots.append(snapshot)

    @mock_print_decorator()
    def delete_snapshot(self, vm, snapshot):
        vm_obj = self._get_vm_by_name(vm)
        try:
            vm_obj.snapshots.remove(snapshot)
        except ValueError:
            raise VMMControllerException()

    @mock_print_decorator()
    def restore_snapshot(self, vm, snapshot):
        vm_obj = self._get_vm_by_name(vm)
        if snapshot not in vm_obj.snapshots:
            raise VMMControllerException()

    @mock_print_decorator()
    def clone(self, vm, snapshot, clone):
        vm_obj = self._get_vm_by_name(vm)
        if snapshot not in vm_obj.snapshots:
            raise VMMControllerException()
        else:
            self.vms.append(VM(clone))

    @mock_print_decorator()
    def get_macs(self, vm):
        vm_obj = self._get_vm_by_name(vm)
        return vm_obj.macs

    @mock_print_decorator()
    def get_mac(self, vm, if_id=1):
        vm_obj = self._get_vm_by_name(vm)
        return vm_obj.macs[if_id - 1]

    @mock_print_decorator()
    def set_mac(self, vm, mac, if_id=1):
        vm_obj = self._get_vm_by_name(vm)
        vm_obj.macs[if_id - 1] = mac

    @mock_print_decorator()
    def set_credentials(self, vm, user, password, domain):
        pass
