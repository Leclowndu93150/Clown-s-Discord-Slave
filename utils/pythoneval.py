import ast
import contextlib
import io
import math
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict


class PythonREPL:
    def __init__(self):
        # Built-in functions and constants that are allowed
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

        # Math module functions
        self.safe_math = {
            name: getattr(math, name)
            for name in ['acos', 'asin', 'atan', 'ceil', 'cos', 'degrees',
                         'e', 'exp', 'factorial', 'floor', 'log', 'log10',
                         'pi', 'pow', 'radians', 'sin', 'sqrt', 'tan']
        }

        # Initialize the global namespace with safe functions
        self.globals = {**self.safe_builtins, **self.safe_math}

        # User variables persist between commands
        self.user_vars: Dict[str, Dict[str, Any]] = {}

        # Track last execution time per user
        self.last_exec: Dict[str, datetime] = {}

        # Maximum execution time (in seconds)
        self.timeout = 5

    def get_user_vars(self, user_id: str) -> Dict[str, Any]:
        """Get or create user's variable namespace"""
        if user_id not in self.user_vars:
            self.user_vars[user_id] = {}
        return self.user_vars[user_id]

    def is_safe_node(self, node: ast.AST) -> bool:
        """Check if an AST node is safe to execute"""
        unsafe_nodes = {
            ast.Delete, ast.Import, ast.ImportFrom,
            ast.Global, ast.AsyncFunctionDef, ast.Await,
            ast.Yield, ast.YieldFrom
        }

        # Check for dangerous attribute access
        if isinstance(node, ast.Attribute):
            # Prevent access to dangerous attributes
            unsafe_attrs = {'__globals__', '__builtins__', '__code__', '__getattribute__',
                            '__class__', '__bases__', '__mro__', '__subclasses__',
                            '__init__', '__new__', '__del__', '__repr__', '__str__'}
            if node.attr in unsafe_attrs:
                return False

        return not any(isinstance(node, unsafe_type) for unsafe_type in unsafe_nodes)

    def execute(self, code: str, user_id: str) -> str:
        """Execute Python code and return the result"""
        # Rate limiting
        now = datetime.now()
        if user_id in self.last_exec:
            time_diff = now - self.last_exec[user_id]
            if time_diff < timedelta(seconds=1):
                return "⚠️ Please wait a second between commands"
        self.last_exec[user_id] = now

        # Get user's variable namespace
        user_vars = self.get_user_vars(user_id)

        # Create combined namespace
        namespace = {**self.globals, **user_vars}

        try:
            # Try to parse as an expression first
            try:
                tree = ast.parse(code, mode='eval')
                if not all(self.is_safe_node(node) for node in ast.walk(tree)):
                    return "❌ This operation is not allowed"

                # Capture stdout for print statements
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    result = eval(code, namespace, user_vars)

                output = stdout.getvalue()

                # Update user's variables
                self.user_vars[user_id].update(user_vars)

                if output:
                    return f"{output}{result if result is not None else ''}"
                return str(result) if result is not None else ""

            except SyntaxError:
                # If it's not an expression, try as a statement
                tree = ast.parse(code, mode='exec')

                # Check for unsafe operations
                if not all(self.is_safe_node(node) for node in ast.walk(tree)):
                    return "❌ This operation is not allowed"

                # Capture stdout
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exec(code, namespace, user_vars)

                # Update user's variables
                self.user_vars[user_id].update(user_vars)

                output = stdout.getvalue()
                return output if output else "Done"

        except Exception as e:
            tb = traceback.format_exception_only(type(e), e)
            return f"❌ Error: {''.join(tb)}"
