import discord
from discord.ext.commands import Cog
from discord.ext import commands
import database as db
from models import TimeSpan
from typing import cast
from utilities import printlog


class StatisticsCog(Cog, name="Statistics"):
    """ Class containing General Walarus' statistics commands """

    # region Commands

    @commands.command(name="messages", aliases=["mymessages"])
    async def messages(self, ctx: commands.Context, user: discord.User = None) -> None:  # type: ignore
        """ Command that sends back how many messages user has sent """
        try:
            guild = ctx.guild
            user = cast(discord.User, ctx.author) if user is None else user
            if guild != None:
                query = cast(dict, db.get_user_stat(
                    guild, user.id, "sent_messages"))
                messages = int(query["sent_messages"])
                if user.id == ctx.author.id:
                    await ctx.send(f"You've sent {messages:,} messages")
                else:
                    await ctx.send(f"{user.name} has sent {messages:,} messages")
        except Exception as e:
            printlog(str(e))
            await ctx.send("I pooped my pants...try again")

    @commands.command(name="vctime", aliases=["timeinvc"])
    async def vctime(self, ctx: commands.Context, user: discord.User = None) -> None:  # type: ignore
        """ Command that sends back how much time user has spent in voice channel """
        try:
            guild = ctx.guild
            user = cast(discord.User, ctx.author) if user is None else user
            if guild != None:
                query = cast(dict, db.get_user_stat(
                    guild, user.id, "time_in_vc"))
                seconds = int(query["time_in_vc"])
                time: TimeSpan = TimeSpan(seconds)
                msg = f"You've spent" if user.id == ctx.author.id else f"{user.name} has spent"
                if time.days() > 0:
                    msg += (f" {time.days()} {time.days_unit()}, {time.hours()} {time.hours_unit()}, "
                            f"{time.minutes()} {time.minutes_unit()}, and {time.seconds()} "
                            f"{time.seconds_unit()} in voice channel")
                elif time.hours() > 0:
                    msg += (f" {time.hours()} {time.hours_unit()}, {time.minutes()} "
                            f"{time.minutes_unit()}, and {time.seconds()} "
                            f"{time.seconds_unit()} in voice channel")
                elif time.minutes() > 0:
                    msg += (f" {time.minutes()} {time.minutes_unit()}, and {time.seconds()} "
                            f"{time.seconds_unit()} in voice channel")
                else:
                    msg += f" {time.seconds()} {time.seconds_unit()} in voice channel"
                await ctx.send(msg)
        except Exception as e:
            printlog(str(e))
            await ctx.send("I pooped my pants...try again")

    @commands.command(name="showstats", aliases=["leaderboard"])
    async def show_stats(self, ctx: commands.Context):
        if ctx.guild == None:
            await ctx.send("Aw poop nuggets, I sharted myself...")
            return
        leaderboard: list = db.get_user_stats(ctx.guild)

        def sort_key(user): return user["sent_messages"] + \
            user["time_in_vc"] + user["mentioned"]
        leaderboard.sort(key=sort_key, reverse=True)
        message = "```SERVER STATS LEADERBOARD\n\n"
        for user in leaderboard:
            username = user["user_name"]
            mentioned = user["mentioned"]
            mentioned_units = "time" if mentioned == 1 else "times"
            sent_messages = user["sent_messages"]
            messages_unit = "message" if sent_messages == 1 else "messages"
            vctime = TimeSpan(user["time_in_vc"])
            message += f"{username}\n"
            message += f"\tMentioned: {mentioned} {mentioned_units}\n"
            message += f"\tMessages sent: {sent_messages} {messages_unit}\n"
            message += (f"\tTime in VC: {vctime.days()} {vctime.days_unit()}, {vctime.hours()} "
                        f"{vctime.hours_unit()}, {vctime.minutes()} {vctime.minutes_unit()}, "
                        f"{vctime.seconds()} {vctime.seconds_unit()}\n")
        message += "```"
        await ctx.send(message)

    # endregion
