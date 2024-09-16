#!/usr/bin/env python3

# Copyright 2016-2022 Fraunhofer FKIE
#
# This file is part of SOCBED.
#
# SOCBED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SOCBED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SOCBED. If not, see <http://www.gnu.org/licenses/>.


import email
from email.mime.text import MIMEText
from smtplib import SMTP
from aiosmtpd.controller import Controller

import time

import logging
from logging.handlers import WatchedFileHandler


def setup_logging():
    logging.Formatter.converter = time.localtime
    logging.Formatter.default_time_format = "%Y-%m-%dT%H:%M:%S"
    is_dst = time.daylight and time.localtime().tm_isdst > 0
    gmt_offset_secs = - (time.altzone if is_dst else time.timezone)
    gmt_offset_string = "{0:+03d}:00".format(gmt_offset_secs // 3600)
    log_handler = WatchedFileHandler(filename="/var/log/breach/external_mail_handler.log")
    logging.basicConfig(
        handlers=[log_handler],
        level=logging.INFO,
        format="%(asctime)s" + gmt_offset_string + " %(name)s %(levelname)s %(message)s",
    )


logger = logging.getLogger(__name__)


class CustomHandler:
    def __init__(self, smtp_out):
        self.smtp_out = smtp_out

    async def handle_DATA(self, server, session, envelope):
        # peer, mail_from, mail_to, rcpt_tos and data are now all encapsulated in 'envelope'
        # keep in mind that envelope.data contains raw bytes which first have to be decoded
        mail = mime_string_to_text_mail(envelope.data.decode("utf-8"))
        logger.info("Received mail from " + str(mail.sender) + " addressed to " + str(mail.receiver))
        self.swap_sender_receiver(mail)
        self.modify_text(mail)
        self.send_mail(mail)
        # A return message is mandatory
        return '250 OK'

    @staticmethod
    def swap_sender_receiver(mail):
        tmp = mail.sender
        mail.sender = mail.receiver
        mail.receiver = tmp

    @staticmethod
    def modify_text(mail):
        mail.text = "You sent me the following text:\n" + mail.text

    def send_mail(self, mail):
        con = SMTP()
        try:
            con.connect(host=self.smtp_out.server_ip, port=self.smtp_out.server_port)
            con.send_message(mail.to_mime_text())
        finally:
            con.quit()


class Responder:
    def __init__(self):
        self.smtp_out = Server("172.18.0.2", 25)
        self.smtp_in = Server("0.0.0.0", 25)
        self.controller: Controller|None = None

    def run(self):
        logger.info("Starting Mail Responder listening at " +
                    str(self.smtp_in.server_ip) +
                    ":" + str(self.smtp_in.server_port))
        logger.info("Sending responses to " +
                    str(self.smtp_out.server_ip) +
                    ":" + str(self.smtp_out.server_port))
        self.init_controller()
        self.controller.start()  # detaches from current thread
        input('SMTP server running. Press Return to stop server and exit.')
        self.controller.stop()

    def init_controller(self):
        handler = CustomHandler(self.smtp_out)
        self.controller = Controller(handler, hostname=self.smtp_in.server_ip, port=self.smtp_in.server_port)


def mime_string_to_text_mail(mime_string):
    mime = email.message_from_string(mime_string)
    sender = mime["From"]
    receiver = mime["To"]
    subject = mime["Subject"] or ""
    text = ""
    for part in mime.walk():
        if part.get_content_type() == "text/plain":
            text += part.get_payload()
    mail = TextMail(sender=sender, receiver=receiver, subject=subject, text=text)
    return mail


class TextMail:
    def __init__(self, sender=None, receiver=None, subject="", text=""):
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.text = text

    def add_header(self, mime):
        mime["Subject"] = self.subject
        mime["To"] = self.receiver
        mime["From"] = self.sender

    def text_to_mime_text(self):
        return MIMEText(self.text)

    def to_mime_text(self):
        mime = self.text_to_mime_text()
        self.add_header(mime)
        return mime


class Server:
    def __init__(self, server_ip=None, server_port=None):
        self.server_port = server_port
        self.server_ip = server_ip


if __name__ == "__main__":
    setup_logging()
    responder = Responder()
    responder.run()