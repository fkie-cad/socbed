#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pytest

from userbehavior.mailing.mailer import MailerException
from userbehavior.mailing.tests.mocks import MockMailer, ExceptionRaisingMailer
from userbehavior.misc.util import Mail


@pytest.fixture()
def mm():
    return MockMailer()


class TestMockMailer:
    def test_mails_init(self, mm: MockMailer):
        assert mm.mails() == []

    def test_fill_with_mails(self, mm: MockMailer):
        mm.fill_with_mails()
        assert mm.mails() != []

    def test_mail_shallow_copy(self, mm: MockMailer):
        mm.fill_with_mails()
        l = mm.mails()
        l.clear()
        assert mm.mails()

    def test_send_mail(self, mm: MockMailer):
        mail = Mail()
        mm.send(mail)

    def test_last_sent_mail(self, mm: MockMailer):
        mail = Mail()
        mm.send(mail)
        assert mm.last_sent_mail == mail

    def test_delete_all(self, mm: MockMailer):
        mm.fill_with_mails()
        mm.delete_all()
        assert mm.mails() == []

    @pytest.mark.parametrize("filled", [True, False])
    def test_reset(self, filled):
        mm = MockMailer(filled=filled)
        mm.fill_with_mails()
        mm.reset()
        assert len(mm.mails()) == len(MockMailer(filled=filled).mails())

    def test_init_filled(self):
        filled_mm = MockMailer(filled=True)
        assert filled_mm.mails()


@pytest.fixture()
def erm():
    return ExceptionRaisingMailer()


class TestExceptionRaisingMailer:
    def test_mails(self, erm: ExceptionRaisingMailer):
        with pytest.raises(MailerException):
            erm.mails()

    def test_delete_all(self, erm: ExceptionRaisingMailer):
        with pytest.raises(MailerException):
            erm.delete_all()

    def test_reset(self, erm: ExceptionRaisingMailer):
        with pytest.raises(MailerException):
            erm.reset()

    def test_send(self, erm: ExceptionRaisingMailer):
        with pytest.raises(MailerException):
            erm.send(Mail())
