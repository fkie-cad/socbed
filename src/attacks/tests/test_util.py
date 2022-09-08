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


import pytest

import attacks.util as util


def test_print_command(capfd):
    util.print_command("echo 123")
    out, err = capfd.readouterr()
    assert out == "\x1b[1m\x1b[92mRunning => \x1b[0m\x1b[94mecho 123\x1b[0m\n\n"
    assert not err
    

def test_print_error(capfd):
    util.print_error("MSG")
    out, err = capfd.readouterr()
    assert out == "\x1b[91mError: MSG\x1b[0m\n"
    assert not err


def test_print_warning(capfd):
    util.print_warning("MSG")
    out, err = capfd.readouterr()
    assert out == "\x1b[93mWarning: MSG\x1b[0m\n"
    assert not err


@pytest.mark.parametrize("val_in", ("y", "yes", "t", "true", "on", "1"))
def test_str_to_bool_true(val_in):
    assert util.str_to_bool(val_in) is True


@pytest.mark.parametrize("val_in", ("n", "no", "f", "false", "off", "0"))
def test_str_to_bool_false(val_in):
    assert not util.str_to_bool(val_in)


def test_str_to_bool_default(capfd):
    assert not util.str_to_bool("NOT_VALID")
    assert util.str_to_bool("NOT_VALID", default=True) is True

    out, err = capfd.readouterr()
    out = out.split("\n")
    assert out[0] == "\x1b[91mError: No valid Boolean value: not_valid\x1b[0m"
    assert out[1] == "\x1b[93mWarning: Default to: False\x1b[0m"
    assert out[2] == "\x1b[91mError: No valid Boolean value: not_valid\x1b[0m"
    assert out[3] == "\x1b[93mWarning: Default to: True\x1b[0m"
    assert not err
