import pytest

from attacks.nmap_attack_options import get_speed


class StubOptions:
    speed = "FAST"


@pytest.mark.parametrize(
    "option, expected",
    (
        ("SLOW", 1),
        ("MEDIUM", 3),
        ("FAST", 5),
        ("slOw", 1),
        ("fAsT", 5),
        ("medium", 3),
    ),
)
def test_get_speed(option, expected):
    options = StubOptions
    options.speed = option
    assert get_speed(options) == expected


def test_get_speed_fail(capfd):
    options = StubOptions
    options.speed = "NOT_VALID"
    assert get_speed(options) == 5

    out, err = capfd.readouterr()
    assert not err
    assert out.split("\n")[0] == "\x1b[91mError: Invalid option: NOT_VALID\x1b[0m"
    assert out.split("\n")[1] == "\x1b[93mWarning: Default to: fast\x1b[0m"
