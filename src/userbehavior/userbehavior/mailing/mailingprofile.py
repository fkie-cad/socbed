#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging

from userbehavior.profile.profile import Profile, ProfileConfig

logger = logging.getLogger(__name__)


class MailingProfileConfig(ProfileConfig):
    pass


class MailingProfile(Profile):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mail_address = self.config.mail_address
        self.known_mail_addresses = self.config.known_mail_addresses

    @classmethod
    def default_config(cls):
        config = MailingProfileConfig()
        config.update(super().default_config())
        config.distributions.update(cls.default_mailing_distributions())
        config.mail_address = "test@localdomain"
        config.known_mail_addresses = list()
        return config

    @classmethod
    def default_mailing_distributions(cls):
        return {
            "Send Mail": {
                "template": "WeightedDistribution",
                "weighted_list": [(True, 20), (False, 1)]}}

    def get_known_mail_address(self):
        if len(self.known_mail_addresses) > 0:
            return self.get_random_choice(self.known_mail_addresses)
        else:
            raise MailingProfileException("No known mail addresses")


class MailingProfileException(Exception):
    pass


class Server:
    def __init__(self, host=None, port=None, user=None, password=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
