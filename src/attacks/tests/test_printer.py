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


import os

from attacks.printer import Printer, ConsolePrinter, FilePrinter, ListPrinter, MultiPrinter


class TestPrinter:
    def test_print(self):
        Printer().print(msg="Hello World")


class TestConsolePrinter:
    def test_print(self, capsys):
        msg = "Hello World"
        ConsolePrinter().print(msg=msg)
        out, err = capsys.readouterr()
        assert out == msg


class TestFilePrinter:
    def test_print(self, tmpdir):
        msg = "Hello World"
        file = os.path.join(str(tmpdir), "print_file")
        FilePrinter(file=file).print(msg=msg)
        with open(file) as f:
            content = f.read()
        assert content == msg + "\n"

    def test_print_multiple_lines(self, tmpdir):
        msgs = ["Hello World {}".format(i) for i in range(5)]
        file = os.path.join(str(tmpdir), "print_file")
        fp = FilePrinter(file=file)
        for msg in msgs:
            fp.print(msg=msg)
        with open(file) as f:
            content = f.read()
        assert content == "\n".join(msgs) + "\n"

    def test_multiple_file_printers_same_file(self, tmpdir):
        msg = "Hello World"
        file = os.path.join(str(tmpdir), "print_file")
        FilePrinter(file=file).print(msg=msg)
        FilePrinter(file=file).print(msg=msg)
        with open(file) as f:
            content = f.read()
        assert content == 2 * (msg + "\n")


class TestListPrinter:
    def test_print(self):
        msg = "Hello World"
        lp = ListPrinter()
        lp.print(msg=msg)
        assert [msg] == lp.printed

    def test_print_multiple_lines(self):
        msgs = ["Hello World {}".format(i) for i in range(5)]
        lp = ListPrinter()
        for msg in msgs:
            lp.print(msg=msg)
        assert msgs == lp.printed


class TestMultiPrinter:
    def test_print(self):
        msg = "Hello World"
        p1 = ListPrinter()
        p2 = ListPrinter()
        p = MultiPrinter(printers=[p1, p2])
        p.print(msg=msg)
        assert p1.printed == [msg]
        assert p2.printed == [msg]
