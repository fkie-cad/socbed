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


from contextlib import redirect_stdout
from io import StringIO
from random import Random
from unittest.mock import Mock

import pytest

from attacks import Attack, AttackInfo
from attacks.generateattackchains import AttackChainGenerator, AttackBlockGenerator, AttackGraph, \
    main


def generate_script(seed=42, number_of_chains=100):
    argv = ["-i", str(number_of_chains), "-s", str(seed)]
    f = StringIO()
    with redirect_stdout(f):
        main(argv=argv)
    out = f.getvalue()
    lines = tuple(line for line in out.split("\n")
                  if not (line.startswith("#") or line == ""))
    return lines


def get_attack_blocks(lines):
    blocks = list()
    for (i, line) in enumerate(lines):
        if not line.split()[0] == "use":
            continue
        j = i + 1
        while not lines[j].split()[0] == "back":
            j += 1
        blocks.append(lines[i:j + 1])
    return blocks


@pytest.fixture(scope="module", params=[42, 43, 44])
def script(request):
    seed = request.param
    return generate_script(seed=seed, number_of_chains=500)


class TestAttackScriptConsistency:
    valid_attacks = AttackGraph().attacks

    def test_attack_script_is_not_empty(self, script):
        assert len(script) > 0

    def test_lines_begin_with_valid_commands(self, script):
        valid_commands = ["run", "use", "back", "sleep", "exit", "set"]
        for line in script:
            assert line.split(" ")[0] in valid_commands

    def test_exit_is_last_command(self, script):
        assert script[-1] == "exit"

    def test_exit_not_in_inner_script(self, script):
        for line in script[:-1]:
            assert not line.split()[0] == "exit"

    def test_only_sleep_between_blocks(self, script):
        in_block = False
        for line in script[:-1]:
            if line.split()[0] == "use":
                in_block = True
                continue
            if line.split()[0] == "back":
                in_block = False
                continue
            if not in_block:
                assert line.split()[0] == "sleep"

    def test_script_contain_sleep_commands(self, script):
        assert any([line.split()[0] == "sleep" for line in script])

    def test_sleep_with_time_arg(self, script):
        for line in script:
            if line.split()[0] == "sleep":
                assert isinstance(int(line.split()[1]), int)

    def test_use_with_valid_attack_arg(self, script):
        for line in script:
            if line.split()[0] == "use":
                assert line.split()[1] in self.valid_attacks


class TestAttackBlockConsistency:
    def test_blocks_contain_only_use_set_run_back(self, script):
        valid_block_commands = ["use", "set", "run", "back"]
        blocks = get_attack_blocks(script)
        for block in blocks:
            for command in block:
                assert command.split()[0] in valid_block_commands

    def test_blocks_start_with_use(self, script):
        blocks = get_attack_blocks(script)
        for block in blocks:
            assert block[0].split()[0] == "use"

    def test_blocks_end_with_back(self, script):
        blocks = get_attack_blocks(script)
        for block in blocks:
            assert block[-1].split()[0] == "back"

    def test_blocks_run_next_to_last(self, script):
        blocks = get_attack_blocks(script)
        for block in blocks:
            assert block[-2].split()[0] == "run"


class TestGraphConsistency:
    start_attacks = AttackGraph.start_attacks
    end_attacks = AttackGraph.end_attacks
    successors = AttackGraph.attack_dict

    def get_attack_type(self, block):
        use_attack = block[0]
        attack_type = use_attack.split()[1]
        return attack_type

    def assert_valid_successor_attack_seq(self, attacks):
        valid_successors = self.start_attacks
        for attack in attacks:
            assert attack in valid_successors
            if attack in self.end_attacks:
                valid_successors = self.start_attacks
            else:
                valid_successors = self.successors[attack]

    def test_graph_consistency(self, script):
        blocks = get_attack_blocks(script)
        attacks = [self.get_attack_type(block) for block in blocks]
        self.assert_valid_successor_attack_seq(attacks)

        # ToDo: write test for valid end node


class TestDeterminism:
    def test_same_script_for_same_seed(self):
        number_of_chains = 100
        assert generate_script(seed=42, number_of_chains=number_of_chains) == generate_script(
            seed=42, number_of_chains=number_of_chains)

    def test_different_script_for_different_seeds(self):
        number_of_chains = 100
        assert generate_script(seed=42, number_of_chains=number_of_chains) != generate_script(
            seed=43, number_of_chains=number_of_chains)


class AttackGraphDummy:
    start_attacks = ["att1"]
    end_attacks = ["att3"]
    attacks = ["att1", "att2", "att3"]

    def successors(self, attack):
        if attack == "att1":
            return ["att2"]
        elif attack == "att2":
            return ["att3"]
        else:
            return []


@pytest.fixture(params=[AttackGraph, AttackGraphDummy])
def acg(request):
    rand = Random()
    rand.seed(0)
    generator = AttackChainGenerator(rand_gen=rand)
    generator.attack_graph = request.param()
    return generator


class TestAttackChainGenerator:
    def test_chain_sequence_contain_right_number_of_chains(self, acg: AttackChainGenerator):
        acg.generate = Mock(return_value="attack_chain")
        res = acg.generate_sequence(50)
        assert len(res) == 50
        assert all([(element == "attack_chain") for element in res])

    def test_chain_start_with_valid_start_attack(self, acg: AttackChainGenerator):
        res = acg.generate()
        assert res[0] in acg.attack_graph.start_attacks

    def test_chain_end_with_valid_end_attack(self, acg: AttackChainGenerator):
        res = acg.generate()
        assert res[-1] in acg.attack_graph.end_attacks

    def test_chain_contain_valid_successor(self, acg: AttackChainGenerator):
        res = acg.generate()
        last_attack = res[0]
        for attack in res[1:]:
            assert attack in acg.attack_graph.successors(last_attack)
            last_attack = attack


class AttackDummy(Attack):
    info = AttackInfo(name="attack_dummy")


class TestAttackBlockGenerator:
    abg = AttackBlockGenerator()
    block = abg.generate(AttackDummy())

    def test_block_start_with_use(self):
        assert self.block[0].split()[0] == "use"

    def test_block_end_with_back(self):
        assert self.block[-1].split()[0] == "back"

    def test_block_run_next_to_last(self):
        assert self.block[-2].split()[0] == "run"
