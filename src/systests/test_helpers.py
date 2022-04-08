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


import time

import pytest

from systests.helpers import try_until_counter_reached

SMALL_DELTA = 0.1
MAX_RUNTIME = 1.0


class TestHelpers():
    def test_try_until_counter_reached_success_on_first_try(self):
        counter = time.perf_counter()
        assert try_until_counter_reached(lambda: 1337, counter + MAX_RUNTIME) == 1337
        assert time.perf_counter() - counter < SMALL_DELTA

    def test_try_until_counter_reached_timeout_because_of_failed_assertion(self):
        counter = time.perf_counter()
        with pytest.raises(TimeoutError):
            try_until_counter_reached(
                lambda: 1338,
                counter + MAX_RUNTIME,
                assertion_func=lambda f: f == 1337,
                sleep_time=1.0)
        assert time.perf_counter() - counter >= MAX_RUNTIME

    def test_try_until_counter_reached_timeout_because_of_exception(self):
        counter = time.perf_counter()
        with pytest.raises(TimeoutError):
            try_until_counter_reached(
                lambda: 1 / 0,
                counter + MAX_RUNTIME,
                exception=ZeroDivisionError,
                sleep_time=1.0)
        assert time.perf_counter() - counter >= MAX_RUNTIME

    def test_try_until_counter_reached_except_multiple_exceptions(self):
        counter = time.perf_counter()
        with pytest.raises(TimeoutError):
            try_until_counter_reached(
                lambda: 1 / 0,
                counter + MAX_RUNTIME,
                exception=(ValueError, ZeroDivisionError),
                sleep_time=1.0)
        assert time.perf_counter() - counter >= MAX_RUNTIME

    def test_try_until_counter_reached_unhandled_exception(self):
        counter = time.perf_counter()
        with pytest.raises(ZeroDivisionError):
            try_until_counter_reached(
                lambda: 1 / 0,
                counter + MAX_RUNTIME,
                exception=ValueError)
        assert time.perf_counter() - counter < SMALL_DELTA

    def test_try_until_counter_reached_no_execution(self):
        counter = time.perf_counter()
        with pytest.raises(TimeoutError):
            try_until_counter_reached(lambda: 1337, counter, at_least_once=False)
        assert time.perf_counter() - counter < SMALL_DELTA
