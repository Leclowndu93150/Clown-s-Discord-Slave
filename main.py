# main.py

import discord
import dotenv
import os
from discord import Intents
from features import commands

import features

dotenv.load_dotenv()
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
intents.presences = True

class MyClient(discord.Client):
    def __init__(self, *, intents: Intents, **options):
        super().__init__(intents=intents, **options)
        self.commands_instance = None
        self.tree = discord.app_commands.CommandTree(self)
        self.owner_id = 363664620583518210
        activity = discord.Activity(type=discord.ActivityType.listening, name="/download")
        self.activity = activity
        self.status = discord.Status.online

    async def setup_hook(self):
        try:
            self.commands_instance = commands.Commands(self)
            await self.tree.sync()
        except Exception as e:
            print(f"Error in setup_hook: {e}")

    async def on_ready(self):
        try:
            await self.change_presence(activity=self.activity, status=self.status)
            user = await self.fetch_user(self.owner_id)
            await user.send(f'Logged in as {self.user}')
            synced = await self.tree.sync()
            await user.send(f"Synced {len(synced)} command(s)")
            print(f"Bot is ready and online! Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Error in on_ready: {e}")

if __name__ == "__main__":
    client = MyClient(intents=intents)
    client.run(os.getenv('DISCORD_TOKEN'))