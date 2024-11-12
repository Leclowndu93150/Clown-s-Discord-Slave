from discord.ext import commands
import discord
import aiohttp


class Fun(commands.Cog):

    @commands.hybrid_command(name="dadjoke", help="Get a random dad joke", brief="Random dad joke")
    async def dadjokes(self, ctx):
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://icanhazdadjoke.com/",
                                       headers={"Accept": "application/json"}) as response:
                    data = await response.json()
                    await ctx.send(data["joke"])

    @commands.hybrid_command(name="meme", help="Get a random meme", brief="Random meme")
    async def meme(self, ctx):
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://meme-api.com/gimme") as response:
                    data = await response.json()
                    embed = discord.Embed(title=data["title"], url=data["postLink"])
                    embed.set_image(url=data["url"])
                    embed.set_footer(text=f"From: r/{data['subreddit']}")
                    await ctx.send(embed=embed)

    @commands.hybrid_command(name="cat", help="Get a random cat image", brief="Random cat")
    async def cat(self, ctx):
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.thecatapi.com/v1/images/search") as response:
                    data = await response.json()
                    embed = discord.Embed()
                    embed.set_image(url=data[0]["url"])
                    await ctx.send(embed=embed)

    @commands.hybrid_command(name="dog", help="Get a random dog image", brief="Random dog")
    async def dog(self, ctx):
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://dog.ceo/api/breeds/image/random") as response:
                    data = await response.json()
                    embed = discord.Embed()
                    embed.set_image(url=data["message"])
                    await ctx.send(embed=embed)

