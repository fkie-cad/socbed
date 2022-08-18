#! /usr/bin/python3
# -*- coding: utf-8 -*-
import time
from unittest.mock import patch, Mock

import pytest
from userbehavior.misc.util import Factory
from userbehavior.usbing.tests.mocks import MockUsbDevice
from userbehavior.usbing.usbdevice import NullUsbDevice
from userbehavior.usbing.usbingprofile import UsbingProfile, UsbingProfileConfig

from userbehavior.usbing.usbing import Usbing, UsbingConfig, UsbDeviceConfig


class TestUsbingConfig:
    def test_from_dict(self):
        d = {'profile': {'seed': 42},
             'usb_device': {'implementation': 'NullUsbDevice'}}
        uc = UsbingConfig.from_dict(d)
        assert uc.profile_config.seed == 42
        assert uc.usb_device_config.implementation == NullUsbDevice


class TestUsbDeviceConfig:
    def test_implementations(self):
        known_implementations = ["NullUsbDevice", "WindowsUsbDevice"]
        for impl in known_implementations:
            assert impl in UsbDeviceConfig.implementations


class SpyFactory(Factory):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_instance = None

    def create(self):
        instance = super().create()
        self.last_instance = instance
        return instance


@pytest.fixture()
def u():
    usb_device_factory = SpyFactory(implementation=MockUsbDevice)
    usbing_profile = UsbingProfile()
    usbing_profile.image_file = "some/file"
    usbing = Usbing(usbing_profile=usbing_profile, usb_device_factory=usb_device_factory)
    usbing.open = Mock()
    usbing.copy = Mock()
    return usbing


class TestUsbing:
    def test_create_from_config(self):
        profile_config = UsbingProfileConfig()
        usb_device_config = UsbDeviceConfig(implementation=MockUsbDevice, image_file="otherImage")
        config = UsbingConfig(profile_config=profile_config, usb_device_config=usb_device_config)
        u = Usbing.from_config(config)
        assert isinstance(u, Usbing)
        assert u.usb_device_factory.implementation == MockUsbDevice
        assert u.usb_device_factory.kwargs["image_file"] == "otherImage"

    def test_mount_usb_device(self, u: Usbing):
        u.usb_device = MockUsbDevice()
        u.mount_usb_device()
        assert u.usb_device.is_mounted()

    def test_unmount_usb_device(self, u: Usbing):
        u.usb_device = MockUsbDevice()
        u.mount_usb_device()
        u.unmount_usb_device()
        assert not u.usb_device.is_mounted()

    def test_set_duration(self, u: Usbing):
        u.set_duration(30)
        assert u.end_time > time.time() + 29

    def test_has_ended(self, u: Usbing):
        u.set_duration(1)
        assert not u.has_ended()
        time.sleep(1)
        assert u.has_ended()

    def test_set_timeout(self, u: Usbing):
        u.timeout = 30
        sleep = Mock()
        p = patch(Usbing.__module__ + ".time.sleep", sleep)
        p.start()
        u.take_timeout()
        p.stop()
        sleep.assert_called_with(30)

    def test_loop_until_has_ended(self, u: Usbing):
        u.has_ended = Mock(side_effect=[False, False, False, True])
        u.device_is_available = Mock(side_effect=[False, False, True])
        u.handle_usb_device = Mock()
        u.take_timeout = Mock()
        u.loop_until_has_ended()
        assert u.has_ended.call_count == 4
        assert u.device_is_available.call_count == 3
        assert u.handle_usb_device.call_count == 1
        assert u.take_timeout.call_count == 3

    def test_normal_start(self, u: Usbing):
        assert u.timeout == 10
        assert u.end_time is None
        u.loop_until_has_ended = Mock()
        u.run()
        assert u.loop_until_has_ended.called

    def test_save_pdfs_to_tmp_folder(self, u: Usbing):
        u.usb_device = MockUsbDevice()
        u.mount_usb_device()
        u.save_pdfs_from_mounted_device()
        assert len(u.saved_files) > 0
        for file in u.saved_files:
            assert file.endswith(".pdf")
