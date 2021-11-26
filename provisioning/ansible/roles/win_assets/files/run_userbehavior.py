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


"""
This script starts the userbehavior.
"""

import datetime
import logging
import os
import re
import time
from subprocess import PIPE, run, CalledProcessError

logger = logging.getLogger(__name__)


class ISOFormatter(logging.Formatter):
    _tz_fix = re.compile(r"([+-]\d{2})(\d{2})$")

    def format(self, record):
        self._add_isotime_to_record(record)
        return super().format(record)

    @classmethod
    def _add_isotime_to_record(cls, record):
        isotime = datetime.datetime.fromtimestamp(record.created).isoformat()
        tz = cls._tz_fix.match(time.strftime("%z"))
        if time.timezone and tz:
            offset_hrs, offset_min = tz.groups()
            isotime += "{0}:{1}".format(offset_hrs, offset_min)
        else:
            isotime += "Z"
        record.__dict__["isotime"] = isotime


def setup_logging():
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename="init_tbf_client.log")
    fmt = "%(isotime)s %(name)s %(levelname)s %(message)s"
    handler.setFormatter(fmt=ISOFormatter(fmt=fmt))
    logger.addHandler(hdlr=handler)


class Main:
    client_dir = "C:\\BREACH"
    userbehavior_pex_file = "userbehavior.pex"

    def run(self, argv=None):
        logger.info("Initalization script for client started!")
        self.run_userbehavior()

    def run_userbehavior(self):
        pex_path = os.path.join(self.client_dir, self.userbehavior_pex_file)
        call_vector = ["python", pex_path, "--use-breach-setup"]
        logger.info("Running userbehavior at " + str(pex_path))
        self.execute_userbehavior(call_vector)

    @staticmethod
    def execute_userbehavior(call_vector):
        return run(call_vector)
    

if __name__ == '__main__':
    setup_logging()
    Main().run()
