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


import json
import logging
import os
import time
from types import SimpleNamespace

from vmcontrol.vmmcontroller import VMMController, VMMControllerException

logger = logging.getLogger(__name__)


class DictNamespace(SimpleNamespace):
    def _asdict(self):
        fields = (key for key in dir(self) if not key.startswith("_"))
        return {field: self.__getattribute__(field) for field in fields}


class SessionConfig(DictNamespace):
    server_vms = ["Internet Router", "Attacker", "Company Router", "Log Server", "Internal Server", "DMZ Server"]
    client_vm = "Client"
    number_of_clones = 3
    vm_start_timeout = 0


class Clone(DictNamespace):
    id = None
    vm = None
    management_mac = None
    internal_mac = None
    user = None
    password = None
    domain = None
    vdre_port = None


class CloneCreator:
    def __init__(
        self, father_vm, base_snapshot, number_of_clones, vmm_controller: VMMController, vdre_port_start=6000
    ):
        self.father_vm = father_vm
        self.base_snapshot = base_snapshot
        self.number_of_clones = number_of_clones
        self.vmmc = vmm_controller
        self.vdre_port_start = vdre_port_start
        self._current_vms = self.vmmc.get_vms()
        self._clones = None

    def create(self):
        self._clones = [Clone(id=i + 1) for i in range(self.number_of_clones)]
        for clone in self._clones:
            self.set_data(clone)
            self.create_vm(clone)
        return self._clones

    def set_data(self, clone):
        self.set_vm_name(clone)
        self.set_management_mac(clone)
        self.set_internal_mac(clone)
        self.set_credentials(clone)
        self.set_vdre_port(clone)

    def set_vm_name(self, clone):
        clone.vm = self.father_vm + "Clone" + str(clone.id)
        while clone.vm in self._current_vms:
            clone.vm += "a"

    def set_management_mac(self, clone):
        clone.management_mac = 0x005056000000 + 0x100 * self.number_of_clones + clone.id

    def set_internal_mac(self, clone):
        clone.internal_mac = 0x005056000000 + clone.id

    def set_credentials(self, clone):
        clone.user = "client" + str(clone.id)
        clone.password = "breach"
        clone.domain = "BREACH"

    def set_vdre_port(self, clone):
        clone.vdre_port = self.vdre_port_start + clone.id - 1

    def create_vm(self, clone):
        self.vmmc.clone(self.father_vm, self.base_snapshot, clone.vm)
        self.vmmc.set_mac(clone.vm, clone.management_mac, if_id=2)
        self.vmmc.set_mac(clone.vm, clone.internal_mac, if_id=1)
        self.vmmc.set_vdre_port(clone.vm, clone.vdre_port)


class SessionHandler:
    clone_creator_class = CloneCreator

    def __init__(self, vmm_controller: VMMController, session_config=None, session_state_file=None):
        self.backup_snapshots = dict()
        self.vmmc = vmm_controller
        self.config = session_config or self.default_config()
        self.session_running = False
        self.clones = list()
        self.session_state_file = session_state_file
        if self.session_state_file is not None:
            self.load_session_state()

    @staticmethod
    def default_config() -> SessionConfig:
        return SessionConfig()

    @property
    def clone_vms(self):
        return [clone.vm for clone in self.clones]

    def load_session_state(self):
        if os.path.isfile(self.session_state_file):
            with open(self.session_state_file) as f:
                self.set_state(json.loads(f.read()))
                logger.info("Found and loaded old session state")

    def save_session_state(self):
        with open(self.session_state_file, "w+") as f:
            json.dump(self.get_state(), f)

    def remove_session_state_file(self):
        if os.path.isfile(self.session_state_file):
            os.remove(self.session_state_file)

    def get_state(self):
        state = DictNamespace()
        state.backup_snapshots = self.backup_snapshots.copy()
        state.config = self.config._asdict()
        state.clones = [clone._asdict() for clone in self.clones]
        state.session_running = self.session_running
        return state._asdict()

    def set_state(self, dict_):
        state = DictNamespace(**dict_)
        self.backup_snapshots = state.backup_snapshots.copy()
        self.config = SessionConfig(**state.config)
        self.clones = [Clone(**clone_dict) for clone_dict in state.clones]
        self.session_running = state.session_running

    def server_and_client_vms(self):
        return self.config.server_vms + [self.config.client_vm]

    def start_session(self):
        if self.session_running:
            raise SessionHandlerException("Session already running")
        logger.info("Starting TBF Session")
        self.create_backup_snapshots(self.server_and_client_vms())
        self.create_clones()
        self.start_all_vms()
        self.session_running = True
        if self.session_state_file is not None:
            self.save_session_state()
        logger.info("TBF Session started")

    def close_session(self):
        if not self.session_running:
            raise SessionHandlerException("No session running")
        logger.info("Closing TBF Session")
        self.poweroff_all_vms()
        self.delete_clones()
        self.restore_delete_backup_snapshots()
        self.session_running = False
        if self.session_state_file is not None:
            self.remove_session_state_file()
        logger.info("TBF Session closed")

    def create_backup_snapshots(self, vms):
        logger.info("Creating backup snapshots for " + str(vms))
        snapshot_trunc = "Backup"
        for vm in vms:
            snapshots = self.vmmc.get_snapshots(vm)
            unique_snapshot_name = snapshot_trunc
            i = 0
            while unique_snapshot_name in snapshots:
                unique_snapshot_name = snapshot_trunc + str(i)
                i += 1
            self.vmmc.create_snapshot(vm, unique_snapshot_name)
            self.backup_snapshots[vm] = unique_snapshot_name

    def create_clones(self):
        logger.info("Creating clones")
        father_vm = self.config.client_vm
        base_snapshot = self.backup_snapshots[father_vm]
        clone_creator = self.clone_creator_class(father_vm, base_snapshot, self.config.number_of_clones, self.vmmc)
        self.clones = clone_creator.create()

    def start_all_vms(self):
        logger.info("Starting all VMs")
        clone_vms = [clone.vm for clone in self.clones]
        self.start_vms(self.config.server_vms + clone_vms)

    def start_clones(self):
        logger.info("Starting clones")
        self.start_vms(self.clone_vms)

    def login_clones(self):
        logger.info("Login clones")
        for clone in self.clones:
            self.vmmc.set_credentials(clone.vm, clone.user, clone.password, clone.domain)

    def poweroff_all_vms(self):
        logger.info("Poweroff all VMs")
        clone_vms = [clone.vm for clone in self.clones]
        try:
            self.poweroff_vms(self.config.server_vms + clone_vms)
        except SessionHandlerException as e:
            logger.warning("Exception: {e}".format(e=e))

    def delete_clones(self):
        logger.info("Deleting clones")
        clone_vms = [clone.vm for clone in self.clones]
        try:
            self.delete_vms(clone_vms)
        except SessionHandlerException as e:
            logger.warning("Exception: {e}".format(e=e))
        self.clones.clear()

    def restore_delete_backup_snapshots(self):
        logger.info("Restoring and deleting backup snapshots")
        try:
            self.restore_delete_snapshots(self.backup_snapshots)
        except SessionHandlerException as e:
            logger.warning("Exception: {e}".format(e=str(e)))
        self.backup_snapshots.clear()

    def start_vms(self, vms):
        for vm in vms:
            self.vmmc.start(vm)
            self.take_vm_start_timeout()

    def restore_delete_snapshots(self, snapshots):
        fails, max_fails, timeout = 0, 100, 0.01
        snaps = snapshots.copy()
        while snaps and fails < max_fails:
            vm, snap = snaps.popitem()
            try:
                self.vmmc.restore_snapshot(vm, snap)
                self.vmmc.delete_snapshot(vm, snap)
            except VMMControllerException:
                fails += 1
                snaps[vm] = snap
                time.sleep(timeout)
        if snaps:
            raise SessionHandlerException(
                "Could not restore and delete all snapshots. Failing: {snaps}".format(snaps=snaps)
            )

    def poweroff_vms(self, vms):
        fails, max_fails, timeout = 0, 100, 0.01
        running_vms = [vm for vm in vms if self.vmmc.is_running(vm)]
        while running_vms and fails < max_fails:
            vm = running_vms.pop()
            try:
                self.vmmc.poweroff(vm)
            except VMMControllerException:
                fails += 1
                running_vms.append(vm)
                time.sleep(timeout)
        if running_vms:
            raise SessionHandlerException(
                "Could not poweroff all machines. Still alive: {vms}".format(vms=running_vms)
            )

    def delete_vms(self, vms):
        fails, max_fails, timeout = 0, 100, 0.01
        current_vms = self.vmmc.get_vms()
        existing_vms = [vm for vm in vms if vm in current_vms]
        while existing_vms and fails < max_fails:
            vm = existing_vms.pop()
            try:
                self.vmmc.delete(vm)
            except VMMControllerException:
                fails += 1
                existing_vms.append(vm)
                time.sleep(timeout)
        if existing_vms:
            raise SessionHandlerException("Could not delete all machines. Still there: {vms}".format(vms=existing_vms))

    def take_vm_start_timeout(self):
        time.sleep(self.config.vm_start_timeout)


class SessionHandlerException(Exception):
    pass
