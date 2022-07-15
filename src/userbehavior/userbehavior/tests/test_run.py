#! /usr/bin/python3
# -*- coding: utf-8 -*-
import json
import os
from unittest.mock import Mock

import pytest

from userbehavior.browsing import BrowsingConfig, BrowserConfig, Browsing, BrowsingProfileConfig
from userbehavior.filing import FilerConfig, FilingConfig, Filing, FilingProfileConfig
from userbehavior.mailing import MailingConfig, MailerConfig, Mailing, MailingProfileConfig
from userbehavior.run import Main
from userbehavior.usbing import UsbingConfig, UsbDeviceConfig, Usbing, UsbingProfileConfig
from userbehavior.userbehavior import Userbehavior, ConfigBuilder, Runner, RunnerBuilder


class TestUserbehavior:
    def test_init(self):
        Userbehavior(configs=[])

    def test_config_to_runners(self):
        test_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_config")
        configs = self.generate_test_configs(test_config_dir)
        ub = Userbehavior(configs=configs)
        ub._init_runners()
        assert any(isinstance(r.behavior, Browsing) for r in ub._runners)
        assert any(isinstance(r.behavior, Mailing) for r in ub._runners)
        assert any(isinstance(r.behavior, Filing) for r in ub._runners)
        assert any(isinstance(r.behavior, Usbing) for r in ub._runners)

    def generate_test_configs(self, test_config_dir):
        if os.path.isdir(test_config_dir):
            config_files = (
                os.path.join(test_config_dir, file)
                for file in os.listdir(test_config_dir)
                if file.endswith(".json"))
            cf = ConfigBuilder()
            configs = [cf.build_from_file(file) for file in config_files]
            return configs
        else:
            raise AssertionError("Could not find directory with test config files...")


@pytest.fixture()
def m():
    return Main()


class TestConfigBuilder:
    def test_init(self):
        cf = ConfigBuilder()

    @pytest.mark.parametrize("b,bcc", [
        ("browsing", BrowsingConfig),
        ("mailing", MailingConfig),
        ("filing", FilingConfig),
        ("usbing", UsbingConfig)])
    def test_behavior_config_classes(self, b, bcc):
        assert ConfigBuilder.behavior_config_classes[b] == bcc

    def test_build_browsing_config(self):
        cf = ConfigBuilder()
        d = {
            "behavior": "browsing",
            "profile": {},
            "browser": {"implementation": "NullBrowser"}}
        assert isinstance(cf.build(d), BrowsingConfig)

    def test_build_mailing_config(self):
        cf = ConfigBuilder()
        d = {
            "behavior": "mailing",
            "profile": {},
            "mailer": {"implementation": "NullMailer"}}
        assert isinstance(cf.build(d), MailingConfig)

    def test_build_filing_config(self):
        cf = ConfigBuilder()
        d = {
            "behavior": "filing",
            "profile": {},
            "filer": {"implementation": "NullFiler"}}
        assert isinstance(cf.build(d), FilingConfig)

    def test_build_usbing_config(self):
        cf = ConfigBuilder()
        d = {
            "behavior": "usbing",
            "profile": {},
            "usb_device": {"implementation": "NullUsbDevice"}}
        assert isinstance(cf.build(d), UsbingConfig)

    def test_build_from_file(self, tmpdir):
        cf = ConfigBuilder()
        dir = str(tmpdir)
        filename = "my.browsing.json"
        path = os.path.join(dir, filename)
        d = {"profile": {}, "browser": {"implementation": "NullBrowser"}}
        with open(path, "w+") as f:
            json.dump(d, f)
        bc = cf.build_from_file(path)
        assert isinstance(bc, BrowsingConfig)


class TestMain:
    def test_parse_args(self, m: Main):
        argv = ["--use-breach-setup"]
        m.parse_args(argv)
        assert m.args.use_breach_setup is True

    def test_init_configs(self, m: Main):
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_config")
        assert m.configs_from_dir(config_dir)


class TestRunner:
    def test_run(self):
        r = Runner(None, None)
        r.behavior = Mock()
        r.behavior.run = Mock()
        r.run()
        assert r.behavior.run.called


@pytest.fixture()
def rb():
    return RunnerBuilder()


class TestRunnerBuilder:
    def test_build_browsing(self, rb: RunnerBuilder):
        config = BrowsingConfig(
            profile_config=BrowsingProfileConfig(),
            browser_config=BrowserConfig())
        runner = rb.build(config=config)
        assert isinstance(runner.behavior, Browsing)

    def test_build_mailing(self, rb: RunnerBuilder):
        config = MailingConfig(
            profile_config=MailingProfileConfig(),
            mailer_config=MailerConfig())
        assert isinstance(rb.build(config=config).behavior, Mailing)

    def test_build_filing(self, rb: RunnerBuilder):
        config = FilingConfig(
            profile_config=FilingProfileConfig(),
            filer_config=FilerConfig())
        assert isinstance(rb.build(config=config).behavior, Filing)

    def test_build_usbing(self, rb: RunnerBuilder):
        config = UsbingConfig(
            profile_config=UsbingProfileConfig(),
            usb_device_config=UsbDeviceConfig())
        assert isinstance(rb.build(config=config).behavior, Usbing)
