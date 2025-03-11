import discord
from discord.ext.commands import Cog
from discord.ext import commands
import os
from typing import List, Literal
from globals import vc_connections, servers
from models import VCConnection
from pydub import AudioSegment
from datetime import datetime


class VoiceCog(Cog, name="Voice"):
    """ Class containing General Walarus' voice commands """

    # region Commands

    @commands.command(name="record", aliases=["startrecording", "join"])
    async def record(self, ctx: commands.Context) -> None:
        voice = ctx.author.voice

        if not voice:
            await ctx.send("You ain't even in a voice channel brotha")

        # Connect to the voice channel the author is in.
        voice_client = await voice.channel.connect()
        sink = discord.sinks.MP3Sink()

        recording = await ctx.send("***BE WARNED*** I'm recording you fuckers 🔴")
        voice_client.start_recording(
            sink,  # The sink type to use.
            VoiceCog.clip_callback,  # What to do once done.
            ctx,  # The command context
            recording,  # Recording message to delete when done
            sync_start=True  # Everyone's audio is in sync
        )

        guild: discord.Guild | None = ctx.guild  # type: ignore
        if guild is None:
            raise Exception("record(): guild is None")
        server = servers[guild]
        if isinstance(voice_client, discord.VoiceClient):
            # Updating the cache with the guild and channel.
            vc_connections.update({guild: VCConnection(server, voice_client)})

    @commands.command(name="clip", aliases=["clipit", "clipthat"])
    async def clip(self, ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.send("You're not even in a voice channel brotha")
            return

        if ctx.guild in vc_connections:  # Check if the guild is in the cache.
            vc = vc_connections[ctx.guild]
            del vc_connections[ctx.guild]
            # Stop recording, and call the callback function.
            vc.voice_client.stop_recording()
        else:
            # Respond with this if we aren't recording.
            await ctx.send("I am currently not recording here.")

    # endregion

    # region Helper Functions

    @staticmethod
    async def clip_callback(sink: discord.sinks.MP3Sink, ctx: commands.Context,
                            recording_msg: discord.Message):
        await recording_msg.delete()
        processing_msg = await ctx.send("Processing your clip...")

        # Combine individual users' audio recordings into into one file
        files = [audio.file for audio in sink.audio_data.values()]

        if files:
            now = datetime.now()
            unique_id = f"{now.year}{now.month}{now.day}{now.hour}{now.minute}{now.second}"
            filename = f"combined{unique_id}.mp3"
            VoiceCog.combine_user_audios(
                audio_files=files, format="mp3", output_filepath=filename)
            combined_file = discord.File(filename, filename="clip.mp3")
            await ctx.send("Here is your clip", files=[combined_file])
            os.remove(filename)
        else:
            await ctx.send("Nothing to clip my man")

        await sink.vc.disconnect()  # Disconnect from the voice channel.
        await processing_msg.delete()

    @staticmethod
    def combine_user_audios(audio_files: List, format: Literal["wav", "mp3"], output_filepath: str,
                            max_length_ms: int = 30000):
        """ Splices the given audio files into one """
        audio_segments = [AudioSegment.from_file(
            file=file, format=format) for file in audio_files]
        max_audio_length = max(
            audio_segments, key=lambda audio: audio.duration_seconds).duration_seconds
        max_audio_length_ms = max_audio_length * 1000  # x1000 to convert seconds to ms
        duration = min(max_audio_length_ms, max_length_ms)
        combined = AudioSegment.silent(duration=max_audio_length_ms)

        # combine to sync all audio segments from the beginning
        for segment in audio_segments:
            combined = combined.overlay(segment)
        combined = combined[-duration:]

        if isinstance(combined, AudioSegment):
            combined.export(output_filepath, format=format)

    # endregion
