import pytest

from attacks.util import print_error, print_warning, str_to_bool, print_command


def test_print_command(capfd):
    print_command("echo 123")
    out, err = capfd.readouterr()
    assert out == "\x1b[1m\x1b[92mRunning => \x1b[0m\x1b[94mecho 123\x1b[0m\n\n"
    assert not err
    

def test_print_error(capfd):
    print_error("MSG")
    out, err = capfd.readouterr()
    assert out == "\x1b[91mError: MSG\x1b[0m\n"
    assert not err


def test_print_warning(capfd):
    print_warning("MSG")
    out, err = capfd.readouterr()
    assert out == "\x1b[93mWarning: MSG\x1b[0m\n"
    assert not err


@pytest.mark.parametrize("val_in", ("y", "yes", "t", "true", "on", "1"))
def test_str_to_bool_true(val_in):
    assert str_to_bool(val_in) is True


@pytest.mark.parametrize("val_in", ("n", "no", "f", "false", "off", "0"))
def test_str_to_bool_false(val_in):
    assert not str_to_bool(val_in)


def test_str_to_bool_default(capfd):
    assert not str_to_bool("NOT_VALID")
    assert str_to_bool("NOT_VALID", default=True) is True

    out, err = capfd.readouterr()
    out = out.split("\n")
    assert out[0] == "\x1b[91mError: No valid Boolean value: not_valid\x1b[0m"
    assert out[1] == "\x1b[93mWarning: Default to: False\x1b[0m"
    assert out[2] == "\x1b[91mError: No valid Boolean value: not_valid\x1b[0m"
    assert out[3] == "\x1b[93mWarning: Default to: True\x1b[0m"
    assert not err
