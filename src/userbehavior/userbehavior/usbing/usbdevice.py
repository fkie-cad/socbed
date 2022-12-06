#! /usr/bin/python3
# -*- coding: utf-8 -*-
import os
import shutil
import time
from subprocess import Popen, PIPE


class UsbDevice:
    def is_available(self):
        raise NotImplementedError()

    def discard(self):
        raise NotImplementedError()

    def mount(self):
        raise NotImplementedError()

    def unmount(self):
        raise NotImplementedError()

    def is_mounted(self):
        raise NotImplementedError()

    def get_files(self):
        raise NotImplementedError()


class NullUsbDevice(UsbDevice):
    def is_available(self):
        return False

    def discard(self):
        pass

    def mount(self):
        pass

    def unmount(self):
        pass

    def is_mounted(self):
        return False

    def get_files(self):
        return []


class WindowsUsbDevice(UsbDevice):
    def __init__(self, image_file, mount_point):
        self.image_file = image_file
        self.mount_point = mount_point
        self.mount_timeout = 60
        self._mounted = False

    def is_available(self):
        return self._image_file_is_available()

    def discard(self):
        self._move_image_file()

    def is_mounted(self):
        return self._mounted

    def mount(self):
        mount_start = time.time()
        call_vector = ["imdisk", "-a", "-f", self.image_file, "-m", self.mount_point]
        self._execute(call_vector)
        while (time.time() - mount_start < self.mount_timeout and
               not self._mount_point_is_available()):
            time.sleep(3)
        self._mounted = self._mount_point_is_available()

    def unmount(self):
        call_vector = ["imdisk", "-D", "-m", self.mount_point]
        self._execute(call_vector)
        while self._mount_point_is_available():
            time.sleep(1)
        self._mounted = False

    def get_files(self):
        if self.is_mounted():
            return [os.path.join(self.mount_point, file) for file in self._files_in_mount_point()]
        else:
            return list()

    def _files_in_mount_point(self):
        return os.listdir(self.mount_point)

    def _mount_point_is_available(self):
        return os.path.isdir(self.mount_point)

    def _image_file_is_available(self):
        return os.path.isfile(self.image_file)

    def _move_image_file(self):
        old_image_trunk = self.image_file + ".old"
        count = 0
        while os.path.isfile(old_image_trunk + str(count)):
            count += 1
        shutil.move(self.image_file, old_image_trunk + str(count))

    @staticmethod
    def _execute(call_vector):
        p = Popen(call_vector, shell=True, stdout=PIPE)
        p.wait()
