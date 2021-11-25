#!/usr/bin/env python3

# Copyright 2016-2021 Fraunhofer FKIE
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


import argparse
import os
from ftplib import FTP

parser = argparse.ArgumentParser(
    description="Upload a file to the Client's C:\BREACH directory via FTP. "
                "No subdirectories will be created.")
parser.add_argument("filename", type=str, help="File to upload")
parser.add_argument(
    "-b", "--binary", help="Use binary transfer mode (default is ASCII transfer mode)",
    action="store_true")
args = parser.parse_args()

basename = os.path.basename(args.filename)
assert basename != ""

ftp = FTP("192.168.56.254")
ftp.login("breach", "breach")
with open(args.filename, "rb") as f:
    cmd = "STOR BREACH/" + basename
    if args.binary:
        ftp.storbinary(cmd, f)
    else:
        ftp.storlines(cmd, f)
ftp.quit()
