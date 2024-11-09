from pytube import YouTube
import discord
from discord.ext import  commands
import re
import os

from utils.exception_handler import DownloadError


async def download_youtube_video(url: str, ctx: discord.ext.commands.Context) -> str:
    youtube_regex = (r'^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(?:-nocookie)?\.com|youtu.be))(\/(?:['
                     r'\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$')

    if not re.match(youtube_regex, url):
        await ctx.send("❌ Invalid YouTube URL provided!")
        raise DownloadError("Invalid YouTube URL")

    try:
        output_path = "downloads"
        os.makedirs(output_path, exist_ok=True)

        yt = YouTube(url)
        await ctx.send(f"📥 Downloading: **{yt.title}**")

        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        if not stream:
            await ctx.send("❌ No suitable video stream found!")
            raise DownloadError("No suitable stream found")

        file_path = stream.download(output_path)
        return file_path

    except Exception as e:
        await ctx.send(f"❌ Error downloading video: {str(e)}")
        raise DownloadError(str(e))
