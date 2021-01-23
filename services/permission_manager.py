from services import db_access
from services import file_manager

config = file_manager.load_config()


def set_tribe_rank(steam_id: str, tribe_size: int):
    user_perms = get_permission_groups(steam_id)

    # get list of all tribe rank groups
    config_perms = set()
    for x in config["tribe_ranks"]:
        config_perms.add(x["permission_group"])

    # remove all other tribe ranks
    common_perms = [x for x in user_perms if x in config_perms]
    for y in common_perms:
        remove_permission_group(steam_id, y)

    # add tribe size group
    tribe_size_group = get_permission_group_from_size(tribe_size)
    print("tribe size group")
    print(tribe_size_group)
    add_permission_group(steam_id, tribe_size_group)


def add_permission_group(steam_id: str, group: str):
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)

    perm_groups = get_permission_groups(steam_id)
    perm_groups.append(group)
    print("perm groups")
    print(perm_groups)
    perm_string = ','.join(perm_groups) + ','

    context.execute(f"UPDATE players SET PermissionGroups = '{perm_string}' WHERE SteamId = '{steam_id}'")

    print("adding permission group to member: " + str(steam_id))
    connection.commit()
    context.close()
    connection.close()


def get_permission_group_from_size(size: int):
    for x in config["tribe_ranks"]:
        print("X")
        print(x)
        if x["tribe_size"] == size:
            return x["permission_group"]

    # ERROR HERE
    # check if no tribe size is defined in config


def get_permission_groups(steam_id: str):
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)

    context.execute(f"SELECT PermissionGroups FROM players WHERE SteamId = {steam_id}")
    record = context.fetchone()
    perm_list = record[0].split(',')

    while '' in perm_list:
        perm_list.remove('')

    context.close()
    connection.close()
    print(perm_list)
    return perm_list


def remove_permission_group(steam_id: str, group: str):
    connection = db_access.get_connection()
    context = connection.cursor(buffered=True)

    perm_groups = get_permission_groups(steam_id)
    perm_groups.remove(group)
    perm_string = ','.join(perm_groups) + ','

    context.execute(f"UPDATE players SET PermissionGroups = '{perm_string}' WHERE SteamId = '{steam_id}'")

    connection.commit()
    context.close()
    connection.close()


