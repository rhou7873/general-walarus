import discord
import io
from google.cloud import vision


class VisionEngine():

    def __init__(self):
        self.__CLIENT = vision.ImageAnnotatorClient()

    async def check_if_nsfw(self, msg: discord.Message) -> None:
        if len(msg.attachments) <= 0:
            return

        # collect the message attachments and mark any
        # NSFW images as spoilers
        resend_attachments = []
        has_nsfw_content = False
        for attachment in msg.attachments:
            if attachment.content_type is None:
                continue

            extension = attachment.content_type.split("/")[-1]
            attachment_bytes = await attachment.read()
            new_file = discord.File(fp=io.BytesIO(
                attachment_bytes), filename=f"bruh.{extension}")

            if attachment.content_type.startswith("image"):
                image = vision.Image(content=attachment_bytes)
                if self.__is_nsfw(image):
                    has_nsfw_content = True
                    new_file = discord.File(fp=io.BytesIO(
                        image.content), filename=f"bruh.{extension}", spoiler=True)

            resend_attachments.append(new_file)

        if has_nsfw_content:
            new_msg_content = (f"**Blurring possible NSFW content in message from {msg.author.mention}**\n"
                               f"*Original message content:* {msg.content}")
            await msg.delete()
            await msg.channel.send(content=new_msg_content, files=resend_attachments)

    def __is_nsfw(self, image: vision.Image) -> bool:
        LIKELIHOOD_NAMES = (
            "UNKNOWN",
            "VERY_UNLIKELY",
            "UNLIKELY",
            "POSSIBLE",
            "LIKELY",
            "VERY_LIKELY",
        )
        UNSAFE_SEARCH_INDICATORS = ['UNKNOWN',
                                    'POSSIBLE', 'LIKELY', 'VERY_LIKELY']
        response = self.__CLIENT.safe_search_detection(image=image)
        safe_search = response.safe_search_annotation

        return (LIKELIHOOD_NAMES[safe_search.racy] in UNSAFE_SEARCH_INDICATORS or
                LIKELIHOOD_NAMES[safe_search.adult] in UNSAFE_SEARCH_INDICATORS)
