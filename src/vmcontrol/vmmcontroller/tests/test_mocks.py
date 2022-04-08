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


import pytest

from vmcontrol.vmmcontroller.tests.mocks import MockVMMController
from vmcontrol.vmmcontroller import VMMControllerException

test_vm = ""


@pytest.fixture()
def mvmmc():
    global test_vm
    vm_controller = MockVMMController()
    test_vm = vm_controller.get_vms()[0]
    return vm_controller


class TestMockVMMController:
    def test_get_vms(self, mvmmc: MockVMMController):
        assert isinstance(mvmmc.get_vms(), list)

    def test_some_vms_already_created(self, mvmmc: MockVMMController):
        vms = mvmmc.get_vms()
        assert len(vms) > 2

    def test_test_vm_created(self, mvmmc: MockVMMController):
        assert test_vm in mvmmc.get_vms()

    def test_no_running(self, mvmmc: MockVMMController):
        for vm in mvmmc.get_vms():
            assert not mvmmc.is_running(vm)

    def test_start(self, mvmmc: MockVMMController):
        mvmmc.start(test_vm)
        assert mvmmc.is_running(test_vm)

    def test_exception_starting_running_vm(self, mvmmc: MockVMMController):
        mvmmc.start(test_vm)
        with pytest.raises(VMMControllerException):
            mvmmc.start(test_vm)

    def test_poweroff(self, mvmmc: MockVMMController):
        mvmmc.start(test_vm)
        mvmmc.poweroff(test_vm)
        assert not mvmmc.is_running(test_vm)

    def test_exception_poweroff_not_running_vm(self, mvmmc: MockVMMController):
        assert not mvmmc.is_running(test_vm)
        with pytest.raises(VMMControllerException):
            mvmmc.poweroff(test_vm)

    def test_delete(self, mvmmc: MockVMMController):
        mvmmc.delete(test_vm)
        assert test_vm not in mvmmc.get_vms()

    def test_get_snapshots(self, mvmmc: MockVMMController):
        for vm in mvmmc.get_vms():
            assert mvmmc.get_snapshots(vm) == []

    def test_create_snapshot(self, mvmmc: MockVMMController):
        mvmmc.create_snapshot(test_vm, "Snap")
        assert mvmmc.get_snapshots(test_vm) == ["Snap"]

    def test_delete_snapshot(self, mvmmc: MockVMMController):
        mvmmc.create_snapshot(test_vm, "Snap")
        mvmmc.delete_snapshot(test_vm, "Snap")
        assert mvmmc.get_snapshots(test_vm) == []

    def test_exception_delete_non_existent_snapshot(self, mvmmc: MockVMMController):
        assert "non_existing_snapshot" not in mvmmc.get_snapshots(test_vm)
        with pytest.raises(VMMControllerException):
            mvmmc.delete_snapshot(test_vm, "non_existing_snapshot")

    def test_restore_nonexisting_snapshot(self, mvmmc: MockVMMController):
        with pytest.raises(VMMControllerException):
            mvmmc.restore_snapshot(test_vm, "Snap")

    def test_restore_snapshot(self, mvmmc: MockVMMController):
        mvmmc.create_snapshot(test_vm, "Snap")
        mvmmc.restore_snapshot(test_vm, "Snap")

    def test_clone(self, mvmmc: MockVMMController):
        mvmmc.create_snapshot(test_vm, "Snap")
        mvmmc.clone(test_vm, "Snap", "Clone")
        assert "Clone" in mvmmc.get_vms()
        assert mvmmc.get_snapshots("Clone") == []

    def test_get_mac(self, mvmmc: MockVMMController):
        mac1 = mvmmc.get_mac(test_vm)
        assert isinstance(mac1, int)
        mac1_cmp = mvmmc.get_mac(test_vm, if_id=1)
        mac2 = mvmmc.get_mac(test_vm, if_id=2)
        assert mac1 == mac1_cmp
        assert mac1 != mac2

    def test_get_macs(self, mvmmc: MockVMMController):
        macs = mvmmc.get_macs(test_vm)
        for i in range(len(macs)):
            assert mvmmc.get_mac(test_vm, if_id=i + 1) in macs

    def test_set_mac(self, mvmmc: MockVMMController):
        mvmmc.set_mac(test_vm, 1)
        mvmmc.set_mac(test_vm, 2, if_id=2)
        assert mvmmc.get_mac(test_vm) == 1
        assert mvmmc.get_mac(test_vm, if_id=2) == 2

    def test_all_different_macs(self, mvmmc: MockVMMController):
        macss = [mvmmc.get_macs(vm) for vm in mvmmc.get_vms()]
        all_macs = list()
        for macs in macss:
            all_macs.extend(macs)
        assert len(set(all_macs)) == len(all_macs)

    def test_set_credentials(self, mvmmc: MockVMMController):
        mvmmc.set_credentials(test_vm, "user", "password", "domain")
