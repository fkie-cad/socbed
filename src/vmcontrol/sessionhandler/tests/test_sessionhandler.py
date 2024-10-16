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


import os
from unittest.mock import Mock, patch

import pytest

from vmcontrol.sessionhandler import SessionHandler, SessionConfig, SessionHandlerException, CloneCreator
from vmcontrol.sessionhandler.sessionhandler import Clone, DictNamespace
from vmcontrol.vmmcontroller import VMMControllerException
from vmcontrol.vmmcontroller.tests.mocks import MockVMMController


class DictNamespaceStub(DictNamespace):
    field1 = None
    field2 = 23


class TestDictNamespace:
    def test_asdict(self):
        dn = DictNamespaceStub()
        assert dn._asdict() == {"field1": None, "field2": 23}

    def test_asdict_with_arguments(self):
        dn = DictNamespaceStub(field1="some_var")
        assert dn._asdict() == {"field1": "some_var", "field2": 23}


class TestSessionConfig:
    def test_init(self):
        SessionConfig()

    def assert_config_state(self, config, state):
        assert state["server_vms"] == config.server_vms
        assert state["client_vm"] == config.client_vm
        assert state["number_of_clones"] == config.number_of_clones
        assert state["vm_start_timeout"] == config.vm_start_timeout

    def test_get_state(self):
        c = SessionConfig()
        state = c._asdict()
        self.assert_config_state(c, state)

    def test_from_state(self):
        state = SessionConfig()._asdict()
        c = SessionConfig(**state)
        self.assert_config_state(c, state)

    def test_with_default_config(self):
        state = SessionHandler.default_config()._asdict()
        c = SessionConfig(**state)
        self.assert_config_state(c, state)


def mock_vmm_controller_from_session_handler_config(config: SessionConfig):
    mvmc = MockVMMController()
    base_vm = mvmc.get_vms()[0]
    base_snapshot = "BaseSnapshot"
    mvmc.create_snapshot(base_vm, base_snapshot)
    vms = config.server_vms + [config.client_vm]
    for vm in vms:
        mvmc.clone(base_vm, base_snapshot, vm)
    return mvmc


@pytest.fixture()
def sh():
    return build_session_handler()


def build_session_handler():
    config = SessionHandler.default_config()
    config.vm_start_timeout = 0
    vm_controller = mock_vmm_controller_from_session_handler_config(config)
    return SessionHandler(vm_controller, config)


@pytest.fixture()
def sh_with_state_file(tmpdir):
    session_state_file = os.path.join(str(tmpdir), "tbfvmsessionstate")
    return build_session_handler_with_state_file(session_state_file)


def build_session_handler_with_state_file(session_state_file):
    config = SessionHandler.default_config()
    config.vm_start_timeout = 0
    vm_controller = mock_vmm_controller_from_session_handler_config(config)
    return SessionHandler(vm_controller, config, session_state_file)


class TestSessionHandler:
    def test_default_config(self):
        config = SessionHandler.default_config()
        assert config.server_vms == [
            "Internet Router",
            "Attacker",
            "Company Router",
            "Log Server",
            "Internal Server",
            "DMZ Server",
        ]
        assert config.client_vm == "Client"
        assert config.number_of_clones == 3
        assert config.vm_start_timeout == 0

    def test_take_timeout(self, sh: SessionHandler):
        sleep_mock = Mock()
        p = patch(SessionHandler.__module__ + ".time.sleep", sleep_mock)
        sh.config.vm_start_timeout = 42
        p.start()
        sh.take_vm_start_timeout()
        p.stop()
        sleep_mock.assert_called_with(42)

    def test_start_vms(self, sh: SessionHandler):
        vms = sh.vmmc.get_vms()
        sh.take_vm_start_timeout = Mock()
        sh.start_vms(vms)
        for vm in vms:
            assert sh.vmmc.is_running(vm)
        assert sh.take_vm_start_timeout.call_count == len(vms)

    def test_poweroff_vms(self, sh: SessionHandler):
        vms = sh.vmmc.get_vms()
        sh.start_vms(vms)
        sh.poweroff_vms(vms)
        for vm in vms:
            assert not sh.vmmc.is_running(vm)

    def test_retry_poweroff(self, sh: SessionHandler):
        vm, *_ = sh.vmmc.get_vms()
        sh.vmmc.poweroff = CallableExceptionRaiser(VMMControllerException, counter=1)
        sh.vmmc.start(vm)
        sh.poweroff_vms([vm])

    def test_delete_vms(self, sh: SessionHandler):
        vms = sh.vmmc.get_vms()
        sh.delete_vms(vms)
        for vm in vms:
            assert vm not in sh.vmmc.get_vms()

    def test_retry_delete(self, sh: SessionHandler):
        vm, *_ = sh.vmmc.get_vms()
        sh.vmmc.delete = CallableExceptionRaiser(VMMControllerException, counter=1)
        sh.delete_vms([vm])

    def test_server_and_client_vms(self, sh: SessionHandler):
        vms = sh.server_and_client_vms()
        compare = sh.config.server_vms + [sh.config.client_vm]
        assert set(vms) == set(compare)

    def test_create_backup_snapshots(self, sh: SessionHandler):
        vms = sh.vmmc.get_vms()
        sh.create_backup_snapshots(vms)
        for vm in vms:
            assert vm in sh.backup_snapshots.keys()
        for vm in vms:
            assert sh.backup_snapshots[vm] in sh.vmmc.get_snapshots(vm)

    def test_vary_backup_snapshot(self, sh: SessionHandler):
        vms = sh.vmmc.get_vms()
        sh.create_backup_snapshots(vms)
        first_backups = sh.backup_snapshots.copy()
        sh.create_backup_snapshots(vms)
        second_backups = sh.backup_snapshots.copy()
        for vm in vms:
            assert first_backups[vm] != second_backups[vm]

    def test_restore_and_delete_backup_snapshots(self, sh: SessionHandler):
        vms = sh.vmmc.get_vms()
        sh.create_backup_snapshots(vms)
        backup_snapshots = sh.backup_snapshots.copy()
        sh.vmmc.restore_snapshot = Mock()
        sh.restore_delete_backup_snapshots()
        for vm in vms:
            sh.vmmc.restore_snapshot.assert_any_call(vm, backup_snapshots[vm])
            assert backup_snapshots[vm] not in sh.vmmc.get_snapshots(vm)
        assert not sh.backup_snapshots

    def test_retry_restore_delete_snapshots(self, sh: SessionHandler):
        vm, *_ = sh.vmmc.get_vms()
        sh.vmmc.create_snapshot(vm, "Snap")
        sh.vmmc.restore_snapshot = CallableExceptionRaiser(VMMControllerException, counter=1)
        sh.vmmc.delete_snapshot = CallableExceptionRaiser(VMMControllerException, counter=1)
        sh.restore_delete_snapshots({vm: "Snap"})

    def test_create_clones(self, sh: SessionHandler):
        sh.create_backup_snapshots([sh.config.client_vm])
        sh.create_clones()
        assert len(sh.clone_vms) == sh.config.number_of_clones
        for vm in sh.clone_vms:
            assert vm in sh.vmmc.get_vms()

    def test_login_clones(self, sh: SessionHandler):
        sh.vmmc.set_credentials = Mock()
        sh.create_backup_snapshots([sh.config.client_vm])
        sh.create_clones()
        sh.login_clones()
        for clone in sh.clones:
            sh.vmmc.set_credentials.assert_any_call(clone.vm, clone.user, clone.password, clone.domain)

    def test_start_session(self, sh: SessionHandler):
        server_vms = sh.config.server_vms
        client_vm = sh.config.client_vm
        assert not sh.session_running
        sh.start_session()
        assert set(server_vms + [client_vm]) == set(sh.backup_snapshots.keys())
        for vm in server_vms:
            assert sh.vmmc.is_running(vm)
        assert not sh.vmmc.is_running(client_vm)
        assert sh.clones
        for clone in sh.clones:
            assert sh.vmmc.is_running(clone.vm)
        assert sh.session_running

    def test_close_session(self, sh: SessionHandler):
        sh.start_session()
        clones = sh.clone_vms.copy()
        backups = sh.backup_snapshots.copy()
        sh.close_session()
        for clone in clones:
            assert clone not in sh.vmmc.get_vms()
        for vm in sh.server_and_client_vms():
            assert not sh.vmmc.is_running(vm)
        for vm, snapshot in backups.items():
            assert snapshot not in sh.vmmc.get_snapshots(vm)
        assert not sh.session_running

    def test_get_set_state(self, sh: SessionHandler):
        sh.start_session()
        state = sh.get_state()
        vmc = sh.vmmc
        del sh
        sh_new = build_session_handler()
        sh_new.vmmc = vmc
        sh_new.set_state(state)
        sh_new.close_session()

    def test_cannot_start_more_than_one_session(self, sh: SessionHandler):
        sh.start_session()
        with pytest.raises(SessionHandlerException):
            sh.start_session()
        sh.close_session()
        sh.start_session()

    def test_cannot_close_if_no_session_running(self, sh: SessionHandler):
        with pytest.raises(SessionHandlerException):
            sh.close_session()

    def test_state_file_is_created(self, sh_with_state_file: SessionHandler):
        sh_with_state_file.start_session()
        assert os.path.isfile(sh_with_state_file.session_state_file)

    def test_state_file_is_removed(self, sh_with_state_file: SessionHandler):
        sh_with_state_file.start_session()
        sh_with_state_file.remove_session_state_file()
        assert not os.path.isfile(sh_with_state_file.session_state_file)

    def test_state_file_is_removed_after_closing(self, sh_with_state_file: SessionHandler):
        sh_with_state_file.start_session()
        sh_with_state_file.close_session()
        assert not os.path.isfile(sh_with_state_file.session_state_file)

    def test_state_file_is_loaded(self, sh_with_state_file: SessionHandler):
        sh_with_state_file.start_session()
        state_file = sh_with_state_file.session_state_file
        del sh_with_state_file
        sh_2 = build_session_handler_with_state_file(state_file)
        assert sh_2.session_running


class CallableExceptionRaiser:
    def __init__(self, exception_class, counter=1):
        self.exception_class = exception_class
        self.counter = counter

    def __call__(self, *args, **kwargs):
        if self.counter > 0:
            self.counter -= 1
            raise self.exception_class()
        else:
            pass


class TestClone:
    def test_init_default_fields(self):
        c = Clone()
        assert c.vm is None
        assert c.id is None
        assert c.management_mac is None
        assert c.internal_mac is None
        assert c.user is None
        assert c.password is None
        assert c.domain is None


@pytest.fixture()
def cc():
    parent_vm = "Client"
    base_snapshot = "CloneShot"
    number_of_clones = 5
    mvmmc = MockVMMController()
    some_vm = mvmmc.get_vms()[0]
    some_shot = "Snap"
    mvmmc.create_snapshot(some_vm, some_shot)
    mvmmc.clone(some_vm, some_shot, parent_vm)
    mvmmc.create_snapshot(parent_vm, base_snapshot)
    cc = CloneCreator(parent_vm, base_snapshot, number_of_clones, mvmmc)
    return cc


class TestCloneCreator:
    def test_init(self, cc: CloneCreator):
        assert cc._clones is None

    def test_generate_ids(self, cc: CloneCreator):
        clones = cc.create()
        assert len(clones) == cc.number_of_clones
        assert {clone.id for clone in cc._clones} == {i + 1 for i in range(cc.number_of_clones)}

    def test_set_vm_name(self, cc: CloneCreator):
        clone = Clone(id=42)
        cc.set_vm_name(clone)
        assert clone.vm.startswith(cc.parent_vm)

    def test_set_vm_name_avoiding_current_vms(self, cc: CloneCreator):
        clone = Clone(id=42)
        cc.set_vm_name(clone)
        clone_vm_before = clone.vm
        cc._current_vms.append(clone_vm_before)
        cc.set_vm_name(clone)
        assert clone.vm.startswith(clone_vm_before)
        assert clone.vm != clone_vm_before

    def test_set_management_mac(self, cc: CloneCreator):
        clone = Clone(id=42)
        cc.set_management_mac(clone)
        assert clone.management_mac % 0x100 == clone.id
        assert (clone.management_mac // 0x100) % 0x100 == cc.number_of_clones

    def test_set_internal_mac(self, cc: CloneCreator):
        clone = Clone(id=42)
        cc.set_internal_mac(clone)
        assert clone.internal_mac % 0x100 == clone.id

    def test_set_credential_data_for_clone(self, cc: CloneCreator):
        clone = Clone(id=42)
        cc.set_credentials(clone)
        assert clone.user == "client" + str(clone.id)
        assert clone.password == "breach"
        assert clone.domain == "BREACH"

    def test_create_vms_for_clones(self, cc: CloneCreator):
        clones = cc.create()
        for clone in clones:
            assert clone.vm in cc.vmmc.get_vms()
            assert cc.vmmc.get_mac(clone.vm, if_id=2) == clone.management_mac
            assert cc.vmmc.get_mac(clone.vm, if_id=1) == clone.internal_mac

    def test_create(self, cc: CloneCreator):
        clones = cc.create()
        for clone in clones:
            assert clone.vm in cc.vmmc.get_vms()
            assert clone.user and clone.password and clone.domain
