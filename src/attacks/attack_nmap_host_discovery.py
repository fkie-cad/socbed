from attacks import Attack, AttackInfo
from attacks.nmap_attack_options import NmapAttackOptions as AttackOptions
from attacks.nmap_attack_options import get_speed


class NmapHostDiscoveryAttackOptions(AttackOptions):
    target: str = "Target range or IP"

    def _set_defaults(self) -> None:
        self.target = "192.168.56.1/23"


class NmapHostDiscoveryAttack(Attack):
    info: AttackInfo = AttackInfo(
        name="misc_nmap_host_discovery",
        description="Scan the network for available hosts",
    )
    options_class = NmapHostDiscoveryAttackOptions

    def run(self) -> None:
        command: str = f"nmap -T{get_speed(self.options)} -n -sn {self.options.target}"
        self.exec_command_on_target(command)
