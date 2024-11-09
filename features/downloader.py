from pytube import YouTube
import discord
import re
import os

from utils.exception_handler import DownloadError


async def download_youtube_video(url: str, interaction: discord.Interaction) -> str:
    youtube_regex = (r'^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(?:-nocookie)?\.com|youtu.be))(\/(?:['
                     r'\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$')

    if not re.match(youtube_regex, url):
        await interaction.followup.send("❌ Invalid YouTube URL provided!")
        raise DownloadError("Invalid YouTube URL")

    try:
        output_path = "downloads"
        os.makedirs(output_path, exist_ok=True)

        yt = YouTube(url)
        await interaction.followup.send(f"📥 Downloading: **{yt.title}**")

        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        if not stream:
            await interaction.followup.send("❌ No suitable video stream found!")
            raise DownloadError("No suitable stream found")

        file_path = stream.download(output_path)
        return file_path

    except Exception as e:
        await interaction.followup.send(f"❌ Error downloading video: {str(e)}")
        raise DownloadError(str(e))
