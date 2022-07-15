#!/usr/bin/python3
# -*- coding: utf-8 -*-
from userbehavior.mailing.mailer import Mailer, MailerException
from userbehavior.misc.util import Mail


class MockMailer(Mailer):
    def __init__(self, filled=False):
        self.last_sent_mail = None
        self._mails_field = list()
        self.mem_filled = filled
        if filled:
            self.fill_with_mails()

    def fill_with_mails(self):
        self._mails_field.extend(
            [Mail(receiver="my@mailaddress.domain",
                  sender="sender" + str(i) + "@somedomain",
                  text="sometext" + str(i))
             for i in range(4)])

    def mails(self):
        return self._mails_field.copy()

    def send(self, mail):
        self.last_sent_mail = mail

    def delete_all(self):
        self._mails_field.clear()

    def reset(self):
        self.__init__(filled=self.mem_filled)


class ExceptionRaisingMailer(Mailer):
    def mails(self):
        raise MailerException()

    def reset(self):
        raise MailerException()

    def send(self, mail):
        raise MailerException()

    def delete_all(self):
        raise MailerException()
