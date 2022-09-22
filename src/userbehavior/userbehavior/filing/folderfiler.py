#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import os
from shutil import copyfile

from userbehavior.filing.filer import Filer, FilerException

logger = logging.getLogger(__name__)


class FolderFiler(Filer):
    """ Implements a Filer acting in a given folder """

    def __init__(self, folder):
        self.set_folder(folder)

    def set_folder(self, folder):
        if not isinstance(folder, str):
            raise FilerException("Folder for FolderFiler has to be a string")
        else:
            try:
                os.makedirs(folder, exist_ok=True)
                self.folder = folder
                logger.info("Using folder {path}".format(path=folder))
            except os.error:
                raise FilerException("Invalid folder: {path}".format(path=folder))

    def get_folder(self):
        return self.folder

    def get_files(self):
        directory_list = os.listdir(self.folder)
        files = list(filter(
            lambda elem: os.path.isfile(self.abs_path(elem)),
            directory_list))
        return files

    def create(self, filename):
        with open(self.abs_path(filename), "w"):
            pass

    def read(self, filename):
        try:
            with open(self.abs_path(filename), "r") as f:
                return f.read()
        except FileNotFoundError:
            raise FilerException("File not found: {path}".format(path=self.abs_path(filename)))

    def append(self, filename, text):
        if os.path.isfile(self.abs_path(filename)):
            with open(self.abs_path(filename), "a") as f:
                f.write(text)
        else:
            raise FilerException("File not found: {path}".format(path=self.abs_path(filename)))

    def delete(self, filename):
        try:
            os.remove(self.abs_path(filename))
        except FileNotFoundError:
            raise FilerException("File not found: {path}".format(path=self.abs_path(filename)))

    def move(self, old_filename, new_filename):
        if os.path.isfile(self.abs_path(old_filename)):
            os.replace(self.abs_path(old_filename), self.abs_path(new_filename))
        else:
            raise FilerException("File not found: {path}".format(path=self.abs_path(old_filename)))

    def copy(self, src_filename, dest_filename):
        if os.path.isfile(self.abs_path(src_filename)):
            copyfile(self.abs_path(src_filename), self.abs_path(dest_filename))
        else:
            raise FilerException("File not found: {path}".format(path=self.abs_path(src_filename)))

    def abs_path(self, filename):
        return os.path.join(self.folder, filename)
