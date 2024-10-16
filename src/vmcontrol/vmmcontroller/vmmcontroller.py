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


import logging

logger = logging.getLogger(__name__)


class VMMController:
    def get_vms(self):
        raise NotImplementedError()

    def start(self, vm):
        raise NotImplementedError()

    def poweroff(self, vm):
        raise NotImplementedError()

    def delete(self, vm):
        raise NotImplementedError()

    def is_running(self, vm):
        raise NotImplementedError()

    def get_macs(self, vm):
        raise NotImplementedError()

    def get_mac(self, vm, if_id=1):
        raise NotImplementedError()

    def set_mac(self, vm, mac, if_id=1):
        raise NotImplementedError()

    def get_snapshots(self, vm):
        raise NotImplementedError()

    def create_snapshot(self, vm, snapshot):
        raise NotImplementedError()

    def delete_snapshot(self, vm, snapshot):
        raise NotImplementedError()

    def restore_snapshot(self, vm, snapshot):
        raise NotImplementedError()

    def clone(self, vm, snapshot, clone):
        raise NotImplementedError()

    def set_credentials(self, vm, user, password, domain):
        raise NotImplementedError()

    def set_vrde_port(self, vm, port):
        raise NotImplementedError()


class VMMControllerException(Exception):
    pass


class LoggingVMMController(VMMController):
    def start(self, vm):
        logger.debug('Starting "{vm}"'.format(vm=vm))
        super().start(vm)

    def poweroff(self, vm):
        logger.debug('Turning off "{vm}"'.format(vm=vm))
        super().poweroff(vm)

    def delete(self, vm):
        logger.debug('Deleting "{vm}"'.format(vm=vm))
        super().delete(vm)

    def set_mac(self, vm, mac, if_id=1):
        mac_string = hex(mac)[2:].rjust(12, "0")
        logger.debug(
            'Setting MAC address of "{vm}" interface {if_id} to {mac}'.format(vm=vm, if_id=if_id, mac=mac_string)
        )
        super().set_mac(vm, mac, if_id=if_id)

    def create_snapshot(self, vm, snapshot):
        logger.debug('Creating snapshot "{snapshot}" for "{vm}"'.format(vm=vm, snapshot=snapshot))
        super().create_snapshot(vm, snapshot)

    def delete_snapshot(self, vm, snapshot):
        logger.debug('Deleting snapshot "{snapshot}" of "{vm}"'.format(vm=vm, snapshot=snapshot))
        super().delete_snapshot(vm, snapshot)

    def restore_snapshot(self, vm, snapshot):
        logger.debug('Restoring snapshot "{snapshot}" of "{vm}"'.format(vm=vm, snapshot=snapshot))
        super().restore_snapshot(vm, snapshot)

    def clone(self, vm, snapshot, clone):
        logger.debug(
            'Cloning "{vm}" with snapshot "{snapshot}" to "{clone}"'.format(vm=vm, snapshot=snapshot, clone=clone)
        )
        super().clone(vm, snapshot, clone)

    def set_credentials(self, vm, user, password, domain):
        logger.debug('Setting credentials of "{vm}" to {cred}'.format(vm=vm, cred=(user, password, domain)))
        super().set_credentials(vm, user, password, domain)
