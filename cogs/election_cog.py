import asyncio
from copy import deepcopy
from discord.ext.commands import Cog
from discord.ext import commands
from datetime import timedelta, datetime
from models import Election, Server
from globals import elections, servers
import random
from typing import cast
from utilities import timef


class ElectionCog(Cog, name="Election"):
    """ Class containing commands pertaining to elections """

    # region Commands

    @commands.command(name="nextresult", aliases=["nextelectionresult"])
    async def next_election_result(self, ctx: commands.Context):
        """ Command that sends the time of the next election result """
        if not ctx.guild:
            raise Exception("ctx.guild is None")
        active_election: Election | None = elections.get(ctx.guild)
        if active_election:
            await ctx.send(f"The next election will be at {active_election.next_time}")
        else:
            await ctx.send("There are no elections currently active")

    @commands.command(name="election", aliases=["startelection"])
    async def start_election(self, ctx: commands.Context, arg="default"):
        """ Command that initiates an automated election """
        if ctx.guild is None:
            raise Exception("ctx.guild is None")
        if ctx.author.id != ctx.guild.owner_id:
            await ctx.send("Only the Supreme Leader can use this command")
            return
        election: Election | None = elections.get(ctx.guild)
        if election is not None:
            if str(arg).lower() == "cancel":
                await ctx.send("Stopping elections...")
                del elections[ctx.guild]
            else:
                await ctx.send("Elections are already happening")
            return
        server: Server = cast(Server, servers.get(ctx.guild))
        elections[ctx.guild] = Election(server)
        await self.carry_out_election(ctx, timedelta(minutes=server.rc_int))

    # endregion

    # region Helper Functions

    async def carry_out_election(self, ctx: commands.Context, freq: timedelta):
        """ Handles repeatedly sending out election result until finished """
        if ctx.guild is None:
            raise Exception("ctx.guild is None")
        server: Server = cast(Server, servers.get(ctx.guild))
        positions: list[str] = deepcopy(server.rshuffle)
        members: list[str] = deepcopy(server.ushuffle)
        positions_used = []
        election: Election = elections[ctx.guild]
        await ctx.send(f"An election has begun @everyone. The first result will be announced at {timef(election.next_time)}")
        while len(members) > 0 and elections.get(ctx.guild) is not None:
            await asyncio.sleep(freq.total_seconds())
            member_num = random.randint(0, len(members) - 1)
            index = random.randint(0, len(positions_used) - 1) if len(
                positions) == 0 else random.randint(0, len(positions) - 1)
            chosen_one = members[member_num]
            chosen_role = positions_used[index] if len(
                positions) == 0 else positions[index]
            await ctx.send(f"New election result @everyone: {chosen_one}'s new position will be {chosen_role}")
            next = datetime.now() + freq
            positions.remove(chosen_role)
            positions_used.append(chosen_role)
            if len(positions) == 0:
                positions = deepcopy(positions_used)
            members.remove(chosen_one)
        await ctx.send("Election results have been finalized!")
        del elections[ctx.guild]

    # endregion
