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
from attacks.attack_hashdump import HashdumpAttack


@pytest.fixture()
def attack():
    HashdumpAttack.ssh_client_class = Mock
    attack = HashdumpAttack()
    attack.ssh_client.exec_command = Mock(return_value=(Mock(), [], []))
    return attack


class TestHashdumpAttack:
    def test_raise_exception_bad_output(self, attack: HashdumpAttack):
        attack.ssh_client.exec_command = Mock(return_value=(Mock(), ["Bad output"], []))
        with pytest.raises(AttackException):
            attack.run()

    def test_no_exception_good_output(self, attack: HashdumpAttack):
        indicator = ("breach:1000:aad3b435b51404eeaad3b435b51404ee:"
                     "2aca7635afdc3febc408bee6b89acf16:::")
        attack.ssh_client.exec_command = Mock(return_value=(Mock(), [indicator], []))
        attack.run()
