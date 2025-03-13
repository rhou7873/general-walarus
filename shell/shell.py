from globals import servers, vc_connections, elections, live_wse_sessions
import os


class _Command:
    """ A class that represents a Walarus Shell command """

    def __init__(self, name: str, description: str, fn) -> None:
        self.name = name
        self.description = description
        self.run = fn


def show_globals() -> None:
    print(f"servers:")
    for server in servers.values():
        print(f"\t{str(server)}")
    print(f"vc_connections:")
    for guild, conn in vc_connections.items():
        print(
            f"\tConnected to '{conn.voice_client.channel}' in '{guild.name}'")
    print(f"elections:")
    for guild in elections.keys():
        print(f"\tActive election in '{guild.name}'")
    print(f"live_wse_sessions:")
    for guild in live_wse_sessions.values():
        print(f"\t{str(guild)}")


def exit_walarus() -> None:
    try:
        os._exit(0)
    except Exception as ex:
        print(str(ex))


def help() -> None:
    for value in cmd_map.values():
        print(f"\t'{value.name}' --> {value.description}")


cmd_map: dict = {
    "exit": _Command("exit", "Close shell and terminate General Walarus", exit_walarus),
    "globals": _Command("globals", "Display current value of global variables", show_globals),
    "help": _Command("help", "List out all the Walarus Shell commands", help),
}


def run_walarus_shell():
    while True:
        command: str = input("8==D ")
        try:
            if cmd_map.get(command) is not None:
                cmd_map[command].run()
            else:
                print("Invalid command")
        except Exception as ex:
            print(str(ex))
