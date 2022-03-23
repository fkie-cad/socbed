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

from attacks import AttackException
from attacks.attack_sqlmap import SQLMapAttack

@pytest.fixture()
def attack():
    SQLMapAttack.ssh_client_class = Mock
    return SQLMapAttack()


class TestSQLMapAttack:
    def test_sqlmap_command(self, attack: SQLMapAttack):
        assert attack._sqlmap_command() == (
            "export COLUMNS=80; echo \"http://172.18.0.2/dvwa/vulnerabilities/sqli/?id=&Submit=Submit\" | "
            "sqlmap --purge --batch --dump")

    def test_raise_exception_bad_output(self, attack: SQLMapAttack):
        attack.exec_commands_on_target = lambda _: attack.printer.print("Bad output")
        with pytest.raises(AttackException):
            attack.run()

    def test_no_exception_good_output(self, attack: SQLMapAttack):
        indicator = "table 'dvwa.users' dumped to CSV file"
        attack.exec_commands_on_target = lambda _: attack.printer.print(indicator)
        attack.run()
