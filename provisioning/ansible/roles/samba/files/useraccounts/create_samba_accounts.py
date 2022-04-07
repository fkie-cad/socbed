#!/usr/bin/env python3

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


"""Outputs commands to create 100 samba users"""


def main():
    print("#!/usr/bin/env bash")
    for i in range(1, 101):
        username = "client" + str(i)
        print(("samba-tool user add " + username + " breach"))
        print(("samba-tool user setexpiry " + username + " --noexpiry"))


if __name__ == "__main__":
    main()
