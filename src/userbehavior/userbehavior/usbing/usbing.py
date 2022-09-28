#! /usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import os
import shutil
import time
from subprocess import Popen, PIPE
from tempfile import gettempdir
from types import SimpleNamespace

from userbehavior.usbing.usbdevice import NullUsbDevice, WindowsUsbDevice
from userbehavior.usbing.usbingprofile import UsbingProfile, UsbingProfileConfig

from userbehavior.misc.util import Factory

logger = logging.getLogger(__name__)


class UsbingConfig:
    def __init__(self, profile_config, usb_device_config):
        self.profile_config = profile_config
        self.usb_device_config = usb_device_config

    @classmethod
    def from_dict(cls, d):
        profile_config = UsbingProfileConfig(**d['profile'])
        usb_device_config = UsbDeviceConfig.from_str_dict(**d['usb_device'])
        return cls(profile_config=profile_config, usb_device_config=usb_device_config)


class UsbDeviceConfig(SimpleNamespace):
    implementations = {
        'NullUsbDevice': NullUsbDevice,
        'WindowsUsbDevice': WindowsUsbDevice}

    def __init__(self, implementation=None, **kwargs):
        self.implementation = implementation or NullUsbDevice
        super().__init__(**kwargs)

    @classmethod
    def from_str_dict(cls, implementation=None, **kwargs):
        parsed_implementation = cls.implementations[implementation]
        return cls(implementation=parsed_implementation, **kwargs)


class Usbing:
    def __init__(self, usbing_profile=None, usb_device_factory=None):
        self.usbing_profile = usbing_profile or self.default_usbing_profile()
        self.usb_device_factory = usb_device_factory or self.default_usb_device_factory()
        self.usb_device = None
        self.tmp_folder = self.default_tmp_folder()
        self.saved_files = list()
        self.end_time = None
        self.timeout = 10

    @classmethod
    def from_config(cls, config: UsbingConfig):
        kwargs = config.usb_device_config.__dict__.copy()
        implementation = kwargs.pop("implementation")
        udf = Factory(implementation=implementation, kwargs=kwargs)
        up = UsbingProfile(config=config.profile_config)
        return cls(usbing_profile=up, usb_device_factory=udf)

    @staticmethod
    def default_usb_device_factory():
        return Factory(implementation=NullUsbDevice)

    @staticmethod
    def default_usbing_profile():
        return UsbingProfile()

    @staticmethod
    def default_tmp_folder():
        mp = os.path.join(gettempdir(), "tmp_usbing")
        if not os.path.isdir(mp):
            os.mkdir(mp)
        return mp

    def set_duration(self, duration):
        if duration is None:
            self.end_time = None
        else:
            self.end_time = time.time() + duration

    def run(self):
        logger.info("Usbing started")
        self.loop_until_has_ended()
        logger.info("Usbing ended")

    def loop_until_has_ended(self):
        log = "Loop handling USB image"
        if self.end_time is not None:
            log += " until " + time.ctime(self.end_time)
        logger.info(log)
        while not self.has_ended():
            self.usb_device = self.usb_device or self.usb_device_factory.create()
            if self.device_is_available():
                self.handle_usb_device()
            self.take_timeout()

    def has_ended(self):
        if self.end_time is None:
            return False
        else:
            return time.time() > self.end_time

    def device_is_available(self):
        logger.info("Check if USB device is available")
        return self.usb_device.is_available()

    def handle_usb_device(self):
        logger.info("Handling USB image")
        self.save_exes_from_usb_device()
        self.discard_old_usb_device()
        self.open_saved_exes()

    def take_timeout(self, secs=None):
        logger.info("Take timeout for " + str(secs or self.timeout) + " secs")
        time.sleep(secs or self.timeout)

    def save_exes_from_usb_device(self):
        logger.info("Saving exes on USB device to tmp folder")
        self.mount_usb_device()
        if self.usb_device_is_mounted():
            self.save_exes_from_mounted_device()
            self.unmount_usb_device()
        else:
            logger.info("Failed to mount USB device")

    def discard_old_usb_device(self):
        logger.info("Discarding old USB device")
        self.usb_device.discard()
        self.usb_device = None

    def open_saved_exes(self):
        logger.info("Opening saved exes")
        for file in self.saved_files:
            self.open(file)
            self.saved_files.remove(file)

    def mount_usb_device(self):
        logger.info("Mounting USB device")
        self.usb_device.mount()

    def save_exes_from_mounted_device(self):
        files = self.usb_device.get_files()
        exes = filter(lambda file: file.endswith(".exe"), files)
        for exe in exes:
            self.save_in_tmp_folder(exe)

    def unmount_usb_device(self):
        logger.info("Unmounting USB device")
        self.usb_device.unmount()

    def save_in_tmp_folder(self, file):
        directory, filename = os.path.split(file)
        count = 0
        while os.path.isfile(os.path.join(self.tmp_folder, str(count) + "-" + filename)):
            count += 1
        file_dest = os.path.join(self.tmp_folder, str(count) + "-" + filename)
        self.copy(file, file_dest)
        self.saved_files.append(file_dest)

    def usb_device_is_mounted(self):
        return self.usb_device.is_mounted()

    @staticmethod
    def open(file):
        logger.info("Opening file " + file)
        call_vector = ["start", file]
        execute(call_vector)

    @staticmethod
    def copy(src, dest):
        logger.info("Copying " + src + " to " + dest)
        shutil.copy(src, dest)


def execute(call_vector):
    p = Popen(call_vector, shell=True, stdout=PIPE)
    p.wait()
