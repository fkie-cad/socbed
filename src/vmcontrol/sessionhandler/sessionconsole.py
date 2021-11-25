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


from vmcontrol.sessionhandler.sessionhandler import SessionHandler, SessionHandlerException
from vmcontrol.vmmcontroller import VMMConsole


class SessionConsole(VMMConsole):
    # intro = ""
    prompt = "SessionConsole> "

    def __init__(self, session_handler: SessionHandler):
        super().__init__(session_handler.vmmc)
        self.session_handler = session_handler

    def do_get_info(self, arg):
        print("Current SessionConfig is:")
        config_dict = vars(self.session_handler.config)
        for field, value in config_dict.items():
            print("{field}\n\t{value}".format(field=field, value=value))

    def do_start_session(self, arg):
        try:
            self.session_handler.start_session()
        except SessionHandlerException as e:
            print(e)

    def do_close_session(self, arg):
        try:
            self.session_handler.close_session()
        except SessionHandlerException as e:
            print(e)

    def do_remove_session_state_file(self, arg):
        if self.session_handler.session_state_file is not None:
            self.session_handler.remove_session_state_file()
            print("Session state file deleted. Reload shell to start a new session.")
        else:
            print("No session state file given")
