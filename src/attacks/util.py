# Copyright 2016-2022 Fraunhofer FKIE
#
# This file is part of SOCBED.
#
# SOCBED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SOCBED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SOCBED. If not, see <http://www.gnu.org/licenses/>.


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
