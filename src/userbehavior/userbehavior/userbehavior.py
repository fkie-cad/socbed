#! /usr/bin/python3
# -*- coding: utf-8 -*-
import json
import os
import threading

from userbehavior.browsing import BrowsingConfig, Browsing
from userbehavior.filing import FilingConfig, Filing
from userbehavior.mailing import MailingConfig, Mailing
from userbehavior.usbing import UsbingConfig, Usbing


class Userbehavior:
    def __init__(self, configs):
        self.behavior_configs = configs
        self._runners = None

    def run(self):
        self._init_runners()
        self._create_threads()
        self._run_threads()
        self._wait_for_threads()

    def _init_runners(self):
        rb = RunnerBuilder()
        self._runners = [rb.build(config) for config in self.behavior_configs]

    def _create_threads(self):
        self._threads = [threading.Thread(target=r.run) for r in self._runners]

    def _run_threads(self):
        for thread in self._threads:
            thread.start()

    def _wait_for_threads(self):
        for thread in self._threads:
            if thread.is_alive():
                thread.join()


class ConfigBuilder:
    behavior_config_classes = {
        "browsing": BrowsingConfig,
        "mailing": MailingConfig,
        "filing": FilingConfig,
        "usbing": UsbingConfig}

    def build(self, d):
        behavior_config_class = self.behavior_config_classes[d["behavior"]]
        return behavior_config_class.from_dict(d)

    def build_from_file(self, file):
        with open(file) as f:
            d = json.load(f)
        path, filename = os.path.split(file)
        name, behavior, format = filename.split(".")
        d["behavior"] = behavior
        d["name"] = name
        return self.build(d)


class Runner:
    def __init__(self, behavior, config):
        self.behavior = behavior
        self.config = config

    def run(self):
        self.behavior.run()


class RunnerBuilder:
    behavior_classes = {
        BrowsingConfig.__name__: Browsing,
        MailingConfig.__name__: Mailing,
        FilingConfig.__name__: Filing,
        UsbingConfig.__name__: Usbing}

    def build(self, config):
        behavior_class = self.behavior_classes[type(config).__name__]
        runner = Runner(behavior=behavior_class.from_config(config=config), config=config)
        return runner
