from attacks.attack_nmap_portscan import NmapPortscanAttack, NmapPortscanAttackOptions
from attacks.tests.test_ssh_client_stub import SSHClientStub

DEFAULT_IP = "192.168.56.101"


def test_nmap_portscan_attack_options_defaults():
    options = NmapPortscanAttackOptions()

    assert options.target == DEFAULT_IP
    assert options.scan_type == "-sT -sU"
    assert options.ports == "top10"


def test_nmap_portscan_attack_with_defaults(capfd):
    ssh_client = SSHClientStub()
    attack = NmapPortscanAttack(ssh_client=ssh_client)

    attack.run()
    out, err = capfd.readouterr()

    assert ssh_client.exec_command == f"sudo nmap -T5 -n -sT -sU {DEFAULT_IP} --top-ports 10"
    assert attack.options.target == DEFAULT_IP

    assert (
        out.rstrip()
        == f"\x1b[1m\x1b[92mRunning => \x1b[0m\x1b[94msudo nmap -T5 -n -sT -sU {DEFAULT_IP} "
        "--top-ports 10\x1b[0m"
    )
    assert not err.rstrip()


def test_nmap_portscan_attack_with_custom_options(capfd):
    ssh_client = SSHClientStub()
    options = NmapPortscanAttackOptions(
        target="192.168.30.12", scan_type="-sU", ports="2404,22,80", speed="MEDIUM"
    )
    attack = NmapPortscanAttack(options, ssh_client=ssh_client)

    attack.run()
    out, err = capfd.readouterr()

    assert ssh_client.exec_command == "sudo nmap -T3 -n -sU 192.168.30.12 -p 2404,22,80"

    assert (
        out.rstrip() == "\x1b[1m\x1b[92mRunning => \x1b[0m\x1b[94msudo nmap -T3 -n -sU "
        "192.168.30.12 -p 2404,22,80\x1b[0m"
    )
    assert not err.rstrip()


def test_nmap_portscan_attack_with_custom_options_ics(capfd):
    ssh_client = SSHClientStub()
    options = NmapPortscanAttackOptions(target="192.168.30.12", scan_type="-sU -sT", ports="ics")
    attack = NmapPortscanAttack(options, ssh_client=ssh_client)

    attack.run()
    out, err = capfd.readouterr()

    assert (
        ssh_client.exec_command == "sudo nmap -T5 -n -sU -sT 192.168.30.12 -p "
        "U:47808,20000,34980,2222,44818,55000-55003,1089-1091,34962-34964,4000,161,"
        "T:20000,44818,1089-1091,102,502,4840,80,443,34962-34964,4000,2404"
    )

    assert (
        out.rstrip()
        == "\x1b[1m\x1b[92mRunning => \x1b[0m\x1b[94msudo nmap -T5 -n -sU -sT 192.168.30.12 -p "
        "U:47808,20000,34980,2222,44818,55000-55003,1089-1091,34962-34964,4000,161,"
        "T:20000,44818,1089-1091,102,502,4840,80,443,34962-34964,4000,2404\x1b[0m"
    )
    assert not err.rstrip()
