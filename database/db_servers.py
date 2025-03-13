import discord
from datetime import datetime
from .db_globals import *
from typing import cast


def log_server(discord_server: discord.Guild) -> bool:
    connected_servers = db.connected_servers
    server_exists = bool(connected_servers.find_one(
        {"_id": discord_server.id}))
    icon_url = "" if discord_server.icon is None else discord_server.icon.url
    description_exists = bool(discord_server.description)
    server_data = {
        "_id": discord_server.id,
        "name": str(discord_server.name),
        "description": str(discord_server.description) if description_exists else "",
        "icon_url": icon_url,
        "creation_at": discord_server.created_at,
        "last_updated": datetime.now(),
        "rshuffle": list(map(_role_name, discord_server.roles)),
        "ushuffle": list(map(_member_name, discord_server.members))
    }
    if not server_exists:
        server_data["joined"] = datetime.now()
    return log(discord_server, connected_servers, server_data)


def _role_name(role: discord.Role) -> str:
    return role.name


def _member_name(member: discord.Member) -> str:
    return member.name


def remove_discord_server(guild: discord.Guild) -> int:
    """ Remove the given server from all relevant collections, returns the number of documents deleted """
    connected_servers = db.connected_servers
    user_stats = db.user_stats
    total = connected_servers.delete_many({"_id": guild.id}).deleted_count
    return total


def get_rshuffle(guild: discord.Guild) -> list[str]:
    connected_servers = db.connected_servers
    query = connected_servers.find_one({
        "_id": guild.id
    },
        {
        "rshuffle": 1
    })
    if query is None:
        return []
    query_dict: dict = cast(dict, query)
    return [] if query_dict.get("rshuffle") == None else query_dict["rshuffle"]


def get_ushuffle(guild: discord.Guild) -> list[str]:
    connected_servers = db.connected_servers
    query = connected_servers.find_one({"_id": guild.id},
                                       {"ushuffle": 1})
    if query is None:
        return []
    query_dict: dict = cast(dict, query)
    return [] if query_dict.get("ushuffle") == None else query_dict["ushuffle"]


def get_archive_category(guild: discord.Guild) -> str:
    connected_servers = db.connected_servers
    query = connected_servers.find_one({"_id": guild.id},
                                       {"archive_category": 1})
    query_dict: dict = cast(dict, query)
    return str(query_dict["archive_category"])


def get_chat_to_archive(guild: discord.Guild) -> str:
    connected_servers = db.connected_servers
    query = connected_servers.find_one({"_id": guild.id},
                                       {"chat_to_archive": 1})
    query_dict: dict = cast(dict, query)
    return str(query_dict["chat_to_archive"])


def get_wse_status(guild: discord.Guild) -> bool:
    connected_servers = db.connected_servers
    query = connected_servers.find_one({"_id": guild.id},
                                       {"wse": 1})
    query_dict = cast(dict, query)
    status = bool(query_dict["wse"])
    return status


def set_wse_status(guild: discord.Guild, status: bool, user_id: int | None = None):
    if status and user_id is None:
        raise Exception(
            "Must provide the ID of the user to crash the WSE if enabling the WSE.")

    connected_servers = db.connected_servers
    query = connected_servers.update_one({"_id": guild.id},
                                         {"$set": {
                                             "wse": status,
                                             "wse_user_id": -1 if user_id is None else user_id
                                         }
    })


def get_active_wse_servers():
    connected_servers = db.connected_servers
    query = connected_servers.find({"wse": True})
    return [server for server in query]


def get_timeout_role(guild: discord.Guild) -> str:
    connected_servers = db.connected_servers
    query = connected_servers.find_one({"_id": guild.id},
                                       {"timeout_role": 1})
    query_dict: dict = cast(dict, query)
    return str(query_dict["timeout_role"])