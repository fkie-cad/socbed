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
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import Envelope
import asyncio
from smtplib import SMTP

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

class Server:
    def __init__(self, server_ip=None, server_port=None):
        self.server_port: None | int = server_port
        self.server_ip: None | str = server_ip

logger = logging.getLogger(__name__)
smtp_out = Server("127.0.0.1", 1025)
smtp_in = Server("0.0.0.0", 1025)


class CustomHandler:
    async def handle_DATA(self, server, session, envelope: Envelope):
        # Contents are available raw bytes, thus requiring decoding
        self.process(envelope.content.decode("utf8"), server)
        # if error_occurred:
        #     return '500 Could not process your message'
        return '250 OK'
    
    def process(self, content, server):
        mail = mime_string_to_text_mail(content)
        logger.info("Received mail from " + str(mail.sender) + " addressed to " + str(mail.receiver))
        self.swap_sender_receiver(mail)
        self.modify_text(mail)
        self.send_mail(mail, smtp_instance=server)
        
    @staticmethod
    def swap_sender_receiver(mail):
        tmp = mail.sender
        mail.sender = mail.receiver
        mail.receiver = tmp

    @staticmethod
    def modify_text(mail):
        mail.text = "You sent me the following text:\n" + mail.text

    @staticmethod
    def send_mail(mail, smtp_instance):
        ip = smtp_out.server_ip
        port = smtp_out.server_port
        if ip and port:
            smtp_instance.connect(host=ip, port=port)
            smtp_instance.send_message(mail.to_mime_text())


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
        self.server_port: None | int = server_port
        self.server_ip: None | str = server_ip


if __name__ == "__main__":
    setup_logging()
    logger.info("Starting Mail Responder listening at " + 
                str(smtp_in.server_ip) + ":" + str(smtp_in.server_port))
    logger.info("Sending responses to " + 
                str(smtp_out.server_ip) + ":" + str(smtp_out.server_port))
    controller = Controller(CustomHandler(), hostname=smtp_in.server_ip, port=smtp_in.server_port)
    while True:
        # don't care about stopping
        pass
