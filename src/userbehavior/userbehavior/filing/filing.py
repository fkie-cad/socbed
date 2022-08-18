#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import time
from types import SimpleNamespace

from userbehavior.filing.filer import NullFiler
from userbehavior.filing.filingprofile import FilingProfile, FilingProfileConfig
from userbehavior.filing.folderfiler import FolderFiler
from userbehavior.misc.util import Factory

logger = logging.getLogger(__name__)


class FilingConfig:
    def __init__(self, profile_config, filer_config):
        self.profile_config = profile_config
        self.filer_config = filer_config

    @classmethod
    def from_dict(cls, d):
        profile_config = FilingProfileConfig(**d['profile'])
        filer_config = FilerConfig.from_str_dict(**d['filer'])
        return cls(profile_config=profile_config, filer_config=filer_config)


class FilerConfig(SimpleNamespace):
    implementations = {
        'NullFiler': NullFiler,
        'FolderFiler': FolderFiler}

    def __init__(self, implementation=None, **kwargs):
        self.implementation = implementation or NullFiler
        super().__init__(**kwargs)

    @classmethod
    def from_str_dict(cls, implementation=None, **kwargs):
        parsed_implementation = cls.implementations[implementation]
        return cls(implementation=parsed_implementation, **kwargs)


class Filing:
    def __init__(self, filing_profile=None, filer_factory=None):
        self.filing_profile = filing_profile or FilingProfile()
        self.filer_factory = filer_factory or self.default_filer_factory()
        self.filer = self.filer_factory.create()
        self.end_time = None
        self.__timeout = 5

    @classmethod
    def from_config(cls, config: FilingConfig):
        kwargs = config.filer_config.__dict__.copy()
        implementation = kwargs.pop("implementation")
        ff = Factory(implementation=implementation, kwargs=kwargs)
        fp = FilingProfile(config=config.profile_config)
        return cls(filing_profile=fp, filer_factory=ff)

    @staticmethod
    def default_filer_factory():
        return Factory(implementation=NullFiler)

    def set_duration(self, duration):
        if duration is None:
            self.end_time = None
        else:
            self.end_time = time.time() + duration

    def set_timeout(self, secs):
        self.__timeout = secs

    def run(self):
        logger.info("Filing started")
        self.loop_actions_until_ended()
        logger.info("Filing ended")

    def loop_actions_until_ended(self):
        log = "Loop actions"
        if self.end_time is not None:
            log += " until " + time.ctime(self.end_time)
        logger.info(log)
        while not self.has_ended():
            self.run_some_action()
            self.take_timeout()

    def has_ended(self):
        if self.end_time is None:
            return False
        else:
            return self.end_time < time.time()

    def run_some_action(self):
        action = self.filing_profile.get_value("Next Action")
        logger.info("Next action is : " + str(action))
        if action == "create":
            self.create_a_file()
        elif action == "delete":
            self.delete_a_file()
        elif action == "append":
            self.append_to_a_file()
        elif action == "read":
            self.read_from_a_file()
        elif action == "move":
            self.move_a_file()
        elif action == "copy":
            self.copy_a_file()
        else:
            raise FilingException("Unknown action: " + str(action))

    def take_timeout(self, secs=None):
        logger.info("Take timeout for " + str(secs or self.__timeout) + " secs")
        time.sleep(secs or self.__timeout)

    def create_a_file(self):
        filename = self.filing_profile.get_random_filename()
        self.filer.create(filename)
        logger.info("File created: " + filename)

    def append_to_a_file(self):
        files = self.filer.get_files()
        if len(files) > 0:
            filename = self.filing_profile.get_random_choice(files)
            text = self.filing_profile.get_random_text()
            self.filer.append(filename, text)
            logger.info("Appended to file: " + filename)
        else:
            logger.info("No files to append to")

    def delete_a_file(self):
        files = self.filer.get_files()
        if len(files) > 0:
            filename = self.filing_profile.get_random_choice(files)
            self.filer.delete(filename)
            logger.info("File deleted: " + filename)
        else:
            logger.info("No files to delete")

    def read_from_a_file(self):
        files = self.filer.get_files()
        if len(files) > 0:
            filename = self.filing_profile.get_random_choice(files)
            self.filer.read(filename)
            logger.info("File read: " + filename)
        else:
            logger.info("No files to read")

    def move_a_file(self):
        files = self.filer.get_files()
        if len(files) > 0:
            filename = self.filing_profile.get_random_choice(files)
            new_filename = self.filing_profile.get_random_filename()
            self.filer.move(filename, new_filename)
            logger.info("File moved: " + filename + " -> " + new_filename)
        else:
            logger.info("No files to move")

    def copy_a_file(self):
        files = self.filer.get_files()
        if len(files) > 0:
            filename = self.filing_profile.get_random_choice(files)
            dest_filename = self.filing_profile.get_random_filename()
            self.filer.copy(filename, dest_filename)
            logger.info("File copied: " + filename + " -> " + dest_filename)
        else:
            logger.info("No files to copy")


class FilingException(Exception):
    pass
