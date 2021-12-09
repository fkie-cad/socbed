#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pytest

from userbehavior.filing.filingprofile import FilingProfile


@pytest.fixture()
def fp():
    return FilingProfile()


class TestFilingProfile:
    def test_distribution_next_action(self, fp: FilingProfile):
        fp.get_value("Next Action")

    def test_get_random_filename(self, fp: FilingProfile):
        assert isinstance(fp.get_random_filename(), str)

    def test_get_random_text(self, fp: FilingProfile):
        assert isinstance(fp.get_random_text(), str)

    def test_get_random_text_of_length(self, fp: FilingProfile):
        rnd_text = fp.get_random_text(length=42)
        assert len(rnd_text) == 42
