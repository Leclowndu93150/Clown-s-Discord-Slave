import asyncio
import json
import websockets
from discord.ext import commands


class AmongUsVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1320854477464404090
        self.bot.loop.create_task(self.connect_capture())

    async def connect_capture(self):
        while True:
            try:
                async with websockets.connect('ws://localhost:42069/api') as ws:
                    await self.handle_states(ws)
            except:
                await asyncio.sleep(5)

    async def handle_states(self, ws):
        while True:
            data = json.loads(await ws.recv())
            if data['EventID'] == 0:
                state = json.loads(data['EventData'])['NewState']
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    if state == 2:
                        await self.unmute_all(channel)
                    elif state == 1:
                        await self.mute_all(channel)
            await asyncio.sleep(2)

    async def mute_all(self, channel):
        for member in channel.members:
            try:
                await member.edit(mute=True)
            except Exception as e:
                print(f"Failed to mute {member}: {e}")

    async def unmute_all(self, channel):
        for member in channel.members:
            try:
                await member.edit(mute=False)
            except Exception as e:
                print(f"Failed to unmute {member}: {e}")
