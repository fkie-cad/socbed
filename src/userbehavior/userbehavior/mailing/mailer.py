#!/usr/bin/python3
# -*- coding: utf-8 -*-


class Mailer:
    def mails(self):
        raise NotImplementedError()

    def delete_all(self):
        raise NotImplementedError()

    def send(self, mail):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()


class MailerException(Exception):
    pass


class NullMailer(Mailer):
    def reset(self):
        pass

    def delete_all(self):
        pass

    def send(self, mail):
        pass

    def mails(self):
        return []
