import os
import subprocess
import json
from discord.ext import commands

class JavaScriptEval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scripts_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
        os.makedirs(self.scripts_dir, exist_ok=True)

        self.js_path = os.path.join(self.scripts_dir, "eval_js.js")
        if not os.path.exists(self.js_path):
            self._create_js_file()

    def _create_js_file(self):
        js_code = '''
const ivm = require('isolated-vm');

async function run() {
    // Create a new isolate with a memory limit
    const isolate = new ivm.Isolate({ memoryLimit: 128 });
    const context = await isolate.createContext();

    // Set up a secure jail
    const jail = context.global;
    await jail.set('global', jail.derefInto());

    // Create a safe console that only allows log
    const safeConsole = {
        log: (...args) => console.log(...args)
    };
    await jail.set('console', new ivm.Reference(safeConsole));

    const code = process.argv[2];
    try {
        // Run the code with a timeout
        const result = await context.eval(code, { timeout: 1000 });
        console.log(JSON.stringify(result));
    } catch (e) {
        console.error(JSON.stringify({ error: e.message }));
        process.exit(1);
    }
}

run();
'''
        with open(self.js_path, 'w') as f:
            f.write(js_code)

    @commands.command(
        name="eval",
        help="Evaluate a JavaScript expression safely in an isolated environment",
        aliases=["js", "javascript"],
        brief="Run JavaScript code"
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def eval_js(self, ctx: commands.Context, *, expression: str):
        """
        Evaluates JavaScript code in a secure sandbox environment.
        The code is run with limited memory and execution time.
        """
        # Remove code block formatting if present
        expression = expression.strip('`')
        if expression.startswith('js\n'):
            expression = expression[3:]

        try:
            # Run the JavaScript code in the isolated environment
            process = subprocess.Popen(
                ['node', self.js_path, expression],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Set a timeout of 5 seconds for the entire process
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                await ctx.send("❌ Execution timed out (5 seconds)")
                return

            if stderr:
                # Try to parse error message from JSON
                try:
                    error_data = json.loads(stderr)
                    error_message = error_data.get('error', stderr)
                except json.JSONDecodeError:
                    error_message = stderr

                await ctx.send(f"❌ Error: {error_message}")
            else:
                # Try to parse the result
                try:
                    result = json.loads(stdout)
                    formatted_result = json.dumps(result, indent=2)
                    await ctx.send(f"```js\n{formatted_result}```")
                except json.JSONDecodeError:
                    await ctx.send(f"```js\n{stdout}```")

        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")