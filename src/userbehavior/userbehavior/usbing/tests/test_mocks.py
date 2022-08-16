#! /usr/bin/python3
# -*- coding: utf-8 -*-
import os.path

import pytest

from userbehavior.usbing.tests.mocks import MockUsbDevice


@pytest.fixture(scope="function")
def mud():
    return MockUsbDevice()


class TestMockUsbDevice:
    def test_init(self, mud: MockUsbDevice):
        assert not mud.is_mounted()
        assert mud.is_available()

    def test_discard(self, mud: MockUsbDevice):
        mud.discard()
        assert not mud.is_available()

    def test_mount(self, mud: MockUsbDevice):
        mud.mount()
        assert mud.is_mounted()

    def test_unmount(self, mud: MockUsbDevice):
        mud.mount()
        mp = mud._mount_point
        mud.unmount()
        assert not mud.is_mounted()
        assert mp is None or not os.path.isdir(mp)

    def test_get_files_unmounted(self, mud: MockUsbDevice):
        if mud.is_mounted():
            mud.unmount()
        assert mud.get_files() == []

    def test_get_files(self, mud: MockUsbDevice):
        if not mud.is_mounted():
            mud.mount()
        files = mud.get_files()
        assert isinstance(files, list)
        assert any(file.endswith("test.pdf") for file in files)
        for file in files:
            assert os.path.isfile(file)
