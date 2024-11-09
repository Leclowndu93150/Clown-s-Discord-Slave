# features/commands.py

import discord
from discord import app_commands
from features.downloader import download_youtube_video
import os
from utils.exception_handler import DownloadError


class Commands(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="youtube", description="YouTube related commands")
        self.bot = bot
        bot.tree.add_command(self)  # Add the group to the tree

    @app_commands.command(name="download", description="Download a YouTube video")
    async def download(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        try:
            file_path = await download_youtube_video(url, interaction)

            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)

                if file_size > 8 * 1024 * 1024:
                    await interaction.followup.send("⚠️ File is too large to send through Discord!")
                else:
                    await interaction.followup.send(
                        "✅ Download complete! Sending file...",
                        file=discord.File(file_path)
                    )
                try:
                    os.remove(file_path)
                except:
                    pass

        except DownloadError:
            await interaction.followup.send("❌ Download error.")
        except Exception as e:
            await interaction.followup.send(f"❌ An unexpected error occurred: {str(e)}")
