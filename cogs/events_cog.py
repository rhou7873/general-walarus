from datetime import datetime, timedelta
import discord
from discord.ext.commands import Cog
from discord.ext import commands
import discord.utils as utils
import database as db
from datetime import timedelta
from ai import LLMEngine, VisionEngine
from typing import cast
from models import Server, WSESession
from globals import servers, live_wse_sessions
from utilities import printlog, send_message
from osdk import OsdkActions
import logging
import threading
from api import run_api

class EventsCog(Cog, name="Events"):
    """ Class containing implementations for Discord bot events """
    log = logging.getLogger(f"{__name__}.EventsCog")

    def __init__(self, bot: discord.Bot, llm_engine: LLMEngine | None, vision_engine: VisionEngine):
        self.bot = bot
        self.llm_engine = llm_engine
        self.vision_engine = vision_engine

    # region Events

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Event that runs once General Walarus is up and running """
        EventsCog.initialize_servers(self.bot)
        EventsCog.initialize_wse_sessions(self.bot)

        ontology_sync_thread = threading.Thread(
            target=OsdkActions.sync_ontology,
            args=[self.bot.guilds],
            kwargs={"force_sync": True},
            daemon=True
        )
        ontology_sync_thread.start()

        EventsCog.log.info(f"General Walarus active in {len(servers)} server(s)")

        # Start FastAPI server in a background thread
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()

        # type: ignore
        await self.bot.get_cog("Archive").repeat_archive(timedelta(weeks=2))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """ Event that runs whenever a user sends something in a text channel """
        if message.guild is None:
            return
        if self.bot.user is None:
            raise Exception("bot.user is None")

        bot_sent = message.author.bot

        # updating user stats in DB
        db.inc_user_stat(message.guild, cast(
            discord.User, message.author), "sent_messages")
        for user in message.mentions:
            user_mentioned_self = user.id == message.author.id
            bot_mentioned_user = bot_sent
            if not user_mentioned_self and not bot_mentioned_user:
                db.inc_user_stat(message.guild, cast(
                    discord.User, user), "mentioned")

        if not bot_sent:
            # Walarus responds if mentioned
            if self.bot.user in message.mentions:
                channel = message.channel
                response: str | None
                async with channel.typing():
                    user_mention = f"@{self.bot.user.id}"
                    msg_to_bot = message.content.replace(
                        user_mention, "").replace("<>", "").strip()
                    response = self.llm_engine.get_llm_response(
                        author=message.author, input=msg_to_bot)
                await send_message(message.channel, response)

            # if NSFW image sent, delete and resend with blur
            await self.vision_engine.check_if_nsfw(message)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """ Event that runs whenever General Walarus joins a new server\n 
            Servers information is added to the database """
        printlog(
            f"General Walarus joined guild '{guild.name}' (id: {guild.id})")
        servers[guild] = Server(guild)
        db.log_server(guild)

        # OSDK update
        OsdkActions.sync_ontology(self.bot.guilds)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """ Event that runs when General Walarus gets removed from a server.\n
            Server information is deleted from database """
        del servers[guild]
        printlog(
            f"General Walarus has been removed from guild '{guild.name}' (id: {guild.id})")
        printlog(
            f"{db.remove_discord_server(guild)} documents removed from database")

        # OSDK update
        OsdkActions.sync_ontology(self.bot.guilds)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        """ Event that runs when a server's information gets updated.\n
            Server information gets updated in the database """
        db.log_server(after)
        printlog(f"Server {before.id} was updated")
        
        # OSDK update
        OsdkActions.upsert_guild(after)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """ Event that runs when a user joins a guild """
        guild = member.guild

        if not db.create_user(guild, member):
            EventsCog.log.error("Failed to create user in MongoDB")

        # the following code is only if there is an active Walarus Stock Exchange
        if live_wse_sessions.get(guild) is not None:
            MAGIC_USER = live_wse_sessions[guild].user_id
            if member.id == MAGIC_USER:
                db.set_current_wse_price(member.guild, 0)
                general: discord.TextChannel | None
                general = utils.find(lambda channel: channel.name ==
                                    "general", guild.text_channels)
                if general is not None:
                    await general.send("@everyone the WSE has crashed!!")

        # OSDK update
        OsdkActions.upsert_member(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """ Event that runs when a user is removed from a guild """
        guild = member.guild

        if not db.remove_user(guild, member):
            EventsCog.log.error("Failed to remove user in MongoDB")

        # OSDK update
        OsdkActions.delete_member(member)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """ Event that runs when a user's information gets updated """
        EventsCog.log.info(f"Member '{after.name}' in '{after.guild.name}' was updated")

        # OSDK update
        OsdkActions.upsert_member(after)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, ex: commands.CommandError):
        """ Event that runs when a user tries a command and it raises an error """
        if type(ex) == commands.CommandNotFound:
            await ctx.send("That ain't a command my brother in Christ")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        """ Event that runs when a user changes voice state (join/leaves VC, gets muted/unmuted, 
            gets deafened/undeafened, etc.) """
        guild: discord.Guild = member.guild
        self.db_update_voice(member, guild, before, after)

        if self.bot.user and member.id == self.bot.user.id:
            if before.channel and not after.channel:
                # bot left VC
                voice_client = before.channel.guild.voice_client
                if voice_client:
                    voice_client.cleanup()

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel
    ):
        """ Event that runs when a channel's information gets updated """
        EventsCog.log.info(f"Channel '{after.name}' in '{after.guild.name}' was updated")

        # OSDK update
        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            OsdkActions.upsert_text_channel(after)
        elif isinstance(before, discord.CategoryChannel) and isinstance(after, discord.CategoryChannel):
            OsdkActions.upsert_channel_category(after)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        EventsCog.log.info(f"Channel '{channel.name}' in '{channel.guild.name}' was created")

        # OSDK update
        if isinstance(channel, discord.TextChannel):
            OsdkActions.upsert_text_channel(channel)
        elif isinstance(channel, discord.CategoryChannel):
            OsdkActions.upsert_channel_category(channel)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        EventsCog.log.info(f"Channel '{channel.name}' in '{channel.guild.name}' was deleted")

        # OSDK update
        if isinstance(channel, discord.TextChannel):
            OsdkActions.delete_text_channel(channel)
        elif isinstance(channel, discord.CategoryChannel):
            OsdkActions.delete_channel_category(channel)

    # endregion

    # region Helper Functions

    def db_update_voice(
        self,
        member: discord.Member,
        guild: discord.Guild,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """ Analyzes before and after voice state and updates user voice status in database """
        now: datetime = datetime.now()
        if before.channel == None and after.channel != None:
            # user joins a voice channel
            db.update_user_stats(
                guild, member, last_connected_to_vc=now, connected_to_vc=True)
            vc_members: list = after.channel.members
            non_bot_count: int = 0
            for vc_member in vc_members:
                if not vc_member.bot:
                    non_bot_count += 1
            vc_timer: bool = non_bot_count > 1
            for vc_member in vc_members:
                db.update_user_stats(guild, vc_member, vc_timer=vc_timer)
        elif before.channel != None and after.channel == None:
            # user leaves a voice channel
            field_name: str = "last_connected_to_vc"
            connected_time: datetime = cast(dict, db.get_user_stat(
                guild, member.id, field_name))[field_name]
            session_length: int = (now - connected_time).seconds
            vc_members: list = before.channel.members
            vc_timer: bool = cast(dict, db.get_user_stat(
                guild, member.id, "vc_timer"))["vc_timer"]
            if len(vc_members) == 1:  # just one more person left in voice channel
                # stop everyone's vc timer and update time in db
                for vc_member in vc_members:
                    update_time: bool = cast(dict, db.get_user_stat(
                        guild, vc_member.id, "vc_timer"))["vc_timer"]
                    if update_time:
                        db.inc_user_stat(guild, vc_member,
                                         "time_in_vc", session_length)
                        db.update_user_stats(guild, vc_member, vc_timer=False)
            if vc_timer:  # update time of the person who's leaving
                db.inc_user_stat(guild, member, "time_in_vc", session_length)
            db.update_user_stats(
                guild, member, connected_to_vc=False, vc_timer=False)

    @staticmethod
    def initialize_servers(bot: discord.Bot):
        for guild in bot.guilds:
            servers[guild] = Server(guild)

    @staticmethod
    def initialize_wse_sessions(bot: discord.Bot):
        db_sessions = db.get_active_wse_servers()
        for item in db_sessions:
            id = item["_id"]
            user_id_to_track = item["wse_user_id"]
            guild = utils.find(lambda guild: guild.id == id, bot.guilds)
            if guild is None:
                raise Exception("guild is None")
            live_wse_sessions[guild] = WSESession(
                guild, user_id_to_track, "0 9 * * *")

    # endregion
