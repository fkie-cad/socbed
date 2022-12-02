from typing import Dict, List

from attacks import Attack, AttackInfo
from attacks.nmap_attack_options import NmapAttackOptions as AttackOptions
from attacks.nmap_attack_options import get_speed
from attacks.util import print_error, print_warning


class NmapServiceDiscoveryAttackOptions(AttackOptions):
    target: str = "Target IP or range"
    scan_type: str = (
        "Scan Type [(comprehensive), os_detect, snmp_info, snmp, iec104_info, vuln, empty]"
    )
    port: str = "Ports to scan"
    exclude_ports: str = "Ports to exclude from scan"
    script: str = "Nmap script to run"

    def _set_defaults(self) -> None:
        self.target = "192.168.56.101"
        self.port = ""
        self.exclude_ports = ""
        self.script = ""
        self.scan_type = "comprehensive"
        self.scan_type_choices = [
            "comprehensive",
            "os_detect",
            "snmp_info",
            "snmp",
            "iec104_info",
            "vuln",
            "empty",
        ]


class NmapServiceDiscoveryAttack(Attack):
    info = AttackInfo(
        name="misc_nmap_service_discovery",
        description="Scan for exposed services",
    )
    options_class = NmapServiceDiscoveryAttackOptions

    def run(self) -> None:
        command: str = (
            f"sudo nmap -T{get_speed(self.options)} -n{self.get_nmap_args()} "
            f"{self.options.target}"
        )
        self.exec_command_on_target(command)

    @staticmethod
    def format_arg(argument: str, user_value: str, variant_value: str = "") -> str:
        # this creates an ordered set of option values
        # https://stackoverflow.com/questions/1653970/does-python-have-an-ordered-set/53657523#53657523
        ordered_values: List[str] = [
            option for option in dict.fromkeys([variant_value, *user_value.split(",")]) if option
        ]

        if not ordered_values:
            return ""
        return f" {argument} {','.join(ordered_values)}"

    def get_nmap_args(self) -> str:
        variants: Dict = dict(
            SNMP_INFO={"option": "-sU", "port": "161", "script": "snmp-info"},
            SNMP={"option": "-sU -sV -sC", "port": "161"},
            IEC104_INFO={"port": "2404", "script": "iec-identify"},
            OS_DETECT={"option": "-O"},
            COMPREHENSIVE={"option": "-A"},
            VULN={"script": "vuln"},
            EMPTY={},
        )

        try:
            variant_options = variants[self.options.scan_type.upper()]
        except LookupError:
            print_error(f"Invalid option: {self.options.scan_type}")
            print_warning("Default to: empty")
            self.options.scan_type = "empty"
            variant_options = variants[self.options.scan_type.upper()]

        return self._resolve_nmap_args(**variant_options)

    def _resolve_nmap_args(self, option="", port="", script="") -> str:
        resolved_args = f" {option}"
        resolved_args += self.format_arg("-p", self.options.port, port)
        resolved_args += self.format_arg("--exclude-ports", self.options.exclude_ports)
        resolved_args += self.format_arg("--script", self.options.script, script)

        return resolved_args
