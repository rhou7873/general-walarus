from bw_secrets import OPENAI_ASST_ID, OPENAI_MODEL
from discord.ext.commands import Cog
from discord.ext import commands
from utilities import printlog
import openai
import os


class OpenAICog(Cog, name="OpenAI"):
    """ Class containing General Walarus' OpenAI commands """

    def __init__(self) -> None:
        openai.api_key = os.getenv("OPENAI_API_KEY")

    # region Commands

    @commands.command(name="gpt", aliases=["ai", "chatgpt"])
    async def chat_gpt(self, ctx: commands.Context, *message_input) -> None:
        """ Command to chat with ChatGPT """
        WAITING_MSG = await ctx.send("ChatGPT is thinking...")
        MAX_TRIES = 3
        try_count = 0
        success = False

        while (try_count < MAX_TRIES):
            try:
                messages = []
                messages.append(
                    {"role": "user", "content": " ".join(message_input)})
                chat = openai.ChatCompletion.create(
                    model=OPENAI_MODEL, messages=messages)
                success = True
                break
            except Exception as e:
                try_count += 1
                printlog(f"gpt command failed (try_count: {try_count})")
        await WAITING_MSG.delete()

        if success:
            # type: ignore
            await ctx.send(f"ChatGPT says: ```{chat.choices[0].message.content}```")
        else:
            await ctx.send("ChatGPT died trying to talk to you...")

    # endregion
