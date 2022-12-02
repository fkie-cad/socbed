from attacks.util import print_command


class SSHClientStub:
    def __init__(self):
        self.exec_command = ""
        self.exec_commands = []
        self.stdin_channel = ""
        self.channel_timeout = ""

    def exec_command_on_target(self, command, _unused_printer):
        print_command(command)
        self.exec_command = command

    def exec_commands_on_target(self, command, _unused_printer):
        print_command(command)
        self.exec_commands.append(command)

    def connect_to_target(self):
        pass
