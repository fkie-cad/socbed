#!/usr/bin/python3
# -*- coding: utf-8 -*-
from userbehavior.mailing.mailer import Mailer, NullMailer


class TestNullMailer:
    def test_init(self):
        isinstance(NullMailer(), Mailer)

    def test_stubbed_methods(self):
        m = NullMailer()
        assert m.mails() == []
        m.delete_all()
        m.send(None)
        m.reset()
