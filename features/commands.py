import discord
from discord.ext import commands
from features.downloader import download_youtube_video
import os
from utils.exception_handler import DownloadError


class Commands:
    def __init__(self, bot):
        self.bot = bot
        self.add_commands()

    def add_commands(self):
        @self.bot.command(name="download")
        async def download(ctx: commands.Context, url: str):
            await ctx.defer()
            try:
                file_path = await download_youtube_video(url, ctx)
                if file_size := os.path.getsize(file_path) > 8 * 1024 * 1024:
                    await ctx.send("⚠️ File is too large to send through Discord!")
                else:
                    await ctx.send("✅ Download complete!", file=discord.File(file_path))
                os.remove(file_path)
            except DownloadError:
                await ctx.send("❌ Download error.")
            except Exception as e:
                await ctx.send(f"❌ An unexpected error occurred: {str(e)}")
