import a2s
import valve.rcon
import socket
import re


def player_tribe_check(address: str, password: str, rcon_port: int):
    rcon_connection = valve.rcon.RCON((address, rcon_port), password, timeout=2, multi_part=False)

    # connect
    try:
        rcon_connection.connect()
    except socket.timeout:
        print("connection timed out")
        return

    # authenticate
    rcon_connection.authenticate(timeout=1)
    if rcon_connection.authenticated is False:
        print("failed to authenticate")
        return

    result = rcon_connection.execute("ListAllPlayerSteamID", block=True, timeout=1)

    return parse_playerlist(result.text)


def parse_playerlist(player_list: str):
    steam_ids = []
    lines = player_list.splitlines()

    while '' in lines:
        lines.remove('')

    while 'No Players Online' in lines:
        lines.remove('No Players Online')

    for x in lines:
        # tribe_name = x.split('[', 1)[1].split(']')[0]
        tribe_name = re.findall(r'\[.*?\]', x)
        steam_ids.append((x[-17:], tribe_name[-1]))

    return steam_ids


def get_server_map(address: str, query_port: int):
    a2s_connection = (address, query_port)

    try:
        map_name = a2s.info(a2s_connection).map_name
        return map_name
    except socket.timeout:
        print("connection timed out")
        return
