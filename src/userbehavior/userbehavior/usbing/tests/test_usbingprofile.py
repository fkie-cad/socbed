#!/usr/bin/python3
# -*- coding: utf-8 -*-
from userbehavior.usbing.usbingprofile import UsbingProfile, UsbingProfileConfig


class TestUsbingProfile:
    def test_init(self):
        UsbingProfile()

    def test_default_is_UsbingProfile_config(self):
        assert isinstance(UsbingProfile.default_config(), UsbingProfileConfig)
