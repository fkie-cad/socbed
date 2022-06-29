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


from attacks.ssh import SSHTarget, BREACHSSHClient


class MockPrinter:
    def __init__(self):
        self.lines = []

    def print(self, s):
        self.lines.append(s)


class MockStdin:
    def __init__(self):
        self.lines = []

    def write(self, line):
        self.lines.append(line)


class MockChannelFile:
    def __init__(self, content, channel):
        self.lines = []
        self.file_content = content
        self.channel = channel

    def __iter__(self):
        return iter(self.file_content)

    def read(self, _):
        res = self.file_content.pop(0).encode()
        if len(self.file_content) < 1:
            self.channel.buffer_full = False
            self.channel.exited = True
        return res


class MockTransport:
    def __init__(self):
        self.remote_version = "SSH-2.0-OpenSSH_7.4p1 Debian-5"


class MockChannel:
    def __init__(self, exit_code=0):
        self.buffer_full = True
        self.exited = False
        self.exit_code = exit_code
        self._transport = MockTransport()

    def exit_status_ready(self):
        return self.exited

    def recv_ready(self):
        return self.buffer_full

    def recv_exit_status(self):
        return self.exit_code


class TestBREACHSSHClient:
    def test_breachsshclient(self):
        ssh_target_1 = SSHTarget(hostname="myhost", port=1337, username="john", password="doe")
        ssh_client_1 = BREACHSSHClient(ssh_target_1)
        assert ssh_client_1 is not None
        assert ssh_client_1.target.hostname == "myhost"
        assert ssh_client_1.target.port == 1337
        assert ssh_client_1.target.username == "john"
        assert ssh_client_1.target.password == "doe"

        ssh_target_2 = SSHTarget(hostname="somewhere")
        ssh_client_2 = BREACHSSHClient(ssh_target_2)
        assert ssh_client_2 is not None
        assert ssh_client_2.target.hostname == "somewhere"
        assert ssh_client_2.target.port == 22
        assert ssh_client_2.target.username == "root"
        assert ssh_client_2.target.password == "breach"

    def test_print_output(self):
        mock_printer = MockPrinter()
        output = MockChannelFile(
            list(" This is a test \n\tof the print_output function\t\n"), MockChannel()
        )

        ssh_client = BREACHSSHClient()
        ssh_client._transport = MockTransport()
        ssh_client.print_output(output, mock_printer)
        assert mock_printer.lines == list(" This is a test \n\tof the print_output function\t\n")

    def test_write_lines(self):
        mock_stdin = MockStdin()
        lines = ["Hallo", "Welt"]
        BREACHSSHClient.write_lines(mock_stdin, lines)
        assert mock_stdin.lines == ["Hallo\n", "Welt\n"]

    def test_set_envs(self):
        ssh_client = BREACHSSHClient(SSHTarget())
        ssh_client._transport = MockTransport()
        assert (
            ssh_client.set_envs("sudo touch file.txt") == "sudo PYTHONUNBUFFERED=1 touch file.txt"
        )
        assert ssh_client.set_envs("touch file.txt") == "PYTHONUNBUFFERED=1 touch file.txt"
