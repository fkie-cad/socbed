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

from init_tbf_client import Main, NetworkInterface


@pytest.fixture()
def main(tmpdir):
    mock_main_staticmethods()
    main = Main()
    mock_main_fields(main, str(tmpdir))
    return main


def mock_main_fields(main, tmp):
    main.client_dir = tmp


def mock_main_staticmethods():
    Main.execute = Mock(return_value=True)
    Main.execute_userbehavior = Mock()
    Main.get_ipconfig = Mock(return_value=ipconfig_output)
    Main.is_first_setup_phase_required = Mock(return_value=False)
    Main.is_second_setup_phase_required = Mock(return_value=False)


class TestMain:
    def test_run(self, main: Main):
        main.run(argv="")

    def test_discover_management_interface(self, main: Main):
        mif = main.get_management_interface()
        assert mif.name == "Local Area Connection 2"

    def test_get_interfaces(self, main: Main):
        interfaces = [
            NetworkInterface(
                name="Local Area Connection",
                mac=int("005056000001", 16),
                ip="172.16.1.1"),
            NetworkInterface(
                name="Local Area Connection 2",
                mac=int("005056000101", 16),
                ip="192.168.56.101")]
        assert set(interfaces) == set(main.get_interfaces())


# Sample output of "ipconfig /all"
# Management interface is "Local Area Connection 2"
ipconfig_output = """

Windows IP Configuration

   Host Name . . . . . . . . . . . . : CLIENT
   Primary Dns Suffix  . . . . . . . : breach.local
   Node Type . . . . . . . . . . . . : Hybrid
   IP Routing Enabled. . . . . . . . : No
   WINS Proxy Enabled. . . . . . . . : No
   DNS Suffix Search List. . . . . . : breach.local

Ethernet adapter Local Area Connection 2:

   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : Intel(R) PRO/1000 MT Desktop Adapter #2
   Physical Address. . . . . . . . . : 00-50-56-00-01-01
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::ad80:f976:130a:abc5%13(Preferred) 
   IPv4 Address. . . . . . . . . . . : 192.168.56.101(Preferred) 
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 
   DHCPv6 IAID . . . . . . . . . . . : 302514215
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-1E-86-20-ED-08-00-27-AF-78-72
   DNS Servers . . . . . . . . . . . : fec0:0:0:ffff::1%1
                                       fec0:0:0:ffff::2%1
                                       fec0:0:0:ffff::3%1
   NetBIOS over Tcpip. . . . . . . . : Enabled

Ethernet adapter Local Area Connection:

   Connection-specific DNS Suffix  . : breach.local
   Description . . . . . . . . . . . : Intel(R) PRO/1000 MT Desktop Adapter
   Physical Address. . . . . . . . . : 00-50-56-00-00-01
   DHCP Enabled. . . . . . . . . . . : Yes
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::b92d:4bbf:69a8:785f%11(Preferred) 
   IPv4 Address. . . . . . . . . . . : 172.16.1.1(Preferred) 
   Subnet Mask . . . . . . . . . . . : 255.255.0.0
   Lease Obtained. . . . . . . . . . : Monday, July 31, 2017 4:37:02 PM
   Lease Expires . . . . . . . . . . : Monday, July 31, 2017 5:36:58 PM
   Default Gateway . . . . . . . . . : 172.16.0.1
   DHCP Server . . . . . . . . . . . : 172.16.0.1
   DHCPv6 IAID . . . . . . . . . . . : 235405351
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-1E-86-20-ED-08-00-27-AF-78-72
   DNS Servers . . . . . . . . . . . : 172.16.0.1
   NetBIOS over Tcpip. . . . . . . . : Enabled

Tunnel adapter isatap.breach.local:

   Media State . . . . . . . . . . . : Media disconnected
   Connection-specific DNS Suffix  . : breach.local
   Description . . . . . . . . . . . : Microsoft ISATAP Adapter
   Physical Address. . . . . . . . . : 00-00-00-00-00-00-00-E0
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes

Tunnel adapter isatap.{D3D472CB-BF07-46FF-AA55-153EAE928929}:

   Media State . . . . . . . . . . . : Media disconnected
   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : Microsoft ISATAP Adapter #2
   Physical Address. . . . . . . . . : 00-00-00-00-00-00-00-E0
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes

"""
