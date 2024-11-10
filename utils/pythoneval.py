import ast
import contextlib
import io
import math
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


class REPLSecurityError(Exception):
    """Custom exception for security violations in the REPL."""
    pass


class PythonREPL:
    def __init__(self):
        # Allowed built-in functions
        self.safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'ascii': ascii,
            'bin': bin, 'bool': bool, 'chr': chr, 'dict': dict,
            'divmod': divmod, 'enumerate': enumerate, 'filter': filter,
            'float': float, 'format': format, 'hex': hex,
            'int': int, 'isinstance': isinstance, 'len': len,
            'list': list, 'map': map, 'max': max, 'min': min,
            'oct': oct, 'ord': ord, 'pow': pow, 'range': range,
            'round': round, 'set': set, 'slice': slice, 'sorted': sorted,
            'str': str, 'sum': sum, 'tuple': tuple, 'zip': zip,
            'True': True, 'False': False, 'None': None,
        }

        # Allowed math functions
        self.safe_math = {
            name: getattr(math, name)
            for name in ['acos', 'asin', 'atan', 'ceil', 'cos', 'degrees',
                         'e', 'exp', 'factorial', 'floor', 'log', 'log10',
                         'pi', 'pow', 'radians', 'sin', 'sqrt', 'tan']
        }

        # Restricted global namespace
        self.globals = {**self.safe_builtins, **self.safe_math}
        self.globals['open'] = self._blocked_open  # Override open
        self.globals['input'] = self._blocked_input  # Override input
        self.user_vars: Dict[str, Dict[str, Any]] = {}
        self.last_exec: Dict[str, datetime] = {}

        # Configuration
        self.timeout_seconds = 5
        self.max_vars_per_user = 1000
        self.rate_limit_seconds = 1

    def _blocked_open(self, *args, **kwargs):
        """Raise an error if 'open' is called."""
        raise REPLSecurityError("File operations are not permitted")

    def _blocked_input(self, *args, **kwargs):
        """Raise an error if 'input' is called."""
        raise REPLSecurityError("Interactive input is not allowed")

    def cleanup_user_vars(self, user_id: str):
        """Clean up user variables if too many accumulate."""
        if len(self.user_vars.get(user_id, {})) > self.max_vars_per_user:
            self.user_vars[user_id] = {}

    def get_user_vars(self, user_id: str) -> Dict[str, Any]:
        """Get or create user's variable namespace."""
        if user_id not in self.user_vars:
            self.user_vars[user_id] = {}
        return self.user_vars[user_id]

    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit."""
        now = datetime.now()
        if user_id in self.last_exec:
            time_diff = now - self.last_exec[user_id]
            if time_diff < timedelta(seconds=self.rate_limit_seconds):
                return False
        self.last_exec[user_id] = now
        return True

    def is_safe_node(self, node: ast.AST) -> bool:
        """Check if an AST node is safe to execute."""
        unsafe_nodes = {
            ast.Delete, ast.Import, ast.ImportFrom,
            ast.Global, ast.AsyncFunctionDef, ast.Await,
            ast.Yield, ast.YieldFrom, ast.ClassDef,
            ast.Lambda
        }

        if isinstance(node, ast.Attribute):
            # Disallowed attributes
            unsafe_attrs = {
                'open', '__globals__', '__builtins__', '__code__', '__getattribute__',
                '__class__', '__bases__', '__mro__', '__subclasses__',
                'input', 'os', 'sys', '__dict__', '__weakref__', '__module__',
            }
            return node.attr not in unsafe_attrs

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {'open', 'input'}:
                return False

        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            if len(node.generators) > 2:
                return False

        return not any(isinstance(node, unsafe_type) for unsafe_type in unsafe_nodes)

    def execute_code(self, code: str, namespace: Dict[str, Any], user_vars: Dict[str, Any]) -> str:
        """Inner function to execute code with a timeout."""
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            try:
                result = eval(code, namespace, user_vars)
                output = stdout.getvalue()
                return f"{output}{result if result is not None else ''}"
            except SyntaxError:
                exec(code, namespace, user_vars)
                return stdout.getvalue() if stdout.getvalue() else "Done"

    def execute(self, code: str, user_id: str) -> str:
        """Execute Python code and return the result with a timeout."""
        if not self.check_rate_limit(user_id):
            return "⚠️ Please wait a second between commands"

        self.cleanup_user_vars(user_id)
        user_vars = self.get_user_vars(user_id)
        namespace = {**self.globals, **user_vars}

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.execute_code, code, namespace, user_vars)
            try:
                result = future.result(timeout=self.timeout_seconds)
                self.user_vars[user_id].update(user_vars)
                return result
            except FutureTimeoutError:
                return "❌ Code execution timed out"
            except REPLSecurityError as e:
                return f"❌ Security Error: {str(e)}"
            except Exception as e:
                return f"❌ Error: {''.join(traceback.format_exception_only(type(e), e))}"

    def reset_user_state(self, user_id: str):
        """Reset a user's variable state."""
        self.user_vars.pop(user_id, None)
        self.last_exec.pop(user_id, None)
