import asyncio
import discord
from discord.ext.commands import Cog
from discord.ext import commands
import discord.utils
from models import Election
from globals import elections
import logging
import random
from osdk import OsdkActions, OsdkObjects


class ElectionCog(Cog, name="Election"):
    """ Class containing commands pertaining to elections """
    log = logging.getLogger(f"{__name__}.ElectionsCog")

    def __init__(self, bot: discord.Bot):
        self.bot = bot

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
            ElectionCog.log.error("ctx.guild is None")
            raise Exception("ctx.guild is None")
        if ctx.author.id != ctx.guild.owner_id:
            await ctx.send("Only the Supreme Leader can use this command")
            return

        guild: discord.Guild
        channel: discord.TextChannel
        try:
            guild = ctx.guild
            channel = ctx.channel
        except Exception as e:
            ElectionCog.log.error(e)
            return

        ElectionCog.log.info(
            f"Election triggered from command: guild={guild}, channel={channel}")

        # Check an election isn't already currently in progress
        if OsdkObjects.election_in_progress(str(guild.id)):
            await ctx.send("Election is already in progress!")
            return

        try:
            # OSDK update
            if not OsdkActions.start_election(guild):
                raise ElectionCogException("Failed to run start_election action in OSDK. An "
                                           "election may already be in progress")
        except ElectionCogException as e:
            ElectionCog.log.error(e.message)
            await ctx.send("Issue trying to initiate election")

    # endregion

    # region Helper Functions

    async def initiate_election(
        self,
        server: str | discord.Guild,
        channel: str | discord.TextChannel | None = None
    ):
        # Get Pycord guild & channel instances
        try:
            server = (server
                      if isinstance(server, discord.Guild)
                      else self.bot.get_guild(int(server)))

            ElectionCog.log.info(f"Got guild instance: guild={server}")

            if isinstance(channel, str):
                channel = (discord.utils.get(server.text_channels, name="general")
                           if channel is not None and isinstance(channel, discord.TextChannel)
                           else self.bot.get_channel(int(channel)))

            if channel is None:
                ElectionCog.log.error("No channel ID provided, and couldn't infer which channel "
                                      "to send election status to: "
                                      f"server={server}, channel={channel}")

            ElectionCog.log.info(f"Got channel instance: channel={channel}")
        except ValueError:
            raise ElectionCogException("Error parsing given server_id and/or channel_id string as "
                                       f"an int: server={server}, channel={channel}")

        osdk_guild = OsdkObjects.get_guild(server.id)
        ElectionCog.log.info(
            f"Election initiated in '{server}' (id: {server.id})")

        if osdk_guild is None:
            raise ElectionCogException("Issue fetching OSDK guild object")
        elif OsdkObjects.election_in_progress(str(server.id)):
            raise ElectionCogException(f"'{osdk_guild.name}' (id: {osdk_guild.server_id}) "
                                       "already has an election in progress")

        member_ids_set = set(osdk_guild.setting_election_members)
        role_ids_set = set(osdk_guild.setting_election_roles)
        members = [member
                   for member
                   in server.members
                   if OsdkActions.get_member_ontology_id(member) in member_ids_set
                   ]
        roles = [role
                 for role
                 in server.roles
                 if str(role.id)
                 in role_ids_set
                 ]
        members_str = ""
        for member in members:
            members_str += (
                f"- {member.name if member.nick is None else member.nick} ({member.name})\n"
            )
        roles_str = ""
        for role in roles:
            roles_str += f"- {role.name}\n"

        ElectionCog.log.info(
            f"'{server}' (id: {server.id}) election: members - {members}")
        ElectionCog.log.info(
            f"'{server}' (id: {server.id}) election: roles - {roles}")

        cadence_minutes = osdk_guild.setting_election_cadence

        if cadence_minutes is None:
            raise ElectionCogException(
                "Was unable to fetch server's election cadence")

        ElectionCog.log.info(
            f"'{server}' (id: {server.id}) election: cadence - {cadence_minutes}")

        # Initiate election loop in the background
        asyncio.create_task(ElectionCog.election_loop(
            guild=server,
            channel=channel,
            members=members,
            roles=roles,
            cadence_minutes=cadence_minutes
        ))

        ElectionCog.log.info(
            f"'{server.name}' (id: {server.id}) election: started election loop")

        await channel.send("@everyone **Election has started!**\n"
                           "```"
                           "members:\n"
                           f"{members_str}"
                           "roles:\n"
                           f"{roles_str}"
                           "```")

        return server, channel

    async def election_loop(
        guild: discord.Guild,
        channel: discord.TextChannel,
        members: list[discord.Member],
        roles: list[discord.Role],
        cadence_minutes: int
    ):
        """ Handles repeatedly sending out election result until finished """
        if not members:
            raise Exception(
                f"Must provide members for election: members={members}")
        if not roles:
            raise Exception(f"Must provide roles for election: roles={roles}")

        members_set = set(members)
        roles_set = set(roles)

        while members_set:
            # Wait until next selection
            await asyncio.sleep(cadence_minutes * 60)

            # If we ran out of roles, reset the role pool
            roles_set = set(roles) if not roles_set else roles_set

            # Chose the member and the role to assign them
            chosen_member = random.choice(tuple(members_set))
            chosen_role = random.choice(tuple(roles_set))

            # Notify result in channel
            await channel.send(f"@everyone **New Election Result**: {chosen_member.mention} is "
                               f"assigned the role of `{chosen_role.name}`")

            # Of the provided roles, remove any of those roles that the
            # member may currently have
            try:
                roles_to_remove = [
                    role for role in chosen_member.roles if role in roles]
                await chosen_member.remove_roles(*roles_to_remove)

                # Grant the new chosen role to the member
                await chosen_member.add_roles(chosen_role)
            except discord.Forbidden:
                await channel.send("I don't have permission to update "
                                   f"`{chosen_member.display_name}`'s roles, you'll have to update "
                                   "their role manually")

            # Remove selections from the members/roles pool
            members_set.remove(chosen_member)
            roles_set.remove(chosen_role)

            # OSDK update
            OsdkActions.get_election_result(guild, chosen_member, chosen_role)

        await channel.send("@everyone **Election complete!**")

        # OSDK update
        OsdkActions.stop_election(guild)

    # endregion


class ElectionCogException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"{message}")
