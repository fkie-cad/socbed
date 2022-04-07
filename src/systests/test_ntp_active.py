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


import datetime
import time

import pytest

from attacks.printer import ListPrinter
from attacks.ssh import BREACHSSHClient
from systests.test_ntp_passive import Time, MachineProperties, machines_using_ntpd_without_routers, \
    SSHTargetsForNtp, NTPConfig, server_machines, NtpdStatus
from vmcontrol.sessionhandler import SessionHandler
from vmcontrol.vmmcontroller import VBoxController

pytestmark = [pytest.mark.systest, pytest.mark.unstable]


@pytest.fixture(scope="module")
def session():
    sh = SessionHandler(VBoxController())
    sh.start_session()
    time.sleep(900)
    yield
    sh.close_session()


class NtpdControl:
    @classmethod
    def start_ntp_server(cls, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("service ntp start", list_printer)

    @classmethod
    def stop_ntp_server(cls, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("service ntp stop", list_printer)

    @classmethod
    def enable_network_time(cls, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("timedatectl set-ntp on", list_printer)

    @classmethod
    def disable_network_time(cls, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("timedatectl set-ntp off", list_printer)


class ActiveNTPTest:
    def shut_down_ntp_services(self, machine):
        machine.os = MachineProperties.get_os(machine)
        NtpdControl.stop_ntp_server(machine)
        if machine.os in ["Kali Linux"]:
            NtpdControl.disable_network_time(machine)
        else:
            pass
        timer_start = time.time()
        old_ntp_datetime, __ = Time.get_time(machine)
        return old_ntp_datetime, timer_start

    def restart_ntp_services(self, machine, sleep_time_after_restarting_ntp_services):
        machine.os = MachineProperties.get_os(machine)
        if machine.os in ["Kali Linux"]:
            NtpdControl.enable_network_time(machine)
        else:
            pass
        NtpdControl.start_ntp_server(machine)
        time.sleep(sleep_time_after_restarting_ntp_services)
        new_ntp_datetime, __ = Time.get_time(machine)
        timer_end = time.time()
        return new_ntp_datetime, timer_end

    def set_system_clock_back(self, machine, old_ntp_datetime, deferred_time_in_seconds):
        deferred_datetime_for_manual_time_setting = \
            old_ntp_datetime \
            - datetime.timedelta(seconds=deferred_time_in_seconds)
        self.set_time_manually(machine, deferred_datetime_for_manual_time_setting.time())
        actual_deferred_time, __ = Time.get_time(machine)
        time_difference = \
            actual_deferred_time \
            - deferred_datetime_for_manual_time_setting
        acceptable_time_difference = 3
        if abs(time_difference.total_seconds()) < acceptable_time_difference:
            deferring_time_successful = True
        else:
            deferring_time_successful = False
        assert deferring_time_successful
        return actual_deferred_time

    def set_time_manually(self, machine, time_a):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        set_time_round_up_to_seconds = str(time_a)[0:8]
        cmd = "date --utc -s {}".format(set_time_round_up_to_seconds)
        ssh_client.exec_command_on_target(cmd, list_printer)
        return list_printer


@pytest.mark.usefixtures("session")
class TestNTPTimeRegeneration(ActiveNTPTest):
    acceptable_timedelta_of_time_correction_test_in_seconds = 3
    deferred_time_in_seconds = 120
    sleep_time_after_restarting_ntp_services = 40
    max_attempts_for_time_check = 5

    timer_start = 0

    @pytest.mark.parametrize("machine", machines_using_ntpd_without_routers, ids=lambda m: m.name)
    def test_change_time_and_check_if_ntp_corrects_the_time(self, machine):
        test_passed = False
        NtpdStatus().check_if_ntpd_is_running(machine, print_ntpd_status=False)
        old_ntp_datetime, timer_start = self.shut_down_ntp_services(machine)
        print("Old NTP datetime before starting time correction test: {}".format(old_ntp_datetime))
        print("NTP services are stopped.")
        actual_deferred_time = self.set_system_clock_back(machine, old_ntp_datetime,
                                                          self.deferred_time_in_seconds)
        print("Setting the clock {} seconds back, ".format(self.deferred_time_in_seconds) +
              "so the deferred datetime is: {}".format(actual_deferred_time))
        for attempt in range(self.max_attempts_for_time_check):
            print("Attempt: {}".format(attempt))
            print("Restart NTP services.")
            new_ntp_datetime, timer_end = \
                self.restart_ntp_services(machine, self.sleep_time_after_restarting_ntp_services)
            elapsed_time_between_shut_down_and_restart_of_ntp_services = timer_end - timer_start
            print("New NTP datetime after NTP time correction: {}".format(new_ntp_datetime))
            system_timedelta_between_shut_down_and_restart_of_ntp_services = new_ntp_datetime - old_ntp_datetime
            timedelta = abs(
                system_timedelta_between_shut_down_and_restart_of_ntp_services.total_seconds() -
                elapsed_time_between_shut_down_and_restart_of_ntp_services)
            print("Timedelta: {} seconds".format(timedelta))
            if (timedelta < self.acceptable_timedelta_of_time_correction_test_in_seconds):
                print("Timedelta is less than {} seconds, so test is passed.".format(
                    self.acceptable_timedelta_of_time_correction_test_in_seconds))
                test_passed = True
                break
            else:
                print("Timedelta is greater than {} seconds, so next attempt (retarting NTP services again).".format(
                    self.acceptable_timedelta_of_time_correction_test_in_seconds))
            time.sleep(10)
        assert test_passed == True


@pytest.mark.usefixtures("session")
class TestDistributingFakeTime(ActiveNTPTest):
    config_local_clock = \
        """# Configuration file for ntpd, created by time.cgi.
            # Do not edit manually.
            #
            restrict default kod limited nomodify nopeer noquery notrap
            restrict 127.0.0.1
            # Our networks
            restrict 172.18.0.0 mask 255.255.0.0 nomodify noquery notrap
            restrict 192.168.56.0 mask 255.255.255.0 nomodify noquery notrap
            # Servers
            #server 0.ipcop.pool.ntp.org iburst
            #server 1.ipcop.pool.ntp.org iburst
            #server 2.ipcop.pool.ntp.org iburst
            # Local clock
            server 127.127.1.0
            fudge  127.127.1.0 stratum 2
            # Other settings
            driftfile /var/log/ntp/drift
            tinker panic 0
            logconfig +allsync +allclock +allsys"""

    max_test_duration_in_seconds = 3600
    deferred_time_in_seconds = 120
    acceptable_time_diff_in_seconds = 3
    test_machines = server_machines + \
                    [SSHTargetsForNtp.company_router] + \
                    [SSHTargetsForNtp.attacker]
    # client machine can not be tested because "Kiss of Death" of Nettime

    timer_start = 0

    def test_if_fake_time_is_distributed(self):
        self.timer_start = time.time()
        self.inject_false_local_time_on_internet_router(SSHTargetsForNtp.internet_router)
        time.sleep(30)
        self.restart_ntp_service_of_company_router()
        time.sleep(60)
        self.restart_all_services_of_ntp_clients()
        time.sleep(30)
        self.check_if_machines_adopted_fake_time()

    def inject_false_local_time_on_internet_router(self, machine):
        self.stop_ntpd_on_ip_cop(machine)
        self.change_ntp_config_to_local_clock(machine)
        old_ntp_datetime, __ = Time.get_time(machine)
        print("Old NTP datetime before injecting false local time: {}".format(old_ntp_datetime))
        actual_deferred_time = self.set_system_clock_back(machine, old_ntp_datetime,
                                                          self.deferred_time_in_seconds)
        print("The injected false local time is " +
              str(self.deferred_time_in_seconds) + " seconds before the old NTP datetime.")
        print("Injected false local clock time:", actual_deferred_time)
        self.start_ntpd_on_ip_cop(machine)

    def stop_ntpd_on_ip_cop(self, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("killall ntpd | echo 'ntpd killed'", list_printer)
        response = "".join(list_printer.printed)
        if "ntpd killed" not in response:
            raise Exception("Can not change ntp.conf")

    def change_ntp_config_to_local_clock(self, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ntp_conf_list = NTPConfig.convert_raw_config_text_to_list(self.config_local_clock)
        ntp_conf_str = "\n".join(ntp_conf_list)
        cmd = "echo -e '{}' > /etc/ntp.conf && echo 'ntp.conf changed'".format(ntp_conf_str)
        ssh_client.exec_command_on_target(cmd, list_printer)
        response = "".join(list_printer.printed)
        if "ntp.conf changed" not in response:
            raise Exception("Can not change ntp.conf")

    def start_ntpd_on_ip_cop(self, machine):
        ssh_client = BREACHSSHClient(target=machine)
        list_printer = ListPrinter()
        ssh_client.exec_command_on_target("/usr/bin/ntpd | echo 'ntpd started'", list_printer)
        response = "".join(list_printer.printed)
        if "ntpd started" not in response:
            raise Exception("Can not change ntp.conf")

    def restart_ntp_service_of_company_router(self):
        self.stop_ntpd_on_ip_cop(SSHTargetsForNtp.company_router)
        self.start_ntpd_on_ip_cop(SSHTargetsForNtp.company_router)

    def restart_all_services_of_ntp_clients(self):
        for machine in machines_using_ntpd_without_routers:
            NtpdControl().stop_ntp_server(machine)
            NtpdControl().start_ntp_server(machine)
        time.sleep(5)
        self.check_if_ntp_services_are_running(machine)

    def check_if_ntp_services_are_running(self, machine):
        machine.os = MachineProperties.get_os(machine)
        if machine.os in ["Ubuntu 14.04", "Ubuntu 16.04", "Kali Linux", "IPCop"]:
            NtpdStatus().check_if_ntpd_is_running(machine, print_ntpd_status=False)
        else:
            pass

    def check_if_machines_adopted_fake_time(self):
        machines_adopted_fake_time = set()
        print("The test passes for each machine, if a machine has a time difference less than " +
              str(self.acceptable_time_diff_in_seconds) + " seconds against the NTP fake time.")
        print("----------")
        while not len(machines_adopted_fake_time) == len(self.test_machines):
            if self.get_test_duration() > self.max_test_duration_in_seconds:
                print("Abort test, maximum test time (" +
                      str(self.max_test_duration_in_seconds) + ") seconds) reached.")
                print("Only this machines adopted the fake time:", machines_adopted_fake_time)
                break
            else:
                for machine in self.test_machines:
                    time_diff = Time.calculate_time_diff(machine,
                                                         SSHTargetsForNtp.internet_router,
                                                         print_time_diff=False)
                    if abs(time_diff) < self.acceptable_time_diff_in_seconds:
                        if machine.name not in machines_adopted_fake_time:
                            print("The " + machine.name +
                                  " adopted the fake time. It has been measurement after " +
                                  str(round(self.get_test_duration(), 2)) + " seconds. " +
                                  "Time diff against NTP fake time: " + str(time_diff))
                            machines_adopted_fake_time.add(machine.name)
                        else:
                            pass
                    else:
                        pass
            self.restart_all_services_of_ntp_clients()
            time.sleep(10)
        print("----------")
        print("Test duration: " + str(round(self.get_test_duration(), 2)) + " seconds")
        assert len(machines_adopted_fake_time) == len(self.test_machines)

    def get_test_duration(self):
        return time.time() - self.timer_start
