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


from unittest.mock import Mock

import pytest

from vmcontrol.vmmcontroller import VMMController, VMMControllerException, VMMConsole
from vmcontrol.vmmcontroller.vmmconsole import Parser


class TestParser:
    def test_basic_string(self):
        p = Parser()
        assert p.parse("Hello") == ["Hello"]
        assert p.parse("Hello World") == ["Hello", "World"]

    def test_in_double_quotes(self):
        p = Parser()
        assert p.parse("\"Hello\"") == ["Hello"]
        assert p.parse("\"Hello World\"") == ["Hello World"]
        assert p.parse("a     space") == ["a", "space"]
        assert p.parse("\"a     space\"") == ["a     space"]

    def test_in_single_quotes(self):
        p = Parser()
        assert p.parse("'Hello'") == ["Hello"]
        assert p.parse("'Hello World'") == ["Hello World"]
        assert p.parse("'Hello \" World'") == ["Hello \" World"]

    def test_escape_backspace(self):
        p = Parser()
        assert p.parse("Hello\\ World") == ["Hello World"]
        assert p.parse("\\  Hello") == [" ", "Hello"]
        assert p.parse("\\\"Hello") == ["\"Hello"]


class VMMControllerStub(VMMController):
    get_vms = Mock()
    start = Mock()
    poweroff = Mock()
    delete = Mock()
    is_running = Mock()
    get_macs = Mock()
    get_mac = Mock()
    set_mac = Mock()
    get_snapshots = Mock()
    create_snapshot = Mock()
    delete_snapshot = Mock()
    restore_snapshot = Mock()
    clone = Mock()
    set_credentials = Mock()


def raise_vm_controller_exception(*args, **kwargs):
    raise VMMControllerException()


class ExceptionRaisingVMMController(VMMController):
    get_vms = Mock(side_effect=raise_vm_controller_exception)
    start = Mock(side_effect=raise_vm_controller_exception)
    poweroff = Mock(side_effect=raise_vm_controller_exception)
    delete = Mock(side_effect=raise_vm_controller_exception)
    is_running = Mock(side_effect=raise_vm_controller_exception)
    get_macs = Mock(side_effect=raise_vm_controller_exception)
    get_mac = Mock(side_effect=raise_vm_controller_exception)
    set_mac = Mock(side_effect=raise_vm_controller_exception)
    get_snapshots = Mock(side_effect=raise_vm_controller_exception)
    create_snapshot = Mock(side_effect=raise_vm_controller_exception)
    delete_snapshot = Mock(side_effect=raise_vm_controller_exception)
    restore_snapshot = Mock(side_effect=raise_vm_controller_exception)
    clone = Mock(side_effect=raise_vm_controller_exception)
    set_credentials = Mock(side_effect=raise_vm_controller_exception)


@pytest.fixture(params=[VMMControllerStub, ExceptionRaisingVMMController])
def shell(request):
    vm_controller = request.param
    return VMMConsole(vmm_controller=vm_controller)


class TestVMControlShell:
    def test_get_vms(self, shell: VMMConsole):
        shell.do_get_vms("")
        assert shell.vmmc.get_vms.called

    def test_start(self, shell: VMMConsole):
        arg = "VM"
        shell.do_start(arg)
        shell.vmmc.start.assert_called_with(vm="VM")

    def test_poweroff(self, shell: VMMConsole):
        arg = "VM"
        shell.do_poweroff(arg)
        shell.vmmc.poweroff.assert_called_with(vm="VM")

    def test_delete(self, shell: VMMConsole):
        arg = "VM"
        shell.do_delete(arg)
        shell.vmmc.delete.assert_called_with(vm="VM")

    def test_is_running(self, shell: VMMConsole):
        arg = "VM"
        shell.do_is_running(arg)
        shell.vmmc.is_running.assert_called_with(vm="VM")

    def test_get_macs(self, shell: VMMConsole):
        arg = "VM"
        shell.do_get_macs(arg)
        shell.vmmc.get_macs.assert_called_with(vm="VM")

    def test_get_mac(self, shell: VMMConsole):
        arg = "VM"
        shell.do_get_mac(arg)
        shell.vmmc.get_mac.assert_called_with(vm="VM")

    def test_get_mac2(self, shell: VMMConsole):
        arg = "VM 2"
        shell.do_get_mac(arg)
        shell.vmmc.get_mac.assert_called_with(vm="VM", if_id=2)

    def test_set_mac(self, shell: VMMConsole):
        arg = "VM 23"
        shell.do_set_mac(arg)
        shell.vmmc.set_mac.assert_called_with(vm="VM", mac=23)

    def test_set_mac3(self, shell: VMMConsole):
        arg = "\"VM\" 23 2"
        shell.do_set_mac(arg)
        shell.vmmc.set_mac.assert_called_with(vm="VM", mac=23, if_id=2)

    def test_get_snapshots(self, shell: VMMConsole):
        arg = "VM"
        shell.do_get_snapshots(arg)
        shell.vmmc.get_snapshots.assert_called_with(vm="VM")

    def test_create_snapshot(self, shell: VMMConsole):
        arg = "VM \"New Snapshot\""
        shell.do_create_snapshot(arg)
        shell.vmmc.create_snapshot.assert_called_with(vm="VM", snapshot="New Snapshot")

    def test_delete_snapshot(self, shell: VMMConsole):
        arg = "VM \"New Snapshot\""
        shell.do_delete_snapshot(arg)
        shell.vmmc.delete_snapshot.assert_called_with(vm="VM", snapshot="New Snapshot")

    def test_restore_snapshot(self, shell: VMMConsole):
        arg = "VM \"Old Snapshot\""
        shell.do_restore_snapshot(arg)
        shell.vmmc.restore_snapshot.assert_called_with(vm="VM", snapshot="Old Snapshot")

    def test_clone(self, shell: VMMConsole):
        arg = "VM Snapshot CloneVM"
        shell.do_clone(arg)
        shell.vmmc.clone.assert_called_with(vm="VM", snapshot="Snapshot", clone="CloneVM")

    def test_set_credentials(self, shell: VMMConsole):
        arg = "VM \"user\" password domain"
        shell.do_set_credentials(arg)
        shell.vmmc.set_credentials.assert_called_with(
            vm="VM", user="user", password="password", domain="domain"
        )
