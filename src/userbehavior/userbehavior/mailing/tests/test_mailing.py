#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
from unittest.mock import patch, Mock

import pytest

from userbehavior.mailing.mailer import NullMailer
from userbehavior.mailing.mailing import Mailing, MailingConfig, MailerConfig
from userbehavior.mailing.mailingprofile import MailingProfile, MailingProfileConfig
from userbehavior.mailing.tests.mocks import MockMailer, ExceptionRaisingMailer
from userbehavior.misc.util import Mail, Factory

long_test = pytest.mark.long_test


class TestMailingConfig:
    def test_from_dict(self):
        d = {'profile': {'seed': 42, 'mail_address': 'some@address'},
             'mailer': {'implementation': 'NullMailer'}}
        mc = MailingConfig.from_dict(d)
        assert mc.profile_config.seed == 42
        assert mc.profile_config.mail_address == 'some@address'
        assert mc.mailer_config.implementation == NullMailer


class TestMailerConfig:
    def test_implementations(self):
        known_implementations = ["NullMailer", "RealMailer"]
        for impl in known_implementations:
            assert impl in MailerConfig.implementations


@pytest.fixture()
def m():
    mf = Factory(implementation=MockMailer)
    mf.kwargs = {"filled": True}
    return Mailing(mailer_factory=mf)


@pytest.fixture()
def open_file_mock(request):
    mock = Mock()
    p = patch(Mailing.__module__ + ".open_file", mock)
    p.start()
    request.addfinalizer(p.stop)
    return mock


@pytest.fixture()
def open_url_mock(request):
    mock = Mock()
    p = patch(Mailing.__module__ + ".open_url", mock)
    p.start()
    request.addfinalizer(p.stop)
    return mock


class TestMailing:
    def test_create_from_config(self):
        profile_config = MailingProfileConfig(mail_address="mymailaddress")
        mailer_config = MailerConfig(implementation=MockMailer, some_key="value")
        config = MailingConfig(profile_config=profile_config, mailer_config=mailer_config)
        m = Mailing.from_config(config)
        assert isinstance(m, Mailing)
        assert m.mailing_profile.mail_address == "mymailaddress"
        assert m.mailer_factory.implementation == MockMailer
        assert m.mailer_factory.kwargs["some_key"] == "value"

    def test_default_mailing_profile(self, m: Mailing):
        assert isinstance(m.default_mailing_profile(), MailingProfile)
        assert m.mailing_profile is not None

    def test_init_mailer(self, m: Mailing):
        m._init_mailer()
        assert m._mailer is not None

    def test_open_attachments(self, m: Mailing, open_file_mock: Mock):
        attachments = ["a/file.txt", "b/file.txt"]
        mail = Mail(attachments=attachments)
        m._open_attachments(mail)
        assert open_file_mock.call_count == len(attachments)

    @pytest.mark.parametrize("text_url", [
        ("Click on http://some.com", "http://some.com"),
        ("another url is google.de", "http://google.de"),
    ])
    def test_open_urls(self, m: Mailing, open_url_mock: Mock, text_url: (str, str)):
        text, url = text_url
        mail_with_url = Mail(text=text)
        m._open_urls(mail_with_url)
        open_url_mock.assert_called_once_with(url)

    def test_open_href_urls_in_html_mail(self, m: Mailing, open_url_mock: Mock):
        mail_with_href_url = Mail(html="<body><a href='some.link.com/to_site.html'>Link</a></html>")
        m._open_urls(mail_with_href_url)
        open_url_mock.assert_called_once_with("http://some.link.com/to_site.html")

    def test_delete_mails(self, m: Mailing):
        m._init_mailer()
        m._delete_mails_in_mailbox()
        assert m._mailer.mails() == []

    def test_handle_new_mails(self, m: Mailing):
        m._init_mailer()
        mails = m._mailer.mails()
        m._open_content = Mock()
        m._lookup_mailbox()
        assert m._open_content.call_count == len(mails)

    def test_send_mail(self, m: Mailing):
        m._init_mailer()
        some_address = "some@address"
        some_text = "Some Random Text"
        m.mailing_profile.get_known_mail_address = lambda: some_address
        m.mailing_profile.get_random_text = lambda length: some_text
        m._send_mail()
        sent_mail = m._mailer.last_sent_mail
        assert sent_mail.receiver == some_address
        assert sent_mail.text == some_text

    def test_send_mail_without_known_addresses(self, m: Mailing):
        m._init_mailer()
        m.mailing_profile.known_mail_addresses = list()
        m._send_mail_to_receiver = Mock()
        m._send_mail()
        assert not m._send_mail_to_receiver.called

    def test_take_timeout(self, m: Mailing):
        begin = time.time()
        m.set_timeout(0.1)
        m._take_timeout()
        end = time.time()
        assert end - begin >= 0.1

    def test_has_ended(self, m: Mailing):
        m.set_duration(0.1)
        assert not m._has_ended()
        time.sleep(0.1)
        assert m._has_ended()

    def test_start(self, m: Mailing):
        m._init_mailer = Mock()
        m._loop_until_has_ended = Mock()
        m.run()
        assert m._init_mailer.called
        assert m._loop_until_has_ended.called

    def test_mailing_runs_in_fast(self, m: Mailing):
        m._take_timeout = Mock()
        duration = 0.2
        begin = time.time()
        m.set_duration(duration)
        m.run()
        end = time.time()
        assert end - begin >= duration

    def test_mailing_runs_in_fast_with_exceptions(self):
        mf = Factory(implementation=ExceptionRaisingMailer)
        m = Mailing(mailer_factory=mf)
        self.test_mailing_runs_in_fast(m)
