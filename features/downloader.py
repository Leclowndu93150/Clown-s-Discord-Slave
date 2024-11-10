import os
import re

import discord
import ffmpeg
from discord.ext import commands
from pytube import YouTube
from redvid import Downloader
import asyncio
from utils.exception_handler import DownloadError


async def download_youtube_audio(url: str, ctx: commands.Context) -> str:
    youtube_regex = (r'^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(?:-nocookie)?\.com|youtu.be))(\/(?:['
                     r'\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$')

    if not re.match(youtube_regex, url):
        await ctx.send("❌ Invalid YouTube URL provided!")
        raise DownloadError("Invalid YouTube URL")

    output_path = "music/songs"
    temp_path = os.path.join(output_path, "temp")
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(temp_path, exist_ok=True)

    sent_messages = []
    temp_audio_path = None

    try:
        async with asyncio.timeout(30):
            yt = await asyncio.to_thread(YouTube, url)
            title = await asyncio.to_thread(lambda: yt.title)
            sent_messages.append(await ctx.send(f"📥 Downloading: **{title}**"))

            audio_stream = await asyncio.to_thread(
                lambda: yt.streams.filter(only_audio=True)
                .order_by('abr')
                .desc()
                .first()
            )

        if not audio_stream:
            await ctx.send("❌ No suitable audio stream found!")
            raise DownloadError("No suitable audio stream found")

        sent_messages.append(await ctx.send(f"🔊 Downloading audio ({audio_stream.abr})..."))

        async with asyncio.timeout(180):
            temp_audio_path = await asyncio.to_thread(
                audio_stream.download,
                output_path=temp_path,
                filename_prefix="audio_"
            )

        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_filename = f"{safe_title}.mp3"
        output_filepath = os.path.join(output_path, output_filename)

        sent_messages.append(await ctx.send("🔄 Converting to MP3..."))

        async with asyncio.timeout(60):
            try:
                ffmpeg.input(temp_audio_path) \
                    .output(output_filepath,
                            acodec='libmp3lame',
                            audio_bitrate='192k',
                            loglevel='error') \
                    .overwrite_output() \
                    .run(capture_stdout=True, capture_stderr=True)

                if temp_audio_path and os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)

                sent_messages.append(await ctx.send("✅ Download complete!"))

                await asyncio.sleep(5)
                for message in sent_messages:
                    await message.delete()

                return output_filepath

            except ffmpeg.Error as e:
                await ctx.send("❌ Error converting to MP3!")
                raise DownloadError(f"FFmpeg error: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}")

    except asyncio.TimeoutError:
        error_message = "❌ Operation timed out. Please try again with a shorter video."
        await ctx.send(error_message)
        raise DownloadError(error_message)

    except Exception as e:
        error_message = f"❌ An unexpected error occurred: {str(e)}"
        print(error_message)
        await ctx.send(error_message)
        raise DownloadError(error_message)

    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception as e:
                print(f"Failed to remove temporary file: {e}")

        try:
            if os.path.exists(temp_path) and not os.listdir(temp_path):
                os.rmdir(temp_path)
        except Exception as e:
            print(f"Failed to remove temp directory: {e}")

async def download_youtube_video(url: str, ctx: discord.ext.commands.Context) -> str:
    youtube_regex = (r'^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(?:-nocookie)?\.com|youtu.be))(\/(?:['
                     r'\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$')

    if not re.match(youtube_regex, url):
        await ctx.send("❌ Invalid YouTube URL provided!")
        raise DownloadError("Invalid YouTube URL")

    try:
        output_path = "downloads/youtube"
        temp_path = os.path.join(output_path, "temp")
        os.makedirs(output_path, exist_ok=True)
        os.makedirs(temp_path, exist_ok=True)

        sent_messages = []

        yt = YouTube(url)
        sent_messages.append(await ctx.send(f"📥 Downloading: **{yt.title}**"))

        video_stream = yt.streams.filter(adaptive=True,
                                         file_extension='mp4',
                                         type="video",
                                         resolution="720p") \
            .first()

        audio_stream = yt.streams.filter(adaptive=True,
                                         type="audio") \
            .order_by('abr') \
            .desc() \
            .first()

        if not video_stream or not audio_stream:
            await ctx.send("❌ No suitable streams found!")
            raise DownloadError("No suitable streams found")

        sent_messages.append(await ctx.send(f"🎥 Downloading video ({video_stream.resolution})..."))
        video_path = video_stream.download(temp_path, filename_prefix="video_")

        sent_messages.append(await ctx.send(f"🔊 Downloading audio ({audio_stream.abr})..."))
        audio_path = audio_stream.download(temp_path, filename_prefix="audio_")

        safe_title = "".join(c for c in yt.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_filename = f"{safe_title}.mp4"
        output_filepath = os.path.join(output_path, output_filename)

        sent_messages.append(await ctx.send("🔄 Merging video and audio..."))
        try:
            input_video = ffmpeg.input(video_path)
            input_audio = ffmpeg.input(audio_path)

            ffmpeg.output(input_video,
                          input_audio,
                          output_filepath,
                          acodec='aac',
                          vcodec='copy') \
                .overwrite_output() \
                .run(capture_stdout=True, capture_stderr=True)

            os.remove(video_path)
            os.remove(audio_path)

            sent_messages.append(await ctx.send(f"✅ Download complete! Resolution: {video_stream.resolution}"))

            for message in sent_messages:
                await message.delete()

            return output_filepath

        except ffmpeg.Error as e:
            await ctx.send("❌ Error merging video and audio!")
            raise DownloadError(f"FFmpeg error: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}")

    except Exception as e:
        error_message = f"❌ An unexpected error occurred: {str(e)}"
        print(error_message)
        await ctx.send(error_message)
        raise DownloadError(error_message)


async def download_reddit_video(url: str, ctx: discord.ext.commands.Context) -> str:
    reddit_regex = (r"^http(?:s)?://(?:www\.)?(?:[\w-]+?\.)?reddit.com(/r/|/user/)?(?(1)([\w:\.]{2,"
                    r"21}))(/comments/)?(?(3)(\w{5,9})(?:/[\w%\\\\-]+)?)?(?(4)/(\w{3,9}))?/?(\?)?(?(6)(\S+))?(\#)?(?("
                    r"8)(\S+))?$")

    if not re.match(reddit_regex, url):
        await ctx.send("❌ Invalid Reddit URL provided!")
        raise DownloadError("Invalid Reddit URL")

    try:
        output_path = "downloads/reddit"
        os.makedirs(output_path, exist_ok=True)
        sent_messages = []

        sent_messages.append(await ctx.send(f"📥 Downloading: **{url}**"))

        reddit = Downloader(max_q=True)
        reddit.path = output_path
        reddit.log = False
        reddit.url = url
        reddit.download()
        file_path = f"{reddit.file_name}"

        for message in sent_messages:
            await message.delete()

        return file_path

    except Exception as e:
        print(f"❌ An unexpected error occurred: {str(e)}")
