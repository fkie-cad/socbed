#! /usr/bin/python3
# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch

import pytest

from userbehavior.usbing.usbdevice import WindowsUsbDevice, UsbDevice, NullUsbDevice


class TestNullUsbDevice:
    def test_init(self):
        assert isinstance(NullUsbDevice(), UsbDevice)

    def test_stubbed_methods(self):
        ud = NullUsbDevice()
        ud.mount()
        ud.unmount()
        assert not ud.is_mounted() and ud.is_mounted() is not None
        assert ud.get_files() == []
        assert not ud.is_available() and ud.is_available() is not None
        ud.discard()


@pytest.fixture(scope="function")
def wud():
    wud = WindowsUsbDevice(image_file="some\\image.img", mount_point="Y:\\")
    wud._execute = Mock()
    return wud


class TestWindowsUsbDevice:
    def test_init(self, wud: WindowsUsbDevice):
        assert not wud.is_mounted()
        assert wud.image_file == "some\\image.img"
        assert wud.mount_point == "Y:\\"

    def test_is_available(self, wud: WindowsUsbDevice):
        wud._image_file_is_available = lambda: True
        assert wud.is_available()
        wud._image_file_is_available = lambda: False
        assert not wud.is_available()

    def test_discard(self, wud: WindowsUsbDevice):
        wud._move_image_file = Mock()
        wud._image_file_is_available = lambda: not wud._move_image_file.called
        assert wud.is_available()
        wud.discard()
        assert not wud.is_available()

    def test_mount(self, wud: WindowsUsbDevice):
        wud._mount_point_is_available = lambda: True
        wud.mount()
        assert wud.is_mounted()
        wud._execute.assert_called_with(["imdisk", "-a", "-f", wud.image_file, "-m", wud.mount_point])

    def test_unmount(self, wud: WindowsUsbDevice):
        wud._mount_point_is_available = lambda: True
        wud.mount()
        wud._mount_point_is_available = lambda: False
        wud.unmount()
        assert not wud.is_mounted()
        wud._execute.assert_called_with(["imdisk", "-D", "-m", wud.mount_point])

    def test_get_files(self, wud: WindowsUsbDevice):
        wud._files_in_mount_point = lambda: ["file1.txt", "file2.exe"]
        wud._mount_point_is_available = lambda: True
        wud.mount()
        files = wud.get_files()
        assert len(files) == 2
        for file in files:
            assert file.startswith(wud.mount_point)

    def test_get_files_unmounted(self, wud: WindowsUsbDevice):
        os_listdir_mock = Mock(return_value=["file1.txt", "file2.exe"])
        p_listdir = patch(WindowsUsbDevice.__module__ + ".os.listdir", os_listdir_mock)
        p_isdir = patch(WindowsUsbDevice.__module__ + ".os.path.isdir", Mock(return_value=True))
        p_listdir.start()
        p_isdir.start()
        files = wud.get_files()
        p_listdir.stop()
        p_isdir.stop()
        assert files == []
