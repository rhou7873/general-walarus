from bw_secrets import BOT_TOKEN
import discord
from discord.ext import commands
from cogs import (ArchiveCog, ElectionCog, EventsCog,
                  MiscellaneousCog, StatisticsCog, VoiceCog,
                  WSECog)
from ai import LLMEngine, VisionEngine
from utilities import get_server_prefix


def run_bot(bot: commands.Bot):
    bot.run(BOT_TOKEN)


def main():
    """ Setup bot intents and cogs and bring General Walarus to life """
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.voice_states = True

    bot: commands.Bot = commands.Bot(
        command_prefix=get_server_prefix(), intents=intents)
    llm_engine: LLMEngine = LLMEngine()
    vision_engine: VisionEngine = VisionEngine()

    bot.add_cog(EventsCog(bot, llm_engine, vision_engine))
    bot.add_cog(ArchiveCog(bot))
    bot.add_cog(ElectionCog())
    bot.add_cog(MiscellaneousCog())
    bot.add_cog(StatisticsCog())
    bot.add_cog(VoiceCog())
    # bot.add_cog(OpenAICog())
    bot.add_cog(WSECog())

    run_bot(bot)


if __name__ == "__main__":
    main()
