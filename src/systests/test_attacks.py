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


import time

import pytest

from attacks.attack import AttackException
from attacks.attack_c2_exfiltration import C2ExfiltrationAttack
from attacks.attack_change_wallpaper import ChangeWallpaperAttack
from attacks.attack_download_malware import DownloadMalwareAttack
from attacks.attack_download_malware_meterpreter import DownloadMalwareMeterpreterAttack
from attacks.attack_email_exe import EmailEXEAttack
from attacks.attack_execute_malware import ExecuteMalwareAttack
from attacks.attack_flashdrive_exfiltration import FlashdriveExfiltrationAttack
from attacks.attack_flashdrive_exe import FlashdriveEXEAttack
from attacks.attack_kill_reverse_connection import KillReverseConnectionAttack
from attacks.attack_hashdump import HashdumpAttack
from attacks.attack_mimikatz import MimikatzAttack
from attacks.attack_set_autostart import SetAutostartAttack
from attacks.attack_sqlmap import SQLMapAttack
from attacks.attack_take_screenshot import TakeScreenshotAttack
from attacks.printer import ListPrinter, MultiPrinter
from systests.helpers import try_until_counter_reached
from vmcontrol.sessionhandler import SessionHandler
from vmcontrol.vmmcontroller import VBoxController

MAX_RUNTIME = 10 * 60  # Ten minutes
pytestmark = pytest.mark.systest


@pytest.fixture(scope="module")
def session():
    sh = SessionHandler(VBoxController())
    sh.start_session()
    yield
    sh.close_session()


@pytest.fixture(scope="module")
def timeout_counter():
    return time.perf_counter() + MAX_RUNTIME


@pytest.mark.usefixtures("session")
class TestAttack:
    attacks = [
        # Misc attacks: These attacks are all self-contained, their order does not matter.
        DownloadMalwareAttack(),
        ExecuteMalwareAttack(),
        FlashdriveExfiltrationAttack(),
        SetAutostartAttack(),
        SQLMapAttack(),
        # Meterpreter-based attacks: These attacks either infect a client with a reverse HTTP
        # payload (attack name starts with "infect_") or start a Meterpreter shell on such a
        # connection and run attack-specific commands (attack name starts with "c2_".
        # Without an infection, a c2 attack won't work. To make sure we are not using an old
        # infection, all reverse HTTP payloads are killed via KillReverseConnection first.
        # Then a sequence of an infection attack and a c2 attack is run. As we currently have more
        # c2 than infection attacks, some infection attacks are run more than once.
        # The order within a category (infect or c2) does not matter, we use alphabetical here.
        
        # FlashdriveEXEAttack() currently fails due to Windows being unable to open
        # the inserted "flashdrive" (some kind of format error)
        
        KillReverseConnectionAttack(), EmailEXEAttack(), ChangeWallpaperAttack(),
        KillReverseConnectionAttack(), EmailEXEAttack(), DownloadMalwareMeterpreterAttack(),
        KillReverseConnectionAttack(), EmailEXEAttack(), C2ExfiltrationAttack(),
        KillReverseConnectionAttack(), EmailEXEAttack(), HashdumpAttack(),
        KillReverseConnectionAttack(), EmailEXEAttack(), TakeScreenshotAttack(),
        KillReverseConnectionAttack(), EmailEXEAttack(), MimikatzAttack()
	]

    @pytest.mark.parametrize("attack", attacks, ids=lambda a: type(a).__name__)
    def test_attack(self, attack, timeout_counter):
        lp = ListPrinter()
        attack.printer = MultiPrinter([lp, attack.printer])
        try_until_counter_reached(
            attack.run,
            timeout_counter,
            exception=AttackException)
        print(lp.printed)
