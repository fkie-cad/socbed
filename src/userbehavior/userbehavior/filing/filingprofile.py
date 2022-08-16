#!/usr/bin/python3
# -*- coding: utf-8 -*-

from userbehavior.profile.profile import Profile, ProfileConfig


class FilingProfileConfig(ProfileConfig):
    pass


class FilingProfile(Profile):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filename_truncs = self.config.filename_truncs

    @classmethod
    def default_config(cls):
        config = FilingProfileConfig()
        config.update(super().default_config())
        config.distributions.update(cls.default_filing_distributions())
        config.filename_truncs = ["AFile", "BFile", "CFile"]
        return config

    @classmethod
    def default_filing_distributions(cls):
        return {
            "Next Action": {
                "template": "WeightedDistribution",
                "weighted_list":
                    [("create", 2),
                     ("read", 5),
                     ("delete", 1),
                     ("append", 10),
                     ("move", 1),
                     ("copy", 2)]}}

    def get_random_filename(self):
        trunc = self.get_random_choice(self.filename_truncs)
        number = self.get_randint(1000)
        return trunc + str(number)
