#!/usr/bin/python3
# -*- coding: utf-8 -*-
from random import Random

import pytest

from userbehavior.profile.profile import Distribution, WeightedDistribution, ConstantDistribution, \
    LognormalDistribution, DistributionBuilder


@pytest.fixture()
def random():
    random = Random()
    random.seed(0)
    return random


@pytest.fixture()
def dist(random: Random):
    return Distribution(name="DistName", random=random)


class TestDistribution:
    def test_attributes(self, random: Random):
        dist = Distribution(name="DistName", random=random)
        assert dist.name == "DistName"
        assert dist.random == random
        with pytest.raises(NotImplementedError):
            dist.get_value()


class TestSubClassDistributions:
    def test_weighted_distribution_init(self, random: Random):
        weighted_list = [("hello", 1), ("you", 2)]
        wd = WeightedDistribution(weighted_list=weighted_list, name="WeightedDistribution", random=random)
        assert wd.weighted_list == weighted_list

    def test_weighted_distribution_get_value(self, random: Random):
        weighted_list = [("some", 3), ("test", 1), ("keys", 2)]
        wd = WeightedDistribution(weighted_list=weighted_list, name="WeightedDistribution", random=random)
        keys, values = zip(*weighted_list)
        weight_before = 0.0
        for key, norm_cum_weight in wd.norm_cum_weighted_list:
            assert norm_cum_weight <= 1.0
            assert norm_cum_weight > weight_before
            weight_before = norm_cum_weight
        assert wd.get_value() in keys

    def test_constant_distribution_init(self, random: Random):
        value = "some value"
        cd = ConstantDistribution(value=value, name="ConstantDistribution", random=random)
        assert cd.value == value

    def test_constant_distribution_get_value(self, random: Random):
        value = "some value"
        cd = ConstantDistribution(value=value, name="ConstantDistribution", random=random)
        assert cd.get_value() == value

    def test_lognormal_distribution_init(self, random: Random):
        mean, sigma = 1, 2
        min_value, max_value = 0, 20
        max_tries_for_interval = 30
        lnd = LognormalDistribution(
            mean=mean, sigma=sigma, min_value=min_value, max_value=max_value,
            max_tries_for_interval=max_tries_for_interval,
            name="LognormalDistribution", random=random)
        assert (lnd.mean, lnd.sigma) == (mean, sigma)
        assert (lnd.min_value, lnd.max_value) == (min_value, max_value)
        assert lnd.max_tries_for_interval == max_tries_for_interval

    def test_lognormal_distribution_get_value(self, random: Random):
        lnd = LognormalDistribution(mean=0, sigma=1, name="LognormalDistribution", random=random)
        assert lnd.get_value() > 0


@pytest.fixture()
def dist_builder(random: Random):
    return DistributionBuilder(random=random)


class TestDistributionFactory:
    def test_build(self, dist_builder: DistributionBuilder):
        dist_dict = {"template": "Distribution", "name": "MyDistro"}
        dist = dist_builder.build(dist_dict)
        assert isinstance(dist, Distribution)
        assert dist.name == "MyDistro"
        assert dist.random == dist_builder.random

    @pytest.mark.parametrize(
        "dist_dict, dist_class", [
            ({"template": "ConstantDistribution", "value": 3, "name": "bla"},
             ConstantDistribution),
            ({"template": "WeightedDistribution", "weighted_list": [("a", 1), ("b", 2)], "name": "bla"},
             WeightedDistribution),
            ({"template": "LognormalDistribution", "mean": 0, "sigma": 1, "name": "bla"},
             LognormalDistribution)])
    def test_build_different_types(self, dist_builder: DistributionBuilder, dist_dict, dist_class):
        assert isinstance(dist_builder.build(dist_dict), dist_class)
