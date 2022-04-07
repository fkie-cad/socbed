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


def try_until_counter_reached(
        func, counter, sleep_time=5, at_least_once=True,
        exception=Exception, assertion_func=lambda x: True):
    first_time = True
    ret = None
    success = False
    while (first_time and at_least_once) or (time.perf_counter() < counter):
        if not first_time:
            time.sleep(sleep_time)
        try:
            ret = func()
            assert assertion_func(ret)
            success = True
        except AssertionError:
            print("AssertionError in try_until_counter_reached")
        except exception as e:
            print("Exception in try_until_counter_reached: " + str(e))
        else:
            break
        first_time = False
    if not success:
        raise TimeoutError
    return ret
