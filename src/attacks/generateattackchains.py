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
from collections import OrderedDict
from random import Random

from attacks import implemented_attacks

attack_classes = {
    attack.info.name: attack for attack in implemented_attacks
}


def name_to_obj(attack_name):
    return attack_classes[attack_name]()


class AttackGraph:
    attack_dict = OrderedDict([
        ("infect_email_exe", ["c2_hashdump", "c2_change_wallpaper", "c2_download_malware"]),
        ("infect_flashdrive_exe", ["c2_hashdump", "c2_change_wallpaper", "c2_download_malware"]),
        ("misc_download_malware", ["misc_execute_malware"]),
        ("misc_execute_malware", ["misc_set_autostart"]),
        ("c2_hashdump", ["c2_exfiltration"]),
        ("c2_change_wallpaper", ["c2_take_screenshot"]),
        ("c2_download_malware", ["misc_set_autostart"]),
        ("c2_exfiltration", ["disinfect_client"]),
        ("c2_take_screenshot", ["disinfect_client"]),
        ("misc_set_autostart", ["disinfect_client"])])
    start_attacks = [
        "infect_email_exe",
        "infect_flashdrive_exe",
        "misc_download_malware",
        "misc_exfiltration",
        "misc_sqlmap"]
    end_attacks = [
        "disinfect_client",
        "misc_exfiltration",
        "misc_sqlmap"]

    def successors(self, attack):
        return list(self.attack_dict[attack])

    @property
    def attacks(self):
        return list(set(self.attack_dict.keys()).union(self.end_attacks))


class AttackBlockGenerator:
    def generate(self, attack):
        block = list()
        block.append("use " + attack.info.name)
        # ToDo: implement set options
        block.append("run")
        block.append("back")
        return block


class AttackChainGenerator:
    attack_graph = AttackGraph()

    def __init__(self, rand_gen):
        self.rand_gen = rand_gen

    def generate(self):
        attack_chain = []
        start_attack = self.rand_gen.choice(self.attack_graph.start_attacks)
        attack_chain.append(start_attack)
        current_attack = start_attack
        while current_attack not in self.attack_graph.end_attacks:
            successor = self.rand_gen.choice(self.attack_graph.successors(current_attack))
            attack_chain.append(successor)
            current_attack = successor
        return attack_chain

    def generate_sequence(self, number_of_chains):
        attack_chain_sequence = []
        for i in range(number_of_chains):
            attack_chain = self.generate()
            attack_chain_sequence.append(attack_chain)
        return attack_chain_sequence


def main(argv=None):
    args = parse_args(argv=argv)
    rand_gen = Random()
    rand_gen.seed(args.seed)
    attack_chain_generator = AttackChainGenerator(rand_gen=rand_gen)
    attack_chain_sequence = attack_chain_generator.generate_sequence(args.number_of_chains)
    attack_script = []
    for attack_chain in attack_chain_sequence:
        for attack in attack_chain:
            attack_block_generator = AttackBlockGenerator()
            attack_script.extend(attack_block_generator.generate(name_to_obj(attack)))
            attack_script.append(
                "sleep " + str(rand_gen.randint(args.delay_between_attacks[0], args.delay_between_attacks[1])))
        attack_script.append(
            "sleep " + str(rand_gen.randint(args.delay_between_chains[0], args.delay_between_chains[1])))
    attack_script.append("exit")
    for command in attack_script:
        print(command)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--number-of-chains", dest="number_of_chains", required=True,
                        type=int, help="number of total attack chains runs", metavar="NUM")
    parser.add_argument("-d", "--delay-between-attacks", dest="delay_between_attacks", required=False, nargs=2,
                        type=int, default=[2, 5], help="random delay between [MIN] and [MAX] seconds",
                        metavar=("MIN", "MAX"))
    parser.add_argument("-D", "--delay-between-chains", dest="delay_between_chains", required=False, nargs=2,
                        type=int, default=[4, 10], help="random delay between [MIN] and [MAX] seconds",
                        metavar=("MIN", "MAX"))
    parser.add_argument("-s", "--seed", required=False,
                        type=int, default=None, help="seed for random number generator as integer value", metavar="NUM")
    args = parser.parse_args(args=argv)
    return args


if __name__ == '__main__':
    main()
