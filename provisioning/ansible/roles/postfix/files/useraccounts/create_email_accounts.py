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


import re
import subprocess


def main():
    print("INSERT INTO domains (id, domain) VALUES "
            "('{}', '{}');".format(1, "localdomain"))
    print("INSERT INTO aliases (id, source, destination) VALUES "
            "('{}', '{}', '{}');".format(1, "test-alias@localdomain", "test@localdomain"))
    for i in range(1, 101):
        print((create_statement_for_one_user(i)))


def get_sha512crypt_hash(password):
    command = "doveadm pw -s SHA512-CRYPT -p " + password
    output = subprocess.getoutput(command)
    if output.startswith("{SHA512-CRYPT}"):
        output = output[len("{SHA512-CRYPT}"):]
    return output


def is_sha512crypt_hash_valid(hash):
    # SHA512-CRYPT format is "$6$<salt>$<hash>",
    # with <salt> and <hash> being base64 encoded.
    base64_chars = "[A-Za-z0-9\./]"
    regex = re.compile("^\$6\$" + base64_chars + "+\$" + base64_chars + "+$")
    return regex.match(hash)


def create_insert_statement(username, domain, password):
    return ("INSERT INTO users (username, domain, password) VALUES "
            "('{}', '{}', '{}');".format(username, domain, password))


def create_fields_for_one_user(id):
    username = "client" + str(id)
    domain = "localdomain"
    password = get_sha512crypt_hash("breach")
    return [username, domain, password]


def create_statement_for_one_user(id):
    [username, domain, password] = create_fields_for_one_user(id)
    return create_insert_statement(username, domain, password)


if __name__ == "__main__":
    main()
