import asyncio

from services import file_manager
from services import rcon_manager
from services import permission_manager
from services import db_access
from datetime import datetime, timedelta

config = file_manager.load_config()


def main_check():
    for x in config["servers"]:

        tribe_list = rcon_manager.player_tribe_check(x["address"], x["password"], x["rcon_port"])
        print(tribe_list)
        if tribe_list is None:
            continue

        map_name = rcon_manager.get_server_map(x["address"], x["query_port"])
        if map_name is None:
            continue

        print("checking " + map_name + " on server: " + x["address"], x["query_port"])
        update_users(tribe_list, map_name)

    check_tribe_leave()


def update_users(tribe_list: list, map_name: str):
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    new_members = []

    # update or set database record for user
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)
    for x in tribe_list:
        # try to find user
        context.execute(f"SELECT * FROM tribes WHERE steam_id = {x[0]} AND tribe_name = '{x[1]}' AND map_name = '{map_name}'")
        record = context.fetchone()

        if record is None:
            # set user record
            context.execute(f"INSERT INTO `tribes`(steam_id,tribe_name,tribe_size,map_name,last_seen)"
                            f" VALUES ({x[0]}, '{x[1]}', {0}, '{map_name}', '{timestamp}')")

            # update tribe size
            new_members.append(x[0])
        else:
            # update last seen
            context.execute(f"UPDATE tribes SET last_seen = '{timestamp}' WHERE steam_id = {x[0]} AND map_name = '{map_name}'")

    context.close()
    connection.commit()
    connection.close()

    members_to_update = []
    # update added members
    for y in new_members:
        tribe_name = get_current_tribe(y, map_name)
        members_to_update.extend(get_tribe_members(tribe_name, map_name))

    for z in members_to_update:

        tribe_name = get_current_tribe(z, map_name)
        calculate_tribe_size(z, tribe_name, map_name)
        max_size = get_max_tribe_size(z)
        print("updating member: " + str(z))
        permission_manager.set_tribe_rank(z, max_size)


# calculate all ranks for tribe based on one new member who joined
def calculate_tribe_size(steam_id: int, tribe_name: str, map_name: str):
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)

    tribe_size = len(get_tribe_members(tribe_name, map_name))
    tribe_name = get_current_tribe(steam_id, map_name)

    # solo no tribe Check
    # if tribe_name == "":
    #     tribe_size = 1

    context.execute(f"UPDATE tribes SET tribe_size = {tribe_size} WHERE steam_id = {steam_id} AND tribe_name = '{tribe_name}' AND map_name = '{map_name}' AND tribe_name != '[]' ")

    context.close()
    connection.commit()
    connection.close()


def get_tribe_members(tribe_name: str, map_name: str):
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)

    context.execute(f"SELECT steam_id FROM tribes WHERE tribe_name = '{tribe_name}' AND map_name = '{map_name}'")
    tribe_members = list(sum(context.fetchall(), ()))

    context.close()
    connection.close()
    return tribe_members


def get_current_tribe(steam_id: int, map_name: str):
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)

    # review
    context.execute(f"SELECT tribe_name FROM tribes WHERE steam_id = {steam_id} AND map_name = '{map_name}' AND last_seen = (SELECT MAX(last_seen) FROM tribes WHERE steam_id = {steam_id} AND map_name = '{map_name}')")
    record = context.fetchone()

    context.close()
    connection.close()
    return record[0]


def check_tribe_leave():
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)
    time = datetime.utcnow() - timedelta(hours=22)

    context.execute(f"SELECT * FROM tribes WHERE last_seen < '{time}'")
    expired_members = context.fetchall()
    context.execute(f"DELETE FROM tribes WHERE last_seen < '{time}'")

    context.close()
    connection.commit()
    connection.close()

    # recalculate tribe size for all tribes who had members that expired
    for x in expired_members:
        print(x)
        tribe_members = get_tribe_members(x[2], x[4])
        print("found members")
        print(tribe_members)

        for y in tribe_members:
            calculate_tribe_size(y, x[2], x[4])


def get_max_tribe_size(steam_id: str):
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)
    time = datetime.utcnow() - timedelta(hours=22)

    # exclude solo tribes here
    context.execute(f"SELECT tribe_size FROM tribes WHERE steam_id = '{steam_id}' AND tribe_name != '[]' ")
    record = context.fetchall()

    max_size = 0
    for x in record:
        if x[0] > max_size:
            max_size = x[0]

    context.close()
    connection.commit()
    connection.close()

    return max_size


def get_steam_id(discord_id: str):
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)

    context.execute(f"SELECT SteamId FROM discordaddonplayers WHERE discid = '{discord_id}'")
    record = context.fetchone()

    if not record:
        context.close()
        connection.commit()
        connection.close()
        return None

    else:
        context.close()
        connection.commit()
        connection.close()
        return record[0]


async def loop_task():
    while True:
        main_check()
        await asyncio.sleep(config["general"]["tribe_check_interval"])


task = asyncio.ensure_future(loop_task())
