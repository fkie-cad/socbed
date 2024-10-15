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


import json
import os
import socket
import ssl

import time

from vmcontrol.vmmcontroller.vmmcontroller import VMMController, VMMControllerException, LoggingVMMController

import logging

logger = logging.getLogger(__name__)


class RemoteVMMController(VMMController):
    def __init__(self, local_host="", port=0):
        address = (local_host, port)
        self.messenger = Messenger(local_address=address)
        self.messenger.listen()
        self.local_address = self.messenger.listening_socket.getsockname()
        logger.info("RemoteVMMController listening at {add}".format(add=self.local_address))

    def __del__(self):
        self.messenger.close()

    def _remote_call(self, vmc_cmd, kwargs):
        call_d = self._wrap_cmd_dict(vmc_cmd, kwargs)
        self.messenger.send(call_d)
        received_d = self.messenger.receive()
        if received_d:
            if received_d["type"] == "return":
                return received_d["value"]
            elif received_d["type"] == "exception":
                raise VMMControllerException(received_d["value"])
            else:
                raise VMMControllerException("Unknown Received Message Type: {type}".format(type=received_d["type"]))
        else:
            raise VMMControllerException("Connection to Daemon lost")

    @staticmethod
    def _wrap_cmd_dict(vmc_cmd, kwargs):
        return {"type": "vmc_cmd", "vmc_cmd": vmc_cmd, "kwargs": kwargs}

    def clone(self, vm, snapshot, clone):
        kwargs = {"vm": vm, "snapshot": snapshot, "clone": clone}
        ret = self._remote_call("clone", kwargs)
        return ret

    def delete(self, vm):
        kwargs = {"vm": vm}
        ret = self._remote_call("delete", kwargs)
        return ret

    def get_vms(self):
        kwargs = {}
        ret = self._remote_call("get_vms", kwargs)
        return ret

    def get_mac(self, vm, if_id=1):
        kwargs = {"vm": vm, "if_id": if_id}
        ret = self._remote_call("get_mac", kwargs)
        return ret

    def set_mac(self, vm, mac, if_id=1):
        kwargs = {"vm": vm, "mac": mac, "if_id": if_id}
        ret = self._remote_call("set_mac", kwargs)
        return ret

    def get_macs(self, vm):
        kwargs = {"vm": vm}
        ret = self._remote_call("get_macs", kwargs)
        return ret

    def restore_snapshot(self, vm, snapshot):
        kwargs = {"vm": vm, "snapshot": snapshot}
        ret = self._remote_call("restore_snapshot", kwargs)
        return ret

    def is_running(self, vm):
        kwargs = {"vm": vm}
        ret = self._remote_call("is_running", kwargs)
        return ret

    def poweroff(self, vm):
        kwargs = {"vm": vm}
        ret = self._remote_call("poweroff", kwargs)
        return ret

    def start(self, vm):
        kwargs = {"vm": vm}
        ret = self._remote_call("start", kwargs)
        return ret

    def create_snapshot(self, vm, snapshot):
        kwargs = {"vm": vm, "snapshot": snapshot}
        ret = self._remote_call("create_snapshot", kwargs)
        return ret

    def set_credentials(self, vm, user, password, domain):
        kwargs = {"vm": vm, "user": user, "password": password, "domain": domain}
        ret = self._remote_call("set_credentials", kwargs)
        return ret

    def delete_snapshot(self, vm, snapshot):
        kwargs = {"vm": vm, "snapshot": snapshot}
        ret = self._remote_call("delete_snapshot", kwargs)
        return ret

    def get_snapshots(self, vm):
        kwargs = {"vm": vm}
        ret = self._remote_call("get_snapshots", kwargs)
        return ret


class LoggingRemoteVMMController(LoggingVMMController, RemoteVMMController):
    pass


class VMMControlDaemon:
    def __init__(self, remote_address, vm_controller):
        self.messenger = Messenger(remote_address=remote_address)
        self.vmc = vm_controller

    def run(self):
        logger.debug("Run VMMControlDaemon")
        self.messenger.connect()
        self._loop_requests()

    def _loop_requests(self):
        logger.debug("Looping trough requests")
        while True:
            try:
                call_d = self.messenger.receive()
            except ConnectionError as e:
                logger.debug(e)
                break
            else:
                if call_d is None:
                    logger.debug("End of connection...")
                    break
                else:
                    self._handle_request(call_d)

    def _handle_request(self, call_d):
        logger.debug("Handle request {call_d}".format(call_d=call_d))
        vmc_method = getattr(self.vmc, call_d["vmc_cmd"])
        try:
            return_value = vmc_method(**call_d["kwargs"])
        except VMMControllerException as e:
            error_d = self._wrap_exception_dict(e)
            self.messenger.send(error_d)
        else:
            return_d = self._wrap_return_dict(return_value)
            self.messenger.send(return_d)

    @staticmethod
    def _wrap_return_dict(return_value):
        return {"type": "return", "value": return_value}

    @staticmethod
    def _wrap_exception_dict(exception):
        return {"type": "exception", "value": str(exception)}


class Messenger:
    def __init__(self, local_address=None, remote_address=None):
        self.local_address = local_address
        self.remote_address = remote_address
        self.listening_socket = None
        self.data_socket = None
        self.cert_dir = "/tmp/certs"

    def __del__(self):
        self.close()

    def close(self):
        self._close_listening_socket()
        self._close_data_socket()

    def listen(self):
        self._open_listening_socket()

    def connect(self):
        self._connect_to_remote_socket()

    def _connect_to_remote_socket(self):
        while not self.data_socket:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.load_verify_locations(os.path.join(self.cert_dir, "cert.pem"))
            self.data_socket = context.wrap_socket(
                socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                server_hostname=self.remote_address[0],
            )
            try:
                logger.debug("Try to connect to {add}".format(add=self.remote_address))
                self.data_socket.connect(self.remote_address)
            except ConnectionError as e:
                self.data_socket = None
                logger.debug(str(e))
                time.sleep(1)

    def _open_listening_socket(self):
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_socket.bind(self.local_address)
        self.listening_socket.listen(5)

    def _close_listening_socket(self):
        if self.listening_socket:
            self.listening_socket.close()

    def _wait_for_data_socket(self):
        new_sock, _ = self.listening_socket.accept()
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(
            certfile=os.path.join(self.cert_dir, "cert.pem"),
            keyfile=os.path.join(self.cert_dir, "cert.key"),
        )
        self.data_socket = context.wrap_socket(new_sock, server_side=True)

    def _close_data_socket(self):
        if self.data_socket:
            self.data_socket.close()

    def send(self, data):
        packed_data = self._pack(data)
        if self.data_socket:
            self.data_socket.sendall(packed_data)
        elif self.listening_socket:
            self._wait_for_data_socket()
            self.data_socket.sendall(packed_data)
        else:
            raise ConnectionError("No data socket to send....")

    def receive(self):
        if self.data_socket:
            received = self.data_socket.recv(1024)
            if len(received) != 0:
                return self._unpack(received)
            else:
                self.data_socket = None
                return None  # Or Exception??
        elif self.listening_socket:
            self._wait_for_data_socket()
            return self.receive()
        else:
            raise ConnectionError("No data socket to receive....")

    def _pack(self, data):
        return bytes(json.dumps(data), "utf-8")

    def _unpack(self, packed_data):
        return json.loads(str(packed_data, encoding="utf-8"))
