import pytest

from userbehavior.breachsetup import BreachSetup
from userbehavior.browsing import BrowsingConfig
from userbehavior.filing import FilingConfig
from userbehavior.mailing import MailingConfig, Server
from userbehavior.usbing import UsbingConfig


@pytest.fixture(scope="class", params=["0ABABABA0101", "0ABABABA2517"])
def bs(request):
    mac = int(request.param, 16)
    setup = BreachSetup.from_mac(mac)
    return setup


class TestBreachSetup:
    def test_from_mac(self):
        mac = int("0ABABABA2517", 16)
        bs = BreachSetup.from_mac(mac)
        assert bs.client_id == mac % 0x100
        assert bs.number_of_clients == (mac // 0x100) % 0x100

    @pytest.mark.parametrize(
        "config_class",
        [BrowsingConfig, MailingConfig, FilingConfig, UsbingConfig])
    def test_configs_are_there(self, bs: BreachSetup, config_class):
        assert any(isinstance(c, config_class) for c in bs.configs)

    def test_set_seed(self, bs: BreachSetup):
        assert all(config.profile_config.seed == bs.client_id for config in bs.configs)

    def test_mail_address(self, bs: BreachSetup):
        client_address = "client{id}@localdomain".format(id=bs.client_id)
        assert bs.breach_mailing_config().profile_config.mail_address == client_address

    def test_mailer_servers(self, bs: BreachSetup):
        mc = bs.breach_mailing_config()
        smtp = Server(**mc.mailer_config.smtp_server)
        imap = Server(**mc.mailer_config.imap_server)
        assert (smtp.host, smtp.port) == ("172.17.0.2", 25)
        assert (imap.host, imap.port) == ("172.17.0.2", 993)
        assert (imap.user, imap.password) == (mc.profile_config.mail_address, "breach")

    def test_generate_known_client_addresses(self, bs: BreachSetup):
        known_mail_addresses = bs.breach_mailing_config().profile_config.known_mail_addresses
        for i in range(bs.number_of_clients):
            if i + 1 != bs.client_id:
                assert "client" + str(i + 1) + "@localdomain" in known_mail_addresses
            else:
                assert "client" + str(i + 1) + "@localdomain" not in known_mail_addresses

    def test_generate_external_addresses(self, bs: BreachSetup):
        for i in range(3):
            assert "dummy@extmail" + str(i + 1) in bs.breach_mailing_config().profile_config.known_mail_addresses

    def test_usbing_usb_device_config(self, bs: BreachSetup):
        usb_device_config = bs.breach_usbing_config().usb_device_config
        assert usb_device_config.image_file == "C:\\BREACH\\evil_image_file.img"
        assert usb_device_config.mount_point == "Y:\\"