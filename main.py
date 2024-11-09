import discord
import dotenv
import os
from discord.ext import commands
from features.commands import Commands

dotenv.load_dotenv()
intents = discord.Intents.all()

client = commands.Bot(command_prefix="!", intents=intents)


@client.event
async def on_ready():
    print(f'Bot is ready: {client.user}')
    await client.add_cog(Commands(client))
    await client.change_presence(status=discord.Status.dnd)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!commands"))


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: {error.param.name}")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")

client.run(os.getenv('DISCORD_TOKEN'))
