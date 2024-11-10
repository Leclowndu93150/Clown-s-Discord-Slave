import ast
import contextlib
import io
import math
import traceback
import inspect
from datetime import datetime, timedelta
from typing import Any, Dict, Set, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import sys


class SecurityViolation(Exception):
    """Custom exception for security violations in the sandbox."""
    pass


class SecurePythonSandbox:
    def __init__(self):
        # Core built-ins that are considered safe
        self.safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'ascii': ascii,
            'bin': bin, 'bool': bool, 'chr': chr, 'dict': dict,
            'divmod': divmod, 'enumerate': enumerate, 'filter': filter,
            'float': float, 'format': format, 'frozenset': frozenset,
            'hex': hex, 'int': int, 'isinstance': isinstance,
            'issubclass': issubclass, 'iter': iter, 'len': len,
            'list': list, 'map': map, 'max': max, 'min': min,
            'next': next, 'oct': oct, 'ord': ord, 'pow': pow,
            'range': range, 'repr': repr, 'reversed': reversed,
            'round': round, 'set': set, 'slice': slice, 'sorted': sorted,
            'str': str, 'sum': sum, 'tuple': tuple, 'zip': zip,
            'True': True, 'False': False, 'None': None,
        }

        # Safe math functions
        self.safe_math = {
            name: getattr(math, name)
            for name in ['acos', 'acosh', 'asin', 'asinh', 'atan', 'atan2',
                         'atanh', 'ceil', 'comb', 'copysign', 'cos', 'cosh',
                         'degrees', 'dist', 'e', 'exp', 'expm1', 'fabs',
                         'factorial', 'floor', 'fmod', 'frexp', 'fsum', 'gamma',
                         'gcd', 'hypot', 'inf', 'isclose', 'isfinite', 'isinf',
                         'isnan', 'isqrt', 'lcm', 'ldexp', 'lgamma', 'log',
                         'log10', 'log1p', 'log2', 'modf', 'nan', 'nextafter',
                         'pi', 'perm', 'pow', 'prod', 'radians', 'remainder',
                         'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'tau', 'trunc']
        }

        # Restricted global namespace
        self.globals = {**self.safe_builtins, **self.safe_math}

        # User state management
        self.user_vars: Dict[str, Dict[str, Any]] = {}
        self.last_exec: Dict[str, datetime] = {}

        # Blacklisted names that shouldn't be allowed in any context
        self.blacklist = {
            'eval', 'exec', 'compile', 'open', 'file', '__import__',
            'input', 'raw_input', 'reload', 'import', 'sys', 'os',
            'subprocess', 'system', 'builtins', '__builtins__', 'frame',
            'globals', 'locals', 'module', '__class__', '__bases__',
            '__subclasses__', '__mro__', '__closure__', '__code__',
            '__globals__', '__dict__', '__getattribute__', '__getattr__',
            '__setattr__', '__delattr__', '__weakref__', '__init__',
            '__new__', '__del__', '__get__', '__set__', '__delete__',
            '__slots__', '__metaclass__', '__subclasshook__', '__instancecheck__',
            'breakpoint', 'credits', 'copyright', 'help', 'license', 'exit', 'quit'
        }

        self.timeout_seconds = 3
        self.max_vars_per_user = 500
        self.rate_limit_seconds = 1
        self.max_memory_mb = 100
        self.max_string_length = 10000
        self.max_collection_size = 10000
        self.max_recursion_depth = 100
        self.max_loop_iterations = 100

    def _check_memory_usage(self, obj: Any, depth: int = 0) -> int:
        """Recursively check memory usage of an object."""
        if depth > self.max_recursion_depth:
            raise SecurityViolation("Maximum recursion depth exceeded")

        size = 0
        seen = set()

        def inner_check(obj: Any, depth: int) -> int:
            if id(obj) in seen:
                return 0
            seen.add(id(obj))

            size = sys.getsizeof(obj)

            if isinstance(obj, (str, bytes)):
                if len(obj) > self.max_string_length:
                    raise SecurityViolation(f"String length exceeds maximum of {self.max_string_length}")

            elif isinstance(obj, (list, tuple, set, frozenset, dict)):
                if len(obj) > self.max_collection_size:
                    raise SecurityViolation(f"Collection size exceeds maximum of {self.max_collection_size}")

                if isinstance(obj, (list, tuple)):
                    for item in obj:
                        size += inner_check(item, depth + 1)
                elif isinstance(obj, (set, frozenset)):
                    for item in obj:
                        size += inner_check(item, depth + 1)
                else:  # dict
                    for k, v in obj.items():
                        size += inner_check(k, depth + 1)
                        size += inner_check(v, depth + 1)

            return size

        return inner_check(obj, depth)

    def check_ast_node(self, node: ast.AST, depth: int = 0) -> bool:
        """Thoroughly check if an AST node is safe to execute."""
        if depth > self.max_recursion_depth:
            raise SecurityViolation("AST recursion depth exceeded")

        # Blacklist of unsafe node types
        unsafe_nodes = {
            ast.Delete, ast.Import, ast.ImportFrom, ast.Global,
            ast.Nonlocal, ast.AsyncFunctionDef, ast.AsyncFor,
            ast.AsyncWith, ast.Await, ast.Yield, ast.YieldFrom,
            ast.ClassDef, ast.Lambda
        }

        if any(isinstance(node, node_type) for node_type in unsafe_nodes):
            return False

        # Check for dangerous attributes
        if isinstance(node, ast.Attribute):
            if node.attr in self.blacklist:
                return False
            # Prevent access to double underscore attributes except __len__
            if node.attr.startswith('__') and node.attr != '__len__':
                return False

        # Check function calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in self.blacklist:
                    return False
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in self.blacklist:
                    return False

        # Check for string literals containing dangerous content
        if isinstance(node, ast.Str):
            lower_str = node.s.lower()
            dangerous_terms = {'import', 'eval', 'exec', 'compile', '__import__'}
            if any(term in lower_str for term in dangerous_terms):
                return False

        # Check for too many nested loops
        if isinstance(node, (ast.For, ast.While)):
            loop_count = 0

            def count_nested_loops(node):
                nonlocal loop_count
                loop_count += 1
                if loop_count > 3:  # Maximum of 3 nested loops
                    return False
                return True

            if not count_nested_loops(node):
                return False

        # Recursively check child nodes
        for child in ast.iter_child_nodes(node):
            if not self.check_ast_node(child, depth + 1):
                return False

        return True

    def sanitize_code(self, code: str) -> str:
        """Sanitize and validate the input code."""
        if not code.strip():
            raise SecurityViolation("Empty code submission")

        if len(code) > 10000:
            raise SecurityViolation("Code length exceeds maximum")

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SecurityViolation(f"Syntax error: {str(e)}")

        # Check each node in the AST
        for node in ast.walk(tree):
            if not self.check_ast_node(node):
                raise SecurityViolation("Unsafe code detected")

        return code

    def execute_with_timeout(self, code: str, user_id: str) -> str:
        """Execute code with timeout and memory limits."""
        if not self.check_rate_limit(user_id):
            return "⚠️ Rate limit exceeded. Please wait."

        try:
            sanitized_code = self.sanitize_code(code)
        except SecurityViolation as e:
            return f"❌ Security Error: {str(e)}"

        user_vars = self.get_user_vars(user_id)
        namespace = {**self.globals, **user_vars}

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._execute_code, sanitized_code, namespace, user_vars)
                    result = future.result(timeout=self.timeout_seconds)

                    # Check memory usage of result
                    if self._check_memory_usage(result) > self.max_memory_mb * 1024 * 1024:
                        raise SecurityViolation("Memory limit exceeded")

                    output = stdout.getvalue()
                    return f"{output}{result if result is not None else ''}"

            except FutureTimeoutError:
                return "❌ Execution timed out"
            except SecurityViolation as e:
                return f"❌ Security Error: {str(e)}"
            except Exception as e:
                return f"❌ Error: {type(e).__name__}: {str(e)}"

    def _execute_code(self, code: str, namespace: dict, user_vars: dict) -> Any:
        """Internal method to execute code in the sandbox."""
        try:
            # Try to evaluate as expression
            return eval(code, namespace, user_vars)
        except SyntaxError:
            # If not an expression, execute as statement
            exec(code, namespace, user_vars)
            return None
        finally:
            # Update user variables, excluding internal names
            user_vars.update({
                k: v for k, v in namespace.items()
                if k not in self.globals and not k.startswith('_')
            })

    def get_user_vars(self, user_id: str) -> Dict[str, Any]:
        """Get or create user's variable namespace with cleanup."""
        if user_id not in self.user_vars:
            self.user_vars[user_id] = {}
        elif len(self.user_vars[user_id]) > self.max_vars_per_user:
            self.user_vars[user_id] = {}
        return self.user_vars[user_id]

    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit."""
        now = datetime.now()
        if user_id in self.last_exec:
            if (now - self.last_exec[user_id]) < timedelta(seconds=self.rate_limit_seconds):
                return False
        self.last_exec[user_id] = now
        return True

    def reset_user(self, user_id: str):
        """Reset all state for a given user."""
        self.user_vars.pop(user_id, None)
        self.last_exec.pop(user_id, None)

    def get_sandbox_info(self) -> Dict[str, Any]:
        """Get information about sandbox configuration."""
        return {
            'timeout_seconds': self.timeout_seconds,
            'max_vars_per_user': self.max_vars_per_user,
            'rate_limit_seconds': self.rate_limit_seconds,
            'max_memory_mb': self.max_memory_mb,
            'max_string_length': self.max_string_length,
            'max_collection_size': self.max_collection_size,
            'max_recursion_depth': self.max_recursion_depth,
            'max_loop_iterations': self.max_loop_iterations,
            'available_builtins': sorted(self.safe_builtins.keys()),
            'available_math': sorted(self.safe_math.keys())
        }
