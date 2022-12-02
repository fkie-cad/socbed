from attacks import Attack, AttackInfo
from attacks.nmap_attack_options import NmapAttackOptions as AttackOptions
from attacks.nmap_attack_options import get_speed


class NmapPortscanAttackOptions(AttackOptions):
    target: str = "Target IP or range"
    scan_type: str = "Scan Type"
    ports: str = "Ports to scan, set to 'ics' to scan a list of ICS-specific ports"

    def _set_defaults(self) -> None:
        self.target = "192.168.56.101"
        self.scan_type = "-sT -sU"
        self.ports = "top10"


class NmapPortscanAttack(Attack):
    info = AttackInfo(
        name="misc_nmap_portscan",
        description="Scan for open ports",
    )
    options_class = NmapPortscanAttackOptions
    ics_ports: str = (
        "U:47808,20000,34980,2222,44818,55000-55003,1089-1091,34962-34964,4000,161,"
        + "T:20000,44818,1089-1091,102,502,4840,80,443,34962-34964,4000,2404"
    )

    def run(self) -> None:
        port = self._set_port()

        command: str = (
            f"sudo nmap -T{get_speed(self.options)} -n {self.options.scan_type} "
            f"{self.options.target}{port}"
        )
        self.exec_command_on_target(command)

    def _set_port(self) -> str:
        if self.options.ports == "ics":
            return f" -p {self.ics_ports}"

        if self.options.ports.startswith("top"):
            return f" --top-ports {self.options.ports.strip('top')}"

        return f" -p {self.options.ports}"
