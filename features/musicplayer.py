import discord
from features import downloader
from discord.ext import commands
import os
import asyncio


class MusicPlayer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.queue = []
        self.now_playing = None
        self.volume = 1.0
        self.loop = False
        self.paused = False

    @commands.command(name="join", help="Join the voice channel", catalogue="Music")
    async def join(self, ctx: commands.Context):
        if ctx.author.voice is None:
            return await ctx.send("❌ You are not in a voice channel")

        if self.voice_client is not None:
            return await ctx.send("❌ Already in a voice channel")

        self.voice_client = await ctx.author.voice.channel.connect()
        await ctx.send(f"🔊 Joined {ctx.author.voice.channel}")

    @commands.command(name="leave", help="Leave the voice channel", catalogue="Music")
    async def leave(self, ctx: commands.Context):
        if self.voice_client is None:
            return await ctx.send("❌ Not in a voice channel")

        await self.voice_client.disconnect()
        self.voice_client = None
        self.queue.clear()  # Clear the queue when leaving
        await ctx.send("🔇 Left the voice channel")

    @commands.command(name="play", help="Play a song from a YouTube search", catalogue="Music")
    async def play(self, ctx: commands.Context, *query: str):
        if not ctx.author.voice:
            return await ctx.send("❌ You must be in a voice channel!")

        if self.voice_client is None:
            try:
                self.voice_client = await ctx.author.voice.channel.connect(timeout=10)
            except Exception as e:
                return await ctx.send(f"❌ Failed to connect: {str(e)}")

        try:
            search_term = " ".join(query)
            file_path = await downloader.download_youtube_audio(search_term, ctx)
            if not file_path or not os.path.exists(file_path):
                return await ctx.send("❌ Error downloading audio")

            self.queue.append(file_path)
            await ctx.send(f"🎵 Added to queue: {os.path.basename(file_path)}")

            if not self.voice_client.is_playing() and not self.voice_client.is_paused():
                await self.play_next(ctx)

        except Exception as e:
            await ctx.send(str(e))

    async def play_next(self, ctx: commands.Context):
        if not self.queue:
            return

        try:
            self.now_playing = self.queue[0] if self.loop else self.queue.pop(0)

            if not os.path.exists(self.now_playing):
                await ctx.send("❌ File not found!")
                return await self.play_next(ctx)

            audio_source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    self.now_playing,
                    options=f'-filter:a volume={self.volume}'
                ),
                volume=self.volume
            )

            def after_playing(error):
                if error:
                    asyncio.run_coroutine_threadsafe(
                        ctx.send(f"❌ Error playing audio: {error}"),
                        self.bot.loop
                    )
                asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx),
                    self.bot.loop
                )

            self.voice_client.play(audio_source, after=after_playing)
            await ctx.send(f"🎶 Now playing: {os.path.basename(self.now_playing)}")

        except Exception as e:
            await ctx.send(str(e))
            await self.play_next(ctx)

    @commands.command(name="pause", help="Pause the current song", catalogue="Music")
    async def pause(self, ctx: commands.Context):
        if self.voice_client.is_playing() and not self.voice_client.is_paused():
            self.voice_client.pause()
            await ctx.send("⏸️ Paused the music")
        else:
            await ctx.send("❌ No music is currently playing")

    @commands.command(name="resume", help="Resume the paused song", catalogue="Music")
    async def resume(self, ctx: commands.Context):
        if self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("▶️ Resumed the music")
        else:
            await ctx.send("❌ No music is paused")

    @commands.command(name="skip", help="Skip the current song", catalogue="Music")
    async def skip(self, ctx: commands.Context):
        if self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send("⏭️ Skipped to the next song")
            await self.play_next(ctx)
        else:
            await ctx.send("❌ No music is playing to skip")

    @commands.command(name="queue", help="Show the current queue", catalogue="Music")
    async def show_queue(self, ctx: commands.Context):
        if not self.queue:
            await ctx.send("🔚 The queue is currently empty")
        else:
            queue_list = "\n".join(f"{idx + 1}. {song}" for idx, song in enumerate(self.queue))
            await ctx.send(f"🎶 Current Queue:\n{queue_list}")

    @commands.command(name="volume", help="Show the current volume", catalogue="Music")
    async def show_volume(self, ctx: commands.Context):
        await ctx.send(f"🔊 Volume is currently set to {int(self.volume * 100)}%")

    @commands.command(name="setvolume", help="Set the volume (0-100)", catalogue="Music")
    async def set_volume(self, ctx: commands.Context, volume: int):
        if 0 <= volume <= 100:
            self.volume = volume / 100.0
            await ctx.send(f"🔊 Volume set to {volume}%")
            if self.voice_client.is_playing():
                self.voice_client.source.volume = self.volume  # Update volume in real-time
        else:
            await ctx.send("❌ Volume must be between 0 and 100")

    @commands.command(name="loop", help="Toggle looping for the current song", catalogue="Music")
    async def toggle_loop(self, ctx: commands.Context):
        self.loop = not self.loop
        status = "enabled" if self.loop else "disabled"
        await ctx.send(f"🔁 Looping is now {status}")
