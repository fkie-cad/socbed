from typing import Union


class Colors:
    lblue: str = "\x1b[94m"
    lgreen: str = "\x1b[92m"
    lred: str = "\x1b[91m"
    lyellow: str = "\x1b[93m"
    endc: str = "\x1b[0m"
    bold: str = "\x1b[1m"


def print_error(msg: str) -> None:
    print(f"{Colors.lred}Error: {msg}{Colors.endc}")


def print_warning(msg: str) -> None:
    print(f"{Colors.lyellow}Warning: {msg}{Colors.endc}")


def str_to_bool(val: Union[str, bool], default: bool = False) -> bool:
    val = str(val).lower()
    if val in {"y", "yes", "t", "true", "on", "1"}:
        return True
    elif val in {"n", "no", "f", "false", "off", "0"}:
        return False

    print_error(f"No valid Boolean value: {val}")
    print_warning(f"Default to: {default}")
    return default
