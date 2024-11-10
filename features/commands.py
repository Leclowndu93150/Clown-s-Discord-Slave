import subprocess

import discord
from discord.ext import commands, tasks
from features.downloader import download_youtube_video, download_reddit_video
from utils.pythoneval import PythonREPL
from utils.uploader import upload_to_temp
from features.reminder import ReminderSystem
import os


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder_system = ReminderSystem()
        self.repl = PythonREPL()
        if not self.check_reminders.is_running():
            self.check_reminders.start()

    @commands.command(name="download_youtube", help="Download a YouTube video or short", catalogue="Downloader")
    async def download_youtube(self, ctx: commands.Context, url: str):
        await ctx.defer()
        try:
            file_path = await download_youtube_video(url, ctx)
            file_size = os.path.getsize(file_path)

            if file_size > 100 * 1024 * 1024:
                await ctx.send(
                    f"⚠️ Max file size exceeded! Size: {file_size / (1024 * 1024):.2f} MB (100 MB limit)")
            elif file_size > 8 * 1024 * 1024:
                await ctx.send("⚠️ File is too large, uploading to a temporary host instead...")
                link = upload_to_temp(file_path)
                parts = link.split('/')
                modified_link = f"https://tmpfiles.org/dl/{parts[3]}/{parts[4]}"
                await ctx.send(f"✅ Upload complete! {modified_link}")
            else:
                await ctx.send("✅ Download complete!", file=discord.File(file_path))

            os.remove(file_path)
        except Exception as e:
            await ctx.send(f"❌ An unexpected error occurred: {str(e)}")
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)

    @commands.command(name="download_reddit", help="Download a Reddit video", catalogue="Downloader")
    async def download_reddit(self, ctx: commands.Context, url: str):
        await ctx.defer()
        try:
            file_path = await download_reddit_video(url, ctx)
            file_size = os.path.getsize(file_path)

            if file_size > 100 * 1024 * 1024:
                await ctx.send(
                    f"⚠️ Max file size exceeded! Size: {file_size / (1024 * 1024):.2f} MB (100 MB limit)")
            elif file_size > 8 * 1024 * 1024:
                await ctx.send("⚠️ File is too large, uploading to a temporary host instead...")
                link = upload_to_temp(file_path)
                parts = link.split('/')
                modified_link = f"https://tmpfiles.org/dl/{parts[3]}/{parts[4]}"
                await ctx.send(f"✅ Upload complete! {modified_link}")
            else:
                await ctx.send("✅ Download complete!", file=discord.File(file_path))

            os.remove(file_path)
        except Exception as e:
            await ctx.send(f"❌ An unexpected error occurred: {str(e)}")
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)

    @commands.command(name='remindme', help='Set a reminder, e.g. !remindme 1d 2h 3m 4s Some reminder text',
                      catalogue="Misc")
    async def remind_me(self, ctx: commands.Context, *, reminder_text: str):
        parts = reminder_text.split(maxsplit=1)
        if len(parts) < 2:
            await ctx.send("Usage: !remindme [time] [message]\nExample: !remindme 1d 2h Check email")
            return

        time_str, message = parts[0], parts[1]
        success, response = self.reminder_system.add_reminder(ctx.author.id, ctx.channel.id, time_str, message)

        if success:
            await ctx.send(f"✅ I'll remind you about '{message}' at {response}")
        else:
            await ctx.send(response)

    @commands.command(name="ping", help="Check the bot's latency", catalogue="Misc")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"🏓 Pong! Latency: {round(self.bot.latency * 1000)}ms")

    @commands.command(name="invite", help="Get the invite link for the bot", catalogue="Misc")
    async def invite(self, ctx: commands.Context):
        await ctx.send(
            "🔗 Invite me to your server: https://discord.com/oauth2/authorize?client_id=1129457269642362900")

    @commands.command(name="commands", help="Get a list of all available commands", catalogue="Help")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(title="Commands", description="List of all available commands", color=0xe342f5)
        for command in self.bot.commands:
            embed.add_field(name=command.name, value=command.help, inline=False)
        await ctx.send(embed=embed)

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        for reminder in self.reminder_system.check_reminders():
            try:
                channel = self.bot.get_channel(reminder["channel_id"])
                if channel:
                    user = self.bot.get_user(reminder["user_id"])
                    mention = user.mention if user else f"<@{reminder['user_id']}>"
                    await channel.send(
                        f"⏰ {mention} Here's your reminder: {reminder['message']}\n"
                        f"(Set {reminder['time_delta']} ago)"
                    )
            except Exception as e:
                print(f"Error sending reminder: {e}")

    @commands.command(name="py", help="Execute Python code", aliases=["python"], catalogue="Python")
    async def python(self, ctx: commands.Context, *, code: str):

        code = code.strip('` \n')
        if code.startswith('python\n'):
            code = code[7:]

        if len(code) > 1000:
            await ctx.send("❌ Code too long (max 1000 characters)")
            return

        try:
            result = self.repl.execute(code, str(ctx.author.id))

            if result:
                result_str = str(result)
                while result_str:
                    chunk = result_str[:1990]
                    result_str = result_str[1990:]
                    await ctx.send(f"```python\n{chunk}```")
            else:
                await ctx.send("```python\nNone```")

        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="pyvars", help="Show your stored variables", catalogue="Python")
    async def show_vars(self, ctx: commands.Context):
        user_vars = self.repl.get_user_vars(str(ctx.author.id))
        if not user_vars:
            await ctx.send("No variables stored")
            return

        var_list = [f"{name} = {repr(value)}" for name, value in user_vars.items()]
        result = "\n".join(var_list)

        await ctx.send(f"```python\n{result}```")

    @commands.command(name="pyclear", help="Clear your stored variables", catalogue="Python")
    async def clear_vars(self, ctx: commands.Context):
        self.repl.user_vars[str(ctx.author.id)] = {}
        await ctx.send("Variables cleared")

    @commands.command(name="iamlucky", catalogue="Fun")
    async def iamlucky(self, ctx: commands.Context):
        path = os.path.join(os.path.dirname(__file__), "..", "scripts", "iamlucky.js")
        try:
            with open(path, "r", encoding="utf-8") as file:
                js_content = file.read()
            await ctx.send(js2py.eval_js(js_content))
        except FileNotFoundError:
            await ctx.send("The JS file was not found!")

    def cog_unload(self):
        self.check_reminders.cancel()
