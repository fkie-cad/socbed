#!/usr/bin/python3
# -*- coding: utf-8 -*-
from userbehavior.profile.profile import Profile, ProfileConfig


class TestProfile:
    def test_default_config(self):
        profile = Profile()
        assert profile.default_config().seed is None
        assert profile.default_config().distributions == {}

    def test_seed(self):
        profile = Profile(config=ProfileConfig(seed=42))
        assert profile.config.seed == 42

    def test_build_distributions(self):
        dists = {
            "MyDist1": {
                "template": "ConstantDistribution",
                "value": 3},
            "MyDist2": {
                "template": "ConstantDistribution",
                "value": 6}}
        profile = Profile(config=ProfileConfig(distributions=dists))
        assert profile.get_value("MyDist1") == 3
        assert profile.get_value("MyDist2") == 6
