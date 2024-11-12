import json
import os
import io

from discord.ext import commands
import discord
import STPyV8


class JavaScriptEval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="eval",
        help="Evaluate a JavaScript expression safely",
        aliases=["js", "javascript"],
        brief="Run JavaScript code"
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def eval_js(self, ctx: commands.Context, *, expression: str):
        """
        Evaluates JavaScript code in a sandboxed environment using STPyV8.
        If the result is a file dictionary, sends it as a file attachment.
        """
        # Remove code block formatting if present
        expression = expression.strip('`')
        if expression.startswith('js\n'):
            expression = expression[3:]

        try:
            with STPyV8.JSContext() as ctxt:
                # Add safe built-ins to context
                ctxt.eval("const console = { log: function(msg) { return msg; } };")

                # Convert the result to a JSON string in JavaScript
                result_js = ctxt.eval(f"JSON.stringify({expression})")

                # Parse the JSON string back to Python
                result = json.loads(result_js)

                # Handle file output if it matches the structure
                if isinstance(result, dict) and 'file' in result and isinstance(result['file'], dict):
                    file_info = result['file']
                    if 'name' in file_info and 'data' in file_info:
                        file_name = file_info['name']
                        file_data = file_info['data']

                        # Prepare the file data for Discord
                        buffer = io.BytesIO(file_data.encode('utf-8'))
                        buffer.seek(0)
                        await ctx.send(file=discord.File(buffer, filename=file_name))
                        return

                # Handle regular output
                formatted_result = json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
                if formatted_result:
                    if len(formatted_result) > 1990:
                        parts = [formatted_result[i:i+1990] for i in range(0, len(formatted_result), 1990)]
                        for part in parts:
                            await ctx.send(f"```js\n{part}```")
                    else:
                        await ctx.send(f"```js\n{formatted_result}```")

        except Exception as e:
            await ctx.send(str(e))

        finally:
            ctxt = None  # Clean up context

    @commands.hybrid_command(name="iamlucky", catalogue="Javascript")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def iamlucky(self, ctx: commands.Context):
        path = os.path.join(os.path.dirname(__file__), "..", "scripts", "iamlucky.js")
        try:
            with open(path, "r", encoding="utf-8") as file:
                js_content = file.read()

            with STPyV8.JSContext() as ctxt:
                ctxt.eval(js_content)
                result = ctxt.eval("result")
                await ctx.send(f"```js\n{result}```")
        except FileNotFoundError:
            await ctx.send("The JS file was not found!")
