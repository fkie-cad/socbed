from attacks.util import print_command


def test_print_command(capfd):
    print_command("echo 123")
    out, err = capfd.readouterr()
    assert out == "\x1b[1m\x1b[92mRunning => \x1b[0m\x1b[94mecho 123\x1b[0m\n\n"
    assert not err
