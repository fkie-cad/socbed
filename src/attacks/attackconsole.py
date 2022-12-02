#!/usr/bin/env python3

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
import logging
import re
import shlex
import subprocess
import sys
import time
from argparse import ArgumentParser
from cmd import Cmd
from collections import OrderedDict
from random import choice
from subprocess import PIPE, SubprocessError

from colorama import Style
from veryprettytable import VeryPrettyTable

from attacks import implemented_attacks, AttackException
from attacks.printer import ConsolePrinter


class LogDict(OrderedDict):
    def __init__(*args, **kwds):
        OrderedDict.__init__(*args, **kwds)
        self, *args = args
        # event key should always be present and the first key to log
        self.setdefault("event", "unknown_event")
        self.move_to_end("event", last=False)

    def __str__(self):
        return "[{kv}]".format(
            kv=" ".join("{}=\"{}\"".format(key, value) for key, value in self.items()))


class LogDictLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        msg, kwargs = super().process(msg, kwargs)
        kwargs["extra"] = kwargs["extra"].copy()
        try:
            kwargs["extra"]["log_dict"] = kwargs.pop("log_dict")
        except KeyError:
            kwargs["extra"]["log_dict"] = LogDict()
        return msg, kwargs


class ISOFormatter(logging.Formatter):
    _tz_fix = re.compile(r"([+-]\d{2})(\d{2})$")

    def format(self, record):
        self._add_isotime_to_record(record)
        return super().format(record)

    @classmethod
    def _add_isotime_to_record(cls, record):
        isotime = datetime.datetime.fromtimestamp(record.created).isoformat()
        tz = cls._tz_fix.match(time.strftime("%z"))
        if time.timezone and tz:
            offset_hrs, offset_min = tz.groups()
            isotime += f"{offset_hrs}:{offset_min}"
        else:
            isotime += "Z"
        record.__dict__["isotime"] = isotime


logger = LogDictLoggerAdapter(logging.getLogger("tbfconsole"), extra={})


def setup_logging(level, log_file=None, log_to_console=False):
    original_logger = logger.logger  # type: logging.Logger
    original_logger.setLevel(level)
    if log_file:
        handler = logging.FileHandler(filename=log_file)
        fmt = "%(isotime)s %(name)s %(levelname)s %(log_dict)s %(message)s"
        handler.setFormatter(fmt=ISOFormatter(fmt=fmt))
        original_logger.addHandler(hdlr=handler)
    if log_to_console:
        handler = logging.StreamHandler()
        fmt = "[%(levelname)s] %(log_dict)s %(message)s"
        handler.setFormatter(fmt=ISOFormatter(fmt=fmt))
        original_logger.addHandler(hdlr=handler)


class SubAttackConsole(Cmd):
    logger = logger

    def __init__(self, attack_class, **kwargs):
        super().__init__(**kwargs)
        log_dict = LogDict(event="start_attack_console", attack=attack_class.info.name)
        self.logger.debug("Start SubAttackConsole", log_dict=log_dict)
        self.attack_class = attack_class
        self.options_class = self.attack_class.options_class
        self.attack_options = self.options_class._options()
        self.attack_option_descriptions = {
            option: self.options_class.__dict__[option]
            for option in self.attack_options}
        self.attack = self.attack_class(printer=ConsolePrinter())
        self.prompt = f"attackconsole ({self.attack_class.info.name}) > "

    def precmd(self, line):
        if not self._stdin_is_a_tty():
            print(line)
        return super().precmd(line)

    def do_info(self, arg):
        print(self._headline("Attack Info"))
        v = VeryPrettyTable()
        v.align = "l"
        v.field_names = ["Name", "Description"]
        v.add_row([self.attack_class.info.name, self.attack_class.info.description])
        print(v)

    def do_options(self, arg):
        print(self._headline("Attack Options"))
        v = VeryPrettyTable()
        v.align = "l"
        v.field_names = ["Name", "Current Setting", "Description"]
        for option in self.attack_options:
            current_setting = str(self.attack.options.__getattribute__(option))
            description = self.attack_option_descriptions[option]
            v.add_row([option, current_setting, description])
        print(v)

    def do_set(self, arg):
        if len(shlex.split(arg)) == 2:
            option, value = shlex.split(arg)[:2]
            if option in self.attack_option_descriptions.keys():
                self.attack.options.__setattr__(option, value)
            else:
                print(f"*** Unknown option: {option}")
        else:
            print("*** Invalid number of option arguments\n*** Usage: set <option> <value>")

    def complete_set(self, text, line, begidx, endidx):
        opt = line.split(" ")[1].strip()
        if opt in self.attack_option_descriptions.keys():
            return [
                option
                for option in self.attack.options.__getattribute__(f"{opt}_choices")
                if option.startswith(text)
            ]
        return [option + " " for option in self.attack_option_descriptions.keys() if
                option.startswith(text)]

    def do_reset(self, _arg):
        self.attack.options._set_options_to_none()
        self.attack.options._set_defaults()

    def do_run(self, arg):
        attack_name = self.attack.info.name
        log_dict = LogDict(event="run_attack", attack=attack_name)
        log_dict.update(sorted(self.attack.options.__dict__.items()))
        self.logger.info("Run attack", log_dict=log_dict)
        try:
            self.attack.run()
        except AttackException as e:
            print(f"*** Exception: {e}")
            log_dict.update(event="attack_failed", failed_with=str(e).replace("\n", " "))
            self.logger.info("Attack failed", log_dict=log_dict)
        except KeyboardInterrupt:
            self.attack.handle_keyboard_interrupt()
        else:
            log_dict.update(event="attack_succeeded")
            self.logger.info("Attack succeeded", log_dict=log_dict)

    def do_back(self, arg):
        log_dict = LogDict(event="exit_attack_console", attack=self.attack_class.info.name)
        self.logger.debug("Exit SubAttackConsole", log_dict=log_dict)
        return True

    def do_EOF(self, arg):
        return self.do_back(arg)

    def _headline(self, h):
        return "{}{}{}{}{}".format("\n", Style.DIM, h, "\n==================\n", Style.RESET_ALL)

    def _stdin_is_a_tty(self):
        return sys.stdin.isatty()


class AttackConsole(Cmd):
    prompt = "attackconsole > "
    sub_attack_console_class = SubAttackConsole
    attack_classes = {attack_class.info.name: attack_class for attack_class in implemented_attacks}
    logger = logger

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kwargs = kwargs
        log_dict = LogDict(event="start_tbf_console", attacks=",".join(self.attack_classes.keys()))
        self.logger.info("Start Console", log_dict=log_dict)

    def precmd(self, line):
        if not self._stdin_is_a_tty():
            print(line)
        return super().precmd(line)

    def do_ls(self, arg):
        print(self._headline("Attacks"))
        v = VeryPrettyTable()
        v.field_names = ["Name", "Description"]
        v.align["Name"] = "l"
        for attack_class in self.attack_classes.values():
            v.add_row([attack_class.info.name, attack_class.info.description])
        print(v.get_string(sortby="Name"))

    def do_use(self, arg):
        attack = arg
        if attack in self.attack_classes.keys():
            sub_attack_console = self.sub_attack_console_class(
                attack_class=self.attack_classes[attack], **self.kwargs)
            sub_attack_console.cmdloop()
        else:
            print(f"*** Unknown attack: {attack}")

    def complete_use(self, text, line, begidx, endidx):
        return [attack for attack in self.attack_classes.keys() if attack.startswith(text)]

    def do_sleep(self, arg):
        self.sleep(int(arg))

    def do_exit(self, arg):
        self.logger.info("Exit Console", log_dict=LogDict(event="exit_tbf_console"))
        return True

    def do_EOF(self, arg):
        return self.do_exit(arg)

    def _headline(self, h):
        return "{}{}{}{}{}".format("\n", Style.DIM, h, "\n==================\n", Style.RESET_ALL)

    def _stdin_is_a_tty(self):
        return sys.stdin.isatty()

    @staticmethod
    def sleep(secs):
        time.sleep(secs)


class IntroGenerator:
    default_fortune = ""

    def generate(self):
        fortune = self.wrap_in_cowsay(self.generate_fortune())
        intro = "\n".join([
            fortune,
            "+ -- - -= [\t BREACH Attack Console \t\t]",
            f"+ -- - -= [\t {len(implemented_attacks)} attack(s)          \t\t]",
            ""])
        return intro

    def generate_fortune(self):
        try:
            fortune = self.execute(["fortune", "-s"])
        except (SubprocessError, FileNotFoundError):
            logger.debug("No fortune found")
            return self.default_fortune
        else:
            return fortune

    def wrap_in_cowsay(self, msg):
        inappropriate_cows = ["head-in", "kiss", "sodomized", "telebears", "sodomized-sheep"]
        try:
            cows_list = self.execute(["cowsay", "-l"])
            cows = cows_list.split("\n", maxsplit=1)[1].split()
            good_cows = [c for c in cows if c not in inappropriate_cows]
            wrapped_msg = self.execute(["cowsay", "-f", choice(good_cows), msg])
        except (SubprocessError, FileNotFoundError):
            logger.debug("Could not wrap message in cowsay")
            return msg
        else:
            return wrapped_msg

    @staticmethod
    def execute(cmd_vector):
        return subprocess.run(cmd_vector, universal_newlines=True, stdout=PIPE).stdout


def parse_args(argv=None):
    parser = ArgumentParser(description="The AttackConsole")
    parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true", default=False,
        help="Increase output verbosity")
    parser.add_argument(
        "-l", "--log-file", dest="log_file", default=None,
        help="Write logs to a file instead of writing to console")
    return parser.parse_args(args=argv)


def main(argv=None):
    args = parse_args(argv=argv)
    setup_logging(level=logging.INFO, log_file=args.log_file, log_to_console=args.verbose)
    console = AttackConsole()
    try:
        console.cmdloop(intro=IntroGenerator().generate())
    except KeyboardInterrupt:
        print("\n*** Keyboard Interrupt, closing attackconsole.")
        console.do_exit(argv)


if __name__ == '__main__':
    main()
