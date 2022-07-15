#!/usr/bin/python3
# -*- coding: utf-8 -*-
from random import Random
from itertools import accumulate
from types import SimpleNamespace


class ProfileConfig(SimpleNamespace):
    def __init__(self, **kwargs):
        self.distributions = dict()
        super().__init__(**kwargs)

    def update(self, update_config):
        update_distributions = update_config.__dict__.pop("distributions", {})
        self.__dict__.update(update_config.__dict__)
        self.distributions.update(update_distributions)


class Profile:
    def __init__(self, config=None):
        self.config = self.default_config()
        if config:
            self.config.update(config)
        self.random = Random()
        self.random.seed(a=self.config.seed)
        self._distribution_builder = DistributionBuilder(random=self.random)
        self._built_distributions = self.build_distributions(self.config.distributions)

    @classmethod
    def default_config(cls):
        return ProfileConfig(seed=None, distributions=dict())

    def build_distributions(self, dist_dicts):
        dist_dicts_with_names = (
            {"name": dist_name, **dist_dict}
            for dist_name, dist_dict in dist_dicts.items())
        return {
            dist.name: dist
            for dist in map(self._distribution_builder.build, dist_dicts_with_names)}

    def get_value(self, distribution_name):
        return self._built_distributions[distribution_name].get_value()

    def get_randint(self, bound):
        return self.random.randint(0, bound)

    def get_random_choice(self, list_):
        return self.random.choice(list_)

    def get_random_text(self, length=50):
        rnd_text = ""
        filler = "Random Text "
        for i in range(length // len(filler)):
            rnd_text += filler
        rnd_text += filler[0:length % len(filler)]
        return rnd_text


class Distribution:
    def __init__(self, name, random=None):
        self.name = name
        self.random = random

    def get_value(self):
        raise NotImplementedError()


class LognormalDistribution(Distribution):
    def __init__(self, mean, sigma, min_value=0, max_value=-1, max_tries_for_interval=20, **kwargs):
        super().__init__(**kwargs)
        self.mean = mean
        self.sigma = sigma
        self.min_value = min_value
        self.max_value = max_value
        self.max_tries_for_interval = max_tries_for_interval

    def get_value(self):
        value_generator = (
            self.random.lognormvariate(mu=self.mean, sigma=self.sigma)
            for i in range(self.max_tries_for_interval))
        last_value = None
        for value in value_generator:
            if value >= self.min_value and self.max_value < 0 or value <= self.max_value:
                return value
            else:
                last_value = value
        else:
            return self.min_value if last_value < self.min_value else self.max_value


class WeightedDistribution(Distribution):
    def __init__(self, weighted_list, **kwargs):
        """ weighted_list is list of (key, weight) pairs"""
        super().__init__(**kwargs)
        self.weighted_list = weighted_list
        keys, weights = zip(*self.weighted_list)
        sum_weights = sum(weights)
        norm_cum_weights = (cw / sum_weights for cw in accumulate(weights))
        self.norm_cum_weighted_list = list(zip(keys, norm_cum_weights))

    def get_value(self):
        draw = self.random.random()
        for key, upper_bound in self.norm_cum_weighted_list:
            if draw < upper_bound:
                return key
        else:
            return self.norm_cum_weighted_list[-1][0]


class ConstantDistribution(Distribution):
    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def get_value(self):
        return self.value


class DistributionBuilder:
    def __init__(self, random=None):
        self.distribution_templates = {
            "Distribution": Distribution,
            "ConstantDistribution": ConstantDistribution,
            "WeightedDistribution": WeightedDistribution,
            "LognormalDistribution": LognormalDistribution}
        self.random = random or Random()

    def build(self, dist_dict):
        kwargs = dist_dict.copy()
        dist_template = self.distribution_templates[kwargs.pop("template")]
        return dist_template(random=self.random, **kwargs)
