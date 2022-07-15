#!/usr/bin/python3
# -*- coding: utf-8 -*-


class Filer:
    def get_files(self):
        raise NotImplementedError()

    def create(self, filename):
        raise NotImplementedError()

    def delete(self, filename):
        raise NotImplementedError()

    def read(self, filename):
        raise NotImplementedError()

    def append(self, filename, text):
        raise NotImplementedError()

    def copy(self, src_filename, dest_filename):
        raise NotImplementedError()

    def move(self, old_filename, new_filename):
        raise NotImplementedError()


class FilerException(Exception):
    pass


class NullFiler(Filer):
    def get_files(self):
        return []

    def move(self, old_filename, new_filename):
        pass

    def create(self, filename):
        pass

    def append(self, filename, text):
        pass

    def copy(self, src_filename, dest_filename):
        pass

    def read(self, filename):
        pass

    def delete(self, filename):
        pass
