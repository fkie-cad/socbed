#!/usr/bin/python3
# -*- coding: utf-8 -*-
from userbehavior.profile.profile import Profile, ProfileConfig


class UsbingProfileConfig(ProfileConfig):
    pass


class UsbingProfile(Profile):
    @classmethod
    def default_config(cls):
        config = UsbingProfileConfig()
        config.update(super().default_config())
        return config
