#!/usr/bin/python3
# -*- coding: utf-8 -*-
import email
import os.path
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tempfile import gettempdir


class Factory:
    def __init__(self, implementation, args=None, kwargs=None):
        self.implementation = implementation
        self.args = args or tuple()
        self.kwargs = kwargs or dict()

    def create(self):
        return self.implementation(*self.args, **self.kwargs)


class Mail:
    def __init__(self, sender=None, receiver=None, subject="", text="", html="", attachments=list()):
        self.html = html
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.text = text
        self.attachments = attachments

    @staticmethod
    def mime_string_to_mail(mime_string):
        mime = email.message_from_string(mime_string)
        sender = mime["From"]
        receiver = mime["To"]
        subject = mime["Subject"] or ""
        text = ""
        html = ""
        for part in mime.walk():
            if part.get_content_type() == "text/plain":
                text += part.get_payload()
            if part.get_content_type() == "text/html":
                html += part.get_payload()
        attachments = store_attachments(mime, directory=os.path.join(gettempdir(), "breach_attachments"))
        mail = Mail(sender=sender, receiver=receiver, subject=subject, text=text, html=html, attachments=attachments)
        return mail

    def to_mime(self):
        parts = self._attachments_to_mime_bases()
        if self.text != "":
            parts.append(self._text_to_mime_text())
        if self.html != "":
            parts.append(self._html_to_mime_text())
        if len(parts) == 0:
            mime = MIMEText("")
        elif len(parts) == 1:
            mime = parts[0]
        else:
            mime = MIMEMultipart()
            for part in parts:
                mime.attach(part)
        self._add_header(mime)
        return mime

    def _text_to_mime_text(self):
        return MIMEText(self.text)

    def _html_to_mime_text(self):
        return MIMEText(self.html, "html")

    def _attachments_to_mime_bases(self):
        return [self._attachment_to_mime_base(att) for att in self.attachments]

    def _attachment_to_mime_base(self, attachment):
        directory, filename = os.path.split(attachment)
        mime = MIMEBase("application", "octet-stream")
        with open(attachment, "rb") as fp:
            mime.set_payload(fp.read())
        email.encoders.encode_base64(mime)
        mime.add_header("Content-Disposition", "attachment", filename=filename)
        return mime

    def _add_header(self, mime):
        mime["Subject"] = self.subject
        mime["To"] = self.receiver
        mime["From"] = self.sender


def store_attachments(mail, directory="./attachments"):
    """ Stores attachments from mail in directory. Returns a list of absolute paths of stored attachments. """

    # Check and create directory if necessary
    os.makedirs(directory, exist_ok=True)

    attachments = []

    for part in mail.walk():
        if part.get("Content-Disposition") is not None:
            filename = part.get_filename()
            if not filename:
                filename = "attachment-" + str(len(attachments)) + ".file"
            if os.path.isfile(os.path.join(directory, filename)):
                filename = "1" + filename
            with open(os.path.join(directory, filename), "wb+") as fp:
                fp.write(part.get_payload(decode=True))
            attachments.append(os.path.abspath(os.path.join(directory, filename)))

    return attachments
