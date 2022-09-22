#! /usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import logging
import os
import re
import time
from collections import namedtuple
from subprocess import PIPE, run

from userbehavior import Userbehavior, ConfigBuilder, BreachSetup


def setup_logging():
    logging.Formatter.converter = time.localtime
    logging.Formatter.default_time_format = "%Y-%m-%dT%H:%M:%S"
    is_dst = time.daylight and time.localtime().tm_isdst > 0
    gmt_offset_secs = - (time.altzone if is_dst else time.timezone)
    gmt_offset_string = "{0:+03d}:00".format(gmt_offset_secs // 3600)
    logging.basicConfig(
        filename="userbehavior.log", level=logging.INFO,
        format="%(asctime)s" + gmt_offset_string + " %(name)s %(levelname)s %(message)s")


logger = logging.getLogger(__name__)


class Main:
    def __init__(self):
        self.args = None
        self.config_dir = "config"
        self.configs = None

    def run(self):
        self.parse_args(argv=None)
        self.init_configs()
        self.run_userbehavior()

    def parse_args(self, argv=None):
        parser = argparse.ArgumentParser(
            description="Run the userbehavior.")
        parser.add_argument(
            "--use-breach-setup", dest="use_breach_setup", action="store_const",
            const=True, default=False,
            help="use the default breach setup for this client")
        self.args = parser.parse_args(args=argv)

    def init_configs(self):
        self.configs = list()
        self.configs.extend(self.configs_from_dir(self.config_dir))
        if self.args.use_breach_setup:
            self.configs.extend(self.breach_configs())

    def run_userbehavior(self):
        ub = Userbehavior(configs=self.configs)
        ub.run()

    @staticmethod
    def breach_configs():
        return BreachSetup.from_mac(get_management_interface().mac).configs

    @staticmethod
    def configs_from_dir(config_dir):
        if os.path.isdir(config_dir):
            config_files = (
                os.path.join(config_dir, file)
                for file in os.listdir(config_dir)
                if file.endswith(".json"))
            cf = ConfigBuilder()
            configs = [cf.build_from_file(file) for file in config_files]
            return configs
        else:
            return []


NetworkInterface = namedtuple("NetworkInterface", ["name", "mac"])


def get_management_interface():
    interfaces = get_interfaces()
    for interface in interfaces:
        if (interface.mac % 0x10000) // 0x100 > 0:
            return interface
    else:
        raise Exception("Could not find management interface in interfaces")


def get_interfaces():
    regex = re.compile(
        r"(Ethernet adapter )(?P<ifname>[^\:]*):\n\n[\s\S]*?(?P<MAC>([0-9A-F]{2}[:-]){5}([0-9A-F]{2}))[\s\S]*?\n")
    ipconfig = run(
        ["ipconfig", "/all"], stdout=PIPE, universal_newlines=True,
        timeout=30, check=True).stdout
    matches = [match for match in regex.finditer(ipconfig)]
    interfaces = [NetworkInterface(m.group("ifname"), int(m.group("MAC").replace("-", ""), 16))
                  for m in matches]
    return interfaces


def main():
    setup_logging()
    Main().run()


if __name__ == "__main__":
    main()
