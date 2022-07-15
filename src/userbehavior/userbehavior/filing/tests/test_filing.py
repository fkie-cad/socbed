#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time

import pytest
from userbehavior.filing.filing import Filing, FilingException, FilingConfig, FilerConfig
from userbehavior.filing.filingprofile import FilingProfile, FilingProfileConfig
from userbehavior.filing.tests.mocks import MockFiler, MockFilingProfile
from userbehavior.misc.util import Factory

from userbehavior.filing.filer import Filer, NullFiler

long_test = pytest.mark.long_test


class TestFilingConfig:
    def test_from_dict(self):
        d = {'profile': {'seed': 42},
             'filer': {'implementation': 'NullFiler'}}
        fc = FilingConfig.from_dict(d)
        assert fc.profile_config.seed == 42
        assert fc.filer_config.implementation == NullFiler


class TestFilerConfig:
    def test_implementations(self):
        known_implementations = ["NullFiler", "FolderFiler"]
        for impl in known_implementations:
            assert impl in FilerConfig.implementations


@pytest.fixture()
def f():
    filer_factory = Factory(implementation=MockFiler)
    filing_profile = FilingProfile(config=FilingProfileConfig(seed=42))
    return Filing(filing_profile=filing_profile, filer_factory=filer_factory)


class MockFilerWithSomeArg(MockFiler):
    def __init__(self, some_arg=None, **kwargs):
        super().__init__(**kwargs)


class TestFiling:
    def test_init_without_profile(self):
        assert Filing(filing_profile=None, filer_factory=Factory(implementation=Filer)) is not None

    def test_create_from_config(self):
        filer_config = FilerConfig(implementation=MockFilerWithSomeArg, some_arg="value")
        profile_config = FilingProfileConfig(
            distributions={"test_dist": {"template": "ConstantDistribution", "value": 2}})
        config = FilingConfig(filer_config=filer_config, profile_config=profile_config)
        f = Filing.from_config(config=config)
        assert isinstance(f, Filing)
        assert f.filer_factory.implementation == MockFilerWithSomeArg
        assert f.filer_factory.kwargs["some_arg"] == "value"
        assert f.filing_profile.get_value("test_dist") == 2

    def test_set_duration(self, f: Filing):
        now = time.time()
        f.set_duration(5)
        assert f.end_time > now + 4

    @pytest.mark.acceptance
    def test_run_for_at_least_5_secs(self, f: Filing):
        begin = time.time()
        f.set_duration(5)
        f.run()
        end = time.time()
        assert end - begin > 4

    @pytest.mark.acceptance
    def test_run_for_at_least_30_secs(self, f: Filing):
        begin = time.time()
        f.set_duration(30)
        f.run()
        end = time.time()
        assert end - begin > 29

    @pytest.mark.parametrize(
        "action", [
            "create", "delete", "append", "read", "move", "copy"])
    def test_run_some_action(self, action, f: Filing):
        mfp = MockFilingProfile()
        mfp.add_mock_distribution("Next Action", action)
        f.filing_profile = mfp
        f.run_some_action()

    def test_run_some_unknown_action(self, f: Filing):
        mfp = MockFilingProfile()
        mfp.add_mock_distribution("Next Action", "ThisIsNotAnAction")
        f.filing_profile = mfp
        with pytest.raises(FilingException) as e:
            f.run_some_action()
        assert "ThisIsNotAnAction" in str(e.value)

    def test_create_a_file(self, f: Filing):
        f.create_a_file()
        assert f.filer.create.called

    def test_read_from_a_file(self, f: Filing):
        f.create_a_file()
        f.read_from_a_file()
        assert f.filer.read.called

    def test_delete_a_file(self, f: Filing):
        f.create_a_file()
        f.delete_a_file()
        assert f.filer.delete.called

    def test_move_a_file(self, f: Filing):
        f.create_a_file()
        f.move_a_file()
        assert f.filer.move.called

    def test_copy_a_file(self, f: Filing):
        f.create_a_file()
        f.copy_a_file()
        assert f.filer.copy.called
