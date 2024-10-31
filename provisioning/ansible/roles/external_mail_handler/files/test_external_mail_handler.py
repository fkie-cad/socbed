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


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import Mock, patch

import pytest
from aiosmtpd.controller import Controller

from external_mail_handler import TextMail, mime_string_to_text_mail, Responder, CustomHandler, Server


@pytest.fixture()
def responder():
    return Responder()


@pytest.fixture()
def handler():
    return CustomHandler(Server("172.18.0.2", 25))


@pytest.fixture()
def patch_smtp(request):
    mock = MockSMTP()
    mock_smtp_creator = Mock(return_value=mock)
    p = patch(Responder.__module__ + ".SMTP", mock_smtp_creator)
    p.start()
    request.addfinalizer(p.stop)
    return mock


class MockSMTP:
    def __init__(self):
        self.quit = Mock()
        self.send_message = Mock()
        self.connect = Mock()


class MockSMTPServer:
    def __init__(self, local_address=None, remote_address=None):
        self.remote_address = remote_address
        self.local_address = local_address
        self.process_message = None


class TestCustomHandler:
    def test_swap_sender_receiver(self, handler: CustomHandler):
        mail = TextMail(sender="some@sender", receiver="some@receiver")
        handler.swap_sender_receiver(mail)
        assert mail.sender == "some@receiver"
        assert mail.receiver == "some@sender"

    def test_send_mail(self, handler: CustomHandler, patch_smtp: MockSMTP):
        mail = TextMail(sender="some@domain", receiver="some@other", text="Some text")
        handler.send_mail(mail)
        assert patch_smtp.connect.called
        assert patch_smtp.send_message.called
        assert patch_smtp.quit.called

    @pytest.mark.asyncio
    async def test_handler(self, handler: CustomHandler):
        handler.swap_sender_receiver = Mock()
        handler.send_mail = Mock()
        envelope = Mock()
        mail = TextMail(sender="some@domain", receiver="other@domain", text="Hallo Welt")
        envelope.peer = "127.0.0.1"
        envelope.mail_to = mail.sender
        envelope.rcpt_to = [mail.receiver]
        envelope.content = mail.to_mime_text().as_string().encode("utf-8")
        await handler.handle_DATA(None, None, envelope)
        assert handler.swap_sender_receiver.called
        assert handler.send_mail.called

    def test_init_controller(self, responder: Responder):
        responder.init_controller()

        assert isinstance(responder.controller, Controller)
        assert isinstance(responder.controller.handler, CustomHandler)
        assert responder.controller.hostname == responder.smtp_in.server_ip
        assert responder.controller.port == responder.smtp_in.server_port

    def test_run(self, responder: Responder):
        responder.init_controller = Mock()
        responder.controller = Mock()
        responder.controller.start = Mock()
        responder.controller.stop = Mock()

        with patch("time.sleep", side_effect=[KeyboardInterrupt]):
            try:
                responder.run()
            except KeyboardInterrupt:
                pass

        assert responder.init_controller.called
        assert responder.controller.start.called
        assert not responder.controller.stop.called


@pytest.fixture()
def mail():
    return TextMail()


class TestTextMail:
    def test_init_with_default_attributes(self):
        mail = TextMail()
        assert mail.receiver is None
        assert mail.sender is None
        assert mail.subject == ""
        assert mail.text == ""

    def test_attributes(self):
        mail = TextMail(sender="other@domain", receiver="some@domain", subject="somesubject", text="sometext")
        assert mail.receiver == "some@domain"
        assert mail.sender == "other@domain"
        assert mail.subject == "somesubject"
        assert mail.text == "sometext"

    def test_text_to_mime(self):
        mail = TextMail(text="sometext")
        in_mime = MIMEText("sometext")
        assert mail.text_to_mime_text().as_string() == in_mime.as_string()

    def test_header_to_mime(self):
        mail = TextMail(sender="other@domain", receiver="some@domain", subject="somesubject")
        mime = mail.text_to_mime_text()
        mail.add_header(mime)
        assert mime["Subject"] == "somesubject"
        assert mime["To"] == "some@domain"
        assert mime["From"] == "other@domain"

    def test_to_mime(self):
        mail = TextMail(subject="Subject1337", text="LoremIpsum1337")
        mime = mail.to_mime_text()
        assert isinstance(mime, MIMEText)
        assert "Subject1337" in mime.as_string()
        assert "LoremIpsum1337" in mime.as_string()


class TestMimeToTextMail:
    def test_just_text(self):
        mime = MIMEText("sometext")
        mail = mime_string_to_text_mail(mime.as_string())
        assert mail.text == "sometext"

    def test_text_in_multipart(self):
        mime = MIMEMultipart()
        mime.attach(MIMEText("sometext"))
        mail = mime_string_to_text_mail(mime.as_string())
        assert mail.text == "sometext"

    def test_header_parsed(self):
        mime = MIMEMultipart()
        mime["Subject"] = "somesubject"
        mime["From"] = "Me"
        mime["To"] = "someone"
        mail = mime_string_to_text_mail(mime.as_string())
        assert mail.sender == "Me"
        assert mail.receiver == "someone"
        assert mail.subject == "somesubject"

    def test_empty_header(self):
        mime = MIMEText("sometext")
        mail = mime_string_to_text_mail(mime.as_string())
        assert mail.sender is None
        assert mail.receiver is None
        assert mail.subject == ""
