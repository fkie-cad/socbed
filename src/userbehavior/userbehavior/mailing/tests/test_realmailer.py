#! /usr/bin/python3
# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest

from userbehavior.mailing.mailingprofile import Server
from userbehavior.mailing.realmailer import RealMailer


def raise_(exception):
    raise exception


@pytest.fixture()
def realmailer():
    imap_connection_stub = SimpleNamespace()
    realmailer = RealMailer({"host": "0.0.0.0"}, {"host": "0.0.0.0"})
    realmailer._imap_connection = imap_connection_stub
    return realmailer


class TestRealMailer:
    def test_creation_with_server_dicts(self):
        server_dict = {"host": "172.17.0.2", "port": 993, "user": "some@address", "password": "breach"}
        rm = RealMailer(imap_server=server_dict, smtp_server=server_dict)
        assert isinstance(rm.imap_server, Server)
        assert isinstance(rm.smtp_server, Server)

    def test_handle_imap_connection_check_returns_TimeoutError(self, realmailer: RealMailer):
        realmailer._imap_connection.check = lambda: raise_(TimeoutError())
        assert not realmailer._imap_is_connected()

    def test_handle_imap_connection_check_returns_ConnectionError(self, realmailer: RealMailer):
        realmailer._imap_connection.check = lambda: raise_(ConnectionError())
        assert not realmailer._imap_is_connected()
