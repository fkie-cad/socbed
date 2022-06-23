from typing import Union


class Colors:
    lblue: str = "\x1b[94m"
    lgreen: str = "\x1b[92m"
    lred: str = "\x1b[91m"
    lyellow: str = "\x1b[93m"
    endc: str = "\x1b[0m"
    bold: str = "\x1b[1m"


def print_command(command: str) -> None:
    print(
        f"{Colors.bold}{Colors.lgreen}Running => "
        f"{Colors.endc}{Colors.lblue}{command}{Colors.endc}\n"
    )
