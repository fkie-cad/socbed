#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pytest

from userbehavior.profile.tests.mocks import MockProfile, MockDistribution


@pytest.fixture()
def mp():
    return MockProfile()


class TestMockProfile:
    def test_init_with_seed(self):
        mp = MockProfile(seed=42)

    def test_get_randint(self, mp):
        randint = mp.get_randint(5)
        assert randint < 5
        assert randint >= 0

    def test_set_randint(self, mp):
        mp.set_randint(10)
        assert mp.get_randint(12) == 10
        assert mp.get_randint(8) == 2

    def test_get_random_choice(self, mp):
        l = ["First", "Should", "Be", "Returned"]
        assert mp.get_random_choice(l) == l[0]

    def test_exception_random_choice_empty_list(self, mp):
        with pytest.raises(IndexError):
            mp.get_random_choice([])

    def test_add_mock_distribution(self, mp):
        mp.add_mock_distribution("name", "value")

    def test_get_value(self, mp):
        mp.add_mock_distribution("name", "value")
        assert mp.get_value("name") == "value"

    def test_get_mock_distribution(self, mp):
        mp.add_mock_distribution("name", "value")
        result = mp.get_mock_distribution("name")
        assert isinstance(result, MockDistribution)
        assert result.get_name() == "name"

    def test_mock_distribution_called(self, mp):
        mp.add_mock_distribution("name", "value")
        mp.get_value("name")
        assert mp.mock_distribution_called("name")

    def test_reset_mock_distributions(self, mp):
        mp.add_mock_distribution("name1", "value")
        mp.add_mock_distribution("name2", "value")
        mp.get_value("name1")
        mp.get_value("name2")
        mp.reset_mock_distributions()
        assert not mp.mock_distribution_called("name1")
        assert not mp.mock_distribution_called("name2")


class TestMockDistribution:
    def test_init(self):
        md = MockDistribution("name", "value")

    def test_get_name(self):
        md = MockDistribution("name", "value")
        assert md.get_name() == "name"

    def test_get_value(self):
        md = MockDistribution("name", "value")
        assert md.get_value() == "value"

    def test_set_value(self):
        md = MockDistribution("name", "value")
        md.set_value(5)
        assert md.get_value() == 5

    def test_called(self):
        md = MockDistribution("name", "value")
        md.get_value()
        assert md.called()

    def test_reset(self):
        md = MockDistribution("name", "value")
        md.get_value()
        md.reset()
        assert not md.called()
