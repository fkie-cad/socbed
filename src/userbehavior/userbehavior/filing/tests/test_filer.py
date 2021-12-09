#!/usr/bin/python3
# -*- coding: utf-8 -*-
from userbehavior.filing.filer import Filer, NullFiler


class TestNullFiler:
    def test_init(self):
        assert isinstance(NullFiler(), Filer)

    def test_stubbed_methods(self):
        f = NullFiler()
        assert f.get_files() == []
        f.create(None)
        f.delete(None)
        f.read(None)
        f.append(None, None)
        f.copy(None, None)
        f.move(None, None)
