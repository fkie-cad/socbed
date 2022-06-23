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


import pytest
import socket
from unittest.mock import patch

from attacks.attack import AttackInfo, AttackOptions, Attack


class PrinterSpy:
    def print(self, msg):
        self.last_msg = msg


class TestAttack:
    def test_run_is_abstract(self):
        with pytest.raises(NotImplementedError):
            Attack().run()

    def test_attack_class_knows_its_options_class(self):
        assert Attack.options_class == AttackOptions

    def test_attack_class_has_info(self):
        assert isinstance(Attack.info, AttackInfo)

    def test_attack_instance_has_options(self):
        attack = Attack()
        assert isinstance(attack.options, Attack.options_class)

    def test_options_as_parameter(self):
        options = AttackOptions()
        attack = Attack(options=options)
        assert attack.options == options

    def test_attack_can_print(self):
        Attack().print(msg="Hello World")

    def test_attack_has_default_printer_object(self):
        assert isinstance(Attack().printer, Attack.printer_class)

    def test_set_printer_via_parameter(self):
        p = PrinterSpy()
        attack = Attack(printer=p)
        msg = "Hello World"
        attack.print(msg=msg)
        assert p.last_msg == msg

    @patch("attacks.attack.Attack.interrupt_handler")
    def test_timeout_exception(self, _mock, capfd):
        attack = Attack()
        with attack.wrap_ssh_exceptions():
            raise socket.timeout
        out = capfd.readouterr()[0].split("\n")
        assert out[0] == "Timeout after 300s"
        assert not out[1]


class TestAttackInfo:
    def test_init(self):
        info = AttackInfo()
        assert info.name
        assert info.description


class SpecificAttackOptions(AttackOptions):
    option1 = "description1"
    option2 = "description2"


class SpecificAttackOptionsWithDefaults(SpecificAttackOptions):
    def _set_defaults(self):
        self.option1 = "value1"
        self.option2 = "value2"


class TestAttackOptions:
    def test_instance_attributes_default_to_none(self):
        options = SpecificAttackOptions()
        assert options.option1 is None
        assert options.option2 is None

    def test_class_attributed_have_descriptions(self):
        assert SpecificAttackOptionsWithDefaults.option1 == "description1"
        assert SpecificAttackOptionsWithDefaults.option2 == "description2"

    def test_instance_attributes_defaults_can_be_set(self):
        options = SpecificAttackOptionsWithDefaults()
        assert options.option1 == "value1"
        assert options.option2 == "value2"

    def test_instance_attributes_can_be_set_when_created(self):
        options = SpecificAttackOptionsWithDefaults(option1="other_value1", option2="other_value2")
        assert options.option1 == "other_value1"
        assert options.option2 == "other_value2"

    def test_get_options(self):
        {"option1", "option2"} == set(SpecificAttackOptionsWithDefaults._options())
