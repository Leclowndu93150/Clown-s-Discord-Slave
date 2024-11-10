import subprocess
import tempfile
import os
import asyncio
import json
from discord.ext import commands
from typing import Dict, Optional


class PyPyExecutor:
    def __init__(self, pypy_path: str):
        self.user_vars: Dict[str, Dict] = {}
        self.pypy_path = pypy_path
        self.temp_dir = tempfile.mkdtemp()

    def _save_vars(self, user_id: str, vars_dict: dict):
        """Save user variables."""
        self.user_vars[user_id] = vars_dict

    def _load_vars(self, user_id: str) -> dict:
        """Load user variables."""
        return self.user_vars.get(user_id, {})

    async def execute_code(self, code: str, user_id: str, timeout: int = 5) -> Optional[str]:
        """Run Python code in PyPy sandbox with a timeout."""
        user_vars = self._load_vars(user_id)
        var_init = "\n".join(f"{k} = {repr(v)}" for k, v in user_vars.items())

        # Build the full script with variable initialization and user code
        full_script = f"""
import json
{var_init}

original_locals = set(locals().keys())
try:
    exec_globals = {{'__builtins__': __builtins__}}
    exec_locals = locals()
    exec({repr(code)}, exec_globals, exec_locals)
except Exception as e:
    print(f"Error: {{str(e)}}", file=sys.stderr)
    sys.exit(1)

new_vars = {{name: exec_locals[name] for name in exec_locals if name not in original_locals and not name.startswith('__')}}
with open('vars.json', 'w') as f:
    json.dump(new_vars, f)
"""

        script_path = os.path.join(self.temp_dir, f"{user_id}_script.py")
        vars_path = os.path.join(self.temp_dir, "vars.json")

        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(full_script)

            # Run the script with a timeout
            process = await asyncio.create_subprocess_exec(
                self.pypy_path, script_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                return "Error: Execution timed out."

            if process.returncode != 0:
                return f"Error: {stderr.decode('utf-8', errors='replace').strip()}"

            # Load new variables if they exist
            if os.path.exists(vars_path):
                with open(vars_path) as f:
                    new_vars = json.load(f)
                    self._save_vars(user_id, new_vars)

            # Return execution result
            output = stdout.decode('utf-8', errors='replace').strip()
            return output if output else "Execution completed without output."

        finally:
            # Clean up temporary files
            for file in [script_path, vars_path]:
                if os.path.exists(file):
                    os.remove(file)


class PythonCommands(commands.Cog):
    def __init__(self, bot, pypy_path):
        self.bot = bot
        self.executor = PyPyExecutor(pypy_path)

    @commands.command(name="py", help="Execute Python code", aliases=["python"], catalogue="Python")
    async def python(self, ctx: commands.Context, *, code: str):
        code = code.strip('` \n')
        if code.startswith('python\n'):
            code = code[7:]

        if len(code) > 1000:
            await ctx.send("Error: Code too long (max 1000 characters)")
            return

        result = await self.executor.execute_code(code, str(ctx.author.id))

        if result:
            result_str = str(result)
            while result_str:
                chunk = result_str[:1990]
                result_str = result_str[1990:]
                await ctx.send(f"```python\n{chunk}```")
        else:
            await ctx.send("```python\nNone```")

    @commands.command(name="pyvars", help="Show your stored variables", catalogue="Python")
    async def show_vars(self, ctx: commands.Context):
        user_vars = self.executor._load_vars(str(ctx.author.id))
        if not user_vars:
            await ctx.send("No variables stored")
            return

        var_list = [f"{name} = {repr(value)}" for name, value in user_vars.items()]
        result = "\n".join(var_list)

        await ctx.send(f"```python\n{result}```")

    @commands.command(name="pyclear", help="Clear your stored variables", catalogue="Python")
    async def clear_vars(self, ctx: commands.Context):
        self.executor._save_vars(str(ctx.author.id), {})
        await ctx.send("Variables cleared.")
