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


from subprocess import Popen, PIPE

from vmcontrol.vmmcontroller.vmmcontroller import VMMController, VMMControllerException, LoggingVMMController


class VBoxController(VMMController):
    def get_vms(self):
        vbox_vector = ["list", "vms"]
        out = self._vboxmanage_execute(vbox_vector)
        vms = self._vm_string_to_list(out)
        return vms

    def start(self, vm):
        vbox_vector = ["startvm", vm, "--type", "headless"]
        self._vboxmanage_execute(vbox_vector)

    def poweroff(self, vm):
        vbox_vector = ["controlvm", vm, "poweroff"]
        self._vboxmanage_execute(vbox_vector)

    def delete(self, vm):
        vbox_vector = ["unregistervm", vm, "--delete"]
        self._vboxmanage_execute(vbox_vector)

    def is_running(self, vm):
        return vm in self._get_running_vms()

    def get_macs(self, vm):
        vm_info = self._get_vm_info(vm)
        macs = [
            int(value, 16)
            for key, value in vm_info.items()
            if key.startswith("macaddress")
            ]
        return macs

    def get_mac(self, vm, if_id=1):
        vm_info = self._get_vm_info(vm)
        try:
            mac_string = vm_info["macaddress" + str(if_id)]
        except KeyError as e:
            raise VMMControllerException(
                "Cannot find MAC address for interface {if_id} on VM \"{vm}\"".
                    format(if_id=if_id, vm=vm)
            )
        mac = int(mac_string, 16)
        return mac

    def set_mac(self, vm, mac, if_id=1):
        mac_string = hex(mac)[2:].rjust(12, "0")
        vbox_vector = ["modifyvm", vm, "--macaddress" + str(if_id), mac_string]
        self._vboxmanage_execute(vbox_vector)

    def get_snapshots(self, vm):
        vbox_vector = ["snapshot", vm, "list", "--machinereadable"]
        try:
            out = self._vboxmanage_execute(vbox_vector)
        except VMMControllerException as e:
            # little hack: VBox sends error if machine has no snapshots...
            # Assumption: We can isolate this error by checking if vm exists
            if vm in self.get_vms():
                # vm exists (and connection to VBox is good). Hence: no snapshots
                snapshots = list()
            else:
                # vm does not exist. Hence: there is a real error
                raise e
        else:
            out_lines = out.splitlines()
            snapshot_lines = filter(lambda line: "=" in line, out_lines)
            snapshots = [
                value.strip("\"")
                for key, value in map(lambda line: line.split("=", maxsplit=1), snapshot_lines)
                if key.strip("\"").startswith("SnapshotName")
                ]
        return snapshots

    def create_snapshot(self, vm, snapshot):
        vbox_vector = ["snapshot", vm, "take", snapshot]
        self._vboxmanage_execute(vbox_vector)

    def delete_snapshot(self, vm, snapshot):
        vbox_vector = ["snapshot", vm, "delete", snapshot]
        self._vboxmanage_execute(vbox_vector)

    def restore_snapshot(self, vm, snapshot):
        vbox_vector = ["snapshot", vm, "restore", snapshot]
        self._vboxmanage_execute(vbox_vector)

    def clone(self, vm, snapshot, clone):
        vbox_vector = [
            "clonevm", vm, "--name", clone,
            "--options", "link", "--snapshot", snapshot,
            "--register"
        ]
        self._vboxmanage_execute(vbox_vector)

    def set_credentials(self, vm, user, password, domain):
        vbox_vector = [
            "controlvm", vm,
            "setcredentials", user, password, domain
        ]
        self._vboxmanage_execute(vbox_vector)

    def _get_running_vms(self):
        vbox_vector = ["list", "runningvms"]
        out = self._vboxmanage_execute(vbox_vector)
        running_vms = self._vm_string_to_list(out)
        return running_vms

    def _vm_string_to_list(self, vm_string):
        lines = vm_string.splitlines()
        vms = [line.split("\"")[1] for line in lines]
        return vms

    def _get_vm_info(self, vm):
        vbox_vector = ["showvminfo", vm, "--machinereadable"]
        out = self._vboxmanage_execute(vbox_vector)
        out_lines = out.splitlines()
        info_lines = filter(lambda line: "=" in line, out_lines)
        vm_info = {
            key.strip("\""): value.strip("\"")
            for key, value in
            map(lambda line: line.split("=", maxsplit=1), info_lines)
            }
        return vm_info

    @staticmethod
    def _vboxmanage_execute(vbox_vector):
        call_vector = ["vboxmanage"] + vbox_vector
        p = Popen(call_vector, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        out, err = p.communicate()
        if p.returncode != 0:
            raise VMMControllerException(
                "Error in execution of {vector}\n"
                "-------\n"
                "{err}"
                "-------"
                    .format(vector=vbox_vector, err=err)
            )
        return out


class LoggingVBoxController(LoggingVMMController, VBoxController):
    pass
