#!/usr/bin/python3
# -*- coding: utf-8 -*-

from unittest.mock import Mock

from userbehavior.filing.filer import Filer, FilerException
from userbehavior.profile.tests.mocks import MockProfile


class MockFiler(Filer):
    def __init__(self):
        self.init_mock_methods()
        self.files = dict()

    def init_mock_methods(self):
        self.get_files = Mock(side_effect=self.mock_get_files)
        self.create = Mock(side_effect=self.mock_create)
        self.append = Mock(side_effect=self.mock_append)
        self.read = Mock(side_effect=self.mock_read)
        self.delete = Mock(side_effect=self.mock_delete)
        self.copy = Mock(side_effect=self.mock_copy)
        self.move = Mock(side_effect=self.mock_move)

    def mock_get_files(self):
        return list(self.files.keys())

    def mock_create(self, filename):
        self.files[filename] = ""

    def mock_read(self, filename):
        try:
            return self.files[filename]
        except KeyError:
            raise FilerException("No such file: " + str(filename))

    def mock_append(self, filename, text):
        try:
            self.files[filename] += self.files[filename] + text
        except KeyError:
            raise FilerException("No such file: " + str(filename))

    def mock_delete(self, filename):
        try:
            del self.files[filename]
        except KeyError:
            raise FilerException("No such file: " + str(filename))

    def mock_copy(self, src_filename, dest_filename):
        try:
            self.files[dest_filename] = self.files[src_filename]
        except KeyError:
            raise FilerException("No such file: " + str(src_filename))

    def mock_move(self, old_filename, new_filename):
        self.mock_copy(old_filename, new_filename)
        self.mock_delete(old_filename)


class MockFilingProfile(MockProfile):
    def __init__(self, filer=None, seed=None):
        MockProfile.__init__(self, seed=seed)
        self.filer = filer or MockFiler()
        self.random_filename_count = 0
        self.init_filing_mock_methods()
        self.init_mock_distributions()

    def init_filing_mock_methods(self):
        self.get_filer = Mock(side_effect=self.mock_get_filer)
        self.get_random_text = Mock(return_value="Random Text")
        self.get_random_filename = Mock(side_effect=self.mock_get_random_filename)

    def init_mock_distributions(self):
        self.add_mock_distribution("Next Action", "create")

    def mock_get_filer(self):
        return self.filer

    def mock_get_random_filename(self):
        fn = "File" + str(self.random_filename_count)
        self.random_filename_count += 1
        return fn
