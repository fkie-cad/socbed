#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging

from userbehavior.profile.profile import Profile, ProfileConfig

logger = logging.getLogger(__name__)


class BrowsingProfileConfig(ProfileConfig):
    pass


class BrowsingProfile(Profile):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.websites = self.config.websites
        self.search_terms = self.config.search_terms

    @classmethod
    def default_config(cls):
        config = BrowsingProfileConfig()
        config.update(super().default_config())
        config.distributions.update(cls.default_browsing_distributions())
        config.websites = cls.default_websites()
        config.search_terms = cls.default_search_terms()
        return config

    @classmethod
    def default_browsing_distributions(cls):
        return {
            "Session Duration":  # in minutes
                {"template": "LognormalDistribution",
                 "mean": 3.15, "sigma": 1.45,
                 "min_value": 0, "max_value": 172},
            "Session Pause":  # in hours
                {"template": "WeightedDistribution",
                 "weighted_list": [
                     (0.5, 0.24),
                     (1.5, 0.17),
                     (2.5, 0.07),
                     (3.5, 0.045),
                     (4.5, 0.03),
                     (5.5, 0.02)]},
            "Stay Time":  # in seconds
                {"template": "LognormalDistribution",
                 "mean": 2.5, "sigma": 2.75,
                 "min_value": 0, "max_value": 600},
            "Search":
                {"template": "WeightedDistribution",
                 "weighted_list": [(True, 1), (False, 1)]}}

    @classmethod
    def default_websites(cls):
        return [
            "http://heise.de",
            "http://www.general-anzeiger-bonn.de",
            "http://www.ebay.de",
            "http://www.bild.de",
            "http://www.spiegel.de",
            "http://www.otto.de",
            "http://www.gutefrage.net",
            "http://www.kicker.de",
            "http://www.uni-bonn.de",
            "http://www.fraunhofer.de",
            "http://www.python.org"]

    @classmethod
    def default_search_terms(cls):
        return [
            "Sonnenfinsternis",
            "Flugzeugabsturz",
            "Dschungelcamp",
            "Paris",
            "iPhone 6s",
            "Griechenland",
            "Charlie Hebdo",
            "Helmut Schmidt",
            "Windows 10",
            "Hallo Welt",
            "Game of Thrones",
            "Marathon",
            "Barack Obama",
            "Österreich",
            "Fraunhofer Gesellschaft",
            "Renault Clio",
            "Dresden",
            "Tag der Arbeit",
            "Feiertage Deutschland",
            "Volkswagen",
            "Katzen",
            "IT Sicherheit",
            "SIEM"]


class SimpleBrowsingProfile(BrowsingProfile):
    def __init__(self, session_duration=0.5, session_pause=1 / (60 * 3), stay_time=4, **kwargs):
        const = {"template": "ConstantDistribution"}
        self.__simple_distributions = {
            "Session Duration": {**const, "value": session_duration},
            "Session Pause": {**const, "value": session_pause},
            "Stay Time": {**const, "value": stay_time}}
        super().__init__(**kwargs)

    def default_config(self):
        config = super().default_config()
        config.distributions.update(self.__simple_distributions)
        return config
