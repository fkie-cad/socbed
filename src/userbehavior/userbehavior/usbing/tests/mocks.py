#! /usr/bin/python3
# -*- coding: utf-8 -*-
import os
import shutil
from tempfile import gettempdir

from userbehavior.usbing.usbdevice import UsbDevice


class MockUsbDevice(UsbDevice):
    def __init__(self):
        self.available = True
        self._mounted = False
        self._mock_payload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_payloads")

    def is_mounted(self):
        return self._mounted

    def is_available(self):
        return self.available

    def discard(self):
        self.available = False

    def mount(self):
        path = os.path.join(gettempdir(), "usb_mount")
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.mkdir(path)
        self._mount_point = path
        self._fill_with_files()
        self._mounted = True

    def get_files(self):
        if self.is_mounted():
            files_relative = os.listdir(self._mount_point)
            files = list(map(lambda rel_path: os.path.join(self._mount_point, rel_path), files_relative))
            return files
        else:
            return list()

    def unmount(self):
        if self.is_mounted():
            if os.path.isdir(self._mount_point):
                shutil.rmtree(self._mount_point)
            self._mounted = False

    def _fill_with_files(self):
        shutil.copy(os.path.join(self._mock_payload_dir, "test.pdf"), self._mount_point)
        shutil.copy(os.path.join(self._mock_payload_dir, "test.jpg"), self._mount_point)
