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
            print(attachment.content_type)

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
        UNSAFE_SEARCH_INDICATORS = ['POSSIBLE', 'LIKELY', 'VERY_LIKELY']

        # build safe-search detection request
        safe_search_feature = vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION)
        request = vision.AnnotateImageRequest(image=image, features=[safe_search_feature])
        requests = vision.BatchAnnotateImagesRequest(requests=[request])

        # process response 
        result = self.__CLIENT.batch_annotate_images(requests)
        safe_search = result.responses[0].safe_search_annotation

        nsfw = (safe_search.racy.name in UNSAFE_SEARCH_INDICATORS
                or safe_search.adult.name in UNSAFE_SEARCH_INDICATORS)
         
        return nsfw
