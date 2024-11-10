import discord
from discord.ext import commands
import random
import aiohttp
import xml.etree.ElementTree as ET
import os


class NSFW(commands.Cog):

    @commands.command(name="r34", help="Search for a random image on rule34.xxx", brief="NSFW random search")
    async def r34(self, ctx: commands.Context, *, tags: str):
        if not ctx.channel.is_nsfw() and ctx.message.author.id != 363664620583518210:
            await ctx.send("🔞 This command can only be used in NSFW channels!")
            return

        api_url = f"https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={tags}&limit=100"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    await ctx.send("❌ Failed to retrieve data from rule34.")
                    return

                data = await response.text()

        root = ET.fromstring(data)
        posts = root.findall("post")

        if not posts:
            await ctx.send(f"No results found for tags: `{tags}`.")
            return

        post = random.choice(posts)
        image_url = post.get("file_url")
        post_id = post.get("id")

        image_name = f"spoiler_image_{post_id}.jpg"
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    with open(image_name, "wb") as f:
                        f.write(await response.read())
                else:
                    await ctx.send("❌ Failed to download the image.")
                    return

        try:
            file = discord.File(image_name, filename=f"SPOILER_{os.path.basename(image_name)}")
            await ctx.send(
                content=f"🔞 Here’s a random result for `{tags}`: ||<https://rule34.xxx/index.php?page=post&s=view&id={post_id}>||",
                file=file
            )
        finally:
            if os.path.exists(image_name):
                os.remove(image_name)

    @commands.command(name="r34tags", help="Get a list of popular tags for rule34.xxx", brief="Popular tags list")
    async def r34_tags(self, ctx: commands.Context):
        if ctx.channel.is_nsfw() or ctx.message.author.id == 363664620583518210:
            await ctx.send("Popular tags: https://rule34.xxx/index.php?page=tags&s=list")
        else:
            await ctx.send("🔞 This command can only be used in NSFW channels!")


    @commands.command(name="e621", help="Search for a random image on e621.net", brief="Purrrrfectly safe search")
    async def e621(self, ctx: commands.Context, *, tags: str):
        if not ctx.channel.is_nsfw() and ctx.message.author.id != 363664620583518210:
            await ctx.send("🔞 This command can only be used in NSFW channels!")
            return

        api_url = f"https://e621.net/posts.json?tags={tags}&limit=320"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers={"User-Agent": "Discord Bot"}) as response:
                if response.status != 200:
                    await ctx.send("❌ Failed to retrieve data from e621.")
                    return

                data = await response.json()

        posts = data["posts"]

        if not posts:
            await ctx.send(f"No results found for tags: `{tags}`.")
            return

        post = random.choice(posts)
        image_url = post["file"]["url"]
        post_id = post["id"]

        image_name = f"spoiler_image_{post_id}.jpg"
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    with open(image_name, "wb") as f:
                        f.write(await response.read())
                else:
                    await ctx.send("❌ Failed to download the image.")
                    return

        try:
            file = discord.File(image_name, filename=f"SPOILER_{os.path.basename(image_name)}")
            await ctx.send(
                content=f"🔞 Here’s a random result for `{tags}`: ||<https://e621.net/posts/{post_id}>||",
                file=file
            )
        finally:
            if os.path.exists(image_name):
                os.remove(image_name)

    @commands.command(name="e621tags", help="Get a list of popular tags for e621.net", brief="Popular tags list")
    async def e621_tags(self, ctx: commands.Context):
        if ctx.channel.is_nsfw() or ctx.message.author.id == 363664620583518210:
            await ctx.send("Popular tags: https://e621.net/tags")
        else:
            await ctx.send("🔞 This command can only be used in NSFW channels")


