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


import ssl
import time
import sys
from types import SimpleNamespace

from pyVim import connect
from pyVmomi import vim

from vmcontrol.vmmcontroller.vmmcontroller import VMMController, VMMControllerException, LoggingVMMController


class ESXiServer(SimpleNamespace):
    host = None
    port = None
    user = None
    password = None
    resource_pool = None
    data_center = None
    vm_folder = None
    data_store = None


class VMWareController(VMMController):
    def __init__(self, esxi_server):
        super().__init__()
        self.esxi = esxi_server
        self.si = None
        self._init_si()

    def __del__(self):
        self._close_si()

    def _init_si(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        ssl_context.verify_mode = ssl.CERT_NONE
        print("Try Connecting", self.esxi.host)
        self.si = connect.SmartConnect(
            host=self.esxi.host, port=self.esxi.port,
            user=self.esxi.user, pwd=self.esxi.password,
            sslContext=ssl_context
        )
        print("Connected SI")

    def _close_si(self):
        if self.si:
            connect.Disconnect(self.si)
            print("Disconnected SI")

    def get_vms(self):
        vms = list(self._vm_obj_dict().keys())
        return vms

    def start(self, vm):
        vm_obj = self._vm_obj(vm)
        self._vmware_execute_task(vm_obj.PowerOn)

    def poweroff(self, vm):
        vm_obj = self._vm_obj(vm)
        self._vmware_execute_task(vm_obj.PowerOff)

    def delete(self, vm):
        vm_obj = self._vm_obj(vm)
        self._vmware_execute_task(vm_obj.Destroy)

    def is_running(self, vm):
        vm_obj = self._vm_obj(vm)
        return vm_obj.runtime.powerState == "poweredOn"

    def get_macs(self, vm):
        mac_strs = [vec_obj.macAddress
                    for vec_obj in self._virtual_ethernet_card_obj_dict(vm).values()]
        macs = [int(mac_str.replace(":", ""), 16)
                for mac_str in mac_strs
                if mac_str is not None]
        return macs

    def get_mac(self, vm, if_id=1):
        adapter_label = self._adapter_label(if_id)
        vec_obj = self._virtual_ethernet_card_obj(vm, adapter_label)
        mac_str = vec_obj.macAddress
        if mac_str:
            mac = int(mac_str.replace(":", ""), 16)
            return mac
        else:
            raise VMMControllerException(
                "MAC address of network adapter labeled {label}"
                " on {vm} is not specified (perhaps not manually set)"
                    .format(label=adapter_label, vm=vm))

    def set_mac(self, vm, mac, if_id=1):
        vm_obj = self._vm_obj(vm)
        vec_obj = self._virtual_ethernet_card_obj(vm, self._adapter_label(if_id))
        tmp_mac_str = hex(mac)[2:].upper().rjust(12, "0")
        mac_str = ":".join([tmp_mac_str[2 * i:2 * (i + 1)] for i in range(6)])
        vd_spec_obj = vim.vm.device.VirtualDeviceSpec()
        vd_spec_obj.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        vd_spec_obj.device = vec_obj
        vd_spec_obj.device.addressType = "manual"
        vd_spec_obj.device.macAddress = mac_str
        dev_changes = [vd_spec_obj]
        config_spec_obj = vim.vm.ConfigSpec()
        config_spec_obj.deviceChange = dev_changes
        self._vmware_execute_task(vm_obj.ReconfigVM_Task, spec=config_spec_obj)

    def get_snapshots(self, vm):
        snapshots = list(self._snapshot_obj_dict(vm).keys())
        return snapshots

    def create_snapshot(self, vm, snapshot):
        vm_obj = self._vm_obj(vm)
        self._vmware_execute_task(vm_obj.CreateSnapshot, name=snapshot, memory=False, quiesce=False)

    def delete_snapshot(self, vm, snapshot):
        snap_obj = self._snapshot_obj(vm, snapshot)
        self._vmware_execute_task(snap_obj.Remove, removeChildren=False, consolidate=True)

    def restore_snapshot(self, vm, snapshot):
        snap_obj = self._snapshot_obj(vm, snapshot)
        self._vmware_execute_task(snap_obj.Revert)

    def clone(self, vm, snapshot, clone):
        vm_obj = self._vm_obj(vm)
        snapshot_obj = self._snapshot_obj_dict(vm)[snapshot]
        data_store = self._data_store_obj(self.esxi.data_store)
        dest_folder = self._vm_folder_obj(self.esxi.vm_folder, self.esxi.data_center)
        resource_pool = self._resource_pool_obj(self.esxi.resource_pool)
        relospec = vim.vm.RelocateSpec()
        relospec.diskMoveType = "createNewChildDiskBacking"
        relospec.datastore = data_store
        relospec.pool = resource_pool
        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        clonespec.snapshot = snapshot_obj
        self._vmware_execute_task(vm_obj.Clone, folder=dest_folder, name=clone, spec=clonespec)

    def set_credentials(self, vm, user, password, domain):
        local_admin_user = "breach"
        local_admin_password = "breach"
        # local_admin_domain = "client"
        powershell_exe = "C:\\Windows\\system32\\WindowsPowerShell\\v1.0\\powershell.exe"
        winlogon_registry_key = "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon"
        change_autologon_script = ";".join([
            "$user = '{user}'".format(user=user),
            "$password = '{password}'".format(password=password),
            "$domain = '{domain}'".format(domain=domain),
            "$winlogon_registry_key = '{reg_key}'".format(reg_key=winlogon_registry_key),
            "New-ItemProperty -Path $winlogon_registry_key -Name DefaultUserName -Value $user -Force",
            "New-ItemProperty -Path $winlogon_registry_key -Name DefaultPassword -Value $password -Force",
            "New-ItemProperty -Path $winlogon_registry_key -Name DefaultDomainName -Value $domain -Force",
            "New-ItemProperty -Path $winlogon_registry_key -Name AutoAdminLogon -Value 1 -Force",
            "Restart-Computer"
        ])
        vm_obj = self._vm_obj(vm)
        cred_obj = vim.vm.guest.NamePasswordAuthentication(
            username=local_admin_user, password=local_admin_password)
        gom = self.si.content.guestOperationsManager
        program_spec = vim.vm.guest.ProcessManager.ProgramSpec(
            programPath=powershell_exe,
            arguments=change_autologon_script,
            workingDirectory="C:\\BREACH"
        )
        executed = False
        print("running.", end="")
        sys.stdout.flush()
        while not executed:
            try:
                gom.processManager.StartProgramInGuest(vm_obj, cred_obj, program_spec)
                executed = True
                print("success")
            except vim.fault.GuestOperationsUnavailable as e:
                print(".", end="")
                sys.stdout.flush()
                time.sleep(1)

    def _resource_pool_obj(self, resource_pool, content=None):
        try:
            return self._obj_dict(vim.ResourcePool, content=content)[resource_pool]
        except KeyError:
            raise VMMControllerException(
                "No resource pool named {resource_pool} found".format(resource_pool=resource_pool))

    def _data_store_obj(self, data_store, content=None):
        try:
            return self._obj_dict(vim.Datastore, content=content)[data_store]
        except KeyError:
            raise VMMControllerException("No data store named {data_store} found".format(data_store=data_store))

    def _data_center_obj(self, data_center, content=None):
        try:
            return self._obj_dict(vim.Datacenter, content=content)[data_center]
        except KeyError:
            raise VMMControllerException("No data center named {data_center} found".format(data_center=data_center))

    def _vm_folder_obj(self, vm_folder, data_center, content=None):
        data_center_obj = self._data_center_obj(data_center)
        try:
            return self._obj_dict(vim.Folder, content=content, container=data_center_obj.vmFolder)[vm_folder]
        except KeyError:
            raise VMMControllerException(
                "No folder named {vm_folder} on {data_center} found".format(vm_folder=vm_folder,
                                                                            data_center=data_center))

    def _vm_obj(self, vm, content=None):
        try:
            return self._vm_obj_dict(content=content)[vm]
        except KeyError:
            raise VMMControllerException("No vm named {vm} found".format(vm=vm))

    def _snapshot_obj(self, vm, snapshot):
        try:
            return self._snapshot_obj_dict(vm)[snapshot]
        except KeyError:
            raise VMMControllerException("No snapshot named {snap} on {vm}".format(snap=snapshot, vm=vm))

    def _virtual_ethernet_card_obj(self, vm, adapter_label):
        try:
            return self._virtual_ethernet_card_obj_dict(vm)[adapter_label]
        except KeyError:
            raise VMMControllerException("No network adapter labeled {label} on {vm}".format(label=adapter_label, vm=vm))

    def _adapter_label(self, vmware_adapter_id):
        return "Network adapter {adapter_id}".format(adapter_id=vmware_adapter_id)

    def _vm_obj_dict(self, content=None):
        content = content or self.si.RetrieveContent()
        if self.esxi.resource_pool is not None:
            container = self._resource_pool_obj(self.esxi.resource_pool, content=content)
        else:
            container = content.rootFolder
        viewType = [vim.VirtualMachine]
        recursive = True
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)
        VmList = containerView.view
        vm_dict = {vm_obj.name: vm_obj for vm_obj in VmList}
        return vm_dict

    def _obj_dict(self, type, content=None, container=None):
        content = content or self.si.RetrieveContent()
        container = container or content.rootFolder
        viewType = [type]
        recursive = True
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)
        ViewList = containerView.view
        obj_dict = {obj.name: obj for obj in ViewList}
        return obj_dict

    def _snapshot_obj_dict(self, vm):
        vm_obj = self._vm_obj(vm)
        if vm_obj.snapshot is None:
            return dict()
        snapshot_root = vm_obj.snapshot.rootSnapshotList
        snap_dict = dict()

        def add_snaps_recursively(snap_objs):
            for snap_obj in snap_objs:
                snap_dict[snap_obj.name] = snap_obj.snapshot
                add_snaps_recursively(snap_obj.childSnapshotList)

        add_snaps_recursively(snapshot_root)
        return snap_dict

    def _virtual_ethernet_card_obj_dict(self, vm):
        vm_obj = self._vm_obj(vm)
        d = {dev.deviceInfo.label: dev
             for dev in vm_obj.config.hardware.device
             if isinstance(dev, vim.vm.device.VirtualEthernetCard)}
        return d

    @staticmethod
    def _vmware_execute_task(function, *args, **kwargs):
        task = function(*args, **kwargs)
        last_state = ""
        while True:
            state = task.info.state
            if last_state == state:
                print(".", end="")
            elif state == "running":
                print("running.", end="")
            elif state == "queued":
                print("queued.", end="")
            elif state == "success":
                print("success")
                return task.info.result
            elif state == "error":
                print()
                raise VMMControllerException("ESX Server error:\n{err}".format(err=str(task.info.error)))
            else:
                print()
                raise VMMControllerException("Unknown task state:\n{task}".format(task=task.info))
            last_state = state
            sys.stdout.flush()
            time.sleep(0.1)


class LoggingVMWareController(LoggingVMMController, VMWareController):
    pass
