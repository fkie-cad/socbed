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


from unittest.mock import Mock

import pytest

from vmcontrol.vmmcontroller import VBoxController, VMMControllerException


@pytest.fixture()
def vbc(request):
    vbc = VBoxController()
    vbc._vboxmanage_execute = Mock()
    return vbc


def assert_call(vbc: VBoxController, vbox_vector):
    vbc._vboxmanage_execute.assert_called_with(vbox_vector)


class TestVBoxController:
    def test_vboxmanage_mock(self, vbc: VBoxController):
        assert isinstance(vbc._vboxmanage_execute, Mock)

    def test_get_vms(self, vbc: VBoxController):
        return_value = "\n".join([
            "\"Attacker\" {8451900b-320a-43b4-9eb9-9bd6656f33ad}",
            "\"Client\" {4d0986c7-eabc-4cd3-a2f3-e28111a66ac1}",
            "\"Company Router\" {d75d3108-266b-420e-aa74-bc73f689ee9c}"
        ])
        vbc._vboxmanage_execute = Mock(return_value=return_value)
        vms = vbc.get_vms()
        assert_call(vbc, ["list", "vms"])
        assert vms == ["Attacker", "Client", "Company Router"]

    def test_start(self, vbc: VBoxController):
        vbc.start("VM")
        assert_call(vbc, ["startvm", "VM", "--type", "headless"])

    def test_poweroff(self, vbc: VBoxController):
        vbc.poweroff("VM")
        assert_call(vbc, ["controlvm", "VM", "poweroff"])

    def test_delete(self, vbc: VBoxController):
        vbc.delete("VM")
        assert_call(vbc, ["unregistervm", "VM", "--delete"])

    def test_is_running(self, vbc: VBoxController):
        vbc._get_running_vms = Mock(return_value=["VM"])
        assert vbc.is_running("VM")
        assert not vbc.is_running("VM2")

    def test_get_running_vms(self, vbc: VBoxController):
        return_value = "\n".join([
            "\"Attacker\" {8451900b-320a-43b4-9eb9-9bd6656f33ad}",
            "\"Client\" {4d0986c7-eabc-4cd3-a2f3-e28111a66ac1}",
            "\"Company Router\" {d75d3108-266b-420e-aa74-bc73f689ee9c}"
        ])
        vbc._vboxmanage_execute = Mock(return_value=return_value)
        vms = vbc._get_running_vms()
        assert_call(vbc, ["list", "runningvms"])
        assert vms == ["Attacker", "Client", "Company Router"]

    def test_get_vm_info(self, vbc: VBoxController):
        vbc._vboxmanage_execute = Mock(return_value=self._some_vbox_info_output())
        info = vbc._get_vm_info("VM")
        assert_call(vbc, ["showvminfo", "VM", "--machinereadable"])
        assert info["ostype"] == "Other Linux (32-bit)"
        assert info["macaddress1"] == "080027CA0E5D"
        assert info["IDE-1-0"] == "emptydrive"

    def test_get_macs(self, vbc: VBoxController):
        return_value = {
            "macaddress1": "0800278144CB",
            "macaddress2": "080027859405",
            "othervalue": "ABAB"
        }
        vbc._get_vm_info = Mock(return_value=return_value)
        macs = vbc.get_macs("VM")
        vbc._get_vm_info.assert_called_with("VM")
        assert set(macs) == {int("0800278144CB", 16), int("080027859405", 16)}

    def test_get_mac(self, vbc: VBoxController):
        return_value = {
            "macaddress1": "0800278144CB",
            "macaddress2": "080027859405",
            "othervalue": "ABAB"
        }
        vbc._get_vm_info = Mock(return_value=return_value)
        mac = vbc.get_mac("VM", if_id=1)
        vbc._get_vm_info.assert_called_with("VM")
        assert mac == int("0800278144CB", 16)

    def test_get_mac_with_if_id(self, vbc: VBoxController):
        return_value = {
            "macaddress1": "0800278144CB",
            "macaddress2": "080027859405",
            "othervalue": "ABAB"
        }
        vbc._get_vm_info = Mock(return_value=return_value)
        mac = vbc.get_mac("VM", if_id=2)
        vbc._get_vm_info.assert_called_with("VM")
        assert mac == int("080027859405", 16)

    def test_get_mac_exception(self, vbc: VBoxController):
        return_value = {
            "macaddress1": "0800278144CB",
            "macaddress2": "080027859405",
            "othervalue": "ABAB"
        }
        vbc._get_vm_info = Mock(return_value=return_value)
        with pytest.raises(VMMControllerException) as ei:
            vbc.get_mac("VirtMachine", if_id=3)
        assert "VirtMachine" in str(ei.value)
        assert "interface 3" in str(ei.value)

    def test_set_mac(self, vbc: VBoxController):
        new_mac = 0x0800278144CB
        vbc.set_mac("VM", new_mac)
        assert_call(vbc, ["modifyvm", "VM", "--macaddress1", "0800278144cb"])

    def test_set_mac_with_if_id(self, vbc: VBoxController):
        new_mac = 0x0800278144CB
        vbc.set_mac("VM", new_mac, if_id=2)
        assert_call(vbc, ["modifyvm", "VM", "--macaddress2", "0800278144cb"])

    def test_get_snapshots(self, vbc: VBoxController):
        return_value = self._some_snapshot_output()
        vbc._vboxmanage_execute = Mock(return_value=return_value)
        snapshots = vbc.get_snapshots("VM")
        assert_call(vbc, ["snapshot", "VM", "list", "--machinereadable"])
        assert "version 2" in snapshots
        assert "238006bc-a851-4b50-a151-3d9104d072c5" not in snapshots

    def test_get_snapshots_when_no_snapshots(self, vbc: VBoxController):
        vm_without_snapshot = "VM"

        def vbox_causes_exception(vbox_vector):
            if "snapshot" in vbox_vector and vm_without_snapshot in vbox_vector and "list" in vbox_vector:
                raise VMMControllerException("Some text....")
            else:
                pass
        vbc._vboxmanage_execute = Mock(side_effect=vbox_causes_exception)
        # get_vms may be used for hack
        vbc.get_vms = Mock(return_value=[vm_without_snapshot])
        snapshots = vbc.get_snapshots(vm_without_snapshot)
        assert snapshots == []

    def test_create_snapshot(self, vbc: VBoxController):
        vbc.create_snapshot("VM", "Snapshot")
        assert_call(vbc, ["snapshot", "VM", "take", "Snapshot"])

    def test_delete_snapshot(self, vbc: VBoxController):
        vbc.delete_snapshot("VM", "Snapshot")
        assert_call(vbc, ["snapshot", "VM", "delete", "Snapshot"])

    def test_restore_snapshot(self, vbc: VBoxController):
        vbc.restore_snapshot("VM", "Snapshot")
        assert_call(vbc, ["snapshot", "VM", "restore", "Snapshot"])

    def test_clone(self, vbc: VBoxController):
        vbc.clone("VM", "Snapshot", "VMClone")
        assert_call(vbc, [
            "clonevm", "VM", "--name", "VMClone",
            "--options", "link", "--snapshot", "Snapshot",
            "--register"
        ])

    def test_set_credentials(self, vbc: VBoxController):
        vbc.set_credentials("VM", "TheUser", "ThePassword", "TheDomain")
        assert_call(vbc, [
            "controlvm", "VM",
            "setcredentials", "TheUser", "ThePassword", "TheDomain"
        ])

    def _some_vbox_info_output(self):
        return """name="Company Router"
groups="/BREACHv4"
ostype="Other Linux (32-bit)"
UUID="d75d3108-266b-420e-aa74-bc73f689ee9c"
hardwareuuid="d75d3108-266b-420e-aa74-bc73f689ee9c"
memory=512
pagefusion="off"
vram=16
cpuexecutioncap=100
hpet="off"
chipset="piix3"
firmware="BIOS"
cpus=1
pae="off"
longmode="off"
triplefaultreset="off"
apic="on"
x2apic="off"
cpuid-portability-level=0
bootmenu="messageandmenu"
boot1="floppy"
boot2="dvd"
boot3="disk"
boot4="none"
acpi="on"
ioapic="on"
biosapic="apic"
biossystemtimeoffset=0
rtcuseutc="on"
hwvirtex="on"
nestedpaging="on"
largepages="off"
vtxvpid="on"
vtxux="on"
paravirtprovider="legacy"
effparavirtprovider="none"
VMState="poweroff"
VMStateChangeTime="2016-11-09T10:28:40.397000000"
monitorcount=1
accelerate3d="off"
accelerate2dvideo="off"
teleporterenabled="off"
teleporterport=0
teleporteraddress=""
teleporterpassword=""
tracing-enabled="off"
tracing-allow-vm-access="off"
tracing-config=""
autostart-enabled="off"
autostart-delay=0
defaultfrontend=""
storagecontrollername0="IDE"
storagecontrollertype0="PIIX4"
storagecontrollerinstance0="0"
storagecontrollermaxportcount0="2"
storagecontrollerportcount0="2"
storagecontrollerbootable0="on"
"IDE-1-0"="emptydrive"
"IDE-IsEjected"="off"
"IDE-1-1"="none"
intnet1="Internet"
macaddress1="080027CA0E5D"
cableconnected1="on"
nic1="intnet"
nictype1="Am79C973"
nicspeed1="0"
intnet2="DMZ"
macaddress2="0800279104ED"
cableconnected2="on"
nic2="intnet"
nictype2="Am79C973"
nicspeed2="0"
intnet3="Internal"
macaddress3="080027859405"
cableconnected3="on"
nic3="intnet"
nictype3="Am79C973"
nicspeed3="0"
hostonlyadapter4="vboxnet0"
macaddress4="080027D98E94"
cableconnected4="on"
nic4="hostonly"
nictype4="Am79C973"
nicspeed4="0"
nic5="none"
nic6="none"
nic7="none"
nic8="none"
hidpointing="usbtablet"
hidkeyboard="ps2kbd"
uart1="off"
uart2="off"
uart3="off"
uart4="off"
lpt1="off"
lpt2="off"
audio="pulse"
clipboard="disabled"
draganddrop="disabled"
vrde="off"
usb="on"
ehci="on"
xhci="off"
vcpenabled="off"
vcpscreens=0
GuestMemoryBalloon=0
"""

    def _some_snapshot_output(self):
        return """SnapshotName="clean userbehavior"
SnapshotUUID="81a0d214-e246-43f7-9095-95deb011bf47"
SnapshotName-1="set autologin"
SnapshotUUID-1="238006bc-a851-4b50-a151-3d9104d072c5"
SnapshotName-1-1="version 2"
SnapshotUUID-1-1="fc34bda5-6922-41cc-85cf-00bdccc64120"
SnapshotName-1-1-1="update Inits"
SnapshotUUID-1-1-1="cc8e5165-e7b8-4242-b007-c411e93a5e16"
SnapshotName-1-1-1-1="disabled ActKey"
SnapshotUUID-1-1-1-1="f100cdf7-b89a-42d7-9274-352aa71140eb"
SnapshotName-1-1-1-1-1="no autologin"
SnapshotUUID-1-1-1-1-1="131cb2ea-c3f3-4d01-a1e6-70fe83d6c3bc"
SnapshotName-1-1-1-1-1-1="no ctrl alt del"
SnapshotUUID-1-1-1-1-1-1="b4dc2196-9213-48bb-8c47-9902d3dde13c"
SnapshotName-1-1-1-1-1-1-1="installed GuestAdditions with autologin"
SnapshotUUID-1-1-1-1-1-1-1="123c7768-6588-4dfa-8949-21d1a33fb5b4"
SnapshotDescription-1-1-1-1-1-1-1="VBoxWindowsAdditions /with_autologin"
SnapshotName-1-1-1-1-1-1-1-1="logout from domain"
SnapshotUUID-1-1-1-1-1-1-1-1="2abd5903-b648-45d6-99dc-c921a1fb30fc"
SnapshotName-1-1-1-1-1-1-1-1-1="login on domain breach"
SnapshotUUID-1-1-1-1-1-1-1-1-1="0a166cc1-306b-4bf7-a8ff-8c81167d3a47"
SnapshotName-1-1-1-1-1-1-1-1-1-1="disable UAC, batch script"
SnapshotUUID-1-1-1-1-1-1-1-1-1-1="c1e76d49-0ec1-4704-98e9-15e624466b79"
SnapshotName-1-1-1-1-1-1-1-1-1-1-1="ipchange, rm batch"
SnapshotUUID-1-1-1-1-1-1-1-1-1-1-1="ecef4b2f-3aec-40d2-a1d0-1fe397f031eb"
SnapshotName-1-1-1-1-1-1-1-1-1-1-1-1="reset domain"
SnapshotUUID-1-1-1-1-1-1-1-1-1-1-1-1="c40df361-99ba-4dbc-8c26-d595b36cdeae"
SnapshotName-1-1-1-1-1-1-1-1-1-1-1-1-1="set default mac"
SnapshotUUID-1-1-1-1-1-1-1-1-1-1-1-1-1="a5235e33-0981-4da3-9bb2-25882b9543d7"
SnapshotName-1-1-1-1-1-1-1-1-1-1-1-1-1-1="update initscript"
SnapshotUUID-1-1-1-1-1-1-1-1-1-1-1-1-1-1="e5d35b49-6271-425e-920c-f94d5259b77f"
SnapshotName-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1="imdisk"
SnapshotUUID-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1="acf23d84-479c-4a4c-8c5e-ccd8f28b14c3"
CurrentSnapshotName="imdisk"
CurrentSnapshotUUID="acf23d84-479c-4a4c-8c5e-ccd8f28b14c3"
CurrentSnapshotNode="SnapshotName-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1"
"""


"""
["VBoxManage", "clonevm", self.father, "--name", c.vm_name,
                     "--options", "link", "--snapshot", "CloneSnapshot",
                     "--register"])
"""