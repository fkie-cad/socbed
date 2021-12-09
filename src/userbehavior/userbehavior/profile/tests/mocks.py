#!/usr/bin/python3
# -*- coding: utf-8 -*-

from unittest.mock import Mock


class MockProfile:

    def __init__(self, seed=None):
        self.randint = 0
        self.mock_distributions = dict()
        self.init_mock_methods()

    def init_mock_methods(self):
        self.get_randint = Mock(side_effect=self.mock_get_randint)
        self.get_random_choice = Mock(side_effect=self.mock_get_random_choice)
        self.get_value = Mock(side_effect=self.mock_get_value)

    def set_randint(self, randint):
        self.randint = randint

    def add_mock_distribution(self, name, value):
        self.mock_distributions[name] = MockDistribution(name, value)

    def get_mock_distribution(self, name):
        return self.mock_distributions[name]

    def mock_distribution_called(self, name):
        return self.mock_distributions[name].called()

    def reset_mock_distributions(self):
        for md in self.mock_distributions.values():
            md.reset()

    def mock_get_randint(self, bound):
        return self.randint % bound

    def mock_get_random_choice(self, list_):
        return list_[0]

    def mock_get_value(self, name):
        return self.mock_distributions[name].get_value()


class MockDistribution:

    def __init__(self, name, value):
        self.name = name
        self.mock = Mock(return_value=value)

    def get_value(self):
        return self.mock()

    def set_value(self, value):
        self.mock.configure_mock(return_value=value)

    def get_name(self):
        return self.name

    def called(self):
        return self.mock.called

    def reset(self):
        self.mock.reset_mock()
