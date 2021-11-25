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


import datetime
import re
import time
from types import SimpleNamespace

import paramiko
import pytest

from attacks.printer import ListPrinter
from attacks.ssh import BREACHSSHClient, SSHTargets
from vmcontrol.sessionhandler import SessionHandler
from vmcontrol.vmmcontroller import VBoxController

pytestmark = [pytest.mark.systest, pytest.mark.longtest]


@pytest.fixture(scope="module")
def session():
    sh = SessionHandler(VBoxController())
    sh.start_session()
    time.sleep(600)
    yield
    sh.close_session()


class MachineProperties:
    @classmethod
    def get_os(cls, machine):
        try:
            ssh_client = BREACHSSHClient(target=machine)
            list_printer = ListPrinter()
            ssh_client.exec_command_on_target("lsb_release -a", list_printer)
            sys_info = "".join(list_printer.printed)
            if "14.04" in sys_info:
                return "Ubuntu 14.04"
            elif "16.04" in sys_info:
                return "Ubuntu 16.04"
            elif "Kali" in sys_info:
                return "Kali Linux"
            elif cls.check_if_machine_is_ip_cop(machine):
                return "IPCop"
            elif cls.check_if_machine_is_ip_fire(machine):
                return "IPFire"
            elif cls.check_if_machine_is_win7_system(machine):
                return "Windows 7"
            else:
                raise Exception("Can not determine os")
        except paramiko.ssh_exception.NoValidConnectionsError:
            raise Exception("Can not connect to machine. Check if machine is started.")

    @staticmethod
    def check_if_machine_is_ip_fire(machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target(
            "ls /var/ipfire && echo \"Directory found\"", list_printer)
        sys_info = "".join(list_printer.printed)
        if "Directory found" in sys_info:
            return True
        else:
            return False

    @staticmethod
    def check_if_machine_is_ip_cop(machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("ls /var/ipcop && echo \"Directory found\"", list_printer)
        sys_info = "".join(list_printer.printed)
        if "Directory found" in sys_info:
            return True
        else:
            return False

    @staticmethod
    def check_if_machine_is_win7_system(machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("cmd.exe /c ver", list_printer)
        sys_info = "".join(list_printer.printed)
        if "Version 6" in sys_info:
            return True
        else:
            return False


class NTPServer(SimpleNamespace):
    name = ""
    ip = ""


class NTPServers(SimpleNamespace):
    ipfire_pool_0 = NTPServer(name="0.ipcop.pool.ntp.org")
    ipfire_pool_1 = NTPServer(name="1.ipcop.pool.ntp.org")
    ipfire_pool_2 = NTPServer(name="2.ipcop.pool.ntp.org")
    internetrouter = NTPServer(name="internetrouter", ip="172.18.0.1")
    companyrouter = NTPServer(name="companyrouter", ip="172.16.0.1")


class NTPZones(SimpleNamespace):
    company_green_zone = NTPServers.companyrouter


class SSHTargetsForNtp(SimpleNamespace):
    attacker = SSHTargets.attacker
    attacker.authoritative_ntp_server = NTPServers.internetrouter

    company_router = SSHTargets.company_router
    company_router.authoritative_ntp_server = NTPServers.internetrouter

    dmz_server = SSHTargets.dmz_server
    dmz_server.authoritative_ntp_server = NTPServers.internetrouter

    log_server = SSHTargets.log_server
    log_server.authoritative_ntp_server = NTPZones.company_green_zone

    internal_server = SSHTargets.internal_server
    internal_server.authoritative_ntp_server = NTPZones.company_green_zone
    internet_router = SSHTargets.internet_router
    internet_router.authoritative_ntp_server = [
        NTPServers.ipfire_pool_0,
        NTPServers.ipfire_pool_1,
        NTPServers.ipfire_pool_2
    ]

    client_1 = SSHTargets.client_1
    client_1.name = "Client 1"
    client_1.authoritative_ntp_server = NTPZones.company_green_zone


server_machines = [
    SSHTargetsForNtp.dmz_server,
    SSHTargetsForNtp.log_server,
    SSHTargetsForNtp.internal_server
]

router_machines = [
    SSHTargetsForNtp.company_router,
    SSHTargetsForNtp.internet_router
]

client_machines = [
    SSHTargetsForNtp.client_1
]

machines_using_ntpd_without_routers = server_machines + [SSHTargetsForNtp.attacker]

machines_using_ntpd = server_machines + router_machines + [SSHTargetsForNtp.attacker]

all_machines = machines_using_ntpd + [SSHTargetsForNtp.client_1]


class Time:
    @classmethod
    def get_time(cls, machine):
        timer_start = time.time()
        actual_time = cls.request_actual_time(machine)
        timer_end = time.time()
        elapsed_time_of_time_request = timer_end - timer_start
        return actual_time, elapsed_time_of_time_request

    @staticmethod
    def request_actual_time(machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        machine.os = MachineProperties.get_os(machine)
        if machine.os in ["Ubuntu 14.04", "Ubuntu 16.04", "Kali Linux", "IPCop", "IPFire"]:
            return Time.request_actual_time_of_linux_machine(list_printer, ssh_client)
        elif machine.os in ["Windows 7"]:
            actual_time = Time.request_actual_time_of_win_client(list_printer, ssh_client)
            return actual_time
        else:
            raise Exception("Unknown OS")

    @staticmethod
    def request_actual_time_of_linux_machine(list_printer, ssh_client):
        ssh_client.exec_command_on_target("date --iso-8601=ns --utc", list_printer)
        actual_time = datetime.datetime.strptime(list_printer.printed[0][0:26],
                                                 "%Y-%m-%dT%H:%M:%S,%f")
        return actual_time

    @staticmethod
    def request_actual_time_of_win_client(list_printer, ssh_client):
        powershell_cmd_for_date = "Get-Date -Format FileDateTimeUniversal"
        ssh_client.exec_command_on_target(
            "powershell -InputFormat none -OutputFormat text -Command \"& {cmd}\"".format(
                cmd=powershell_cmd_for_date), list_printer)
        actual_time = datetime.datetime.strptime(list_printer.printed[0].strip(),
                                                 "%Y%m%dT%H%M%S%fZ")
        return actual_time

    @staticmethod
    def calculate_time_diff(first_machine, second_machine, print_time_diff=False):
        actual_time_first_machine, __ = Time.get_time(first_machine)

        actual_time_second_machine, elapsed_time_of_time_request = Time.get_time(
            second_machine)
        adjusted_actual_time_second_machine = \
            actual_time_second_machine \
            - datetime.timedelta(seconds=elapsed_time_of_time_request)
        time_diff = (
                adjusted_actual_time_second_machine -
                actual_time_first_machine).total_seconds()
        if print_time_diff:
            print("Datetime of " + first_machine.name + ":", actual_time_first_machine)
            print("Datetime of " + second_machine.name + ":", adjusted_actual_time_second_machine)
            print("Time difference (" + first_machine.name + " - " + second_machine.name + ") is: "
                  + str(time_diff) + " seconds \n")
        return time_diff


class NTPConfig:
    attacker_last_line_config = "server {ip} iburst".format(
        ip=SSHTargetsForNtp.attacker.authoritative_ntp_server.ip)

    company_router_full_raw_config = \
        """# Configuration file for ntpd, created by time.cgi.
            # Do not edit manually.
            #
            restrict default kod limited nomodify nopeer noquery notrap
            restrict 127.0.0.1
            # Our networks
            restrict 172.16.0.0 mask 255.255.0.0 nomodify noquery notrap
            restrict 192.168.56.0 mask 255.255.255.0 nomodify noquery notrap
            # Servers
            server {server_no_0} iburst
            # Local clock
            #server 127.127.1.0
            #fudge  127.127.1.0 stratum 7
            # Other settings
            driftfile /var/log/ntp/drift
            tinker panic 0
            logconfig +allsync +allclock +allsys""".format(
            server_no_0=SSHTargetsForNtp.company_router.authoritative_ntp_server.ip)

    dmz_server_last_line_config = "server {ip} iburst".format(
        ip=SSHTargetsForNtp.dmz_server.authoritative_ntp_server.ip)

    log_server_last_line_config = "server {ip} iburst".format(
        ip=SSHTargetsForNtp.log_server.authoritative_ntp_server.ip)

    internal_server_last_line_config = "server {ip} iburst".format(
        ip=SSHTargetsForNtp.internal_server.authoritative_ntp_server.ip)

    internet_router_full_raw_config = \
        """# Configuration file for ntpd, created by time.cgi.
            # Do not edit manually.
            #
            restrict default kod limited nomodify nopeer noquery notrap
            restrict 127.0.0.1
            # Our networks
            restrict 172.18.0.0 mask 255.255.0.0 nomodify noquery notrap
            restrict 192.168.56.0 mask 255.255.255.0 nomodify noquery notrap
            # Servers
            server {server_no_0} iburst
            server {server_no_1} iburst
            server {server_no_2} iburst
            # Local clock
            #server 127.127.1.0
            #fudge  127.127.1.0 stratum 7
            # Other settings
            driftfile /var/log/ntp/drift
            tinker panic 0
            logconfig +allsync +allclock +allsys""".format(
            server_no_0=SSHTargetsForNtp.internet_router.authoritative_ntp_server[0].name,
            server_no_1=SSHTargetsForNtp.internet_router.authoritative_ntp_server[1].name,
            server_no_2=SSHTargetsForNtp.internet_router.authoritative_ntp_server[2].name)

    @property
    def company_router_full_config(self):
        return self.convert_raw_config_text_to_list(self.company_router_full_raw_config)

    @property
    def internet_router_full_config(self):
        return self.convert_raw_config_text_to_list(self.internet_router_full_raw_config)

    @staticmethod
    def convert_raw_config_text_to_list(config_raw):
        config_list = []
        for line in config_raw.split("\n"):
            line_without_whitespace = line.lstrip()
            config_list.append(line_without_whitespace)
        return config_list


@pytest.mark.usefixtures("session")
class TestNTPConfig:
    ntpd_config_file = "/etc/ntp.conf"
    machines_for_full_config_check = router_machines
    machines_for_last_line_config_check = machines_using_ntpd_without_routers
    machines_for_windows_registry_check = [SSHTargetsForNtp.client_1]
    os_with_ntpstats = ["Ubuntu 14.04", "Ubuntu 16.04", "Kali Linux"]

    @pytest.mark.parametrize("machine", machines_using_ntpd, ids=lambda m: m.name)
    def test_config_of_ntpd(self, machine):
        actual_ntp_config = self.get_actual_ntp_config(machine)
        print(actual_ntp_config)
        expected_ntp_config = self.get_expected_ntp_config(machine)
        print(expected_ntp_config)
        self.compare_actual_to_expected_ntpd_config(machine, actual_ntp_config,
                                                    expected_ntp_config)
        machine.os = MachineProperties.get_os(machine)
        if machine.os in self.os_with_ntpstats:
            self.check_ntpstats_enabled(machine)

    def compare_actual_to_expected_ntpd_config(self, machine, actual_ntp_config,
                                               expected_ntp_config):
        if machine in self.machines_for_full_config_check:
            assert actual_ntp_config == expected_ntp_config
        elif machine in self.machines_for_last_line_config_check:
            correct_config_found = expected_ntp_config in actual_ntp_config[0]
            assert correct_config_found
        else:
            raise Exception("No config for machine defined")

    def get_actual_ntp_config(self, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        if machine in self.machines_for_full_config_check:
            ssh_client.exec_command_on_target(
                "cat {file}".format(file=self.ntpd_config_file),
                list_printer)
        elif machine in self.machines_for_last_line_config_check:
            ssh_client.exec_command_on_target(
                "tail -1 {file}".format(file=self.ntpd_config_file),
                list_printer)
        else:
            raise Exception("No config for machine defined")
        return list_printer.printed

    @staticmethod
    def get_expected_ntp_config(machine):
        if machine == SSHTargetsForNtp.attacker:
            return NTPConfig().attacker_last_line_config
        elif machine == SSHTargetsForNtp.company_router:
            return NTPConfig().company_router_full_config
        elif machine == SSHTargetsForNtp.dmz_server:
            return NTPConfig().dmz_server_last_line_config
        elif machine == SSHTargetsForNtp.log_server:
            return NTPConfig().log_server_last_line_config
        elif machine == SSHTargetsForNtp.internal_server:
            return NTPConfig().internal_server_last_line_config
        elif machine == SSHTargetsForNtp.internet_router:
            return NTPConfig().internet_router_full_config
        elif machine == SSHTargetsForNtp.client_1:
            return NTPConfig().client_1_registry_for_w32tm
        else:
            raise Exception("No config for machine defined")

    def check_ntpstats_enabled(self, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("cat {file}".format(file=self.ntpd_config_file),
                                          list_printer)
        ntpstats_enabled = False
        for line in list_printer.printed:
            if "statsdir /var/log/ntpstats/" in line:
                if "#" not in line:
                    ntpstats_enabled = True
                    print("Ntpstats is enabled:", line)
        assert ntpstats_enabled


class NtpdStatus:
    def check_if_ntpd_is_running(self, machine, print_ntpd_status):
        ntp_daemon_status = self.get_ntp_daemon_status(machine, print_ntpd_status)
        machine.os = MachineProperties.get_os(machine)
        ntp_daemon_is_running = (
                (machine.os in ["Ubuntu 14.04"] and
                 "NTP server is running" in ntp_daemon_status[0])
                or
                (machine.os in ["Ubuntu 16.04", "Kali Linux"] and
                 "Active: active (running)" in ntp_daemon_status[2])
                or
                (machine.os in ["IPCop", "IPFire"] and
                 "/usr/bin/ntpd" in ntp_daemon_status[0])
        )
        assert ntp_daemon_is_running

    @staticmethod
    def get_ntp_daemon_status(machine, print_ntpd_status):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        machine.os = MachineProperties.get_os(machine)
        if machine.os in ["Ubuntu 14.04", "Ubuntu 16.04", "Kali Linux"]:
            ssh_client.exec_command_on_target("sudo service ntp status", list_printer)
        elif machine.os in ["IPCop", "IPFire"]:
            ssh_client.exec_command_on_target("ps -ax | grep ntp", list_printer)
        else:
            raise Exception("Unknown OS or machine not started")
        if print_ntpd_status:
            for line in list_printer.printed:
                print(line)
        return list_printer.printed


@pytest.mark.usefixtures("session")
class TestNTPStateLinux(NtpdStatus):
    machines_using_company_or_internet_router_as_ntp_server = SSHTargetsForNtp.log_server, \
                                                              SSHTargetsForNtp.internal_server, \
                                                              SSHTargetsForNtp.dmz_server, \
                                                              SSHTargetsForNtp.attacker

    column_reach_value = -4  # for the "ntpq --peer" output

    @pytest.mark.parametrize("machine", machines_using_ntpd, ids=lambda m: m.name)
    def test_ntpd_is_running(self, machine, print_ntpd_status=True):
        NtpdStatus().check_if_ntpd_is_running(machine, print_ntpd_status)

    @pytest.mark.parametrize("machine", machines_using_company_or_internet_router_as_ntp_server,
                             ids=lambda m: m.name)
    def test_ntpq_if_correct_authoritative_ntp_server_is_used(self, machine):
        actual_ntp_server = self.get_ntp_server_peer_list(machine, output=True)
        expected_ntp_server = self.get_correct_indicator_for_ntpq_ntp_server_test(machine)
        ntp_server_indicator_found = expected_ntp_server in actual_ntp_server[2]
        print("\n" + "Expected authoritative NTP server is:", expected_ntp_server)
        print("Actual authoritative NTP server is:", actual_ntp_server[2].split()[0])
        ntpq_reach_value = int(actual_ntp_server[2].split()[self.column_reach_value])
        print("Ntpq reach value must be greater than 0, the actual value is:", ntpq_reach_value)
        assert ntp_server_indicator_found
        assert ntpq_reach_value > 0

    @staticmethod
    def get_ntp_server_peer_list(machine, output=False):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("ntpq --peer", list_printer)
        if output is True:
            for line in list_printer.printed:
                print(line)
        return list_printer.printed

    @staticmethod
    def get_correct_indicator_for_ntpq_ntp_server_test(machine):
        if machine == SSHTargetsForNtp.attacker:
            return SSHTargetsForNtp.attacker.authoritative_ntp_server.name
        elif machine == SSHTargetsForNtp.dmz_server:
            return SSHTargetsForNtp.dmz_server.authoritative_ntp_server.name
        elif machine == SSHTargetsForNtp.log_server:
            return SSHTargetsForNtp.log_server.authoritative_ntp_server.name
        elif machine == SSHTargetsForNtp.internal_server:
            return SSHTargetsForNtp.internal_server.authoritative_ntp_server.name
        elif machine == SSHTargetsForNtp.company_router:
            return SSHTargetsForNtp.company_router.authoritative_ntp_server.ip
        else:
            raise Exception("No authoritative NTP server for machine defined.")

    def check_ntpq_reach_value(self, machine):
        ntp_server_peer_list = self.get_ntp_server_peer_list(machine, output=False)
        ntpq_reach_value = int(ntp_server_peer_list[2].split()[self.column_reach_value])
        print("Ntpq reach value is:", ntpq_reach_value)
        assert ntpq_reach_value > 0

    def test_ntpq_if_company_router_is_using_internet_router_as_ntp_server(self):
        machine = SSHTargetsForNtp.company_router
        machine.os = MachineProperties.get_os(machine)
        if machine.os in ["IPCop"]:
            expected_ntp_server = self.get_correct_indicator_for_ntpq_ntp_server_test(machine)
        elif machine.os in ["IPFire"]:
            expected_ntp_server = "gateway"
        else:
            raise Exception("Unknown OS or machine not started")
        actual_ntp_server_peer_list = self.get_ntp_server_peer_list(machine, output=True)
        ntp_server_status_line = [line for line in actual_ntp_server_peer_list if
                                  expected_ntp_server in line]
        assert len(ntp_server_status_line) == 1
        ntp_server_status_line = ntp_server_status_line[0]
        ntpq_reach_value = int(ntp_server_status_line.split()[self.column_reach_value])
        print("\n" + "Expected authoritative NTP server is:", expected_ntp_server)
        print("Actual authoritative NTP server is:", ntp_server_status_line.split()[0])
        print("Ntpq reach value for " + expected_ntp_server + " is:", ntpq_reach_value)
        assert ntpq_reach_value > 0

    def test_ntpq_if_internet_router_is_using_ntp_servers(self):
        machine = SSHTargetsForNtp.internet_router
        actual_ntp_server_peer_list = self.get_ntp_server_peer_list(machine, output=True)
        try:
            ntp_peers_status = actual_ntp_server_peer_list[2:5]
        except IndexError:
            print("No valid peer list")
        print("\n" + "Expected: Ntpq reach values for NTP servers must be greater than 0")
        ntpq_reach_values = []
        for ntp_peer_status in ntp_peers_status:
            ntpq_reach_value = int(ntp_peer_status.split()[self.column_reach_value])
            ntpq_reach_values.append(ntpq_reach_value)
            assert ntpq_reach_value > 0
        print("Actual: Ntpq reach values are: " + str(ntpq_reach_values))

    @pytest.mark.parametrize("machine", machines_using_ntpd_without_routers, ids=lambda m: m.name)
    def test_timedatectl_status_if_correct_value_for_ntp_option(self, machine):
        timedatectl_actual_state = self.get_timedatectl_status_actual_state(machine)
        timedatectl_expected_state = self.get_timedatectl_status_expected_state(machine)
        ntp_is_enabled = timedatectl_expected_state["ntp_enabled_string"] in \
                         timedatectl_actual_state[
                             timedatectl_expected_state["ntp_enabled_line_index"]]
        assert ntp_is_enabled

    @staticmethod
    def get_timedatectl_status_actual_state(machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("timedatectl status", list_printer)
        for line in list_printer.printed:
            print(line)
        return list_printer.printed

    @staticmethod
    def get_timedatectl_status_expected_state(machine):
        machine.os = MachineProperties.get_os(machine)
        if machine.os in ["Ubuntu 14.04"]:
            return {
                "ntp_enabled_line_index": 4,
                "ntp_enabled_string": "NTP enabled: yes",
            }
        elif machine.os in ["Kali Linux"]:
            return {
                "ntp_enabled_line_index": 4,
                "ntp_enabled_string": "Network time on: yes",
            }
        elif machine.os in ["Ubuntu 16.04"]:
            return {
                "ntp_enabled_line_index": 4,
                "ntp_enabled_string": "Network time on: no",
                # because system should use ntpd, and should not use the default daemon timesyncd
            }
        else:
            raise Exception("No config for OS defined")


class W32timeStatus:
    def request_w32tm_status(self, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        powershell_cmd_for_date = "w32tm /query /status"
        ssh_client.exec_command_on_target(
            "powershell -InputFormat none -OutputFormat text -Command \"& {cmd}\"".format(
                cmd=powershell_cmd_for_date), list_printer)
        return list_printer.printed

    def convert_status_lines_to_dict(self, lines):
        key_value_pattern = re.compile("^(.*?): (.*)$")
        status_dict = {}
        for line in lines:
            m = key_value_pattern.search(line)
            if m:
                attribute = m.group(1)
                value = m.group(2).strip()
                status_dict[attribute] = value
            else:
                pass  # no attribute value pair
        return status_dict

    def get_ntp_last_sync_time(self):
        machine = SSHTargetsForNtp.client_1
        status_dict = self.convert_status_lines_to_dict(self.request_w32tm_status(machine))
        sync_time_string = status_dict["Last Successful Sync Time"]
        try:
            last_sync_time = datetime.datetime.strptime(sync_time_string, "%m/%d/%Y %I:%M:%S %p")
        except ValueError:
            print("No valid timestamp format")
            print("Last Successful Sync Time:", status_dict["Last Successful Sync Time"])
        return last_sync_time

    def get_sync_time_diff(self, last_sync_time, actual_time):
        time_diff = (actual_time - last_sync_time).total_seconds()
        return time_diff


@pytest.mark.usefixtures("session")
class TestNTPTimeComparison:
    max_test_duration_in_seconds = 1200
    default_acceptable_time_diff_in_seconds = 1.0
    acceptable_time_diff_client_vs_internet_router = 0.5
    machines_adopted_correct_time = set()

    machines_without_internet_router = server_machines + \
                                       [SSHTargetsForNtp.company_router] + \
                                       [SSHTargetsForNtp.attacker] + \
                                       client_machines

    timer_start = 0

    def test_time_diff_between_machines_and_internet_router(self):
        self.timer_start = time.time()

        while not len(self.machines_adopted_correct_time) == len(
                self.machines_without_internet_router):
            if self.get_test_duration() > self.max_test_duration_in_seconds:
                print("Abort test, maximum test time (" +
                      str(self.max_test_duration_in_seconds) + ") seconds) reached.")
                print("Only this machines adopted the correct time:",
                      self.machines_adopted_correct_time)
                break
            else:
                for machine in self.machines_without_internet_router:
                    machine.os = MachineProperties.get_os(machine)
                    if machine.os in ["Windows 7"]:
                        self.check_time_diff(machine,
                                             SSHTargetsForNtp.internet_router,
                                             self.acceptable_time_diff_client_vs_internet_router)
                    else:
                        self.check_time_diff(machine,
                                             SSHTargetsForNtp.internet_router,
                                             self.default_acceptable_time_diff_in_seconds)
            time.sleep(10)
        print("----------")
        print("Test duration: " + str(round(self.get_test_duration(), 2)) + " seconds")
        assert len(self.machines_adopted_correct_time) == len(self.machines_without_internet_router)

    def check_time_diff(self, first_machine, second_machine, acceptable_time_diff_in_seconds):
        time_diff = Time.calculate_time_diff(first_machine, second_machine, print_time_diff=True)
        if abs(time_diff) < acceptable_time_diff_in_seconds:
            self.machines_adopted_correct_time.add(first_machine.name)
        else:
            pass

    def get_test_duration(self):
        return time.time() - self.timer_start
