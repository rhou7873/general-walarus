import asyncio
import discord
from discord.ext.commands import Cog
from discord.ext import commands
import discord.utils
import database as db
from datetime import timedelta, datetime
from pytz import timezone
import logging
from osdk import OsdkActions

class ArchiveCog(Cog, name="Archive"):
    """ Class containing commands pertaining to archiving general chat """
    log = logging.getLogger(f"{__name__}.ArchiveCog")

    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    # region Commands

    @commands.command(name="archivegeneral", aliases=["archive"])
    async def test_archive_general(self, ctx: commands.Context, freq=2) -> None:
        """ Command that manually runs archive function for testing purposes """
        if ctx.guild is None:
            raise Exception("ctx.guild is None")
        if ctx.author.id == ctx.guild.owner_id:
            await self.archive_general(ctx.guild)
        else:
            await ctx.send("Only the owner can use this command")

    @commands.command(name="nextarchivedate", aliases=["nextarchive"])
    async def next_archive_date_command(self, ctx: commands.Context) -> None:
        """ Command that sends the date of the next general chat archive. 
            Assumes global archive date """
        if ctx.guild is None:
            raise Exception("ctx.guild is None")
        eastern = timezone("US/Eastern")
        date = db.get_next_archive_date()
        hour = date.hour % 12
        if date.hour == 12 or date.hour == 0:
            hour = "12"
        meridiem = "AM" if date.hour < 12 else "PM"
        dt_str = (f"{date.month}/{date.day}/{date.year} {hour}:{date.minute:<02} "
                  f"{meridiem} EST")
        await ctx.send(f"Next archive date: {dt_str}")

    # endregion

    # region Helper Functions

    async def archive_general(self, guild: discord.Guild, freq=2, try_time=0) -> None:
        """ Houses the actual logic of archiving general chat """
        if try_time == 3:  # recursive base case for protection
            return

        archive_cat_name = db.get_archive_category(guild)
        name = db.get_chat_to_archive(guild)
        new_name = db.get_archived_name(name)
        archive_category = await self.get_channel_category(guild, archive_cat_name, False)
        try:
            chat_to_archive, general_category = self.get_channel_to_archive(
                guild, name, False)
            await chat_to_archive.move(beginning=True, category=archive_category, sync_permissions=True)
            await chat_to_archive.edit(name=new_name)
            new_channel = await guild.create_text_channel(name, category=general_category)
            await new_channel.send("good morning @everyone")

            # OSDK update
            OsdkActions.upsert_archive_event(chat_to_archive, archive_category)
        except discord.HTTPException as ex:
            if ex.code == 50035:  # too many channels in category, make new archive category
                ArchiveCog.log.info((f"Channel category '{archive_cat_name}' reached limit of "
                          f"50 channels in '{guild.name}' (id: {guild.id})"))
                await guild.create_category_channel(archive_cat_name, position=archive_category.position-1)
                await self.archive_general(guild, try_time=try_time+1)
            else:
                ArchiveCog.log.error(str(ex))
        except Exception as ex:
            ArchiveCog.log.error(str(ex))

    async def repeat_archive(self, freq: timedelta) -> None:
        """ Handles repeatedly archiving general chat """
        await self.sleep_until_archive()
        while True:
            for guild in self.bot.guilds:
                now = datetime.now()
                try:
                    await self.archive_general(guild=guild)
                    ArchiveCog.log.info(
                        str(now) + f": general archived in '{guild.name}' (id: {guild.id})")
                except Exception as ex:
                    ArchiveCog.log.error(str(
                        now) + f": there was an error archiving general in '{guild.name}' (id: {guild.id}): {str(ex)}")
            db.update_next_archive_date(freq)
            await self.sleep_until_archive()

    async def sleep_until_archive(self) -> None:
        """ Handles waiting for the next archive date """
        now = datetime.now(tz=timezone("US/Eastern"))
        then = db.get_next_archive_date()
        wait_time = (then - now).total_seconds()
        await asyncio.sleep(wait_time)

    async def get_channel_category(self, guild: discord.Guild, name: str,
                                   case_sens: bool) -> discord.CategoryChannel:
        """ Returns the discord.CategoryChannel of the first channel category 
            in the given guild that matches the given name """
        def search_predicate(category: discord.CategoryChannel) -> bool:
            return (category.name == name if case_sens else
                    category.name.lower() == name.lower())

        result = discord.utils.find(search_predicate, guild.categories)
        if result == None:
            result = await guild.create_category(name)
            printlog((f"The channel category '{name}' doesn't exist in "
                      f"'{guild.name}', so new category created "
                      f"(id: {guild.id})"))

        return result

    def get_channel_to_archive(self, guild: discord.Guild,
                               name: str, case_sens: bool) -> tuple[discord.TextChannel, discord.CategoryChannel]:
        """ Returns the discord.TextChannel of the first text channel in the given guild 
            that matches the given name. Also, returns the channel category that the
            channel was in """
        def search_category_predicate(category: discord.CategoryChannel) -> bool:
            for channel in category.text_channels:
                if case_sens:
                    if channel.name == name:
                        return True
                else:
                    if channel.name.lower() == name.lower():
                        return True
            return False

        def search_channel_predicate(channel: discord.TextChannel) -> bool:
            return (channel.name == name if case_sens else
                    channel.name.lower() == name.lower())

        category = discord.utils.find(
            search_category_predicate, guild.categories)
        if category != None:  # channel is in a category
            channel = discord.utils.find(
                search_channel_predicate, category.text_channels)
            if channel == None:
                raise Exception((f"Couldn't find a channel named '{name}' in the channel "
                                 f"category '{category.name}' in '{guild.name} (id: {guild.id})'"))
            return channel, category

        # channel is not in a category
        channel = discord.utils.find(
            search_channel_predicate, guild.text_channels)
        if channel == None:
            raise Exception((f"Couldn't find a channel named '{name}' in "
                             f"'{guild.name} (id: {guild.id})'"))

        return channel, None  # type: ignore

    # endregion
