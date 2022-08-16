#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pytest

from userbehavior.mailing.mailingprofile import MailingProfile, MailingProfileException, MailingProfileConfig


@pytest.fixture()
def mp():
    return MailingProfile()


class TestMailingProfile:
    def test_attributes(self, mp: MailingProfile):
        assert isinstance(mp.mail_address, str)
        assert isinstance(mp.known_mail_addresses, list)

    def test_write_mail_distributions(self, mp: MailingProfile):
        value = mp.get_value("Send Mail")
        assert value in [True, False]

    def test_get_known_mail_address(self, mp: MailingProfile):
        address = "test@address"
        mp.known_mail_addresses = [address]
        assert mp.get_known_mail_address() == address

    def test_raise_exception_if_no_known_addresses(self, mp: MailingProfile):
        mp.known_mail_addresses = []
        with pytest.raises(MailingProfileException) as e:
            mp.get_known_mail_address()
        assert "mail address" in str(e.value)

    def test_config_mail_address(self):
        mail_address = "hallo@welt"
        config = MailingProfileConfig(mail_address=mail_address)
        mp = MailingProfile(config=config)
        assert mp.mail_address == "hallo@welt"

    def test_config_known_mail_addresses(self):
        known = ["i@me.org", "some@other.place"]
        config = MailingProfileConfig(known_mail_addresses=known)
        mp = MailingProfile(config=config)
        assert mp.known_mail_addresses == known
