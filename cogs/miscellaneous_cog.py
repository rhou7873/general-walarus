import discord
from discord.ext.commands import Cog
from discord.ext import commands
import database as db
from datetime import datetime
from globals import servers
from models import Server, TimeSpan
import os
from pytz import timezone
from utilities import now_time, timef
from typing import cast


class MiscellaneousCog(Cog, name="Miscellaneous"):
    """ Class containing General Walarus' miscellaneous commands """

    # region Commands

    @commands.command(name="anjayunban")
    async def anjay_unban(self, ctx: commands.Context) -> None:
        eastern = timezone("US/Eastern")
        now: datetime = datetime.now(tz=eastern)
        datetime_unbanned: datetime = eastern.localize(
            datetime(year=2024, month=9, day=19, hour=21, minute=40)
        )
        sec_until: int = (datetime_unbanned - now).total_seconds().__floor__()

        if sec_until <= 0:
            await ctx.send("Anjay has been unbanned")
            return

        time_until: TimeSpan = TimeSpan(sec_until)

        if time_until.days() > 0:
            await ctx.send(
                (f"Anjay will be unbanned in {time_until.days()} {time_until.days_unit()}, "
                 f"{time_until.hours()} {time_until.hours_unit()}, {time_until.minutes()} "
                 f"{time_until.minutes_unit()}, {time_until.seconds()} {time_until.seconds_unit()}")
            )
        elif time_until.hours() > 0:
            await ctx.send(
                (f"Anjay will be unbanned in {time_until.hours()} {time_until.hours_unit()}, "
                 f"{time_until.minutes()} {time_until.minutes_unit()}, {time_until.seconds()} "
                 f"{time_until.seconds_unit()}")
            )
        elif time_until.minutes() > 0:
            await ctx.send(
                (f"Anjay will be unbanned in {time_until.minutes()} {time_until.minutes_unit()}, "
                 f"{time_until.seconds()} {time_until.seconds_unit()}")
            )
        else:
            await ctx.send(
                (f"Anjay will be unbanned in {time_until.seconds()} {time_until.seconds_unit()}")
            )

    @commands.command(name="bruh")
    async def bruh(self, ctx: commands.Context) -> None:
        """ Stupid command that just has General Walarus send 'bruh' """
        await ctx.send("bruh")

    @commands.command(name="echo", aliases=["say"])
    async def echo(self, ctx: commands.Context, *words) -> None:
        """ Command that has General Walarus repeat back command args """
        message = ""
        for word in words:
            message += word + " "
        await ctx.send(message)

    @commands.command(name="intodatabase", aliases=["intodb"])
    async def log_server_into_database(self, ctx: commands.Context):
        """ Command to manually log a server into the database """
        if ctx.guild is None:
            raise Exception("ctx.guild is None")
        if ctx.author.id == ctx.guild.owner_id:
            created_new = db.log_server(ctx.guild)
            if created_new:
                await ctx.send("Logged this server into the database")
            else:
                await ctx.send("Updated this server in database")
        else:
            await ctx.send("Only the owner can use this command")

    @commands.command(name="datetime", aliases=["date", "time"])
    async def time(self, ctx: commands.Context) -> None:
        """ Get the current datetime in the timezone of the given server """
        if ctx.guild is None:
            raise Exception("ctx.guild is None")
        server: Server = cast(Server, servers.get(ctx.guild))
        now: datetime = now_time(server)
        await ctx.send(f"It is {now.date()}, {timef(now)}")

    @commands.command(name="settings")
    async def settings(self, ctx: commands.Context) -> None:

        author: discord.Member = cast(discord.Member, ctx.author)
        guild: discord.Guild = cast(discord.Guild, ctx.guild)
        perm = ctx.author.id == guild.owner_id

        for role in author.roles:
            if role.permissions.administrator:
                perm = True
                break

        if not perm:
            await ctx.send("You don't have permission to this command")
            return

        dm = ctx.author.dm_channel
        if dm == None:
            dm = await ctx.author.create_dm()

        lip_bite = discord.File("lip_bite.png")
        base_url = os.getenv("SERVER_SETTINGS_URL",
                             "https://general-walarus-web-app.vercel.app")
        await ctx.send("Check yo DMs", file=lip_bite)
        await dm.send((f"Link to your server settings: {base_url}/settings/{guild.id} "
                       f"(**DO NOT SHARE URL WITH ANYONE**)"))

    @commands.command(name="pfp")
    async def profile_pic(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        if member is None:
            member = ctx.author
        filename = f"{member.id}-avatar.jpg"
        await member.avatar.save(filename)
        await ctx.send(file=discord.File(filename))
        os.remove(filename)

    @commands.command(name="test")
    async def test(self, ctx: commands.Context) -> None:
        """ Command reserved for testing purposes """
        if ctx.guild is None:
            raise Exception("ctx.guild is None")
        await ctx.send("Boi wat you tryna test 🫱")

    # endregion
