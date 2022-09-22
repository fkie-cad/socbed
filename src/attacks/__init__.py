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


import inspect
import os
from importlib import import_module

from attacks.attack import Attack, AttackInfo, AttackOptions, AttackException

module_dir = os.path.dirname(os.path.abspath(__file__))
package = __name__

attack_module_names = [
    file.split(".py")[0] for file in os.listdir(module_dir)
    if file.startswith("attack_") and file.endswith(".py")]

attack_modules = [import_module("." + str(attack_module_name), package=package)
                  for attack_module_name in attack_module_names]

attack_subclasses = set()
for attack_module in attack_modules:
    attack_subclasses.update(
        inspect.getmembers(attack_module, lambda obj: inspect.isclass(obj) and issubclass(obj, Attack)))

implemented_attacks = [attack_class for attack_name, attack_class in attack_subclasses if attack_class is not Attack]
