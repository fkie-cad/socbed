#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import time
from types import SimpleNamespace

from userbehavior.mailing.helpers import open_file, open_url, get_urls_in_text, get_urls_in_html
from userbehavior.mailing.mailer import MailerException, NullMailer
from userbehavior.mailing.mailingprofile import MailingProfile, MailingProfileException, MailingProfileConfig
from userbehavior.mailing.realmailer import RealMailer
from userbehavior.misc.util import Mail, Factory

logger = logging.getLogger(__name__)


class MailingConfig:
    def __init__(self, profile_config, mailer_config):
        self.profile_config = profile_config
        self.mailer_config = mailer_config

    @classmethod
    def from_dict(cls, d):
        profile_config = MailingProfileConfig(**d['profile'])
        mailer_config = MailerConfig.from_str_dict(**d['mailer'])
        return cls(profile_config=profile_config, mailer_config=mailer_config)


class MailerConfig(SimpleNamespace):
    implementations = {
        'NullMailer': NullMailer,
        'RealMailer': RealMailer}

    def __init__(self, implementation=None, **kwargs):
        self.implementation = implementation or NullMailer
        super().__init__(**kwargs)

    @classmethod
    def from_str_dict(cls, implementation=None, **kwargs):
        parsed_implementation = cls.implementations[implementation]
        return cls(implementation=parsed_implementation, **kwargs)


class Mailing:
    def __init__(self, mailing_profile=None, mailer_factory=None):
        self.mailing_profile = mailing_profile or self.default_mailing_profile()
        self.mailer_factory = mailer_factory or self.default_mailer_factory()
        self.end_time = None
        self._timeout = 5
        self._mailer = None

    @classmethod
    def from_config(cls, config: MailingConfig):
        kwargs = config.mailer_config.__dict__.copy()
        implementation = kwargs.pop("implementation")
        mf = Factory(implementation=implementation, kwargs=kwargs)
        mp = MailingProfile(config=config.profile_config)
        return cls(mailing_profile=mp, mailer_factory=mf)

    @staticmethod
    def default_mailer_factory():
        return Factory(implementation=NullMailer)

    @staticmethod
    def default_mailing_profile():
        return MailingProfile()

    def set_timeout(self, secs):
        self._timeout = secs

    def set_duration(self, secs):
        if secs is None:
            self.end_time = None
        else:
            self.end_time = time.time() + secs

    def run(self):
        logger.info("Mailing started")
        self._init_mailer()
        self._loop_until_has_ended()
        logger.info("Mailing ended")

    def _init_mailer(self):
        logger.info("Initializing Mailer")
        self._mailer = self.mailer_factory.create()

    def _loop_until_has_ended(self):
        log = "Loop actions"
        if self.end_time is not None:
            log += " until " + time.ctime(self.end_time)
        logger.info(log)
        while not self._has_ended():
            self._lookup_mailbox()
            self._delete_mails_in_mailbox()
            if self.mailing_profile.get_value("Send Mail"):
                self._send_mail()
            self._take_timeout()

    def _has_ended(self):
        if self.end_time is None:
            return False
        else:
            return time.time() > self.end_time

    def _lookup_mailbox(self):
        try:
            mails = self._mailer.mails()
        except MailerException as e:
            logger.info("Could not get mails: {e}".format(e=str(e)))
        else:
            logger.info("Found {len} new mails".format(len=len(mails)))
            self._handle_mails(mails)

    def _handle_mails(self, mails):
        for mail in mails:
            self._open_content(mail)

    def _delete_mails_in_mailbox(self):
        try:
            self._mailer.delete_all()
            logger.info("Deleted all mails in mailbox")
        except MailerException as e:
            logger.info("Could not delete mails: {e}".format(e=str(e)))

    def _open_content(self, mail):
        self._open_urls(mail)
        self._open_attachments(mail)

    @staticmethod
    def _open_urls(mail):
        urls = get_urls_in_text(mail.text) + get_urls_in_html(mail.html)
        for url in urls:
            logger.info("Open url: " + str(url))
            open_url(url)

    @staticmethod
    def _open_attachments(mail):
        for att in mail.attachments:
            logger.info("Open attachment: " + str(att))
            open_file(att)

    def _send_mail(self):
        logger.info("Try to send a mail")
        try:
            receiver = self.mailing_profile.get_known_mail_address()
        except MailingProfileException:
            logger.info("No known mail addresses found")
        else:
            self._send_mail_to_receiver(receiver)

    def _send_mail_to_receiver(self, receiver):
        logger.info("Sending mail to {receiver}".format(receiver=str(receiver)))
        mail = Mail(
            sender=self.mailing_profile.mail_address,
            receiver=receiver,
            subject=self.mailing_profile.get_random_text(length=20),
            text=self.mailing_profile.get_random_text(length=100)
        )
        try:
            self._mailer.send(mail)
        except MailerException as e:
            logger.info("Sending email failed: {e}".format(e=str(e)))

    def _take_timeout(self, secs=None):
        logger.info("Taking timeout for " + str(secs or self._timeout) + " secs")
        time.sleep(secs or self._timeout)


class MailingException(Exception):
    pass
