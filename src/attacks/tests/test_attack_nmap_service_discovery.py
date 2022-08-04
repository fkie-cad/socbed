import pytest

from attacks.attack_nmap_service_discovery import NmapServiceDiscoveryAttack
from attacks.attack_nmap_service_discovery import NmapServiceDiscoveryAttackOptions as Options
from attacks.tests.test_ssh_client_stub import SSHClientStub

DEFAULT_IP = "192.168.56.101"


def test_nmap_service_discovery_format_arg():
    attack = NmapServiceDiscoveryAttack

    assert attack.format_arg("-p", "22,80,22,23,443,443", "161") == " -p 161,22,80,23,443"
    assert attack.format_arg("--exclude-ports", "1337,99") == " --exclude-ports 1337,99"
    assert (
        attack.format_arg("--script", "ssh-auth-methods,vuln") == " --script ssh-auth-methods,vuln"
    )


def test_nmap_service_discovery_options_defaults():
    options = Options()

    assert options.target == DEFAULT_IP
    assert options.scan_type == "comprehensive"
    assert not options.port
    assert not options.script


def test_nmap_service_discovery_with_defaults():
    ssh_client = SSHClientStub()
    attack = NmapServiceDiscoveryAttack(ssh_client=ssh_client)

    attack.run()

    assert ssh_client.exec_command == f"sudo nmap -T5 -n -A {DEFAULT_IP}"


@pytest.mark.parametrize(
    "options, expected",
    (
        (Options(scan_type="comprehensive"), "-A"),
        (Options(scan_type="comprehensive", exclude_ports="161"), "-A --exclude-ports 161"),
        (Options(scan_type="os_detect"), "-O"),
        (Options(scan_type="os_detect", script="user-script"), "-O --script user-script"),
        (Options(scan_type="snmp_info"), "-sU -p 161 --script snmp-info"),
        (Options(scan_type="snmp_info", script="foobar"), "-sU -p 161 --script snmp-info,foobar"),
        (Options(scan_type="snmp"), "-sU -sV -sC -p 161"),
        (Options(scan_type="snmp", port="162,163"), "-sU -sV -sC -p 161,162,163"),
        (Options(scan_type="iec104_info"), "-p 2404 --script iec-identify"),
        (Options(scan_type="iec104_info", port="22,80"), "-p 2404,22,80 --script iec-identify"),
        (Options(scan_type="vuln"), "--script vuln"),
        (Options(scan_type="vuln", script="foobar"), "--script vuln,foobar"),
        (Options(scan_type="empty"), ""),
        (Options(scan_type="empty", port="80,8080"), "-p 80,8080"),
        (Options(scan_type="bogus"), ""),
    ),
)
def test_nmap_service_discovery_with_options(options, expected):
    prefix = "sudo nmap -T5 -n"
    target = options.target
    ssh_client = SSHClientStub()

    attack = NmapServiceDiscoveryAttack(options, ssh_client=ssh_client)
    attack.run()

    assert ssh_client.exec_command.startswith(prefix)
    assert ssh_client.exec_command.endswith(target)

    other_options = ssh_client.exec_command[len(prefix) : -len(target)].strip()
    assert other_options == expected


def test_nmap_service_discovery_invalid_option_output(capfd):
    ssh_client = SSHClientStub()
    options = Options(
        target="192.168.30.12",
        scan_type="NoN_vAlId",
        port="22,443",
        exclude_ports="",
        script="",
        speed="SLOW",
    )
    attack = NmapServiceDiscoveryAttack(options, ssh_client=ssh_client)
    attack.run()

    out = capfd.readouterr()[0].split("\n")
    assert out[0] == "\x1b[91mError: Invalid option: NoN_vAlId\x1b[0m"
    assert out[1] == "\x1b[93mWarning: Default to: empty\x1b[0m"
    assert (
        out[2] == "\x1b[1m\x1b[92mRunning => \x1b[0m\x1b[94msudo nmap -T1 -n  -p 22,443 "
        "192.168.30.12\x1b[0m"
    )
    assert not out[3]
    assert not out[4]

    assert ssh_client.exec_command == "sudo nmap -T1 -n  -p 22,443 192.168.30.12"
