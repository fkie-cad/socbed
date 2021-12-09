#! /usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import os
from tempfile import gettempdir

from userbehavior.browsing import BrowsingProfile, BrowserConfig, FirefoxBrowser, BrowsingConfig
from userbehavior.filing import FilingProfile, FilerConfig, FolderFiler, FilingConfig
from userbehavior.mailing import MailingProfile, MailerConfig, RealMailer, MailingConfig
from userbehavior.usbing import UsbingProfile, UsbDeviceConfig, WindowsUsbDevice, UsbingConfig

logger = logging.getLogger(__name__)


class BreachSetup:
    def __init__(self, client_id, number_of_clients):
        self.number_of_clients = number_of_clients
        self.client_id = client_id
        logger.info("Client ID: {id}".format(id=self.client_id))
        logger.info("Number of Clients: {num_clients}".format(num_clients=self.number_of_clients))
        self._seed = self.client_id
        logger.info("Seed: {seed}".format(seed=self._seed))
        self.configs = [
            self.breach_browsing_config(),
            self.breach_mailing_config(),
            self.breach_filing_config(),
            self.breach_usbing_config()]

    @classmethod
    def from_mac(cls, mac):
        logger.info("Generating Breach Setup for MAC address {mac}".format(mac=hex(mac)[2:]))
        client_id = mac % 0x100
        number_of_clients = (mac // 0x100) % 0x100
        return BreachSetup(client_id=client_id, number_of_clients=number_of_clients)

    def breach_browsing_config(self):
        profile_config = BrowsingProfile.default_config()
        profile_config.seed = self._seed
        browser_config = BrowserConfig(implementation=FirefoxBrowser)
        return BrowsingConfig(profile_config=profile_config, browser_config=browser_config)

    def breach_mailing_config(self):
        profile_config = MailingProfile.default_config()
        profile_config.seed = self._seed
        profile_config.mail_address = "client" + str(self.client_id) + "@localdomain"
        profile_config.known_mail_addresses = self._generate_known_mail_addresses()
        logger.info("Mail address: {addr}".format(addr=profile_config.mail_address))
        mailer_config = MailerConfig(implementation=RealMailer)
        mailer_config.imap_server = {
            "host": "172.17.0.2", "port": 993, "user": profile_config.mail_address, "password": "breach"}
        logger.info("IMAP Server: {host}".format(host=mailer_config.imap_server["host"]))
        mailer_config.smtp_server = {
            "host": "172.17.0.2", "port": 25}
        logger.info("SMTP Server: {host}".format(host=mailer_config.smtp_server["host"]))
        return MailingConfig(profile_config=profile_config, mailer_config=mailer_config)

    def breach_filing_config(self):
        fc = FilingProfile.default_config()
        fc.seed = self._seed
        filer_config = FilerConfig(implementation=FolderFiler)
        filer_config.folder = os.path.join(gettempdir(), "filing")
        logger.info("Folder for filing: {folder}".format(folder=filer_config.folder))
        return FilingConfig(profile_config=fc, filer_config=filer_config)

    def breach_usbing_config(self):
        profile_config = UsbingProfile.default_config()
        profile_config.seed = self._seed
        usb_device_config = UsbDeviceConfig(implementation=WindowsUsbDevice)
        usb_device_config.image_file = "C:\\BREACH\\evil_image_file.img"
        usb_device_config.mount_point = "Y:\\"
        logger.info("USB image file: {image_file} (mounting on {mount_point})".format(
            image_file=usb_device_config.image_file,
            mount_point=usb_device_config.mount_point))
        return UsbingConfig(profile_config=profile_config, usb_device_config=usb_device_config)

    def _generate_known_mail_addresses(self):
        other_client_ids = [i + 1 for i in range(self.number_of_clients)]
        other_client_ids.remove(self.client_id)
        internal_addresses = ["client{id}@localdomain".format(id=id_) for id_ in other_client_ids]
        external_addresses = ["dummy@extmail{i}".format(i=i + 1) for i in range(3)]
        known_mail_addresses = internal_addresses + external_addresses
        logger.info(
            "I know {num_int} internal and {num_ext} external mail addresses."
                .format(num_int=len(internal_addresses), num_ext=len(external_addresses)))
        return known_mail_addresses
