#!/usr/bin/python3
# -*- coding: utf-8 -*-
import imaplib
import logging
import smtplib
from contextlib import suppress

from userbehavior.mailing.mailer import Mailer, MailerException
from userbehavior.mailing.mailingprofile import Server
from userbehavior.misc.util import Mail

logger = logging.getLogger(__name__)


class RealMailer(Mailer):
    def __init__(self, imap_server, smtp_server, mailbox="INBOX"):
        self.imap_server = Server(**imap_server)
        self.smtp_server = Server(**smtp_server)
        self.mailbox = mailbox
        self.reconnect_limit = 12
        self.reconnect_timeout = 10
        self._imap_connection = None

    def __del__(self):
        self._imap_close_logout()

    def mails(self):
        logger.debug("Getting mails from mailbox {mb}".format(mb=self.mailbox))
        self._imap_refresh()
        raw_mail_indices = self._try_imap_search("ALL")
        mails = [self._raw_mail_to_mail(self._try_imap_fetch(raw_mail_index))
                 for raw_mail_index in raw_mail_indices]
        return mails

    @staticmethod
    def _raw_mail_to_mail(raw_mail):
        return Mail.mime_string_to_mail(raw_mail[0][1].decode("utf-8"))

    def reset(self):
        self._imap_close_logout()
        self._imap_connect()

    def delete_all(self):
        logger.debug("Deleting all mails in \"" + str(self.mailbox) + "\"")
        self._imap_refresh()
        raw_mail_indices = self._try_imap_search("ALL")
        for raw_mail_index in raw_mail_indices:
            self._try_imap_store_flag(raw_mail_index, "\\Deleted")
        self._try_imap_expunge()

    def send(self, mail):
        logger.debug("Sending mail")
        try:
            with smtplib.SMTP(host=self.smtp_server.host, port=self.smtp_server.port, timeout=30) as s:
                s.send_message(mail.to_mime())
        except OSError as e:
            raise MailerException("Could not send mail: {e}".format(e=str(e)))

    def _imap_connect(self):
        reconnect_countdown = self.reconnect_limit
        while not self._imap_is_connected():
            try:
                self._try_imap_connect()
            except MailerException as e:
                if reconnect_countdown > 0:
                    logger.debug(str(e))
                    logger.debug("Try to reconnect {cd} times".format(cd=reconnect_countdown))
                    reconnect_countdown -= 1
                else:
                    raise

    def _imap_refresh(self):
        if self._imap_is_connected():
            try:
                self._try_imap_select()
            except imaplib.IMAP4_SSL.error:
                self._imap_connect()
        else:
            self._imap_connect()

    def _imap_close_logout(self):
        if self._imap_connection is not None:
            with suppress(Exception):
                self._imap_connection.close()
            with suppress(Exception):
                self._imap_connection.logout()
            self._imap_connection = None

    def _try_imap_connect(self):
        self._try_imap_create()
        self._try_imap_login()
        self._try_imap_select()

    def _try_imap_create(self):
        try:
            self._imap_connection = imaplib.IMAP4_SSL(
                host=self.imap_server.host,
                port=self.imap_server.port)
        except (OSError, imaplib.IMAP4_SSL.error) as e:
            raise MailerException("Failed to create connection object: {e}".format(e=str(e)))

    def _imap_is_connected(self):
        if self._imap_connection is None:
            return False
        else:
            try:
                err, msg = self._imap_connection.check()
                return err == "OK"
            except (imaplib.IMAP4_SSL.error, TimeoutError, ConnectionError):
                return False

    def _try_imap_login(self):
        try:
            self._imap_connection.login(
                self.imap_server.user,
                self.imap_server.password)
        except imaplib.IMAP4_SSL.error as e:
            raise MailerException("Failed to login: {e}".format(e=str(e)))

    def _try_imap_select(self):
        try:
            self._imap_connection.select(self.mailbox)
        except imaplib.IMAP4_SSL.error as e:
            raise MailerException("Failed to select mailbox: {e}".format(e=str(e)))

    def _try_imap_fetch(self, raw_mail_index):
        try:
            typ, raw_mail = self._imap_connection.fetch(raw_mail_index, "(UID RFC822)")
        except imaplib.IMAP4_SSL.error as e:
            MailerException("Could not fetch: {e}".format(e=str(e)))
        else:
            return raw_mail

    def _try_imap_search(self, query):
        try:
            typ, raw_mail_indices = self._imap_connection.search(None, query)
        except imaplib.IMAP4_SSL.error as e:
            raise MailerException("Failed Mail search: {e}".format(e=str(e)))
        else:
            raw_mail_indices = raw_mail_indices[0].decode("utf-8").split()
            return raw_mail_indices

    def _try_imap_store_flag(self, raw_mail_index, flag):
        try:
            self._imap_connection.store(raw_mail_index, "+FLAGS", flag)
        except imaplib.IMAP4_SSL.error as e:
            MailerException("Failed to store flag: {e}".format(e=str(e)))

    def _try_imap_expunge(self):
        try:
            self._imap_connection.expunge()
        except imaplib.IMAP4_SSL.error as e:
            MailerException("Failed to expunge: {e}".format(e=str(e)))
