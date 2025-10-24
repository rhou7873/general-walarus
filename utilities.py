import asyncio
from bw_secrets import CMD_PREFIX
import database as db
from datetime import datetime
import discord
from discord.abc import Messageable
from models.server import Server
import os
from pytz import timezone


def printlog(message: str) -> None:
    """ Prints input message to log file """
    eastern = timezone("US/Eastern")
    now = datetime.now(tz=eastern)
    log_file = open("log", "a")
    log_file.write(f"{now}: {message}\n")
    log_file.close()


def timef(dt: datetime) -> str:
    """ Format time of given datetime (ex. 02:47 PM CST) """
    return dt.strftime("%I:%M %p %Z")


def now_time(server: Server) -> datetime:
    """ Gives datetime.now() with timezone of given server """
    return datetime.now(tz=timezone(server.timezone))


def make_offset_aware(server: Server, dt: datetime) -> datetime:
    """ Getting datetime from DB gives offset-naive, by default, so 
    this function will convert it to offset-aware """
    result: datetime = dt.replace(tzinfo=timezone(server.timezone))
    return result


def get_server_prefix() -> str:
    """ Returns the given server's command prefix from DB 
    (this is just a placeholder for now) """
    result = CMD_PREFIX
    return str(result)


async def send_message(channel: Messageable, msg: str | None):
    if msg is None:
        return

    # if under Discord message limit, just send as is
    DISCORD_MSG_LIMIT = 2000
    if len(msg) < DISCORD_MSG_LIMIT:
        await channel.send(msg)
        return

    # otherwise put message in a file and send file
    OUTPUT_FILE = "message.md"
    with open(OUTPUT_FILE, "x") as f:
        f.write(msg)
    with open(OUTPUT_FILE, "rb") as f:
        msg_file = discord.File(fp=f, filename=OUTPUT_FILE)
        await channel.send(file=msg_file)

    os.remove(OUTPUT_FILE)

async def send_user_to_timeout(guild: discord.Guild,
                               member: discord.Member,
                               reason: str,
                               delay: int = 0) -> None:
    if guild.owner_id == member.id:
        return

    await asyncio.sleep(delay)
    timeout_role_str = db.get_timeout_role(guild)
    timeout_role = None

    for role in guild.roles:
        if role.name == timeout_role_str:
            timeout_role = role
            break

    if timeout_role is not None:
        await member.remove_roles(*member.roles[1:])
        await member.add_roles(timeout_role, reason=reason)
