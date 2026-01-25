from ai import LLMEngine, VisionEngine
from cogs import (ArchiveCog, ElectionCog, EventsCog,
                  MiscellaneousCog, StatisticsCog, VoiceCog,
                  WSECog)
import discord
from discord.ext import commands
from utilities import get_server_prefix

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

BOT: commands.Bot = commands.Bot(
    command_prefix=get_server_prefix(), intents=intents)
llm_engine: LLMEngine = LLMEngine()
vision_engine: VisionEngine = VisionEngine()

BOT.add_cog(EventsCog(BOT, llm_engine, vision_engine))
BOT.add_cog(ArchiveCog(BOT))
BOT.add_cog(ElectionCog(BOT))
BOT.add_cog(MiscellaneousCog())
BOT.add_cog(StatisticsCog())
BOT.add_cog(VoiceCog())
BOT.add_cog(WSECog())
