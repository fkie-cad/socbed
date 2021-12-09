#!/usr/bin/python3
# -*- coding: utf-8 -*-
import mimetypes
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email import encoders

import os.path

import pytest

from userbehavior.misc.util import Mail
from userbehavior.misc.util import store_attachments


@pytest.fixture()
def mail():
    return Mail()


@pytest.fixture
def path():
    return os.path.dirname(os.path.abspath(__file__))


class TestMail:
    def test_init_with_default_attributes(self):
        mail = Mail()
        assert mail.receiver is None
        assert mail.sender is None
        assert mail.subject == ""
        assert mail.text == ""
        assert mail.html == ""
        assert mail.attachments == []

    def test_attributes(self):
        mail = Mail(sender="other@domain", receiver="some@domain", subject="somesubject",
                    text="sometext", html="<body>SomeHtml</body>", attachments=["att1", "att2"])
        assert mail.receiver == "some@domain"
        assert mail.sender == "other@domain"
        assert mail.subject == "somesubject"
        assert mail.text == "sometext"
        assert mail.html == "<body>SomeHtml</body>"
        assert "att1" in mail.attachments

    def test_add_header_to_mime(self):
        mail = Mail(sender="other@domain", receiver="some@domain", subject="somesubject")
        mime = MIMEText("sometext")
        mail._add_header(mime)
        assert mime["Subject"] == "somesubject"
        assert mime["To"] == "some@domain"
        assert mime["From"] == "other@domain"

    def test_to_mime(self):
        mail = Mail(subject="Subject1337", text="LoremIpsum1337")
        mime = mail.to_mime()
        assert "Subject1337" in mime.as_string()
        assert "LoremIpsum1337" in mime.as_string()

    def test_mail_without_attachments(self):
        mail = Mail(text="Hello World", subject="somesubject")
        assert isinstance(mail.to_mime(), MIMEText)

    def test_to_mime_only_html(self):
        mail = Mail(subject="Subject1337", html="<body>Hello</body>")
        mime = mail.to_mime()
        assert mime.get_content_subtype() == 'html'
        assert "Hello" in mime.as_string()

    def test_attachment_to_mime_base(self, mail: Mail, path, tmpdir):
        filename = "test.pdf"
        file_path = os.path.join(path, "test_payloads", filename)
        assert os.path.isfile(file_path)
        mime = mail._attachment_to_mime_base(file_path)
        res = store_attachments(mime, directory=str(tmpdir))
        assert os.path.isfile(res[0])

    def test_mail_with_attachments(self, path):
        filename = "test.pdf"
        file_path = os.path.join(path, "test_payloads", filename)
        assert os.path.isfile(file_path)
        mail = Mail(text="sometext", sender="somesender", receiver="somereceiver", attachments=[file_path])
        mime = mail.to_mime()
        mime_header = MIMEText("")
        mail._add_header(mime_header)
        assert isinstance(mime, MIMEMultipart)
        assert mime["From"] == mime_header["From"]
        assert mime["To"] == mime_header["To"]
        assert mime["Subject"] == mime_header["Subject"]
        assert filename in mime.as_string()
        assert mail.text in mime.as_string()

    def test_to_mime_text(self):
        mail = Mail(sender="some", receiver="address", text="sometext")
        mime = mail.to_mime()
        assert isinstance(mime, MIMEText)
        assert mail.text in mime.as_string()
        assert mail.sender == mime["From"]
        assert mail.receiver == mime["To"]


class TestMimeToMail:
    def test_just_text(self):
        mime = MIMEText("sometext")
        mail = Mail.mime_string_to_mail(mime.as_string())
        assert mail.text == "sometext"

    def test_text_in_multipart(self):
        mime = MIMEMultipart()
        mime.attach(MIMEText("sometext"))
        mail = Mail.mime_string_to_mail(mime.as_string())
        assert mail.text == "sometext"

    def test_html_in_multipart(self):
        mime = MIMEMultipart()
        mime.attach(MIMEText("<body>sometext</body>", "html"))
        mail = Mail.mime_string_to_mail(mime.as_string())
        assert mail.html == "<body>sometext</body>"

    def test_header_parsed(self):
        mime = MIMEMultipart()
        mime["Subject"] = "somesubject"
        mime["From"] = "Me"
        mime["To"] = "someone"
        mail = Mail.mime_string_to_mail(mime.as_string())
        assert mail.sender == "Me"
        assert mail.receiver == "someone"
        assert mail.subject == "somesubject"

    def test_empty_header(self):
        mime = MIMEText("sometext")
        mail = Mail.mime_string_to_mail(mime.as_string())
        assert mail.sender is None
        assert mail.receiver is None
        assert mail.subject == ""


@pytest.fixture(params=["pdf", "jpg"])
def file_extension(request):
    # the file extensions correspond to files "test." + extension in test_payloads
    return request.param


class TestStoreAttachments:
    def test_some_attachments(self, path, file_extension, tmpdir):
        mail = MIMEMultipart()
        file = os.path.join(path, "test_payloads/test." + str(file_extension))
        assert os.path.isfile(file)

        file_type, encoding = mimetypes.guess_type(file)
        if file_type is None or encoding is not None:
            file_type = "application/octet-stream"
        mtype, stype = file_type.split("/", 1)

        with open(file, "rb") as fp:
            if mtype == "text":
                att = MIMEText(fp.read(), _subtype=stype)
            elif mtype == "image":
                att = MIMEImage(fp.read(), _subtype=stype)
            elif mtype == "audio":
                att = MIMEAudio(fp.read(), _subtype=stype)
            elif mtype == "application":
                att = MIMEApplication(fp.read(), _subtype=stype)
            else:
                att = MIMEBase(mtype, stype)
                att.set_payload(fp.read())
                encoders.encode_base64(att)

        att.add_header("Content-Disposition", "attachment", filename="test." + str(file_extension))
        mail.attach(att)

        res = store_attachments(mail, directory=os.path.join(str(tmpdir), "test_attachments"))
        assert os.path.isfile(res[0])
        assert res[0] == os.path.join(str(tmpdir), "test_attachments", "test." + str(file_extension))
