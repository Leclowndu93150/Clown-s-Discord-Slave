from discord.ext import commands
import discord


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 363664620583518210

    @commands.command(name="shutdown", help="Shut down the bot", catalogue="Admin")
    async def shutdown(self, ctx: commands.Context):
        if ctx.author.id == self.owner_id:
            await ctx.send("Shutting down...")
            await self.bot.close()
        else:
            await ctx.send("You don't have permission to do that!")

    @commands.command("setname", help="Set the bot's username", catalogue="Admin")
    async def set_name(self, ctx: commands.Context, *, name: str):
        if ctx.author.id == self.owner_id:
            await self.bot.user.edit(username=name)
            await ctx.send(f"Username set to {name}")
        else:
            await ctx.send("You don't have permission to do that!")

    @commands.command("setavatar", help="Set the bot's avatar", catalogue="Admin")
    async def set_avatar(self, ctx: commands.Context, url: str):
        if ctx.author.id == self.owner_id:
            async with self.bot.session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    await self.bot.user.edit(avatar=data)
                    await ctx.send("Avatar set!")
                else:
                    await ctx.send("Failed to fetch image!")
        else:
            await ctx.send("You don't have permission to do that!")

    @commands.command("setactivity", help="Set the bot's activity", catalogue="Admin")
    async def set_activity(self, ctx: commands.Context, *, activity: str):
        if ctx.author.id == self.owner_id:
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.listening, name=activity))
            await ctx.send(f"Activity set to {activity}")
        else:
            await ctx.send("You don't have permission to do that!")

    @commands.command("setstatus", help="Set the bot's status", catalogue="Admin")
    async def set_status(self, ctx: commands.Context, status: str):
        if ctx.author.id == self.owner_id:
            await self.bot.change_presence(status=discord.Status[status])
            await ctx.send(f"Status set to {status}")
        else:
            await ctx.send("You don't have permission to do that!")
