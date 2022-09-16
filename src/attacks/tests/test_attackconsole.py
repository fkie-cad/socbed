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
import traceback

from contextlib import redirect_stdout
from unittest.mock import Mock, patch, MagicMock

import io
import pytest

import attacks
from attacks.attack import Attack, AttackOptions, AttackInfo, AttackException
from attacks.attackconsole import AttackConsole, SubAttackConsole, parse_args


class FakeAttackOptions(AttackOptions):
    fake_option = "desc"
    other_fake_option = "desc2"


class FakeAttack(Attack):
    info = AttackInfo(name="fake_attack")
    options_class = FakeAttackOptions
    run = Mock()


def _raise(exception):
    raise exception


@pytest.fixture()
def ac():
    FakeAttack.run.reset_mock()
    return SubAttackConsole(attack_class=FakeAttack)


class LoggerSpy:
    def __init__(self):
        self.last_msg = None
        self.last_log_dict = None

    def info(self, msg, log_dict):
        self.last_msg = msg
        self.last_log_dict = log_dict


class TestSubAttackConsole:
    def test_attributes(self):
        attack_class = FakeAttack
        console = SubAttackConsole(attack_class=attack_class)
        assert console.attack_class == attack_class
        assert console.options_class == attack_class.options_class
        assert isinstance(console.attack, attack_class)

    def test_set_options(self, ac: SubAttackConsole):
        ac.onecmd("set fake_option some_value")
        assert ac.attack.options.fake_option == "some_value"

    def test_do_not_set_unknown_options(self, ac: SubAttackConsole):
        ac.onecmd("set unknown_option bla")
        assert "unknown_option" not in ac.attack.__dict__

    def test_run(self, ac: SubAttackConsole):
        ac.onecmd("run")
        assert ac.attack.run.called

    @patch("attacks.Attack.handle_interrupt")
    def test_keyboard_interrupt_is_caught(self, ac: SubAttackConsole):
        FakeAttack.run = Mock(side_effect=lambda: _raise(KeyboardInterrupt))
        ac.onecmd("run")
        assert True  # No Exception is thrown

    def test_run_attack_exception_is_caught(self, ac: SubAttackConsole):
        FakeAttack.run = Mock(side_effect=lambda: _raise(AttackException()))
        ac.onecmd("run")
        assert True  # No Exception is thrown

    def test_attack_logging(self, ac: SubAttackConsole):
        ac.logger = LoggerSpy()
        ac.attack.run = lambda: None
        ac.onecmd("set fake_option some@bla.de")
        ac.onecmd("set other_fake_option \"Name of target\"")
        ac.onecmd("run")
        assert ac.logger.last_msg == "Attack succeeded"
        kv_str = " ".join([
            "event=\"attack_succeeded\"",
            "attack=\"fake_attack\"",
            "fake_option=\"some@bla.de\"",
            "other_fake_option=\"Name of target\""])
        assert str(ac.logger.last_log_dict) == "[" + kv_str + "]"

    @pytest.mark.parametrize("cmd", ["info", "options", "back"])
    def test_other_commands_work(self, ac: SubAttackConsole, cmd):
        ac.onecmd(cmd)

    def test_print_if_stdin_is_not_a_tty(self, ac: SubAttackConsole):
        ac._stdin_is_a_tty = Mock(return_value=False)
        ac.cmdqueue = ["set fake_option some_value", "back"]
        f = io.StringIO()
        with redirect_stdout(f):
            ac.cmdloop()
        out = f.getvalue()
        assert "set fake_option some_value" in out

    def test_no_print_if_stdin_is_a_tty(self, ac: SubAttackConsole):
        ac._stdin_is_a_tty = Mock(return_value=True)
        ac.cmdqueue = ["set fake_option some_value", "back"]
        f = io.StringIO()
        with redirect_stdout(f):
            ac.cmdloop()
        out = f.getvalue()
        assert "set fake_option some_value" not in out


class AttackConsoleForTesting(AttackConsole):
    attack_classes = {FakeAttack.info.name: FakeAttack}
    sub_attack_console_class = Mock()
    sleep = Mock()


@pytest.fixture()
def tbfc():
    tbf_console = AttackConsoleForTesting()
    tbf_console.sub_attack_console_class.reset_mock()
    tbf_console.sleep.reset_mock()
    return tbf_console


class TestTBFConsole:
    def test_use_known_attack(self, tbfc: AttackConsoleForTesting):
        tbfc.onecmd("use fake_attack")
        kwargs = {"attack_class": FakeAttack}
        kwargs.update(tbfc.kwargs)
        tbfc.sub_attack_console_class.assert_called_with(**kwargs)

    def test_do_not_use_unknown_attack(self, tbfc: AttackConsoleForTesting):
        tbfc.onecmd("use unknown_attack")
        assert not tbfc.sub_attack_console_class.called

    def test_sleep(self, tbfc: AttackConsoleForTesting):
        tbfc.onecmd("sleep 42")
        tbfc.sleep.assert_called_with(42)

    @pytest.mark.parametrize("cmd", ["ls", "exit"])
    def test_other_commands_work(self, tbfc: AttackConsoleForTesting, cmd):
        tbfc.onecmd(cmd)

    def test_print_if_stdin_is_not_a_tty(self, tbfc: AttackConsoleForTesting):
        tbfc._stdin_is_a_tty = Mock(return_value=False)
        tbfc.cmdqueue = ["use fake_attack", "exit"]
        f = io.StringIO()
        with redirect_stdout(f):
            tbfc.cmdloop()
        out = f.getvalue()
        assert "use fake_attack" in out

    def test_no_print_if_stdin_is_a_tty(self, tbfc: AttackConsoleForTesting):
        tbfc._stdin_is_a_tty = Mock(return_value=True)
        tbfc.cmdqueue = ["use fake_attack", "exit"]
        f = io.StringIO()
        with redirect_stdout(f):
            tbfc.cmdloop()
        out = f.getvalue()
        assert "use fake_attack" not in out


class TestArgs:
    def test_default_arguments(self):
        args = parse_args(argv=[])
        assert args.log_file is None
        assert not args.verbose

    def test_log_file(self):
        args = parse_args(argv=["--log-file", "some_file", "--verbose"])
        assert args.log_file == "some_file"
        assert args.verbose
