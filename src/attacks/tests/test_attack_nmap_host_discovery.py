from attacks.attack_nmap_host_discovery import (
    NmapHostDiscoveryAttack,
    NmapHostDiscoveryAttackOptions,
)
from attacks.tests.test_ssh_client_stub import SSHClientStub


def test_nmap_portscan_attack_options_defaults():
    options = NmapHostDiscoveryAttackOptions()

    assert options.target == "192.168.56.1/23"


def test_nmap_portscan_attack_with_defaults():
    ssh_client = SSHClientStub()
    attack = NmapHostDiscoveryAttack(ssh_client=ssh_client)

    attack.run()

    assert ssh_client.exec_command == "nmap -T5 -n -sn 192.168.56.1/23"
    assert attack.options.target == "192.168.56.1/23"


def test_nmap_portscan_attack_with_custom_options():
    ssh_client = SSHClientStub()
    options = NmapHostDiscoveryAttackOptions(target="192.168.30.11")
    attack = NmapHostDiscoveryAttack(options, ssh_client=ssh_client)

    attack.run()

    assert ssh_client.exec_command == "nmap -T5 -n -sn 192.168.30.11"
