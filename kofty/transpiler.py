"""
InterScript transpiler: Python AST → Raylib C++ source.

Scope (honest):
  - Top-level statements and function definitions
  - Variables (int, float, str, bool) via simple assignment
  - Arithmetic and comparison expressions
  - if / elif / else
  - while loops
  - for loops over range()
  - Function calls (both built-in Raylib wrappers and user functions)
  - return statements
  - print() to console

Supported:
  - class definitions with __init__ and instance fields
    (single __init__ per class; fields default to `int`)

NOT yet supported (will raise TranspileError):
  - instance methods on classes (Phase A-2)
  - inheritance, super(), class-level variables
  - match statements
  - Lists, dicts, tuples
  - imports
  - exceptions
"""

import ast
from typing import List


class TranspileError(Exception):
    """Raised when InterScript encounters unsupported syntax."""
    pass


# ---- Built-in function table ---------------------------------------------
# Maps InterScript function name → (arity, C++ emission template)
# The template uses {0}, {1}, ... for positional args.
# ---- Language-level builtins (always available, no external deps) ----
CORE_BUILTINS = {
    # These are handled by special cases in _call_expr, so the table
    # entries here are mostly for arity checking where applicable.
    # (print, str, int, float, len, vec2, ptr are all special-cased.)
}

# ---- Batch 25: names that are always in scope ----
# Every name Kofty recognizes as a builtin, constant, or importable module.
# Any Name not in this set, and not bound anywhere in the source, raises
# TranspileError at expression-emission time.
_BUILTIN_NAMES: set = {
    # Builtin functions (dispatched in _call_expr)
    "print", "input", "str", "int", "float", "bool", "len",
    "vec2", "ptr",
    # Builtin functions that only appear in for-loop iter position
    "range", "enumerate", "zip",
    # Meta
    "super",
    # Constants (also handled as ast.Constant in some paths)
    "True", "False", "None",
    # Module names — valid as `Name` when followed by an Attribute
    "math", "random", "time", "raylib",
}
# ---- Batch 25: raylib constants (only in scope when `import raylib`) ----
_RAYLIB_CONSTANTS: set = {
    "KEY_LEFT", "KEY_RIGHT", "KEY_UP", "KEY_DOWN", "KEY_SPACE",
    "KEY_ENTER", "KEY_ESCAPE", "KEY_BACKSPACE", "KEY_TAB",
    "MOUSE_BUTTON_LEFT", "MOUSE_BUTTON_RIGHT", "MOUSE_BUTTON_MIDDLE",
}
# ---- Batch 25: raylib constants (only in scope when `import raylib`) ----
_RAYLIB_CONSTANTS: set = {
    "KEY_LEFT", "KEY_RIGHT", "KEY_UP", "KEY_DOWN", "KEY_SPACE",
    "KEY_ENTER", "KEY_ESCAPE", "KEY_BACKSPACE", "KEY_TAB",
    "MOUSE_BUTTON_LEFT", "MOUSE_BUTTON_RIGHT", "MOUSE_BUTTON_MIDDLE",
}
# ---- Batch 25: raylib constants (only in scope when `import raylib`) ----
_RAYLIB_CONSTANTS: set = {
    "KEY_LEFT", "KEY_RIGHT", "KEY_UP", "KEY_DOWN", "KEY_SPACE",
    "KEY_ENTER", "KEY_ESCAPE",
    "MOUSE_BUTTON_LEFT", "MOUSE_BUTTON_RIGHT", "MOUSE_BUTTON_MIDDLE",
}

# ---- Raylib builtins (only available when `import raylib` is present) ----
RAYLIB_BUILTINS = {
    # Window / lifecycle
    "window":        (3, "InitWindow({0}, {1}, {2});"),
    "set_fps":       (1, "SetTargetFPS({0});"),
    "close_window":  (0, "CloseWindow();"),

    # Drawing
    "begin_draw":    (0, "BeginDrawing();"),
    "end_draw":      (0, "EndDrawing();"),
    "clear":         (3, "ClearBackground((Color){{{0}, {1}, {2}, 255}});"),
    "draw_text":     (7, "DrawText({0}, {1}, {2}, {3}, (Color){{{4}, {5}, {6}, 255}});"),
    "draw_rectangle":(7, "DrawRectangle({0}, {1}, {2}, {3}, (Color){{{4}, {5}, {6}, 255}});"),
    "draw_circle":   (6, "DrawCircle({0}, {1}, {2}, (Color){{{3}, {4}, {5}, 255}});"),

    # Input
    "running":       (0, "!WindowShouldClose()"),
    "is_key_down":   (1, "IsKeyDown({0})"),
    "is_key_pressed":(1, "IsKeyPressed({0})"),
    "get_mouse_x":   (0, "GetMouseX()"),
    "get_mouse_y":   (0, "GetMouseY()"),
    "measure_text":  (2, "MeasureText({0}, {1})"),
    "is_mouse_down": (1, "IsMouseButtonDown({0})"),
    "is_mouse_pressed": (1, "IsMouseButtonPressed({0})"),
}

# C++ reserved keywords. Using any of these as a function, method,
# variable, or class name will produce cryptic g++ errors. We reject
# them at transpile time with a friendly error message instead.
CPP_RESERVED = {
    # Built-in types
    "int", "float", "double", "char", "bool", "void", "auto",
    "short", "long", "signed", "unsigned", "wchar_t", "char16_t",
    "char32_t",
    # Control flow
    "if", "else", "while", "for", "do", "switch", "case", "default",
    "break", "continue", "return", "goto",
    # Declarations
    "class", "struct", "union", "enum", "namespace", "using",
    "typedef", "template", "typename",
    # Storage / qualifiers
    "static", "extern", "register", "mutable", "const", "constexpr",
    "volatile", "inline", "virtual", "friend", "explicit", "operator",
    # Memory / pointers
    "new", "delete", "this", "nullptr",
    # Access
    "public", "private", "protected",
    # Other
    "try", "catch", "throw", "sizeof", "typeid", "static_cast",
    "dynamic_cast", "const_cast", "reinterpret_cast",
    # C++20
    "concept", "requires", "co_await", "co_yield", "co_return",
}


class CppEmitter(ast.NodeVisitor):
    """Walks a Python AST and emits C++ lines with indentation."""

    def __init__(self):
        self.lines: List[str] = []
        self.indent = 1  # inside main()
        self.functions: List[str] = []  # function bodies emitted separately
        self.user_funcs: set = set()
        # Batch 27: names of functions shadowed by a later def of the same name.
        self.shadowed_funcs: set = set()
        # Batch 5b: name -> C++ element type of a *args variadic param.
        # Presence in this dict means the function has a *args param.
        self.func_varargs: dict = {}
        # Batch 13d: how many leading positional params precede
        # the *args vararg. Used at call sites to know how many
        # leading args stay positional and how many go into the
        # wrapped vector.
        self.func_vararg_leading: dict = {}
        # Batch 5c: name -> C++ value type of a **kwargs variadic param.
        # Presence in this dict means the function has a **kwargs param.
        self.func_kwargs: dict = {}
        # Batch 5d: names that hold a lambda value.
        # A call to one of these names emits as a variable call,
        # not as a call to a registered user function.
        self.lambda_vars: set = set()
        self.declared: set = set()  # variable names already declared in current scope
        self.classes: List[str] = []  # class definitions emitted separately
        self.user_classes: set = set()
        # Batch 25: every name bound anywhere in the source (assign targets,
        # for-loop targets, function params, import aliases, def/class names).
        # Populated by _collect_bound_names() in transpile().
        self.all_bound_names: set = set()
        # Batch 11c.1: name -> element C++ type (was a set before).
        # e.g. 'int', 'std::string', 'std::pair<int, int>'. The
        # presence of a name still means 'this is a list'.
        self.list_vars: dict = {}
        self.class_bases: dict = {}      # child class name → list of parent names
        self.class_methods: dict = {}    # class name → set of method names
        self.current_class: str = None   # set during visit_ClassDef method emission
        self.class_has_explicit_init: dict = {}   # class name → bool
        self.pointer_vars: set = set()          # var name → holds a pointer
        self.pointer_list_vars: dict = {}       # list var name → element class name
        self.vec2_vars: set = set()             # names known to hold vec2 (std::pair<double,double>)
        # Batch 8b: instance tracking for __str__ dispatch.
        self.instance_vars: dict = {}   # var name -> class name (for print/str dispatch)
        self.class_field_types: dict = {}  # Batch 10k.2: class name -> {field -> C++ type}
        # Batch 13h: class name -> {param_index -> inferred C++ type}
        # Filled by the ctor-arg pre-pass in transpile().
        self.class_ctor_arg_types: dict = {}
        self.str_classes: set = set()   # user classes that define __str__
        # Batch 11a: name -> literal string captured at assignment time.
        # Used by .format() on a variable receiver.
        self.str_literal_vars: dict = {}
        self.string_vars: set = set()   # Batch 15: names assigned from input() or str literals
        self.global_vars: dict = {}     # Batch 22: scalar top-level vars hoisted to global scope
        self.global_declared: set = set()  # Batch 24: names declared `global` in current function
        self.current_function = None       # Batch 26: name of enclosing function, None at module level
        # Batch 11b: name -> tuple arity returned by a function.
        # Populated in visit_FunctionDef; consumed in visit_Assign.
        self.func_return_arity: dict = {}
        self.add_classes: set = set()   # user classes that define __add__
        # Batch 8d: property tracking.
        self.property_getters: dict = {}   # class name -> set of @property names
        self.property_setters: dict = {}   # class name -> set of names with @x.setter
        # Batch 8e: @classmethod tracking.
        self.classmethod_names: dict = {}  # class name -> set of @classmethod names
        self._classmethod_param: str = ""  # first-param name inside a classmethod body
        self._current_class: str = ""      # enclosing class during field/method emission
        self.needs_raylib: bool = False         # True if source has `import raylib`
        # Batch 7a: track which standard modules have been imported.
        # Populated by visit_Import; consumed by expr/_call_expr for
        # `math.X` gating.
        self.imported_modules: set = set()
        self.optional_funcs: set = set()        # functions that return std::optional<T>
        self.optional_func_types: dict = {}      # func name -> inner T
        self.optional_vars: dict = {}           # var name -> T for std::optional<T>
        self.set_vars: dict = {}                # var name -> element type for std::set<T>
        self.tuple_vars: dict = {}        # var name -> arity (2 for pair, 3+ for tuple)
        self.use_optional: bool = False         # True if any std::optional emitted
        self.dict_vars: dict = {}    # var name → value type (for subscript dispatch)
        # ---- for...else state (Batch 4b) -----------------------------
        # Counter for unique flag names (__broke_1, __broke_2, ...).
        self._for_else_counter: int = 0
        # Stack of currently-active for-else flag names. When a `break`
        # is emitted and the stack is non-empty, we set the top-of-stack
        # flag before emitting `break;` so the else block is skipped.
        self._for_else_stack: list = []

    def _parse_format_spec(self, spec_node):
        """Batch 9a: parse an f-string format_spec AST into a plain string.

        Returns the raw spec string (e.g. ".2f", "05d", ">10") or None
        if there is no format_spec.
        """
        if spec_node is None:
            return None
        # In Python 3.12+, format_spec is an ast.JoinedStr whose .values
        # are ast.Constant string pieces.
        if isinstance(spec_node, ast.JoinedStr):
            pieces = []
            for piece in spec_node.values:
                if isinstance(piece, ast.Constant) and isinstance(piece.value, str):
                    pieces.append(piece.value)
                else:
                    raise TranspileError(
                        "Nested f-string format specs (e.g. {x:{width}}) "
                        "are not supported yet."
                    )
            return "".join(pieces)
        # Fallback for older AST shapes.
        if isinstance(spec_node, ast.Constant) and isinstance(spec_node.value, str):
            return spec_node.value
        raise TranspileError(
            f"Unsupported f-string format spec node: {spec_node!r}"
        )

    def _emit_format_spec(self, inner_cpp: str, spec: str) -> str:
        """Batch 9a: emit a helper call for the given format spec.

        Supports: .Nf, .N, Nd, 0Nd, >N, <N, ^N, N.Mf.
        Raises TranspileError for anything else.
        """
        import re
        # Width + precision float: N.Mf
        m = re.fullmatch(r"(\d+)\.(\d+)f", spec)
        if m:
            w, p = m.group(1), m.group(2)
            return f"fmt_width_float({inner_cpp}, {w}, {p})"
        # Precision float: .Nf
        m = re.fullmatch(r"\.(\d+)f", spec)
        if m:
            return f"fmt_float({inner_cpp}, {m.group(1)})"
        # Bare precision: .N
        m = re.fullmatch(r"\.(\d+)", spec)
        if m:
            return f"fmt_float({inner_cpp}, {m.group(1)})"
        # Zero-padded int: 0Nd
        m = re.fullmatch(r"0(\d+)d", spec)
        if m:
            return f"fmt_int_pad({inner_cpp}, {m.group(1)}, '0')"
        # Width-padded int: Nd
        m = re.fullmatch(r"(\d+)d", spec)
        if m:
            return f"fmt_int_pad({inner_cpp}, {m.group(1)}, ' ')"
        # Alignment: >N, <N, ^N
        m = re.fullmatch(r"([<>^])(\d+)", spec)
        if m:
            return f"fmt_align({inner_cpp}, {m.group(2)}, '{m.group(1)}')"
        # Batch 9b: empty spec -> same as no spec.
        if spec == "":
            return f"is_to_string({inner_cpp})"
        # Batch 9b: string precision .Ns -> truncate to N chars.
        m = re.fullmatch(r"\.(\d+)s", spec)
        if m:
            return f"str_truncate({inner_cpp}, {m.group(1)})"
        # Batch 9b: integer base conversions.
        if spec == "x":
            return f"fmt_int_base({inner_cpp}, 16, false)"
        if spec == "X":
            return f"fmt_int_base({inner_cpp}, 16, true)"
        if spec == "o":
            return f"fmt_int_base({inner_cpp}, 8, false)"
        if spec == "b":
            return f"fmt_int_base({inner_cpp}, 2, false)"
        # Batch 9b: comma thousands separator.
        if spec == ",":
            return f"fmt_int_comma({inner_cpp})"
        raise TranspileError(
            f"Unsupported f-string format spec: ':{spec}'. "
            f"Supported: .Nf, .N, Nd, 0Nd, >N, <N, ^N, N.Mf, "
            f".Ns, x, X, o, b, ','."
        )

    def _container_kind(self, node):
        """Batch 13b: return 'list' | 'set' | 'dict' | 'tuple' | None.

        Like _container_repr but reports the kind without emitting
        code, so callers can decide whether to wrap a subexpression.
        Recurses through BinOp (list + list, set algebra) and
        Subscript-with-Slice over a tracked list.
        """
        if isinstance(node, ast.List):
            return "list"
        if isinstance(node, ast.Dict):
            return "dict"
        if isinstance(node, ast.Set):
            return "set"
        if isinstance(node, ast.Tuple):
            return "tuple"
        if isinstance(node, ast.Name):
            if node.id in self.list_vars:
                return "list"
            if node.id in self.dict_vars:
                return "dict"
            if node.id in self.set_vars:
                return "set"
            if node.id in self.tuple_vars:
                return "tuple"
        if isinstance(node, ast.BinOp):
            lk = self._container_kind(node.left)
            rk = self._container_kind(node.right)
            if isinstance(node.op, ast.Add) and lk == "list" and rk == "list":
                return "list"
            if isinstance(node.op,
                          (ast.BitOr, ast.BitAnd, ast.Sub, ast.BitXor)) \
               and lk == "set" and rk == "set":
                return "set"
        if isinstance(node, ast.Subscript) \
           and isinstance(node.value, ast.Name) \
           and node.value.id in self.list_vars \
           and isinstance(node.slice, ast.Slice):
            return "list"
        # Batch 13b.1: source-level calls that return containers.
        # We match on the *source* name — the AST for "a,b,c".split(",")
        # has func=ast.Attribute(attr="split"), not func=ast.Name.
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "split":
                    return "list"
            if isinstance(node.func, ast.Name):
                # str.split as a free call is unusual but harmless to allow.
                if node.func.id == "split":
                    return "list"
        return None

    def _container_repr(self, node, emitted: str):
        """Batch 10a: return a repr_X(...) call for a container expr, else None.

        Handles both literals (ast.List/Dict/Set/Tuple) and Names that
        are tracked in list_vars / dict_vars / set_vars / tuple_vars.
        Extended in Batch 13b to binops, slices and calls.
        """
        # Literal containers.
        if isinstance(node, ast.List):
            return f"repr_vector({emitted})"
        if isinstance(node, ast.Dict):
            return f"repr_map({emitted})"
        if isinstance(node, ast.Set):
            return f"repr_set({emitted})"
        if isinstance(node, ast.Tuple):
            return f"repr_tuple({emitted})"
        # Name lookups.
        if isinstance(node, ast.Name):
            if node.id in self.list_vars:
                return f"repr_vector({emitted})"
            if node.id in self.dict_vars:
                return f"repr_map({emitted})"
            if node.id in self.set_vars:
                return f"repr_set({emitted})"
            if node.id in self.tuple_vars:
                arity = self.tuple_vars[node.id]
                if arity == 2:
                    return f"repr_pair({emitted})"
                return f"repr_tuple({emitted})"
        # Batch 13b: binops, slices, calls that yield containers.
        kind = self._container_kind(node)
        if kind == "list":
            return f"repr_vector({emitted})"
        if kind == "set":
            return f"repr_set({emitted})"
        if kind == "dict":
            return f"repr_map({emitted})"
        if kind == "tuple":
            return f"repr_tuple({emitted})"
        return None

    def _check_name(self, name: str, context: str):
        """Reject C++ reserved words used as identifiers."""
        if name in CPP_RESERVED:
            raise TranspileError(
                f"{context} '{name}' is a reserved C++ keyword and "
                f"cannot be used as a name. Please rename it."
            )

    def _class_of_expr(self, node):
        """Return the user-class name of an expression node, or None.

        Handles (Batch 8b/8c):
          - Name in instance_vars -> its class
          - ClassName(...) where ClassName is a user class
          - BinOp(Add, L, R) where _class_of_expr(L) ==
            _class_of_expr(R) != None (recurses, so nested
            adds like `a + b + c` work)
        """
        if isinstance(node, ast.Name):
            return self.instance_vars.get(node.id)
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in self.user_classes):
            return node.func.id
        if (isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Add)):
            _lcls = self._class_of_expr(node.left)
            _rcls = self._class_of_expr(node.right)
            if _lcls is not None and _lcls == _rcls:
                return _lcls

        # Batch 10k.2: `self.field` reads inside a method body — look
        # up the field type from the enclosing class.
        if (isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
                and self._current_class):
            ftype = self.class_field_types.get(
                self._current_class, {}).get(node.attr)
            if ftype is not None and ftype in self.user_classes:
                return ftype
        return None

    def _is_int_expr(self, node) -> bool:
        """True if `node` will emit as an integer-typed C++ expression.

        Used by the `/` handler to decide whether to cast to double
        (Python true division) or emit as-is.
        """
        if isinstance(node, ast.Constant):
            return isinstance(node.value, int) and not isinstance(
                node.value, bool)
        if isinstance(node, ast.Name):
            # Tracked int variables. `list_vars`/`dict_vars` are
            # containers; `instance_vars` are user classes. If the
            # name isn't tracked as any of those, or as a known
            # float, treat it as int (matches Kofty's existing
            # "unannotated = int-ish" convention).
            if node.id in self.list_vars:
                return False
            if node.id in self.dict_vars:
                return False
            if node.id in self.set_vars:
                return False
            if node.id in self.tuple_vars:
                return False
            if node.id in self.instance_vars:
                return False
            return True
        if isinstance(node, ast.BinOp):
            # A BinOp produces an int if both sides are int and the
            # operator is int-preserving (+ - * // % & | ^).
            if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult,
                                     ast.FloorDiv, ast.Mod,
                                     ast.BitAnd, ast.BitOr, ast.BitXor)):
                return (self._is_int_expr(node.left)
                        and self._is_int_expr(node.right))
            # Division, power, etc. produce float.
            return False
        if isinstance(node, ast.UnaryOp):
            # -x, +x, ~x preserve int-ness of the operand. `not` is bool.
            if isinstance(node.op, (ast.USub, ast.UAdd, ast.Invert)):
                return self._is_int_expr(node.operand)
            return False
        # Anything else (Call, Subscript, IfExp, ...) — assume not int,
        # so we don't cast unless we're sure.
        return False

    # ---- helpers ---------------------------------------------------------
    def emit(self, line: str):
        self.lines.append("    " * self.indent + line)

    def expr(self, node: ast.AST) -> str:
        """Convert a Python expression node to a C++ expression string."""
        if isinstance(node, ast.Constant):
            if node.value is None:
                return "nullptr"
            if isinstance(node.value, str):
                # Escape quotes/backslashes for C++ string literal
                s = node.value.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{s}"'
            if isinstance(node.value, bool):
                return "true" if node.value else "false"
            if isinstance(node.value, (int, float)):
                return repr(node.value)
            raise TranspileError(f"Unsupported constant: {node.value!r}")

        if isinstance(node, ast.Name):
            # Batch 25: reject names that aren't bound anywhere in the
            # source. Lenient (whole-file analysis): a name used before
            # it's assigned is allowed, matching Python's behavior for
            # module-level forward references.
            _nm = node.id
            if (
                _nm not in _BUILTIN_NAMES
                and _nm not in self.all_bound_names
                and _nm not in self.user_funcs
                and _nm not in self.user_classes
                and _nm not in self.declared
                and _nm not in self.instance_vars
                and _nm not in self.global_vars
                and _nm not in self.lambda_vars
            ):
                raise TranspileError(f"name '{_nm}' is not defined")
            return node.id
        if isinstance(node, ast.JoinedStr):
            # f-string: JoinStr values are Constant (literal text)
            # or FormattedValue (an embedded expression).
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    s = str(v.value).replace("\\", "\\\\")
                    s = s.replace('"', '\\"')
                    parts.append(f'std::string("{s}")')
                elif isinstance(v, ast.FormattedValue):
                    if v.conversion != -1:
                        raise TranspileError(
                            "f-string conversions (e.g. {x!r}) "
                            "are not supported yet."
                        )
                    inner_cpp = self.expr(v.value)
                    # Batch 9a: parse format_spec if present.
                    _spec = self._parse_format_spec(v.format_spec)

                    if _spec is None:
                        # Batch 10i: if the inner expression is a user-class
                        # instance, dispatch to its __str__() method instead of
                        # calling is_to_string (which has no overload for user
                        # classes).
                        _cls = self._class_of_expr(v.value)
                        if _cls is not None and _cls in self.str_classes:
                            parts.append(f"{inner_cpp}.__str__()")
                        else:
                            parts.append(f"is_to_string({inner_cpp})")
                    else:
                        parts.append(
                        self._emit_format_spec(inner_cpp, _spec)
                    )

                else:
                    raise TranspileError(
                        f"Unsupported f-string part: {v!r}"
                    )
            if not parts:
                return 'std::string("")'
            return "(" + " + ".join(parts) + ")"

        if isinstance(node, ast.Lambda):
            # Batch 5d: lambda -> C++ lambda.
            #   lambda x: x * 2    -> [&](auto x) { return x * 2; }
            #   lambda a, b: a+b   -> [&](auto a, auto b) { return a+b; }
            #   lambda: 42         -> [&]() { return 42; }
            # Captures all outer variables by reference ([&]).
            # Params are untyped (auto). Body is a single expression.
            if node.args.defaults or node.args.vararg or node.args.kwarg:
                raise TranspileError(
                    "lambda does not support default args, *args, "
                    "or **kwargs in this build."
                )
            param_names = [a.arg for a in node.args.args]
            params_cpp = ", ".join(f"auto {p}" for p in param_names)
            body_cpp = self.expr(node.body)
            return f"[&]({params_cpp}) {{ return {body_cpp}; }}"

        if isinstance(node, ast.IfExp):
            # Ternary: a if cond else b
            # C++ ternary requires compatible types across branches;
            # mixing types (e.g. int and str) is a compile error.
            test_cpp = self.expr(node.test)
            body_cpp = self.expr(node.body)
            orelse_cpp = self.expr(node.orelse)
            return f"(({test_cpp}) ? ({body_cpp}) : ({orelse_cpp}))"

        if isinstance(node, ast.BinOp):
            op = self._binop(node.op)
            left = self.expr(node.left)
            right = self.expr(node.right)

            # Batch 8c: T + T for user classes (Option a).
            # Both operands must be Names in instance_vars and
            # the same class, and that class must define __add__.
            if (isinstance(node.op, ast.Add)
                    and isinstance(node.left, ast.Name)
                    and isinstance(node.right, ast.Name)
                    and node.left.id in self.instance_vars
                    and node.right.id in self.instance_vars):
                _lcls = self.instance_vars[node.left.id]
                _rcls = self.instance_vars[node.right.id]
                if _lcls != _rcls:
                    raise TranspileError(
                        f"__add__ across classes not supported: "
                        f"{_lcls} + {_rcls}"
                    )
                if _lcls not in self.add_classes:
                    raise TranspileError(
                        f"{_lcls} + {_rcls} requires {_lcls} "
                        f"to define __add__"
                    )
                return f"({node.left.id} + {node.right.id})"

            # ** -> std::pow (always returns double)
            if isinstance(node.op, ast.Pow):
                return f"std::pow({left}, {right})"
            # // -> floor division with correct sign handling
            if isinstance(node.op, ast.FloorDiv):
                return f"is_floordiv({left}, {right})"

            # Batch 10l: `/` is Python true division. C++ `/` on two
            # ints truncates. Cast both sides to double when both
            # operands are int-typed.
            if isinstance(node.op, ast.Div):
                if (self._is_int_expr(node.left)
                        and self._is_int_expr(node.right)):
                    return f"((double){left} / (double){right})"
                return f"({left} / {right})"

            # String repetition: str * int  or  int * str.
            # Python: "=" * 40 -> 40 equals signs.
            if isinstance(node.op, ast.Mult):
                left_is_str = self._is_string_expr(node.left)
                right_is_str = self._is_string_expr(node.right)
                left_is_int_lit = (
                    isinstance(node.left, ast.Constant)
                    and isinstance(node.left.value, int)
                    and not isinstance(node.left.value, bool)
                )
                right_is_int_lit = (
                    isinstance(node.right, ast.Constant)
                    and isinstance(node.right.value, int)
                    and not isinstance(node.right.value, bool)
                )
                if left_is_str and right_is_int_lit:
                    return f"str_repeat({left}, {right})"
                if right_is_str and left_is_int_lit:
                    return f"str_repeat({right}, {left})"

            # Set operations: |, &, -, ^ between two known set vars or literals.
            if isinstance(node.op, (ast.BitOr, ast.BitAnd, ast.Sub, ast.BitXor)):
                if self._is_set_expr(node.left) and self._is_set_expr(node.right):
                    left_s = self._emit_set_expr(node.left, left)
                    right_s = self._emit_set_expr(node.right, right)
                    if isinstance(node.op, ast.BitOr):
                        return f"set_op_union({left_s}, {right_s})"
                    if isinstance(node.op, ast.BitAnd):
                        return f"set_op_intersection({left_s}, {right_s})"
                    if isinstance(node.op, ast.Sub):
                        return f"set_op_difference({left_s}, {right_s})"
                    if isinstance(node.op, ast.BitXor):
                        return f"set_op_symdiff({left_s}, {right_s})"

            # List concat: if both sides are known lists and op is +,
            # use vec_concat.
            if isinstance(node.op, ast.Add):
                left_is_list = (isinstance(node.left, ast.Name)
                                and node.left.id in self.list_vars)
                right_is_list = (isinstance(node.right, ast.Name)
                                 and node.right.id in self.list_vars)
                if left_is_list and right_is_list:
                    return f"vec_concat({left}, {right})"

            # vec2 arithmetic: if both sides are vec2 vars (or a vec2 var
            # and a scalar), emit a helper call instead of raw C++.
            left_is_vec2 = (isinstance(node.left, ast.Name)
                            and node.left.id in self.vec2_vars)
            right_is_vec2 = (isinstance(node.right, ast.Name)
                             and node.right.id in self.vec2_vars)

            if left_is_vec2 and right_is_vec2:
                if isinstance(node.op, ast.Add):
                    return f"vec2_add({left}, {right})"
                if isinstance(node.op, ast.Sub):
                    return f"vec2_sub({left}, {right})"

            # vec2 * scalar or scalar * vec2
            if isinstance(node.op, ast.Mult):
                if left_is_vec2 and not right_is_vec2:
                    return f"vec2_scale({left}, {right})"
                if right_is_vec2 and not left_is_vec2:
                    return f"vec2_scale({right}, {left})"

            # Special case: if either side of `+` is a string, wrap both
            # in std::string(...) so C++ performs string concatenation
            # rather than failing on const char* arithmetic.
            if isinstance(node.op, ast.Add) and (
                self._is_string_expr(node.left) or
                self._is_string_expr(node.right)
            ):
                left = self._as_std_string(node.left, left)
                right = self._as_std_string(node.right, right)
            return f"({left} {op} {right})"

        if isinstance(node, ast.BoolOp):
            op = self._boolop(node.op)
            parts = [self.expr(v) for v in node.values]
            return "(" + f" {op} ".join(parts) + ")"

        if isinstance(node, ast.UnaryOp):
            op = self._unaryop(node.op)
            return f"({op}{self.expr(node.operand)})"

        if isinstance(node, ast.Compare):
            # Only support single comparisons for now (a < b), not chains.
            if len(node.ops) != 1:
                raise TranspileError("Chained comparisons are not supported.")

            # `x in xs` / `x not in xs` — membership test on a known list.
            cmp_op = node.ops[0]
            right_node = node.comparators[0]
            if isinstance(cmp_op, (ast.In, ast.NotIn)):
                left_cpp = self.expr(node.left)

                # `k in d` / `k not in d` for dicts
                if (isinstance(right_node, ast.Name)
                        and right_node.id in self.dict_vars):
                    d_name = right_node.id
                    inner = f"{d_name}.count({left_cpp}) > 0"
                    if isinstance(cmp_op, ast.In):
                        return f"({inner})"
                    else:
                        return f"(!({inner}))"

                # `x in s` / `x not in s` for sets
                if (isinstance(right_node, ast.Name)
                        and right_node.id in self.set_vars):
                    s_name = right_node.id
                    inner = f"{s_name}.count({left_cpp}) > 0"
                    if isinstance(cmp_op, ast.In):
                        return f"({inner})"
                    else:
                        return f"(!({inner}))"

                # `x in xs` / `x not in xs` for lists
                if (isinstance(right_node, ast.Name)
                        and right_node.id in self.list_vars):
                    list_name = right_node.id
                    inner = (
                        f"std::find({list_name}.begin(), {list_name}.end(), "
                        f"{left_cpp}) != {list_name}.end()"
                    )
                    if isinstance(cmp_op, ast.In):
                        return f"({inner})"
                    else:
                        return f"(!({inner}))"

                raise TranspileError(
                    "`in` / `not in` only supported on known list, dict, "
                    "or set variables for now."
                )

            left = self.expr(node.left)
            # `is` / `is not` — Python's identity comparison. We map to
            # C++ == and != (used mainly for `is None` checks).
            cmp_op = node.ops[0]
            right_node = node.comparators[0]

            # `x is None` / `x is not None` on an optional var
            is_none_cmp = (
                isinstance(cmp_op, (ast.Is, ast.IsNot))
                and isinstance(right_node, ast.Constant)
                and right_node.value is None
            )
            if is_none_cmp and isinstance(node.left, ast.Name):
                if node.left.id in self.optional_vars:
                    if isinstance(cmp_op, ast.Is):
                        return f"(!{left}.has_value())"
                    else:
                        return f"({left}.has_value())"

            if isinstance(cmp_op, ast.Is):
                op = "=="
            elif isinstance(cmp_op, ast.IsNot):
                op = "!="
            else:
                op = self._cmpop(cmp_op)
            right = self.expr(right_node)
            return f"({left} {op} {right})"

        if isinstance(node, ast.Call):
            return self._call_expr(node)

        if isinstance(node, ast.Attribute):
            # Batch 7a: math.pi, math.e.
            if (isinstance(node.value, ast.Name)
                    and node.value.id == "math"
                    and node.attr in ("pi", "e")):
                if "math" not in self.imported_modules:
                    raise TranspileError(
                        f"math.{node.attr} used without `import math`."
                    )
                if node.attr == "pi":
                    return "3.141592653589793"
                return "2.718281828459045"

            # self.x  →  this->x
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                # Batch 8d: self.prop -> this->prop() when prop is a
                # @property on the enclosing class.
                if (self._current_class
                        and node.attr in self.property_getters.get(
                            self._current_class, set())):
                    return f"this->{node.attr}()"
                return f"this->{node.attr}"
                        # Pointer field read: p.x  →  p->x
            if (isinstance(node.value, ast.Name)
                    and node.value.id in self.pointer_vars):
                return f"{node.value.id}->{node.attr}"
            # Instance field read: obj.field → obj.field  (identical in C++)
            # Counter.count (class attribute)  →  Counter::count
            if (isinstance(node.value, ast.Name)
                    and node.value.id in self.user_classes):
                return f"{node.value.id}::{node.attr}"
            # Batch 8d: obj.prop -> obj.prop() when prop is a @property.
            _objcls = self._class_of_expr(node.value)
            if _objcls is None and (isinstance(node.value, ast.Name)
                    and node.value.id == "self"
                    and self._current_class):
                _objcls = self._current_class
            if (_objcls is not None
                    and node.attr in self.property_getters.get(_objcls, set())):
                _inner = self.expr(node.value)
                return f"{_inner}.{node.attr}()"
            obj = self.expr(node.value)
            return f"{obj}.{node.attr}"

        if isinstance(node, ast.Tuple):
            # 2-element tuples -> std::pair; N>=3 -> std::tuple.
            n = len(node.elts)
            if n < 2:
                raise TranspileError(
                    f"Tuples must have at least 2 elements; got {n}."
                )
            parts = [self.expr(e) for e in node.elts]
            if n == 2:
                return f"std::make_pair({parts[0]}, {parts[1]})"
            return f"std::make_tuple({', '.join(parts)})"

        if isinstance(node, ast.List):
            # Literal lists only. Element types supported:
            #   scalars         → std::vector<T>
            #   tuples (N >= 2) → std::vector<std::pair<..>> (N=2)
            #                     or std::vector<std::tuple<..>> (N>=3)
            # Empty lists and nested lists are rejected.
            if len(node.elts) == 0:
                raise TranspileError(
                    "empty list literals are not supported (no type to "
                    "infer). Add at least one element."
                )

            def _unwrap_sign(elt):
                if (isinstance(elt, ast.UnaryOp)
                        and isinstance(elt.op, (ast.USub, ast.UAdd))):
                    return elt.operand
                return elt

            def _scalar_cpp(n):
                n = _unwrap_sign(n)
                if not isinstance(n, ast.Constant):
                    raise TranspileError(
                        "List-of-tuple elements must be scalar literals."
                    )
                v = n.value
                if isinstance(v, bool):
                    return "bool"
                if isinstance(v, int):
                    return "int"
                if isinstance(v, float):
                    return "double"
                if isinstance(v, str):
                    return "std::string"
                raise TranspileError(
                    f"Unsupported tuple element: {v!r}"
                )

            # List of tuples: first element is a tuple literal.
            if isinstance(node.elts[0], ast.Tuple):
                _t0 = node.elts[0]
                if len(_t0.elts) < 2:
                    raise TranspileError(
                        "List-of-tuple elements must have arity >= 2; "
                        f"got {len(_t0.elts)}."
                    )
                _elem_arity = len(_t0.elts)
                _elem_types = tuple(_scalar_cpp(e) for e in _t0.elts)
                for elt in node.elts[1:]:
                    if (not isinstance(elt, ast.Tuple)
                            or len(elt.elts) != _elem_arity):
                        raise TranspileError(
                            f"All list elements must be {_elem_arity}-tuples "
                            f"of the same element types."
                        )
                    this_types = tuple(_scalar_cpp(e) for e in elt.elts)
                    if this_types != _elem_types:
                        raise TranspileError(
                            "List-of-tuple elements must have the same "
                            "types across the list."
                        )
                if _elem_arity == 2:
                    _elem_cpp = f"std::pair<{_elem_types[0]}, {_elem_types[1]}>"
                else:
                    _elem_cpp = ("std::tuple<"
                                 + ", ".join(_elem_types) + ">")
                tuples_cpp = []
                for elt in node.elts:
                    inner = ", ".join(self.expr(e) for e in elt.elts)
                    tuples_cpp.append(f"{_elem_cpp}{{{inner}}}")
                return (
                    f"std::vector<{_elem_cpp}>{{"
                    + ", ".join(tuples_cpp) + "}"
                )

            # Scalar list: infer a single element type.
            has_float = False
            has_int = False
            has_str = False
            for elt in node.elts:
                inner = _unwrap_sign(elt)
                if isinstance(inner, ast.Constant):
                    if isinstance(inner.value, bool):
                        raise TranspileError(
                            "Lists of booleans are not supported yet."
                        )
                    if isinstance(inner.value, float):
                        has_float = True
                    elif isinstance(inner.value, int):
                        has_int = True
                    elif isinstance(inner.value, str):
                        has_str = True
                    else:
                        raise TranspileError(
                            f"Unsupported list element: {inner.value!r}"
                        )
                else:
                    raise TranspileError(
                        "List elements must be literals for now "
                        "(no variables, no expressions)."
                    )
            if has_str and (has_int or has_float):
                raise TranspileError(
                    "Lists cannot mix strings with numbers."
                )
            if has_str:
                elem_type = "std::string"
            elif has_float:
                elem_type = "double"
            else:
                elem_type = "int"
            elts_cpp = ", ".join(self.expr(e) for e in node.elts)
            return f"std::vector<{elem_type}>{{{elts_cpp}}}"

        if isinstance(node, ast.Dict):
            if len(node.keys) == 0:
                raise TranspileError(
                    "empty dict literals are not supported (no value "
                    "type to infer). Add at least one entry."
                )
            # Validate: all keys must be string literals
            for k in node.keys:
                if not (isinstance(k, ast.Constant)
                        and isinstance(k.value, str)):
                    raise TranspileError(
                        "Dict keys must be string literals for now."
                    )
            # Infer value type from first value (recursive for nested dicts).
            def _infer_dict_value_type(val_node):
                    if isinstance(val_node, ast.Constant):
                        v = val_node.value
                        if isinstance(v, bool): return "bool"
                        if isinstance(v, int): return "int"
                        if isinstance(v, float): return "double"
                        if isinstance(v, str): return "std::string"
                        return None
                    if isinstance(val_node, ast.UnaryOp):
                        if isinstance(val_node.operand, ast.Constant):
                            v = val_node.operand.value
                            if isinstance(v, int): return "int"
                            if isinstance(v, float): return "double"
                        return None
                    if isinstance(val_node, ast.Dict):
                        if len(val_node.values) == 0:
                            return None
                        inner_t = _infer_dict_value_type(val_node.values[0])
                        if inner_t is None:
                            return None
                        return f"std::map<std::string, {inner_t}>"
                    # Batch 11c.3: dict values that are tuples.
                    if isinstance(val_node, ast.Tuple) and len(val_node.elts) >= 2:
                        def _scalar_cpp(n):
                            if isinstance(n, ast.UnaryOp):
                                n = n.operand
                            v = n.value
                            if isinstance(v, bool): return "bool"
                            if isinstance(v, int): return "int"
                            if isinstance(v, float): return "double"
                            if isinstance(v, str): return "std::string"
                            return None
                        _types = []
                        for e in val_node.elts:
                            t = _scalar_cpp(e)
                            if t is None:
                                return None
                            _types.append(t)
                        if len(_types) == 2:
                            return f"std::pair<{_types[0]}, {_types[1]}>"
                        return "std::tuple<" + ", ".join(_types) + ">"
                    return None

            first_val = node.values[0]
            val_type = _infer_dict_value_type(first_val)
            if val_type is None:
                raise TranspileError(
                    f"Unsupported dict value type in {ast.unparse(first_val)}."
                )
            # All other values must be same type (skip full check for nested)
            for val in node.values[1:]:
                this_type = _infer_dict_value_type(val)
                if this_type is not None and this_type != val_type:
                    raise TranspileError(
                        f"Dict values must all be the same type. "
                        f"First value is {val_type}, but found {this_type}."
                    )
            # Emit the map literal
            pairs = []
            for k, val in zip(node.keys, node.values):
                k_cpp = self.expr(k)
                v_cpp = self.expr(val)
                pairs.append(f"{{{k_cpp}, {v_cpp}}}")
            pairs_str = ", ".join(pairs)
            return f"std::map<std::string, {val_type}>{{{pairs_str}}}"

        if isinstance(node, ast.Set):
            # Set literal: {1, 2, 3} -> std::set<int>{1, 2, 3}
            if len(node.elts) == 0:
                raise TranspileError(
                    "empty set literals are not supported. "
                    "Use `set()` or add at least one element."
                )

            def _unwrap_sign_set(elt):
                if (isinstance(elt, ast.UnaryOp)
                        and isinstance(elt.op, (ast.USub, ast.UAdd))):
                    return elt.operand
                return elt

            has_float = False
            has_int = False
            has_str = False
            for elt in node.elts:
                inner = _unwrap_sign_set(elt)
                if isinstance(inner, ast.Constant):
                    v = inner.value
                    if isinstance(v, bool):
                        raise TranspileError(
                            "Sets of booleans are not supported yet."
                        )
                    if isinstance(v, float):
                        has_float = True
                    elif isinstance(v, int):
                        has_int = True
                    elif isinstance(v, str):
                        has_str = True
                    else:
                        raise TranspileError(
                            f"Unsupported set element: {v!r}"
                        )
                else:
                    raise TranspileError(
                        "Set elements must be literals for now."
                    )
            if has_str and (has_int or has_float):
                raise TranspileError(
                    "Sets cannot mix strings with numbers."
                )
            if has_str:
                elem_type = "std::string"
            elif has_float:
                elem_type = "double"
            else:
                elem_type = "int"
            elts_cpp = ", ".join(self.expr(e) for e in node.elts)
            return f"std::set<{elem_type}>{{{elts_cpp}}}"

        if isinstance(node, ast.Subscript):
            # Distinguish list indexing from tuple indexing:
            #   - If the target is a known list variable → C++ `[]` operator
            #   - Otherwise → tuple `.first`/`.second` (0 or 1 only)
            target_name = None
            if isinstance(node.value, ast.Name):
                target_name = node.value.id

            if target_name is not None and target_name in self.list_vars:
                # Slice: xs[a:b] -> std::vector<T>(xs.begin()+a, xs.begin()+b)
                if isinstance(node.slice, ast.Slice):
                    if (isinstance(node.slice.step, ast.Constant)
                            and node.slice.step.value is not None):
                        raise TranspileError(
                            "Slice with step is not supported yet."
                        )
                    start = ("0" if node.slice.lower is None
                             else self.expr(node.slice.lower))
                    if node.slice.upper is None:
                        end = f"{target_name}.size()"
                    else:
                        end = self.expr(node.slice.upper)
                    return (
                        f"std::vector<int>({target_name}.begin() + {start}, "
                        f"{target_name}.begin() + {end})"
                    )
                # Negative literal index: xs[-1] -> xs[xs.size() - 1]
                if (isinstance(node.slice, ast.UnaryOp)
                        and isinstance(node.slice.op, ast.USub)
                        and isinstance(node.slice.operand, ast.Constant)):
                    n = node.slice.operand.value
                    return f"{target_name}[{target_name}.size() - {n}]"
                # List: any integer index expression is allowed
                idx = self.expr(node.slice)
                return f"{target_name}[{idx}]"

            # Dict access: d["key"] → d["key"]
            if target_name is not None and target_name in self.dict_vars:
                idx = self.expr(node.slice)
                return f"{target_name}[{idx}]"

            # Nested dict access: d["a"]["x"]
            # If the value is itself a subscript whose inner target is a
            # known dict var, emit the whole chain as-is.
            if (isinstance(node.value, ast.Subscript)
                    and isinstance(node.value.value, ast.Name)
                    and node.value.value.id in self.dict_vars):
                inner_cpp = self.expr(node.value)
                idx = self.expr(node.slice)
                return f"{inner_cpp}[{idx}]"

            # Tuple: literal index required.
            if not isinstance(node.slice, ast.Constant):
                raise TranspileError(
                    "Tuple index must be a literal number."
                )
            idx = node.slice.value
            # N>=3 tuple variable -> std::get<N>(var)
            if (target_name is not None
                    and target_name in self.tuple_vars
                    and self.tuple_vars[target_name] >= 3):
                return f"std::get<{idx}>({target_name})"
            # 2-element pair (literal or variable) -> .first/.second
            if idx == 0:
                return f"{self.expr(node.value)}.first"
            if idx == 1:
                return f"{self.expr(node.value)}.second"
            raise TranspileError(
                f"Tuple index must be 0 or 1 for 2-tuples; got {idx}."
            )

        raise TranspileError(f"Unsupported expression: {ast.dump(node)}")

    def _binop(self, op):
        return {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*",
            ast.Pow: "**",  # not reached from expr(); expr() intercepts
            ast.Div: "/", ast.FloorDiv: "/", ast.Mod: "%",
            ast.BitOr: "|", ast.BitAnd: "&", ast.BitXor: "^",
        }.get(type(op)) or self._fail("binary operator", op)

    def _infer_field_type(self, value_node: ast.AST) -> str:
        """Infer the C++ type of a class field from the value assigned to it.
        Returns "int" as a safe fallback when the type can't be determined.
        """
        # Literal values
        if isinstance(value_node, ast.Constant):
            v = value_node.value
            if isinstance(v, bool):
                return "bool"
            if isinstance(v, int):
                return "int"
            if isinstance(v, float):
                return "double"
            if isinstance(v, str):
                return "std::string"
            return "int"
        # vec2(x, y) call → std::pair<double, double>
        if (isinstance(value_node, ast.Call)
                and isinstance(value_node.func, ast.Name)
                and value_node.func.id == "vec2"):
            return "std::pair<double, double>"
        # List literal → std::vector<T>
        if isinstance(value_node, ast.List):
            if len(value_node.elts) == 0:
                return "int"  # can't infer element type
            has_float = False
            has_str = False
            for elt in value_node.elts:
                if isinstance(elt, ast.Constant):
                    if isinstance(elt.value, float):
                        has_float = True
                    elif isinstance(elt.value, str):
                        has_str = True
            if has_str:
                return "std::vector<std::string>"
            if has_float:
                return "std::vector<double>"
            return "std::vector<int>"
        # Everything else — variables, method calls, etc. → fallback
        return "int"

    def _detect_super_init(self, init_method: ast.FunctionDef):
        """Check if the first statement of __init__ is `super().__init__(args)`.
        Returns (args_as_cpp, body_without_super_call) or (None, body).

        Enforces the rule: super().__init__() must be the FIRST statement.
        """
        if not init_method.body:
            return None, init_method.body

        first = init_method.body[0]

        # Look for `super().__init__(...)` as an Expr statement
        if not isinstance(first, ast.Expr):
            return None, init_method.body
        if not isinstance(first.value, ast.Call):
            return None, init_method.body

        call = first.value
        if not isinstance(call.func, ast.Attribute):
            return None, init_method.body
        if call.func.attr != "__init__":
            return None, init_method.body
        if not isinstance(call.func.value, ast.Call):
            return None, init_method.body
        if not (isinstance(call.func.value.func, ast.Name)
                and call.func.value.func.id == "super"):
            return None, init_method.body

        # Found super().__init__(...). Extract args.
        args_cpp = [self.expr(a) for a in call.args]
        body_without_super = init_method.body[1:]

        # Check the rest of the body doesn't also call super().__init__
        for stmt in body_without_super:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                s_call = stmt.value
                if (isinstance(s_call.func, ast.Attribute)
                        and s_call.func.attr == "__init__"
                        and isinstance(s_call.func.value, ast.Call)
                        and isinstance(s_call.func.value.func, ast.Name)
                        and s_call.func.value.func.id == "super"):
                    raise TranspileError(
                        "super().__init__() must be the first statement "
                        "in __init__, not repeated elsewhere."
                    )

        return args_cpp, body_without_super

    def _detect_multiple_parent_inits(self, init_method: ast.FunctionDef,
                                       class_name: str,
                                       bases: list):
        """For multiple inheritance, expect the first N statements of
        __init__ to be `ParentName.__init__(self, args)` calls, in the
        same order as `bases`.

        Returns (init_list_cpp, body_without_parent_calls).

        `init_list_cpp` is a list of strings like "Walkable(name)" that
        go into the C++ initializer list.
        """
        # Special case: if the first statement is super().__init__(...),
        # give a specific error — super() is ambiguous with multiple parents.
        if init_method.body:
            first = init_method.body[0]
            if (isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Call)
                    and isinstance(first.value.func, ast.Attribute)
                    and first.value.func.attr == "__init__"
                    and isinstance(first.value.func.value, ast.Call)
                    and isinstance(first.value.func.value.func, ast.Name)
                    and first.value.func.value.func.id == "super"):
                raise TranspileError(
                    f"super().__init__() is not allowed in a class with "
                    f"multiple parents ('{class_name}'). Use explicit "
                    f"`Parent.__init__(self, ...)` calls for each parent: "
                    f"{', '.join(bases)}."
                )

        # Look at the first len(bases) statements
        if len(init_method.body) < len(bases):
            raise TranspileError(
                f"Class '{class_name}' must call each parent's __init__ "
                f"explicitly. It inherits from {len(bases)} parents "
                f"({', '.join(bases)}) but its __init__ has fewer than "
                f"{len(bases)} statements. "
                f"Add `{bases[len(init_method.body)]}.__init__(self, ...)` "
                f"as the next statement."
            )

        calls_found = []
        for i in range(len(bases)):
            stmt = init_method.body[i]
            if not isinstance(stmt, ast.Expr):
                raise TranspileError(
                    f"Statement {i+1} of {class_name}.__init__ must be a "
                    f"call to `{bases[i]}.__init__(self, ...)`."
                )
            call = stmt.value
            if not isinstance(call, ast.Call):
                raise TranspileError(
                    f"Statement {i+1} of {class_name}.__init__ must be a call."
                )
            if not isinstance(call.func, ast.Attribute):
                raise TranspileError(
                    f"Statement {i+1} of {class_name}.__init__ must call "
                    f"a parent constructor."
                )
            if call.func.attr != "__init__":
                raise TranspileError(
                    f"Statement {i+1} of {class_name}.__init__ must be a "
                    f"__init__ call. Got: .{call.func.attr}"
                )
            # The object of the call must be a Name (the parent class name)
            if not isinstance(call.func.value, ast.Name):
                raise TranspileError(
                    f"Statement {i+1} of {class_name}.__init__ must call "
                    f"`ParentName.__init__(self, ...)`."
                )
            parent_called = call.func.value.id

            if parent_called != bases[i]:
                raise TranspileError(
                    f"Class '{class_name}' parent __init__ calls must be in "
                    f"the same order as the base classes in the class "
                    f"declaration. Expected '{bases[i]}' at statement {i+1}, "
                    f"got '{parent_called}'."
                )

            # First argument must be `self`
            if len(call.args) < 1 or not (
                    isinstance(call.args[0], ast.Name)
                    and call.args[0].id == "self"):
                raise TranspileError(
                    f"`{parent_called}.__init__` first argument must be `self`."
                )

            # Remaining args go into the C++ initializer list
            rest_args = [self.expr(a) for a in call.args[1:]]
            calls_found.append(f"{parent_called}({', '.join(rest_args)})")

        body_without_parents = init_method.body[len(bases):]
        return calls_found, body_without_parents

    def _annot_to_cpp_type(self, annotation) -> str:
        """Map a Python type annotation AST node to a C++ type string.
        Returns "int" when there's no annotation or an unknown one.
        """
        if annotation is None:
            return "int"
        if isinstance(annotation, ast.Name):
            mapping = {
                "int": "int",
                "float": "double",
                "str": "std::string",
                "bool": "bool",
            }

            if annotation.id in mapping:
                return mapping[annotation.id]
            # Batch 10j: user-class annotation (e.g. `p: Point`).
            # Emit the class name directly.
            if annotation.id in self.user_classes:
                return annotation.id
            # Unknown annotation -> fall back to int (unchanged
            # behavior for anything the transpiler doesn't know).
            return "int"
        return "int"

    def _infer_default_type(self, node: ast.AST) -> str:
        """Infer the C++ type of a parameter from its default value.

        Used for `def f(a, b=10)`: we need an explicit type for `b`
        because C++ rejects `auto b = 10` in a parameter list (and
        `auto` params can't have defaults anyway).

        Supported default value shapes:
            int literal     -> int
            float literal   -> double
            str literal     -> std::string
            bool literal    -> bool
            negative number -> type of the unary operand
        """
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, bool):
                return "bool"
            if isinstance(v, int):
                return "int"
            if isinstance(v, float):
                return "double"
            if isinstance(v, str):
                return "std::string"
            if v is None:
                raise TranspileError(
                    "default value None is not supported yet."
                )
        if isinstance(node, ast.UnaryOp):
            # Negative numbers parse as UnaryOp(USub, Constant(5)).
            return self._infer_default_type(node.operand)
        raise TranspileError(
            f"Unsupported default value: {ast.dump(node)}. "
            f"Only literal defaults (int, float, str, bool) are "
            f"supported."
        )

    def _method_return_type(self, method: ast.FunctionDef, has_return: bool):
        """Determine the C++ return type and virtual keyword for a method.

        Returns (ret_type, virtual_kw).

        Rules:
          - `-> ReturnType` (Name annotation)   → concrete type, virtual
          - `-> None` (Constant None)           → void, virtual
          - No annotation + has return          → auto, NOT virtual
          - No annotation + no return           → void, virtual
        """
        # `-> None` → void
        if (isinstance(method.returns, ast.Constant)
                and method.returns.value is None):
            return "void", "virtual "
        # `-> int` / `-> float` / etc.
        if isinstance(method.returns, ast.Name):
            cpp = self._annot_to_cpp_type(method.returns)
            return cpp, "virtual "
        # No annotation
        if has_return:
            return "auto", ""
        return "void", "virtual "

    # -----------------------------------------------------------------
    # Batch 13d.2: infer a concrete return type for methods that have
    # no annotation but a `return <expr>` body. Used only for base-class
    # methods, since `virtual auto` is invalid C++.
    # -----------------------------------------------------------------

    def _infer_method_return_type(self, method: ast.FunctionDef):
        """Infer a concrete C++ return type for an unannotated method.

        Returns a C++ type string, or None if the return type cannot
        be determined consistently. Only inspects `return <expr>`
        statements; `return` with no value is treated as void.
        """
        seen = set()
        for stmt in ast.walk(method):
            if not isinstance(stmt, ast.Return):
                continue
            if stmt.value is None:
                seen.add("void")
                continue
            t = self._infer_expr_type(stmt.value)
            if t is None:
                return None
            seen.add(t)
        # No return statements at all -> caller treats has_return=False.
        if not seen:
            return None
        if len(seen) != 1:
            # Mixed return types -> can't unify. Give up.
            return None
        return seen.pop()

    def _infer_expr_type(self, node: ast.AST):
        """Conservative C++ type inference for a single expression.

        Returns a C++ type string, or None if the type cannot be
        determined. Does NOT recurse into user-function return types
        (avoids infinite loops) — only inspects annotations.
        """
        # Literals
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, bool):
                return "bool"
            if isinstance(v, int):
                return "int"
            if isinstance(v, float):
                return "double"
            if isinstance(v, str):
                return "std::string"
            if v is None:
                return "void"
            return None
        # vec2(x, y) -> std::pair<double, double>
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "vec2"):
            return "std::pair<double, double>"
        # List literal
        if isinstance(node, ast.List):
            if len(node.elts) == 0:
                return None
            has_str = any(isinstance(e, ast.Constant)
                          and isinstance(e.value, str) for e in node.elts)
            has_float = any(isinstance(e, ast.Constant)
                            and isinstance(e.value, float) for e in node.elts)
            if has_str:
                return "std::vector<std::string>"
            if has_float:
                return "std::vector<double>"
            return "std::vector<int>"
        # Tuple literal -> pair (2-element) or tuple (3+)
        if isinstance(node, ast.Tuple):
            elts = [self._infer_expr_type(e) for e in node.elts]
            if len(elts) < 2 or any(t is None for t in elts):
                return None
            if len(elts) == 2:
                return f"std::pair<{elts[0]}, {elts[1]}>"
            return f"std::tuple<{', '.join(elts)}>"
        # self.<field> read
        if (isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
                and self.current_class is not None):
            field_types = self.class_field_types.get(self.current_class, {})
            if node.attr in field_types:
                return field_types[node.attr]
            return None
        # BinOp — addition / subtraction / multiplication / division
        if isinstance(node, ast.BinOp):
            lt = self._infer_expr_type(node.left)
            rt = self._infer_expr_type(node.right)
            if isinstance(node.op, ast.Add):
                # str + anything -> str
                if lt == "std::string" or rt == "std::string":
                    return "std::string"
            if lt is None or rt is None:
                return None
            # Arithmetic on numbers
            numeric = {"int", "double", "float"}
            if lt in numeric and rt in numeric:
                if lt == "double" or rt == "double":
                    return "double"
                if lt == "float" or rt == "float":
                    return "double"  # Kofty treats float as double
                return "int"
            return None
        # Name — only infer if it's a known constant-ish var. Conservative:
        # we don't track variable types at method-emission time, so skip.
        return None

    def _is_string_expr(self, node: ast.AST) -> bool:
        """Return True if the expression is known to produce a string."""
        # String literal
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        # str(...) call — always produces a string
        if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'str':
            return True
        # f-strings always produce a string.
        if isinstance(node, ast.JoinedStr):
            return True
        # .format() on a string literal produces a string.
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "format"
                and isinstance(node.func.value, ast.Constant)
                and isinstance(node.func.value.value, str)):
            return True
        # Nested string concatenation: `("a" + b) + c` — if either
        # operand is a string, the whole BinOp is a string.
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return (self._is_string_expr(node.left)
                    or self._is_string_expr(node.right))
        return False

    def _is_set_expr(self, node):
        """True if `node` is a known set variable or a set literal."""
        if isinstance(node, ast.Name):
            return node.id in self.set_vars
        if isinstance(node, ast.Set):
            return True
        return False

    def _emit_set_expr(self, node, already_emitted):
        """Emit a set expression: a Name as-is, or a literal wrapped in
        std::set<int>{...}. Element type is inferred as int for this batch."""
        if isinstance(node, ast.Name):
            return already_emitted
        if isinstance(node, ast.Set):
            elems = ", ".join(self.expr(e) for e in node.elts)
            return f"std::set<int>{{{elems}}}"
        raise TranspileError(f"Unsupported set expression: {type(node).__name__}")

    def _as_std_string(self, node: ast.AST, cpp_expr: str) -> str:
        """Ensure the emitted C++ is a std::string.

        Only string LITERALS need explicit wrapping — everything else was
        already handled by expr() (str() emits std::to_string() which
        returns a std::string).
        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return f"std::string({cpp_expr})"
        return cpp_expr

    def _boolop(self, op):
        return {
            ast.And: "&&", ast.Or: "||",
        }.get(type(op)) or self._fail("boolean operator", op)

    def _unaryop(self, op):
        return {
            ast.USub: "-", ast.UAdd: "+", ast.Not: "!",
        }.get(type(op)) or self._fail("unary operator", op)

    def _cmpop(self, op):
        return {
            ast.Eq: "==", ast.NotEq: "!=",
            ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">=",
        }.get(type(op)) or self._fail("comparison operator", op)

    def _fail(self, what, node):
        raise TranspileError(f"Unsupported {what}: {ast.dump(node)}")

    def _emit_format(self, node: ast.Call) -> str:
        """Emit a .format() call on a string literal.

        Parses the format string at emit time, splitting into
        literal text and {N} / {} placeholders. Produces a
        concatenation of std::string literals and is_to_string()
        calls.
        """
        import re
        fmt = node.func.value.value
        args = [self.expr(a) for a in node.args]

        parts = []
        pos = 0
        auto_idx = 0
        for m in re.finditer(r"\{(\d*)\}", fmt):
            if m.start() > pos:
                text = fmt[pos:m.start()]
                text = text.replace("\\", "\\\\")
                text = text.replace('"', '\\"')
                parts.append(f'std::string("{text}")')
            idx_str = m.group(1)
            if idx_str == "":
                idx = auto_idx
                auto_idx += 1
            else:
                idx = int(idx_str)
            if idx >= len(args):
                raise TranspileError(
                    f"format() index {{{idx}}} out of range; "
                    f"got {len(args)} arg(s)"
                )
            parts.append(f"is_to_string({args[idx]})")
            pos = m.end()
        if pos < len(fmt):
            text = fmt[pos:]
            text = text.replace("\\", "\\\\")
            text = text.replace('"', '\\"')
            parts.append(f'std::string("{text}")')

        if not parts:
            return 'std::string("")'
        return "(" + " + ".join(parts) + ")"

    def _call_expr(self, node: ast.Call) -> str:
        """Emit a function call. Handles builtins and user functions."""
        # Batch 8e: inside a @classmethod body, `cls(...)` -> `Class(...)`
        # and `cls.method(...)` -> `Class::method(...)`.
        if self._classmethod_param:
            if (isinstance(node.func, ast.Name)
                    and node.func.id == self._classmethod_param):
                _cargs = [self.expr(a) for a in node.args]
                return f"{self._current_class}({', '.join(_cargs)})"
            if (isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == self._classmethod_param):
                _cargs = [self.expr(a) for a in node.args]
                return (f"{self._current_class}::{node.func.attr}"
                        f"({', '.join(_cargs)})")
        # Instance method call: obj.method(args) → obj.method(args)
                # Method call: obj.method(args) → obj.method(args)
        # Special case: self.method(args) → this->method(args)
                # Method call: obj.method(args)
        # Special cases: self.method(...) → this->method(...)
        #                list.append(x)  → list.push_back(x)
        # Reject bare super() calls — they must be `super().__init__(...)`
        # Reject bare super() (not followed by .method(...))
        # super().method(...) is handled below in the attribute-call branch.
        if isinstance(node.func, ast.Name) and node.func.id == "super":
            raise TranspileError(
                "super() must be followed by a method call, e.g. "
                "super().__init__(...) or super().method(...)"
            )
        # enumerate() and zip() are only meaningful as for-loop iterables.
        if (isinstance(node.func, ast.Name)
                and node.func.id in ("enumerate", "zip")):
            raise TranspileError(
                f"{node.func.id}() is only supported as the iterable "
                f"of a for-loop, e.g. `for i, x in {node.func.id}(...)`."
            )
        if isinstance(node.func, ast.Attribute):
            # Batch 7a: math.X(...) -> std::X(...).
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "math"):
                if "math" not in self.imported_modules:
                    raise TranspileError(
                        f"math.{node.func.attr} used without `import math`."
                    )
                _MATH = {
                    "sqrt":  "std::sqrt",
                    "pow":   "std::pow",
                    "sin":   "std::sin",
                    "cos":   "std::cos",
                    "tan":   "std::tan",
                    "floor": "std::floor",
                    "ceil":  "std::ceil",
                    "fabs":  "std::fabs",
                    "exp":   "std::exp",
                    "log":   "std::log",
                }
                if node.func.attr not in _MATH:
                    raise TranspileError(
                        f"math.{node.func.attr} is not supported yet."
                    )
                _math_args = [self.expr(a) for a in node.args]
                return f"{_MATH[node.func.attr]}({', '.join(_math_args)})"

            # Batch 7b: random.X(...) -> rand_* helper calls.
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "random"):
                if "random" not in self.imported_modules:
                    raise TranspileError(
                        f"random.{node.func.attr} used without "
                        f"`import random`."
                    )
                _rnd_args = [self.expr(a) for a in node.args]
                _rnd_name = node.func.attr
                if _rnd_name == "random" and len(_rnd_args) == 0:
                    return "rand_float()"
                if _rnd_name == "randint" and len(_rnd_args) == 2:
                    return f"rand_int({_rnd_args[0]}, {_rnd_args[1]})"
                if _rnd_name == "choice" and len(_rnd_args) == 1:
                    return f"rand_choice({_rnd_args[0]})"
                if _rnd_name == "shuffle" and len(_rnd_args) == 1:
                    # shuffle is a statement-like call; emit as
                    # expression statement `rand_shuffle(xs);`
                    return f"rand_shuffle({_rnd_args[0]})"
                if _rnd_name == "seed" and len(_rnd_args) == 1:
                    return f"rand_seed({_rnd_args[0]})"
                raise TranspileError(
                    f"random.{_rnd_name} is not supported yet "
                    f"(or called with wrong argument count)."
                )

            # Batch 7c: time.X(...) -> time_* helpers.
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "time"):
                if "time" not in self.imported_modules:
                    raise TranspileError(
                        f"time.{node.func.attr} used without "
                        f"`import time`."
                    )
                _t_args = [self.expr(a) for a in node.args]
                _t_name = node.func.attr
                if _t_name == "time" and len(_t_args) == 0:
                    return "time_now()"
                if _t_name == "sleep" and len(_t_args) == 1:
                    return f"time_sleep({_t_args[0]})"
                raise TranspileError(
                    f"time.{_t_name} is not supported yet "
                    f"(or called with wrong argument count)."
                )

            args = [self.expr(a) for a in node.args]

            # super().method(args) → Parent::method(args)
            if (isinstance(node.func.value, ast.Call)
                    and isinstance(node.func.value.func, ast.Name)
                    and node.func.value.func.id == "super"):
                method_name = node.func.attr
                bases = self.class_bases.get(self.current_class, [])
                if not bases:
                    raise TranspileError(
                        f"super().{method_name}() called outside of a subclass."
                    )
                if len(bases) > 1:
                    raise TranspileError(
                        f"super().{method_name}() is not allowed in a class "
                        f"with multiple parents ('{self.current_class}'). "
                        f"Use ParentClass.{method_name}() explicitly."
                    )
                parent = bases[0]
                parent_methods = self.class_methods.get(parent, set())
                if method_name not in parent_methods:
                    raise TranspileError(
                        f"super().{method_name}() called but parent class "
                        f"'{parent}' has no method '{method_name}'."
                    )
                args_str = ", ".join(args)
                return f"{parent}::{method_name}({args_str})"

            # Pointer method call: p.method(args) → p->method(args)
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id in self.pointer_vars):
                args_str = ", ".join(args)
                return f"{node.func.value.id}->{node.func.attr}({args_str})"

            # Dict methods: only when target is a known dict var
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id in self.dict_vars):
                dname = node.func.value.id
                dmethod = node.func.attr

                if dmethod == "get":
                    if len(args) < 1 or len(args) > 2:
                        raise TranspileError(
                            f"get() takes 1 or 2 arguments, got {len(args)}"
                        )
                    inner_type = self.dict_vars[dname]
                    if len(args) == 2:
                        default = args[1]
                    else:
                        # Default to zero/empty based on inner type
                        if inner_type == "int":
                            default = "0"
                        elif inner_type == "double":
                            default = "0.0"
                        elif inner_type == "bool":
                            default = "false"
                        elif inner_type == "std::string":
                            default = 'std::string()'
                        else:
                            default = f"{inner_type}()"
                    return (
                        f"({dname}.count({args[0]}) ? "
                        f"{dname}[{args[0]}] : {default})"
                    )

                if dmethod == "pop":
                    if len(args) != 1:
                        raise TranspileError(
                            f"pop() takes exactly 1 argument, got {len(args)}"
                        )
                    # Wrap string-literal keys in std::string so template
                    # deduction for dict_pop<K, V> is unambiguous.
                    key_arg = args[0]
                    if (isinstance(node.args[0], ast.Constant)
                            and isinstance(node.args[0].value, str)):
                        key_arg = f"std::string({key_arg})"
                    return f"dict_pop({dname}, {key_arg})"

                if dmethod == "update":
                    if len(args) != 1:
                        raise TranspileError(
                            f"update() takes exactly 1 argument, got {len(args)}"
                        )
                    return f"{dname}.insert({args[0]}.begin(), {args[0]}.end())"

                if dmethod == "clear":
                    if len(args) != 0:
                        raise TranspileError(
                            f"clear() takes no arguments, got {len(args)}"
                        )
                    return f"{dname}.clear()"

                if dmethod == "keys":
                    if len(args) != 0:
                        raise TranspileError(
                            f"keys() takes no arguments, got {len(args)}"
                        )
                    # Keys are used in for-loops; a bare call isn't a value.
                    # Return a marker that only visit_For knows how to use.
                    return f"__dict_keys({dname})"

                if dmethod == "values":
                    if len(args) != 0:
                        raise TranspileError(
                            f"values() takes no arguments, got {len(args)}"
                        )
                    return f"__dict_values({dname})"

                if dmethod == "items":
                    if len(args) != 0:
                        raise TranspileError(
                            f"items() takes no arguments, got {len(args)}"
                        )
                    return f"__dict_items({dname})"

            # Set methods: only when target is a known set var
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id in self.set_vars):
                sname = node.func.value.id
                smethod = node.func.attr

                if smethod == "add":
                    if len(args) != 1:
                        raise TranspileError(
                            f"add() takes exactly 1 argument, got {len(args)}"
                        )
                    return f"{sname}.insert({args[0]})"

                if smethod in ("remove", "discard"):
                    if len(args) != 1:
                        raise TranspileError(
                            f"{smethod}() takes exactly 1 argument, got {len(args)}"
                        )
                    return f"{sname}.erase({args[0]})"

                if smethod == "clear":
                    if len(args) != 0:
                        raise TranspileError(
                            f"clear() takes no arguments, got {len(args)}"
                        )
                    return f"{sname}.clear()"

            # List append: xs.append(x) → xs.push_back(x)
            if (node.func.attr == "append"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in self.list_vars):
                if len(args) != 1:
                    raise TranspileError(
                        f"append() takes exactly 1 argument, got {len(args)}"
                    )
                return f"{node.func.value.id}.push_back({args[0]})"

            # List methods: only when target is a known list var
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id in self.list_vars):
                list_name = node.func.value.id
                method = node.func.attr

                if method == "insert":
                    if len(args) != 2:
                        raise TranspileError(
                            f"insert() takes exactly 2 arguments, got {len(args)}"
                        )
                    return f"{list_name}.insert({list_name}.begin() + {args[0]}, {args[1]})"

                if method == "remove":
                    if len(args) != 1:
                        raise TranspileError(
                            f"remove() takes exactly 1 argument, got {len(args)}"
                        )
                    return (
                        f"{list_name}.erase(std::find({list_name}.begin(), "
                        f"{list_name}.end(), {args[0]}))"
                    )

                if method == "sort":
                    if len(args) != 0:
                        raise TranspileError(
                            f"sort() takes no arguments, got {len(args)}"
                        )
                    return f"std::sort({list_name}.begin(), {list_name}.end())"

                if method == "reverse":
                    if len(args) != 0:
                        raise TranspileError(
                            f"reverse() takes no arguments, got {len(args)}"
                        )
                    return f"std::reverse({list_name}.begin(), {list_name}.end())"

                if method == "clear":
                    if len(args) != 0:
                        raise TranspileError(
                            f"clear() takes no arguments, got {len(args)}"
                        )
                    return f"{list_name}.clear()"

                if method == "pop":
                    if len(args) == 0:
                        # Batch 8f: pop() removes AND returns the last
                        # element. vec_pop(v) is a template helper.
                        return f"vec_pop({list_name})"
                    if len(args) == 1:
                        # Batch 8g: pop(i) removes AND returns the
                        # element at index i. Negative indices work
                        # via the helper.
                        return f"vec_pop_at({list_name}, {args[0]})"
                    raise TranspileError(
                        f"pop() takes 0 or 1 arguments, got {len(args)}"
                    )

            # ---- String methods ----------------------------------
            # Dispatch on method name. Safe because no other type
            # in InterScript currently has methods with these names.
            # Receiver is coerced to std::string to handle string
            # literals and concatenations uniformly.
            _sm = node.func.attr
            _recv = self._as_std_string(node.func.value,
                                        self.expr(node.func.value))
            if _sm == "upper" and not args:
                return f"str_toupper({_recv})"
            if _sm == "lower" and not args:
                return f"str_tolower({_recv})"
            if _sm == "strip" and not args:
                return f"str_strip({_recv})"
            if _sm == "lstrip" and not args:
                return f"str_lstrip({_recv})"
            if _sm == "rstrip" and not args:
                return f"str_rstrip({_recv})"
            if _sm == "startswith" and len(args) == 1:
                return f"str_startswith({_recv}, {args[0]})"
            if _sm == "endswith" and len(args) == 1:
                return f"str_endswith({_recv}, {args[0]})"
            if _sm == "replace" and len(args) == 2:
                return f"str_replace({_recv}, {args[0]}, {args[1]})"
            if _sm == "split" and len(args) == 1:
                return f"str_split({_recv}, {args[0]})"
            if _sm == "join" and len(args) == 1:
                return f"str_join({_recv}, {args[0]})"
            if _sm == "find" and len(args) == 1:
                return f"str_find({_recv}, {args[0]})"
            if _sm == "count" and len(args) == 1:
                return f"str_count({_recv}, {args[0]})"
            # Batch 10c: four more string methods.
            if _sm == "title" and not args:
                return f"str_title({_recv})"
            if _sm == "capitalize" and not args:
                return f"str_capitalize({_recv})"
            if _sm == "isalpha" and not args:
                return f"str_isalpha({_recv})"
            if _sm == "isdigit" and not args:
                return f"str_isdigit({_recv})"

            # ---- .format() on a string receiver -----------------
            # Batch 2b: literal receivers.
            # Batch 11a: variable receivers whose literal was captured
            # at assignment time. Untracked names raise.
            if (isinstance(node.func, ast.Attribute)
                    and node.func.attr == "format"):
                recv = node.func.value
                if (isinstance(recv, ast.Constant)
                        and isinstance(recv.value, str)):
                    return self._emit_format(node)
                if (isinstance(recv, ast.Name)
                        and recv.id in self.str_literal_vars):
                    lit = self.str_literal_vars[recv.id]
                    synth = ast.Call(
                        func=ast.Attribute(
                            value=ast.Constant(value=lit),
                            attr="format",
                            ctx=ast.Load(),
                        ),
                        args=node.args,
                        keywords=node.keywords,
                    )
                    ast.fix_missing_locations(synth)
                    return self._emit_format(synth)
                if isinstance(recv, ast.Name):
                    raise TranspileError(
                        f".format() on variable '{recv.id}' requires "
                        f"'{recv.id}' to be initialized from a string "
                        f"literal earlier in the same scope"
                    )

            # self.method(...) → this->method(...)
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"):
                return f"this->{node.func.attr}({', '.join(args)})"

            # ⬇⬇⬇ ADD THIS NEW BLOCK RIGHT HERE ⬇⬇⬇
            # Batch 8e: obj.classmethod(args) -> Class::classmethod(args).
            # Python allows calling a classmethod through an instance;
            # C++ requires the class name for a static member function.
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id in self.instance_vars):
                _objcls = self.instance_vars[node.func.value.id]
                if node.func.attr in self.classmethod_names.get(_objcls, set()):
                    return (f"{_objcls}::{node.func.attr}"
                            f"({', '.join(args)})")

            # Static method call: ClassName.method(args) → ClassName::method(args)
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id in self.user_classes):
                return f"{node.func.value.id}::{node.func.attr}({', '.join(args)})"
            # ⬆⬆⬆ END OF NEW BLOCK ⬆⬆⬆

            # Pointer-list element method call: shapes[i].method() → shapes[i]->method()
            if (isinstance(node.func.value, ast.Subscript)
                    and isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id in self.pointer_list_vars):
                sub_cpp = self.expr(node.func.value)
                args_str = ", ".join(args)
                return f"{sub_cpp}->{node.func.attr}({args_str})"

            # Pointer-list element method call: shapes[i].method() → shapes[i]->method()
            if (isinstance(node.func.value, ast.Subscript)
                    and isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id in self.pointer_list_vars):
                sub_cpp = self.expr(node.func.value)
                args_str = ", ".join(args)
                return f"{sub_cpp}->{node.func.attr}({args_str})"

            # Generic: obj.method(...) → obj.method(...)
            obj = self.expr(node.func.value)
            return f"{obj}.{node.func.attr}({', '.join(args)})"

        if not isinstance(node.func, ast.Name):
            raise TranspileError("Unsupported call expression.")
        name = node.func.id

        # Batch 5c: if the callee has a **kwargs param, intercept the
        # empty-dict arg BEFORE self.expr runs on it (empty dict
        # literals are not supported otherwise). A non-empty dict
        # argument already emits as std::map and needs no fixup.
        if name in self.func_kwargs and node.args:
            value_type = self.func_kwargs[name]
            args = []
            last_i = len(node.args) - 1
            for i, a in enumerate(node.args):
                if (i == last_i
                        and isinstance(a, ast.Dict)
                        and len(a.keys) == 0):
                    args.append(
                        f"std::map<std::string, {value_type}>{{}}"
                    )
                else:
                    args.append(self.expr(a))
        elif name in self.func_varargs:
            # Batch 13d: wrap all trailing positional args into a single
            # std::vector<T>{...} at the call site. Leading args (before
            # the vararg) stay positional.
            elem_type = self.func_varargs[name]
            leading = self.func_vararg_leading.get(name, 0)
            leading_cpp = [self.expr(a) for a in node.args[:leading]]
            rest_cpp = [self.expr(a) for a in node.args[leading:]]
            if rest_cpp:
                vec_cpp = (
                    f"std::vector<{elem_type}>{{{', '.join(rest_cpp)}}}"
                )
            else:
                vec_cpp = f"std::vector<{elem_type}>{{}}"
            args = leading_cpp + [vec_cpp]
        else:
            args = [self.expr(a) for a in node.args]

        # Special case: print() has variadic args and emits a stream expression.
        if name == "print":
            # Batch 17: allow multiple arguments, join with spaces.
            # Each arg goes through the same dispatch as single-arg
            # print (class __str__, container repr, or raw stream).
            if len(args) == 0:
                return 'std::cout << "" << std::endl'
            parts = []
            for i, a in enumerate(node.args):
                expr_cpp = args[i]
                # User class -> __str__()
                _pcls = self._class_of_expr(a)
                if _pcls is not None:
                    if _pcls not in self.str_classes:
                        raise TranspileError(
                            f"print(<{_pcls}>) requires {_pcls} "
                            f"to define __str__"
                        )
                    if isinstance(a, ast.BinOp):
                        expr_cpp = f"({expr_cpp})"
                    parts.append(f"{expr_cpp}.__str__()")
                    continue
                # Container -> repr_X()
                _prepr = self._container_repr(a, expr_cpp)
                if _prepr is not None:
                    parts.append(_prepr)
                    continue
                # Scalar -> is_to_string
                parts.append(f"is_to_string({expr_cpp})")
            return (
                "std::cout << "
                + ' << " " << '.join(parts)
                + " << std::endl"
            )

        # Batch 12: input() reads a line from stdin.
        #   input()          -> input_line("")
        #   input(prompt)    -> input_line("prompt")
        if name == "input":
            if len(args) == 0:
                return 'input_line("")'
            if len(args) == 1:
                return f"input_line({args[0]})"
            raise TranspileError(
                f"input() takes 0 or 1 argument, got {len(args)}"
            )

        # Special case: str() converts a value to a string.
        # Works on number literals, variables (assumed numeric for now),
        # and expressions. String literals pass through unchanged.
        if name == "str":
            if len(args) != 1:
                raise TranspileError(
                    f"str() takes exactly 1 argument, got {len(args)}"
                )
            # If the argument is already a string literal, return it as-is.
            if (isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                return args[0]
            # Batch 8b/8c: str(obj) or str(a + b) -> __str__().
            _scls = self._class_of_expr(node.args[0])
            if _scls is not None:
                if _scls not in self.str_classes:
                    raise TranspileError(
                        f"str(<{_scls}>) requires {_scls} "
                        f"to define __str__"
                    )
                _sinner = args[0]
                if isinstance(node.args[0], ast.BinOp):
                    _sinner = f"({_sinner})"
                return f"{_sinner}.__str__()"
            # Batch 10a: str(container) -> repr_X(...)
            _srepr = self._container_repr(node.args[0], args[0])
            if _srepr is not None:
                return _srepr
            # If the argument is an optional var, unwrap with .value()
            if (isinstance(node.args[0], ast.Name)
                    and node.args[0].id in self.optional_vars):
                return f"format_float({args[0]}.value())"
            return f"format_float({args[0]})"
                # Special case: int(x) → C-style cast to int
        if name == "int":
            if len(args) != 1:
                raise TranspileError(
                    f"int() takes exactly 1 argument, got {len(args)}"
                )
            # Batch 15: parse std::string via std::stoi.
            # Cases that produce a string: input() call, a Name
            # (variable holding user input). Numeric literals and
            # arithmetic expressions keep the C-style cast.
            if (isinstance(node.args[0], ast.Call)
                    and isinstance(node.args[0].func, ast.Name)
                    and node.args[0].func.id == "input"):
                return f"std::stoi({args[0]})"
            if (isinstance(node.args[0], ast.Name)
                    and node.args[0].id in self.string_vars):
                return f"std::stoi({args[0]})"
            if (isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                return f"std::stoi({args[0]})"
            return f"(int){args[0]}"
        # Special case: float(x) → C-style cast to double
        if name == "float":
            if len(args) != 1:
                raise TranspileError(
                    f"float() takes exactly 1 argument, got {len(args)}"
                )
            # Batch 15: parse std::string via std::stod.
            if (isinstance(node.args[0], ast.Call)
                    and isinstance(node.args[0].func, ast.Name)
                    and node.args[0].func.id == "input"):
                return f"std::stod({args[0]})"
            if (isinstance(node.args[0], ast.Name)
                    and node.args[0].id in self.string_vars):
                return f"std::stod({args[0]})"
            if (isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                return f"std::stod({args[0]})"
            return f"(double){args[0]}"

        # ---- Batch 29: constructor functions ---------------------------------
        if name == "bool":
            if len(args) != 1:
                raise TranspileError(
                    f"bool() takes exactly 1 argument, got {len(args)}"
                )
            return f"(bool)({args[0]})"

        if name == "list":
            if len(args) != 1:
                raise TranspileError(
                    "list() requires exactly 1 argument in this build. "
                    "Supported: list((a, b, c)) or list([a, b, c]) or "
                    "list(xs) where xs is a list variable."
                )
            arg = node.args[0]
            if isinstance(arg, ast.Tuple):
                # Rewrap as a list literal so the existing ast.List
                # emitter handles element types uniformly.
                if len(arg.elts) == 0:
                    raise TranspileError(
                        "list(()) requires element types; use a "
                        "non-empty tuple or list literal."
                    )
                synthetic = ast.List(elts=arg.elts, ctx=ast.Load())
                return self.expr(synthetic)
            # List literal, list variable, or slice — pass through.
            return self.expr(arg)

        if name == "tuple":
            if len(args) != 1:
                raise TranspileError(
                    "tuple() requires exactly 1 argument in this build. "
                    "Supported: tuple((a, b)) or tuple([a, b]) where the "
                    "argument is a 2-element or 3+-element iterable."
                )
            arg = node.args[0]
            if isinstance(arg, ast.List):
                if len(arg.elts) < 2:
                    raise TranspileError(
                        "tuple(...) requires at least 2 elements."
                    )
                synthetic = ast.Tuple(elts=arg.elts, ctx=ast.Load())
                return self.expr(synthetic)
            # Tuple literal or name — pass through.
            return self.expr(arg)

        if name == "set":
            if len(args) != 1:
                raise TranspileError(
                    "set() requires exactly 1 argument in this build. "
                    "Supported: set((a, b, c)) or set([a, b, c]) or "
                    "set(xs) where xs is a set variable."
                )
            arg = node.args[0]
            if isinstance(arg, (ast.Tuple, ast.List)):
                if len(arg.elts) == 0:
                    raise TranspileError(
                        "set() from an empty literal requires a set "
                        "variable: use `set()` is not supported yet."
                    )
                synthetic = ast.Set(elts=arg.elts)
                return self.expr(synthetic)
            # Set variable or other — pass through.
            return self.expr(arg)

        if name == "dict":
            if len(args) != 1:
                raise TranspileError(
                    "dict() with 0 arguments is not supported "
                    "(no key/value types to infer). "
                    "dict(**kwargs) is not supported yet. "
                    "Supported: dict({...}) with a dict literal."
                )
            arg = node.args[0]
            if not isinstance(arg, ast.Dict):
                raise TranspileError(
                    "dict(...) requires a dict literal argument in this "
                    "build. Supported: dict({\"k\": v, ...})."
                )
            return self.expr(arg)

        # Special case: ptr(ClassName(args)) → new ClassName(args)
        # Creates a heap-allocated pointer to a class instance.
        if name == "ptr":
            if len(args) != 1:
                raise TranspileError(
                    f"ptr() takes exactly 1 argument, got {len(args)}"
                )
            inner = node.args[0]
            if not isinstance(inner, ast.Call):
                raise TranspileError(
                    "ptr() argument must be a class constructor call, "
                    "e.g. ptr(Circle(2.0))."
                )
            if not (isinstance(inner.func, ast.Name)
                    and inner.func.id in self.user_classes):
                raise TranspileError(
                    f"ptr() argument must be a call to a known class. "
                    f"Got: {ast.unparse(inner)}"
                )
            class_name = inner.func.id
            inner_args = [self.expr(a) for a in inner.args]
            return f"new {class_name}({', '.join(inner_args)})"

        # Special case: len(xs) → xs.size()
        if name == "len":
            if len(args) != 1:
                raise TranspileError(
                    f"len() takes exactly 1 argument, got {len(args)}"
                )
            # Assume the argument is a list/vector variable
            return f"{args[0]}.size()"

        # Special case: vec2(x, y) → std::pair<double, double>
        # Values are always cast to double so vec2 arithmetic stays
        # in floating-point, matching the intent of positions/velocities.
        if name == "vec2":
            if len(args) != 2:
                raise TranspileError(
                    f"vec2() takes exactly 2 arguments, got {len(args)}"
                )
            return f"std::make_pair((double){args[0]}, (double){args[1]})"
        # Special case: draw_text needs its first arg coerced to const char*.
        if name == "draw_text":
            if len(args) != 7:
                raise TranspileError(
                    f"draw_text() expects 7 args, got {len(args)}"
                )
            text_arg = self._to_c_string(node.args[0], args[0])
            return (
                f"DrawText({text_arg}, {args[1]}, {args[2]}, "
                f"{args[3]}, (Color){{{args[4]}, {args[5]}, {args[6]}, 255}});"
            )

        # Special case: measure_text needs its first arg coerced to const char*
        # for the same reason draw_text does — raylib's MeasureText takes
        # const char*, not std::string.
        if name == "measure_text":
            if len(args) != 2:
                raise TranspileError(
                    f"measure_text() expects 2 args, got {len(args)}"
                )
            text_arg = self._to_c_string(node.args[0], args[0])
            return f"MeasureText({text_arg}, {args[1]})"
        # Special case: rects_overlap() emits an inline AABB overlap check.
        # Two rectangles A(ax,ay,aw,ah) and B(bx,by,bw,bh) overlap iff:
        #   A.x < B.x + B.w  AND  A.x + A.w > B.x
        #   A.y < B.y + B.h  AND  A.y + A.h > B.y
        if name == "rects_overlap":
            if len(args) != 8:
                raise TranspileError(
                    f"rects_overlap() expects 8 args, got {len(args)}"
                )
            ax, ay, aw, ah, bx, by, bw, bh = args
            return (
                f"({ax} < ({bx} + {bw}) && ({ax} + {aw}) > {bx} && "
                f"{ay} < ({by} + {bh}) && ({ay} + {ah}) > {by})"
            )
        if name in CORE_BUILTINS or name in RAYLIB_BUILTINS:
            table = CORE_BUILTINS if name in CORE_BUILTINS else RAYLIB_BUILTINS
            arity, template = table[name]
            if len(args) != arity:
                raise TranspileError(
                    f"{name}() expects {arity} args, got {len(args)}"
                )
            return template.format(*args)

        if name in self.user_funcs or name in self.lambda_vars:
            return f"{name}({', '.join(args)})"

        raise TranspileError(f"Unknown function: {name}()")

    # ---- statements ------------------------------------------------------
    def visit_Expr(self, node: ast.Expr):
        """A bare expression statement — usually a function call."""
        if isinstance(node.value, ast.Call):
            code = self._call_expr(node.value)
            if not code.endswith(";"):
                code += ";"
            self.emit(code)
            return
        # Batch 18: bare string literal (Python docstring idiom) is a
        # no-op. Accept it silently.
        if (isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            return
        raise TranspileError("Only function-call expressions are allowed as statements.")

    def _to_c_string(self, node: ast.AST, cpp_expr: str) -> str:
        """
        Raylib's DrawText takes `const char*`. Plain C++ string literals
        ("hello") already are const char*. Anything else (a std::string
        from concatenation or from std::to_string) needs .c_str().
        """
        # Plain string literal → no conversion needed.
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return cpp_expr
        # Anything else → wrap in a temporary std::string and call .c_str()
        return f"std::string({cpp_expr}).c_str()"

    def visit_Assign(self, node: ast.Assign):
        # Batch 20: chained assignment `a = b = c = value`.
        # Python evaluates RHS once and assigns to each target.
        # We expand to multiple single-target assignments sharing
        # the same value node. Safe for literal RHS; may double-
        # evaluate a side-effectful RHS (documented).
        if len(node.targets) > 1:
            for target in node.targets:
                sub = ast.Assign(targets=[target], value=node.value)
                ast.fix_missing_locations(sub)
                self.visit_Assign(sub)
            return
        if len(node.targets) != 1:
            raise TranspileError("Multiple assignment targets are not supported.")
        target = node.targets[0]

        # Case 1: simple name target — `x = value`
        if isinstance(target, ast.Name):
            name = target.id

        # Case 1: simple name target — `x = value`
        if isinstance(target, ast.Name):
            name = target.id
            self._check_name(name, "Variable name")
            # Track tuple arity so subscript dispatch knows pair vs tuple.
            if isinstance(node.value, ast.Tuple):
                self.tuple_vars[name] = len(node.value.elts)
            # Batch 11b: `t = make()` where make returns a known-arity tuple.
            elif (isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id in self.func_return_arity):
                self.tuple_vars[name] = self.func_return_arity[
                    node.value.func.id
                ]

            # Optional variable: `x = None` then later `x = 5`
            if name in self.optional_vars:
                inner = self.optional_vars[name]
                if name not in self.declared:
                    self.emit(f"std::optional<{inner}> {name};")
                    self.declared.add(name)
                # Assign the value (None -> std::nullopt)
                if (isinstance(node.value, ast.Constant)
                        and node.value.value is None):
                    self.emit(f"{name} = std::nullopt;")
                else:
                    self.emit(f"{name} = {self.expr(node.value)};")
                return

            # Variable assigned the result of an optional-returning call.
            # `result = find(...)` where find returns std::optional<T>
            # makes result itself optional.
            if (isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id in self.optional_funcs):
                if name not in self.declared:
                    inner_type = self.optional_func_types.get(
                        node.value.func.id, "int"
                    )
                    self.emit(f"std::optional<{inner_type}> {name};")
                    self.declared.add(name)
                    self.optional_vars[name] = inner_type
                    self.use_optional = True
                self.emit(f"{name} = {self.expr(node.value)};")
                return

            # Batch 8b/8c: register `x = <class-instance expr>`.
            # `_class_of_expr` handles ClassName(...) and any
            # depth of Add of same-class operands, so this single
            # call covers `x = Vec(1, 2)`, `x = a + b`, and
            # `x = a + b + c`.
            _vcls = self._class_of_expr(node.value)
            if _vcls is not None:
                self.instance_vars[name] = _vcls
            # Batch 11a: capture string literals for .format() on a var.
            if (isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)):
                self.str_literal_vars[name] = node.value.value
            # Batch 8e: `x = ClassName.classmethod(...)` or
            # `x = obj.classmethod(...)` — register x as an instance
            # of the class that defines the classmethod, so later
            # `x.property` and `x.method()` dispatch correctly.
            if (isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and isinstance(node.value.func.value, ast.Name)):
                _cm_attr = node.value.func.attr
                _cm_base = node.value.func.value
                _cm_cls = None
                if _cm_base.id in self.user_classes:
                    if _cm_attr in self.classmethod_names.get(_cm_base.id, set()):
                        _cm_cls = _cm_base.id
                elif _cm_base.id in self.instance_vars:
                    _bcls = self.instance_vars[_cm_base.id]
                    if _cm_attr in self.classmethod_names.get(_bcls, set()):
                        _cm_cls = _bcls
                if _cm_cls is not None:
                    self.instance_vars[name] = _cm_cls

            # Set variable: `s = {1, 2, 3}` — record element type.
            if isinstance(node.value, ast.Set):
                # Infer element type (same logic as expr())
                if len(node.value.elts) == 0:
                    raise TranspileError(
                        "empty set literals are not supported."
                    )
                first = node.value.elts[0]
                if (isinstance(first, ast.UnaryOp)
                        and isinstance(first.operand, ast.Constant)):
                    first = first.operand
                if isinstance(first, ast.Constant):
                    v = first.value
                    if isinstance(v, bool):
                        raise TranspileError(
                            "Sets of booleans are not supported yet."
                        )
                    if isinstance(v, str):
                        elem_type = "std::string"
                    elif isinstance(v, float):
                        elem_type = "double"
                    elif isinstance(v, int):
                        elem_type = "int"
                    else:
                        raise TranspileError(
                            f"Unsupported set element: {v!r}"
                        )
                else:
                    raise TranspileError(
                        "Set elements must be literals for now."
                    )
                value_cpp = self.expr(node.value)
                if name in self.declared:
                    self.emit(f"{name} = {value_cpp};")
                else:
                    self.emit(f"auto {name} = {value_cpp};")
                    self.declared.add(name)
                self.set_vars[name] = elem_type
                return

            # Special sub-case: `p = xs[i]` where xs is a pointer list
            # → p is a pointer, and `p.field`/`p.method()` use `->`
            if (isinstance(node.value, ast.Subscript)
                    and isinstance(node.value.value, ast.Name)
                    and node.value.value.id in self.pointer_list_vars):
                value_cpp = self.expr(node.value)
                self.emit(f"auto {name} = {value_cpp};")
                self.declared.add(name)
                self.pointer_vars.add(name)
                return
            # Special sub-case: `xs = []` where xs is a pointer list
            if (isinstance(node.value, ast.List)
                    and len(node.value.elts) == 0
                    and name in self.pointer_list_vars):
                class_name = self.pointer_list_vars[name]
                self.emit(f"std::vector<{class_name}*> {name};")
                self.declared.add(name)
                self.list_vars[name] = f"{class_name}*"
                return

            # Special sub-case: `v = vec2(x, y)` — remember v as a vec2 variable
            if (isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "vec2"):
                value_cpp = self.expr(node.value)
                if name in self.declared:
                    self.emit(f"{name} = {value_cpp};")
                else:
                    self.emit(f"auto {name} = {value_cpp};")
                    self.declared.add(name)
                self.vec2_vars.add(name)
                return

            # Special sub-case: `p = ptr(ClassName(args))` — a pointer
            # to a heap-allocated class instance.
            if (isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "ptr"):
                value_cpp = self.expr(node.value)
                self.emit(f"auto {name} = {value_cpp};")
                self.declared.add(name)
                self.pointer_vars.add(name)
                return

            # Special sub-case: `p = ClassName(args)` — a class instance.
            # C++ syntax is `ClassName p(args);` not `auto p = ClassName(args);`
            if (isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id in self.user_classes):
                class_name = node.value.func.id
                args = [self.expr(a) for a in node.value.args]
                self.emit(f"{class_name} {name}{{{', '.join(args)}}};")
                self.declared.add(name)
                return

            # Special sub-case: `d = {...}` — a dict literal.
            # Record the value type so subscript dispatch works later.
            if isinstance(node.value, ast.Dict):
                if len(node.value.values) == 0:
                    raise TranspileError(
                        "empty dict literals are not supported."
                    )

                def _infer_dict_value_type(val_node):
                    if isinstance(val_node, ast.Constant):
                        v = val_node.value
                        if isinstance(v, bool): return "bool"
                        if isinstance(v, int): return "int"
                        if isinstance(v, float): return "double"
                        if isinstance(v, str): return "std::string"
                        return None
                    if isinstance(val_node, ast.UnaryOp):
                        if isinstance(val_node.operand, ast.Constant):
                            v = val_node.operand.value
                            if isinstance(v, int): return "int"
                            if isinstance(v, float): return "double"
                        return None
                    if isinstance(val_node, ast.Dict):
                        if len(val_node.values) == 0:
                            return None
                        inner_t = _infer_dict_value_type(val_node.values[0])
                        if inner_t is None:
                            return None
                        return f"std::map<std::string, {inner_t}>"
                    # Batch 11c.3: dict values that are tuples.
                    if (isinstance(val_node, ast.Tuple)
                            and len(val_node.elts) >= 2):
                        def _scalar_cpp(n):
                            if isinstance(n, ast.UnaryOp):
                                n = n.operand
                            v = n.value
                            if isinstance(v, bool): return "bool"
                            if isinstance(v, int): return "int"
                            if isinstance(v, float): return "double"
                            if isinstance(v, str): return "std::string"
                            return None
                        _types = []
                        for e in val_node.elts:
                            t = _scalar_cpp(e)
                            if t is None:
                                return None
                            _types.append(t)
                        if len(_types) == 2:
                            return f"std::pair<{_types[0]}, {_types[1]}>"
                        return "std::tuple<" + ", ".join(_types) + ">"
                    return None
                val_type = _infer_dict_value_type(node.value.values[0])
                if val_type is None:
                    raise TranspileError(
                        f"Unsupported dict value type."
                    )
                value_cpp = self.expr(node.value)
                self.emit(f"auto {name} = {value_cpp};")
                self.declared.add(name)
                self.dict_vars[name] = val_type
                return

            # Special sub-case: `parts = s.split(sep)` — result is
            # a list of strings. Track it so parts[i] uses vector
            # indexing, not tuple .first/.second dispatch.
            if (isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == "split"):
                value_cpp = self.expr(node.value)
                self.emit(f"auto {name} = {value_cpp};")
                self.declared.add(name)
                self.list_vars[name] = "std::string"
                return

            # Batch 5d: if RHS is a lambda, remember the target
            # name so future calls dispatch through the variable.
            if isinstance(node.value, ast.Lambda):
                self.lambda_vars.add(name)

            # Normal variable assignment
            value = self.expr(node.value)
            # Batch 15: track variables that hold strings, so int()/
            # float() know whether to parse (std::stoi/stod) or cast.
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "input":
                self.string_vars.add(name)
            elif isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                self.string_vars.add(name)
            # If this is a fresh variable initialized with a raw string
            # literal, wrap it in std::string(...) so future assignments
            # of other strings don't fail (C++ won't assign std::string
            # to const char*).
            if (name not in self.declared
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)):
                value = f"std::string({value})"
            # Batch 22/24/26: a name is written to the C++ global only
            # when:
            #   - we're at module level (current_function is None) and
            #     the name was hoisted to global scope, OR
            #   - the enclosing function declared the name `global`.
            # Otherwise, a name in global_vars is shadowed locally.
            _is_global_write = (
                (self.current_function is None
                 and name in self.global_vars)
                or name in self.global_declared
            )
            if _is_global_write:
                self.emit(f"{name} = {value};")
                self.declared.add(name)
            elif name in self.declared:
                self.emit(f"{name} = {value};")
            else:
                self.emit(f"auto {name} = {value};")
                self.declared.add(name)
                if isinstance(node.value, ast.List):
                    # Batch 11c.1: compute the element C++ type so
                    # for-loops and other dispatch know what's inside.
                    _elts = node.value.elts
                    if _elts:
                        _first = _elts[0]
                        if isinstance(_first, ast.Tuple) and len(_first.elts) >= 2:
                            def _scalar_cpp(n):
                                v = n.value
                                if isinstance(v, bool): return "bool"
                                if isinstance(v, int): return "int"
                                if isinstance(v, float): return "double"
                                if isinstance(v, str): return "std::string"
                                return "int"
                            _types = [_scalar_cpp(e) for e in _first.elts]
                            if len(_types) == 2:
                                _et = f"std::pair<{_types[0]}, {_types[1]}>"
                            else:
                                _et = ("std::tuple<"
                                       + ", ".join(_types) + ">")
                        elif isinstance(_first, ast.Constant):
                            v = _first.value
                            if isinstance(v, bool): _et = "bool"
                            elif isinstance(v, int): _et = "int"
                            elif isinstance(v, float): _et = "double"
                            elif isinstance(v, str): _et = "std::string"
                    self.list_vars[name] = _et
            return

        # Case 1b: tuple-unpacking target — `a, b = value` (or N>=3)
        if isinstance(target, ast.Tuple):
            if len(target.elts) < 2:
                raise TranspileError(
                    f"Tuple unpacking requires at least 2 targets; "
                    f"got {len(target.elts)}."
                )
            if not all(isinstance(e, ast.Name) for e in target.elts):
                raise TranspileError(
                    "Tuple unpacking targets must be simple variable names."
                )
            # The right-hand side can be any expression that yields a
            # std::pair: a variable (`t`), an attribute (`obj.pos`), or
            # a function call. We emit its C++ form and access .first/.second.
            src = self.expr(node.value)
            # Batch 21: list unpacking uses subscript; tuple/pair uses
            # .first/.second (arity 2) or std::get<N> (arity 3+).
            if (isinstance(node.value, ast.Name)
                    and node.value.id in self.list_vars):
                for i, elt in enumerate(target.elts):
                    self._check_name(elt.id, "Variable name")
                    self.emit(f"auto {elt.id} = {src}[{i}];")
                    self.declared.add(elt.id)
                return
            # Determine arity: prefer RHS variable's recorded arity,
            # fall back to len(target.elts).
            arity = len(target.elts)
            if (isinstance(node.value, ast.Name)
                    and node.value.id in self.tuple_vars):
                arity = self.tuple_vars[node.value.id]
            # Batch 11b: `a, b, c = make()` — arity from the function.
            elif (isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id in self.func_return_arity):
                arity = self.func_return_arity[node.value.func.id]
            for i, elt in enumerate(target.elts):
                self._check_name(elt.id, "Variable name")
                if arity == 2:
                    field = "first" if i == 0 else "second"
                    self.emit(f"auto {elt.id} = {src}.{field};")
                else:
                    self.emit(f"auto {elt.id} = std::get<{i}>({src});")
                self.declared.add(elt.id)
            return

        if isinstance(node, ast.Subscript):
            target_name = None
            if isinstance(node.value, ast.Name):
                target_name = node.value.id

            # Dict access: d["key"] → d["key"]
            if target_name is not None and target_name in self.dict_vars:
                idx = self.expr(node.slice)
                return f"{target_name}[{idx}]"

            # (existing list and tuple branches below)
            ...

        # Case 1c: subscript target
        if isinstance(target, ast.Subscript):
            target_name = None
            if isinstance(target.value, ast.Name):
                target_name = target.value.id

            # Dict assignment: d["key"] = value
            if target_name is not None and target_name in self.dict_vars:
                idx = self.expr(target.slice)
                value = self.expr(node.value)
                self.emit(f"{target_name}[{idx}] = {value};")
                return

            # (existing list and tuple branches below)
            ...

        # Case 1c: subscript target — `xs[i] = value` or `t[0] = value`
        if isinstance(target, ast.Subscript):
            # List assignment: xs[i] = value
            target_name = None
            if isinstance(target.value, ast.Name):
                target_name = target.value.id

            if target_name is not None and target_name in self.list_vars:
                idx = self.expr(target.slice)
                value = self.expr(node.value)
                self.emit(f"{target_name}[{idx}] = {value};")
                return

            # Tuple item assignment: t[N] = value.
            if not isinstance(target.slice, ast.Constant):
                raise TranspileError(
                    "Tuple index must be a literal number. "
                    "(For list indexing, the variable must be a list.)"
                )
            idx = target.slice.value
            value_cpp = self.expr(node.value)
            # N>=3 tuple variable -> std::get<N>(var) = value
            if (target_name is not None
                    and target_name in self.tuple_vars
                    and self.tuple_vars[target_name] >= 3):
                self.emit(
                    f"std::get<{idx}>({target_name}) = {value_cpp};"
                )
                return
            # 2-element pair
            if idx == 0:
                field = "first"
            elif idx == 1:
                field = "second"
            else:
                raise TranspileError(
                    f"Tuple index must be 0 or 1 for 2-tuples; got {idx}."
                )
            self.emit(
                f"{self.expr(target.value)}.{field} = {value_cpp};"
            )
            return

        # Case 2: attribute target — `self.x = value`
        # Case 2: attribute target — `self.x = value` or `obj.x = value`
        if isinstance(target, ast.Attribute):
            value = self.expr(node.value)
            # Batch 8d: resolve the target's class for property dispatch.
            _tcls = self._class_of_expr(target.value)
            if _tcls is None and (isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    and self._current_class):
                _tcls = self._current_class
            # self.x = v  →  this->x = v  (or this->x(v) if setter)
            if isinstance(target.value, ast.Name) and target.value.id == "self":
                if (_tcls is not None
                        and target.attr in self.property_setters.get(_tcls, set())):
                    self.emit(f"this->{target.attr}({value});")
                    return
                if (_tcls is not None
                        and target.attr in self.property_getters.get(_tcls, set())):
                    raise TranspileError(
                        f"property '{_tcls}.{target.attr}' is read-only "
                        f"(no @{target.attr}.setter defined)"
                    )
                self.emit(f"this->{target.attr} = {value};")
                return
            # obj.x = v  →  obj.x = v  (or obj.x(v) if setter)
            obj = self.expr(target.value)
            if (_tcls is not None
                    and target.attr in self.property_setters.get(_tcls, set())):
                self.emit(f"{obj}.{target.attr}({value});")
                return
            if (_tcls is not None
                    and target.attr in self.property_getters.get(_tcls, set())):
                raise TranspileError(
                    f"property '{_tcls}.{target.attr}' is read-only "
                    f"(no @{target.attr}.setter defined)"
                )
            self.emit(f"{obj}.{target.attr} = {value};")
            return

        raise TranspileError(
            f"Unsupported assignment target: {ast.unparse(target)}"
        )

    def visit_AugAssign(self, node: ast.AugAssign):
        if not isinstance(node.target, ast.Name):
            raise TranspileError("Augmented assignment target must be a name.")
        name = node.target.id

        # vec2 augmented assignment: pos += vel  →  pos = vec2_add(pos, vel)
        if name in self.vec2_vars:
            rhs = self.expr(node.value)
            if isinstance(node.op, ast.Add):
                self.emit(f"{name} = vec2_add({name}, {rhs});")
                return
            if isinstance(node.op, ast.Sub):
                self.emit(f"{name} = vec2_sub({name}, {rhs});")
                return
            if isinstance(node.op, ast.Mult):
                self.emit(f"{name} = vec2_scale({name}, {rhs});")
                return

        # Default: plain C++ compound assignment
        op = self._binop(node.op)
        self.emit(f"{name} {op}= {self.expr(node.value)};")

    def visit_Raise(self, node: ast.Raise):
        """Batch 6b: raise X(...) -> throw std::runtime_error(...).

        All exception names collapse to std::runtime_error, since
        InterScript has no exception class hierarchy in the runtime.
          raise X("msg")  -> throw std::runtime_error("msg");
          raise X          -> throw std::runtime_error("");
        Bare `raise` (re-raise) is not supported.
        """
        if node.exc is None:
            raise TranspileError(
                "bare `raise` (re-raise) is not supported yet."
            )
        if isinstance(node.exc, ast.Call):
            # raise ValueError("msg") -> throw std::runtime_error("msg");
            call_args = [self.expr(a) for a in node.exc.args]
            if len(call_args) == 0:
                self.emit("throw std::runtime_error(\"\");")
            elif len(call_args) == 1:
                self.emit(f"throw std::runtime_error({call_args[0]});")
            else:
                raise TranspileError(
                    "raise X(...) takes at most 1 argument."
                )
            return
        if isinstance(node.exc, ast.Name):
            # raise SomeError (no call, no args)
            self.emit("throw std::runtime_error(\"\");")
            return
        raise TranspileError(
            f"Unsupported raise expression: {ast.dump(node.exc)}"
        )

    def visit_Try(self, node: ast.Try):
        """Batch 6b: try/except with catch-all.

        Only one except block is supported, and it must be a bare
        `except:` or `except Exception:` -- both emit `catch (...)`.
        else/finally are not supported.
        """
        if node.orelse:
            raise TranspileError("try/else is not supported yet.")
        if node.finalbody:
            raise TranspileError("try/finally is not supported yet.")
        if len(node.handlers) == 0:
            raise TranspileError("try must have an except block.")
        if len(node.handlers) > 1:
            raise TranspileError(
                "try with multiple except blocks is not supported yet."
            )
        handler = node.handlers[0]
        # Accept bare `except:` (handler.type is None) or a single
        # exception type. Both emit `catch (...)`.
        if handler.name is not None:
            raise TranspileError(
                "`except X as e:` is not supported yet."
            )
        self.emit("try {")
        self.indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent -= 1
        self.emit("} catch (...) {")
        self.indent += 1
        for stmt in handler.body:
            self.visit(stmt)
        self.indent -= 1
        self.emit("}")

    def visit_Match(self, node: ast.Match):
        """Batch 6a: match/case with literal patterns.

        Emits as if / else-if / else. Supported pattern kinds:
          - MatchValue:      case 1:  case "x":  case 3.14:
          - MatchSingleton:  case True:  case False:
          - MatchAs:         case _:  (wildcard only; no capture)
        """
        subject = self.expr(node.subject)
        first = True
        has_wildcard = False

        def _emit_case_header(cond_cpp):
            nonlocal first
            if first:
                self.emit(f"if ({cond_cpp}) {{")
                first = False
            else:
                self.emit(f"}} else if ({cond_cpp}) {{")

        def _emit_wildcard_header():
            nonlocal first, has_wildcard
            if first:
                # Only case is _: emit `if (true)`.
                self.emit("if (true) {")
                first = False
            else:
                self.emit("} else {")
            has_wildcard = True

        for case in node.cases:
            pat = case.pattern
            if has_wildcard:
                raise TranspileError(
                    "match/case: no cases allowed after `case _:`."
                )
            if isinstance(pat, ast.MatchValue):
                lit_cpp = self.expr(pat.value)
                _emit_case_header(f"{subject} == {lit_cpp}")
            elif isinstance(pat, ast.MatchSingleton):
                v = pat.value
                if v is True:
                    _emit_case_header(f"{subject} == true")
                elif v is False:
                    _emit_case_header(f"{subject} == false")
                else:
                    raise TranspileError(
                        "match/case: `case None:` not supported yet."
                    )
            elif isinstance(pat, ast.MatchAs):
                if pat.name is not None:
                    raise TranspileError(
                        "match/case: capture patterns (case x:) "
                        "are not supported yet."
                    )
                _emit_wildcard_header()
            else:
                raise TranspileError(
                    f"match/case: unsupported pattern "
                    f"{type(pat).__name__}."
                )
            # Emit case body.
            self.indent += 1
            for stmt in case.body:
                self.visit(stmt)
            self.indent -= 1

        if first:
            # Zero cases: emit nothing (rare).
            return
        self.emit("}")

    def visit_If(self, node: ast.If):
        self.emit(f"if ({self.expr(node.test)}) {{")
        self.indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent -= 1

        # Handle the chain of elif / else that follows.
        # Python represents `elif` as an If node inside orelse.
        # We walk that chain and emit `} else if (...)` for each elif
        # and a plain `} else {` only for the final else.
        chain = node
        while chain.orelse and len(chain.orelse) == 1 \
                and isinstance(chain.orelse[0], ast.If):
            next_if = chain.orelse[0]
            self.emit(f"}} else if ({self.expr(next_if.test)}) {{")
            self.indent += 1
            for stmt in next_if.body:
                self.visit(stmt)
            self.indent -= 1
            chain = next_if

        if chain.orelse:
            self.emit("} else {")
            self.indent += 1
            for stmt in chain.orelse:
                self.visit(stmt)
            self.indent -= 1

        self.emit("}")

    def visit_While(self, node: ast.While):
        self.emit(f"while ({self.expr(node.test)}) {{")
        self.indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent -= 1
        self.emit("}")

    def visit_For(self, node: ast.For):
        # Batch 4b: for...else wrapper.
        # If the for-loop has an else block, wrap the whole thing in
        # a block with a `__broke_N` flag. Any `break` inside the
        # loop body will set that flag; after the loop completes
        # without break, the else block runs.
        if not node.orelse:
            self._visit_for_inner(node)
            return

        self._for_else_counter += 1
        flag = f"__broke_{self._for_else_counter}"
        self._for_else_stack.append(flag)
        try:
            self.emit("{")
            self.indent += 1
            self.emit(f"bool {flag} = false;")
            self._visit_for_inner(node)
            self.emit(f"if (!{flag}) {{")
            self.indent += 1
            for stmt in node.orelse:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            self.indent -= 1
            self.emit("}")
        finally:
            self._for_else_stack.pop()

    def _visit_for_inner(self, node: ast.For):

        # --- Dict iteration ---
        # Handles:
        #   for k in d:                  (keys default)
        #   for k in d.keys():           (keys explicit)
        #   for v in d.values():         (values)
        #   for k, v in d.items():       (pairs)
        def _is_dict_name(n):
            return isinstance(n, ast.Name) and n.id in self.dict_vars

        def _method_call_of(n, method):
            return (isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute)
                    and n.func.attr == method
                    and isinstance(n.func.value, ast.Name)
                    and n.func.value.id in self.dict_vars)

        # for k, v in d.items():
        if (isinstance(node.target, ast.Tuple)
                and len(node.target.elts) == 2
                and all(isinstance(e, ast.Name) for e in node.target.elts)
                and _method_call_of(node.iter, "items")):
            k_name = node.target.elts[0].id
            v_name = node.target.elts[1].id
            d_name = node.iter.func.value.id
            self._check_name(k_name, "Loop variable")
            self._check_name(v_name, "Loop variable")
            self.emit(f"for (auto& [{k_name}, {v_name}] : {d_name}) {{")
            self.indent += 1
            self.declared.add(k_name)
            self.declared.add(v_name)
            for stmt in node.body:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            return

        # ---- for i, x in enumerate(xs): --------------------------
        if (isinstance(node.target, ast.Tuple)
                and len(node.target.elts) == 2
                and all(isinstance(e, ast.Name) for e in node.target.elts)
                and isinstance(node.iter, ast.Call)
                and isinstance(node.iter.func, ast.Name)
                and node.iter.func.id == "enumerate"):
            idx_name = node.target.elts[0].id
            val_name = node.target.elts[1].id
            self._check_name(idx_name, "Loop variable")
            self._check_name(val_name, "Loop variable")
            # enumerate(xs) or enumerate(xs, start)
            enum_args = node.iter.args
            if len(enum_args) == 1:
                src_list = self.expr(enum_args[0])
                start_cpp = "0"
            elif len(enum_args) == 2:
                src_list = self.expr(enum_args[0])
                start_cpp = self.expr(enum_args[1])
            else:
                raise TranspileError(
                    "enumerate() takes 1 or 2 arguments, got "
                    f"{len(enum_args)}."
                )
            self.emit(
                f"for (int __ei = 0; "
                f"__ei < (int)({src_list}).size(); ++__ei) {{"
            )
            self.indent += 1
            self.emit(
                f"int {idx_name} = {start_cpp} + __ei;"
            )
            self.emit(
                f"auto {val_name} = ({src_list})[__ei];"
            )
            self.declared.add(idx_name)
            self.declared.add(val_name)
            for stmt in node.body:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            return

        # ---- for x, y in zip(a, b): -------------------------------
        if (isinstance(node.target, ast.Tuple)
                and len(node.target.elts) == 2
                and all(isinstance(e, ast.Name) for e in node.target.elts)
                and isinstance(node.iter, ast.Call)
                and isinstance(node.iter.func, ast.Name)
                and node.iter.func.id == "zip"):
            x_name = node.target.elts[0].id
            y_name = node.target.elts[1].id
            self._check_name(x_name, "Loop variable")
            self._check_name(y_name, "Loop variable")
            zip_args = node.iter.args
            if len(zip_args) != 2:
                raise TranspileError(
                    "zip() takes exactly 2 arguments, got "
                    f"{len(zip_args)}."
                )
            a_cpp = self.expr(zip_args[0])
            b_cpp = self.expr(zip_args[1])
            self.emit(
                f"for (size_t __zi = 0; "
                f"__zi < std::min(({a_cpp}).size(), ({b_cpp}).size()); "
                f"++__zi) {{"
            )
            self.indent += 1
            self.emit(f"auto {x_name} = ({a_cpp})[__zi];")
            self.emit(f"auto {y_name} = ({b_cpp})[__zi];")
            self.declared.add(x_name)
            self.declared.add(y_name)
            for stmt in node.body:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            return

        # Batch 11c.1/11c.2: for a, b, [c, ...] in xs where xs is a
        # known list of pairs or tuples.
        if isinstance(node.target, ast.Tuple):
            if len(node.target.elts) < 2:
                raise TranspileError(
                    "Tuple-unpacking for-loops need at least 2 targets."
                )
            if not all(isinstance(e, ast.Name) for e in node.target.elts):
                raise TranspileError(
                    "Nested tuple-unpacking in for-loops is not "
                    "supported yet."
                )
            target_names = [e.id for e in node.target.elts]
            for tn in target_names:
                self._check_name(tn, "Loop variable")
            elem_type = None
            if (isinstance(node.iter, ast.Name)
                    and node.iter.id in self.list_vars
                    and isinstance(self.list_vars[node.iter.id], str)):
                elem_type = self.list_vars[node.iter.id]
            is_pair = (elem_type is not None
                       and elem_type.startswith("std::pair<"))
            is_tuple = (elem_type is not None
                        and elem_type.startswith("std::tuple<"))
            if is_pair or is_tuple:
                list_name = node.iter.id
                n = len(target_names)
                if is_pair and n != 2:
                    raise TranspileError(
                        f"Unpacking a list of pairs requires exactly 2 "
                        f"targets; got {n}."
                    )
                self.emit(
                    f"for (const auto& __it : {list_name}) {{"
                )
                self.indent += 1
                if is_pair:
                    self.emit(f"auto {target_names[0]} = __it.first;")
                    self.emit(f"auto {target_names[1]} = __it.second;")
                else:
                    for i, tn in enumerate(target_names):
                        self.emit(f"auto {tn} = std::get<{i}>(__it);")
                for tn in target_names:
                    self.declared.add(tn)
                for stmt in node.body:
                    self.visit(stmt)
                self.indent -= 1
                self.emit("}")
                return
            raise TranspileError(
                "Tuple-unpacking for-loop only supports iterating a "
                "known list of pairs or tuples."
            )

        if not isinstance(node.target, ast.Name):
            raise TranspileError("For loop target must be a single name.")

        var = node.target.id
        self._check_name(var, "Loop variable")

        # for k in d:  (keys default)
        if _is_dict_name(node.iter):
            d_name = node.iter.id
            self.emit(f"for (auto& [{var}, _] : {d_name}) {{")
            self.indent += 1
            self.declared.add(var)
            for stmt in node.body:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            return

        # for k in d.keys():
        if _method_call_of(node.iter, "keys"):
            d_name = node.iter.func.value.id
            self.emit(f"for (auto& [{var}, _] : {d_name}) {{")
            self.indent += 1
            self.declared.add(var)
            for stmt in node.body:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            return

        # for v in d.values():
        if _method_call_of(node.iter, "values"):
            d_name = node.iter.func.value.id
            self.emit(f"for (auto& [_, {var}] : {d_name}) {{")
            self.indent += 1
            self.declared.add(var)
            for stmt in node.body:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            return

        # Case 1: `for i in range(...)` — classic counted loop
        if (isinstance(node.iter, ast.Call)
                and isinstance(node.iter.func, ast.Name)
                and node.iter.func.id == "range"):
            args = [self.expr(a) for a in node.iter.args]
            if len(args) == 1:
                start, stop = "0", args[0]
            elif len(args) == 2:
                start, stop = args[0], args[1]
            elif len(args) == 3:
                raise TranspileError("range() with step is not supported yet.")
            else:
                raise TranspileError("range() takes 1 or 2 arguments.")

            self.emit(f"for (int {var} = {start}; {var} < {stop}; ++{var}) {{")
            self.indent += 1
            for stmt in node.body:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            return

        # Case 2: `for x in xs` — iterate over a list variable
        if (isinstance(node.iter, ast.Name)
                and node.iter.id in self.list_vars):
            list_name = node.iter.id
            self.emit(f"for (auto {var} : {list_name}) {{")
            self.indent += 1
            self.declared.add(var)
            for stmt in node.body:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            return

        # Case 3: `for x in <unknown name>` — could be a function parameter
        # of unknown type, or a variable we can't prove is a list.
        # Emit `for (auto x : name)` and let g++ verify.
        if isinstance(node.iter, ast.Name):
            list_name = node.iter.id
            self.emit(f"for (auto {var} : {list_name}) {{")
            self.indent += 1
            self.declared.add(var)
            for stmt in node.body:
                self.visit(stmt)
            self.indent -= 1
            self.emit("}")
            return

        raise TranspileError(
            "For loops must iterate over range() or a list variable "
            f"(got: {ast.unparse(node.iter)})."
        )

    def _scan_return_types(self, node: ast.FunctionDef):
        """Scan a function body for return statements.

        Returns (has_none, has_value) where:
          has_none  — at least one `return` / `return None`
          has_value — at least one `return <expr>` where expr isn't None

        Used to decide whether a function should return std::optional<T>.
        """
        has_none = False
        has_value = False
        for sub in ast.walk(node):
            if isinstance(sub, ast.Return):
                if sub.value is None:
                    has_none = True
                elif (isinstance(sub.value, ast.Constant)
                      and sub.value.value is None):
                    has_none = True
                else:
                    has_value = True
        return has_none, has_value

    def _infer_return_type(self, node: ast.FunctionDef):
        """Infer the C++ type T for std::optional<T> from a function's
        non-None return statements. Falls back to `int` if unknown."""
        for sub in ast.walk(node):
            if isinstance(sub, ast.Return) and sub.value is not None:
                if (isinstance(sub.value, ast.Constant)
                        and sub.value.value is None):
                    continue
                # Literal
                if isinstance(sub.value, ast.Constant):
                    v = sub.value.value
                    if isinstance(v, bool):
                        return "bool"
                    if isinstance(v, int):
                        return "int"
                    if isinstance(v, float):
                        return "double"
                    if isinstance(v, str):
                        return "std::string"
                # UnaryOp on constant (e.g. -1)
                if (isinstance(sub.value, ast.UnaryOp)
                        and isinstance(sub.value.operand, ast.Constant)):
                    v = sub.value.operand.value
                    if isinstance(v, int):
                        return "int"
                    if isinstance(v, float):
                        return "double"
                # Name: use declared var type if we know it
                if isinstance(sub.value, ast.Name):
                    name = sub.value.id
                    if name in self.optional_vars:
                        return self.optional_vars[name]
                    # Can't infer; fall through to try other returns
        return "int"

    def _infer_tuple_return_arity(self, node: ast.FunctionDef):
        """Batch 11b: return the tuple arity this function returns, or None.

        Checks two sources:
          1. `-> tuple[...]` annotation. Arity = number of elements in
             the subscript slice (or 1 for a single-element form).
          2. Unannotated: every `Return` in the body whose value is a
             Tuple literal must have the same arity. If they all agree,
             use that; otherwise None.
        Scalar returns, or no returns, yield None.
        """
        # Annotated case: -> tuple[a, b, c]
        if node.returns is not None:
            r = node.returns
            if (isinstance(r, ast.Subscript)
                    and isinstance(r.value, ast.Name)
                    and r.value.id == "tuple"):
                sl = r.slice
                if isinstance(sl, ast.Tuple):
                    return len(sl.elts)
                if isinstance(sl, ast.Name):
                    # Bare `tuple[x]` -> arity 1
                    return 1
                # tuple[()] or anything else: unknown
                return None

        # Unannotated: scan returns for a tuple literal.
        arities = set()
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                if isinstance(stmt.value, ast.Tuple):
                    arities.add(len(stmt.value.elts))
                else:
                    # A non-tuple return makes the tuple arity unreliable.
                    arities.add(None)
        if arities == {3}:
            return 3
        if len(arities) == 1 and None not in arities:
            return arities.pop()
        return None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """User-defined function. Uses `auto` return type unless annotated."""
        self._check_name(node.name, "Function name")
        if id(node) in self.shadowed_funcs:
            return
        self.user_funcs.add(node.name)

        # Batch 11b: record tuple return arity, if determinable.
        _arity = self._infer_tuple_return_arity(node)
        if _arity is not None:
            self.func_return_arity[node.name] = _arity

        # Parameter handling:
        #   1. Annotated param  -> use annotation type
        #   2. Default value    -> infer type from the default; emit
        #                          `T name = default` in the signature
        #   3. Neither          -> `auto name`
        #
        # Python aligns node.args.defaults to the LAST N params. So
        # with 2 defaults and 4 params, params[2] and params[3] have
        # defaults; params[0] and params[1] do not.
        defaults = list(node.args.defaults or [])
        n_total = len(node.args.args)
        n_defaults = len(defaults)
        first_default_idx = n_total - n_defaults

        arg_parts = []
        for i, a in enumerate(node.args.args):
            self._check_name(a.arg, "Parameter name")
            has_default = i >= first_default_idx
            default_node = (
                defaults[i - first_default_idx] if has_default else None
            )

            # Decide the C++ type for this param.
            if a.annotation:
                cpp_type = self._annot_to_cpp_type(a.annotation)
            elif has_default:
                cpp_type = self._infer_default_type(default_node)
            else:
                cpp_type = None

            if cpp_type is None:
                arg_parts.append(f"auto {a.arg}")
            elif has_default:
                default_cpp = self.expr(default_node)
                arg_parts.append(f"{cpp_type} {a.arg} = {default_cpp}")
            else:
                arg_parts.append(f"{cpp_type} {a.arg}")

        # Batch 5b: *args -> std::vector<T> name (last parameter).
        if node.args.vararg is not None:
            va = node.args.vararg
            if va.annotation is not None:
                elem_type = self._annot_to_cpp_type(va.annotation)
            else:
                elem_type = "int"
            arg_parts.append(
                f"std::vector<{elem_type}> {va.arg}"
            )
            self.func_varargs[node.name] = elem_type
            # Batch 13d: how many leading positional params precede
            # the *args vararg (so the call site can split args).
            self.func_vararg_leading[node.name] = len(node.args.args)
            # Mark the vararg name as a list so nums[0], len(nums),
            # `x in nums`, and `for n in nums` all use list code paths.
            self.list_vars[va.arg] = elem_type

        # Batch 5c: **kwargs -> std::map<std::string, T> name.
        if node.args.kwarg is not None:
            kw = node.args.kwarg
            if kw.annotation is not None:
                value_type = self._annot_to_cpp_type(kw.annotation)
            else:
                value_type = "std::string"
            arg_parts.append(
                f"std::map<std::string, {value_type}> {kw.arg}"
            )
            self.func_kwargs[node.name] = value_type
            # Mark the kwarg name as a dict so .get(), .items(),
            # .values(), `k in kw`, len(kw), and dict iteration
            # all dispatch through the dict code paths.
            self.dict_vars[kw.arg] = value_type

        args_cpp = ", ".join(arg_parts)

        # Return type: annotated or `auto`
        if isinstance(node.returns, ast.Name):
            ret_type = self._annot_to_cpp_type(node.returns)
        elif (isinstance(node.returns, ast.Constant)
                and node.returns.value is None):
            ret_type = "void"
        else:
            ret_type = "auto"

        # Detect optional: mixed `return None` and `return <value>`.
        has_none, has_value = self._scan_return_types(node)
        if has_none and has_value:
            inner_type = self._infer_return_type(node)
            ret_type = f"std::optional<{inner_type}>"
            self.optional_funcs.add(node.name)
            self.optional_func_types[node.name] = inner_type
            self.use_optional = True

        self.current_function = node.name

        # Batch 10k.1: register class-typed parameters in
        # instance_vars so that `p.x`, `p.property`, `is_to_string(p)`,
        # and `{p}` in f-strings all dispatch as if `p` were a
        # tracked instance variable. Save/restore so params don't
        # leak past this function's body.
        saved_instance_vars = dict(self.instance_vars)
        for a in node.args.args:
            if a.annotation is None:
                continue
            t = self._annot_to_cpp_type(a.annotation)
            if t in self.user_classes:
                self.instance_vars[a.arg] = t

        # We emit functions *before* main(), so we collect them separately.
        body_lines = []
        saved_lines, saved_indent = self.lines, self.indent
        # Batch 24/26: per-function scope for `global` declarations
        # and for local variables. A local `x` in a function must not
        # be visible as the module-level `x`.
        saved_global_declared = self.global_declared
        saved_declared = self.declared
        self.lines, self.indent = body_lines, 1
        self.global_declared = set()
        self.declared = set()
        try:
            for stmt in node.body:
                self.visit(stmt)
        finally:
            self.lines, self.indent = saved_lines, saved_indent
            self.global_declared = saved_global_declared
            self.declared = saved_declared

        # Restore instance_vars to its pre-call state.
        self.instance_vars = saved_instance_vars

        func = [f"{ret_type} {node.name}({args_cpp}) {{"]
        func.extend("    " * 1 + l for l in body_lines)
        func.append("}")
        self.functions.append("\n".join(func))
        self.current_function = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Emit a C++ struct for a Python-style class.

        Supports:
          - Single inheritance: `class Dog(Animal):`
          - Constructor chaining: `super().__init__(args)` as first statement
          - Method override (parent methods emitted `virtual`, child `override`)
          - Field type inference from annotations and literals
        """
        class_name = node.name
        self._check_name(class_name, "Class name")

        # Determine base classes
        bases = self.class_bases.get(class_name, [])
        is_multi = len(bases) > 1
        parent_name = bases[0] if len(bases) == 1 else None

        # Find __init__ and other methods
        init_method = None
        other_methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "__init__":
                    init_method = item
                else:
                    other_methods.append(item)
        # Collect class attributes (top-level assignments in class body)
        # Collect class attributes (top-level assignments in class body)
        class_attrs: dict = {}     # name → (type_str, init_value_cpp)
        for item in node.body:
            if isinstance(item, ast.Assign):
                if len(item.targets) != 1:
                    continue
                tgt = item.targets[0]
                if isinstance(tgt, ast.Name):
                    attr_name = tgt.id
                    self._check_name(attr_name, "Class attribute name")
                    attr_type = self._infer_field_type(item.value)
                    attr_init = self.expr(item.value)
                    # If the field type is std::string but the value is
                    # a raw string literal, wrap in std::string(...)
                    if (attr_type == "std::string"
                            and isinstance(item.value, ast.Constant)
                            and isinstance(item.value.value, str)):
                        attr_init = f"std::string({attr_init})"
                    class_attrs[attr_name] = (attr_type, attr_init)

        if init_method is None:
            # No __init__ — synthesize a default no-arg constructor
            init_method = ast.FunctionDef(
                name="__init__",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="self", annotation=None)],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                    vararg=None,
                    kwarg=None,
                ),
                body=[ast.Pass()],
                decorator_list=[],
                returns=None,
            )

        # Detect parent constructor calls based on single vs multiple inheritance
        if is_multi:
            super_args_cpp, init_body = self._detect_multiple_parent_inits(
                init_method, class_name, bases
            )
        else:
            super_args_cpp, init_body = self._detect_super_init(init_method)
            if parent_name is not None and super_args_cpp is None:
                # Only require super().__init__() if the parent actually
                # has an explicit __init__ in the source. Otherwise, the
                # parent has a synthetic empty constructor and super() is
                # not required.
                parent_has_init = self.class_has_explicit_init.get(parent_name, False)
                if parent_has_init:
                    raise TranspileError(
                        f"Class '{class_name}' inherits from '{parent_name}' and "
                        f"defines __init__, but does not call super().__init__() "
                        f"as the first statement."
                    )
        # Build parameter types from constructor annotations
        param_types: dict = {}
        _defaults = list(init_method.args.defaults or [])
        _n_total = len(init_method.args.args)
        _n_defaults = len(_defaults)
        _first_default_idx = _n_total - _n_defaults
        for i, arg in enumerate(init_method.args.args):
            if arg.arg == "self":
                continue
            if arg.annotation is not None:
                param_types[arg.arg] = self._annot_to_cpp_type(arg.annotation)
            elif i >= _first_default_idx:
                # Batch 13h: infer from default value.
                default_node = _defaults[i - _first_default_idx]
                try:
                    param_types[arg.arg] = self._infer_default_type(default_node)
                except TranspileError:
                    param_types[arg.arg] = None
            else:
                # Batch 13h: unknown — try call-site inference below.
                param_types[arg.arg] = None

        # Batch 13h: backfill from call-site inference.
        _ctor_hint = self.class_ctor_arg_types.get(class_name, {})
        for i, arg in enumerate(init_method.args.args):
            if arg.arg == "self":
                continue
            if param_types[arg.arg] is None:
                _param_index = i - 1  # skip self
                if _param_index in _ctor_hint:
                    param_types[arg.arg] = _ctor_hint[_param_index]

        # Batch 13h / 13h.1: raise only if the class is actually
        # called somewhere and we still can't infer a param type.
        # Dead classes (no call site) default to int, matching
        # pre-13h behavior — a class that's never instantiated can't
        # produce a broken call site.
        _has_call_site = class_name in self.class_ctor_arg_types
        for arg in init_method.args.args:
            if arg.arg == "self":
                continue
            if param_types[arg.arg] is None:
                if _has_call_site:
                    raise TranspileError(
                        f"cannot infer type of parameter '{arg.arg}' in "
                        f"{class_name}.__init__. Add a type annotation, e.g. "
                        f"`def __init__(self, {arg.arg}: str):`."
                    )
                # Dead class: fall back to int (old behavior).
                param_types[arg.arg] = "int"

        # Collect field names and types from the stripped init_body
        field_types: dict = {}
        for stmt in init_body:
            if isinstance(stmt, ast.Assign):
                if (len(stmt.targets) == 1
                        and isinstance(stmt.targets[0], ast.Attribute)
                        and isinstance(stmt.targets[0].value, ast.Name)
                        and stmt.targets[0].value.id == "self"):
                    field_name = stmt.targets[0].attr
                    if field_name not in field_types:
                        if (isinstance(stmt.value, ast.Name)
                                and stmt.value.id in param_types):
                            field_types[field_name] = param_types[stmt.value.id]
                        else:
                            field_types[field_name] = self._infer_field_type(stmt.value)

        # Batch 10k.2: remember field types by class name so that
        # `self.field` reads inside method bodies can resolve to a
        # user-class type for __str__ / property dispatch.
        self.class_field_types[class_name] = dict(field_types)

        # Build the struct block
        if bases:
            bases_str = ", ".join(bases)
            lines = [f"struct {class_name} : {bases_str} {{"]
        else:
            lines = [f"struct {class_name} {{"]

                # 1. Field declarations (only for fields NOT inherited)
        # Split into private (`_` prefix) and public (everything else)
        private_fields = {
            name: ftype for name, ftype in field_types.items()
            if name.startswith("_")
        }
        public_fields = {
            name: ftype for name, ftype in field_types.items()
            if not name.startswith("_")
        }

        # Batch 8d: track the enclosing class during field+method
        # emission so self.prop / self.prop = v can dispatch.
        _prev_current_class = self._current_class
        self._current_class = class_name

        # Emit private section first (C++ label applies to everything below)
        if private_fields:
            lines.append("private:")
            for fname, ftype in private_fields.items():
                lines.append(f"    {ftype} {fname};")
        # Then public section
        if public_fields:
            lines.append("public:")
            for fname, ftype in public_fields.items():
                lines.append(f"    {ftype} {fname};")
        # Emit class (static) attributes (always public)
        if class_attrs:
            lines.append("public:")
            for attr_name, (attr_type, _init) in class_attrs.items():
                lines.append(f"    static {attr_type} {attr_name};")

        if field_types or class_attrs:
            lines.append("")

        # Batch 8d: ensure the constructor and methods below are
        # always public, even when a class has only `_`-prefixed
        # fields (pre-existing privacy bug exposed by 8d).
        lines.append("public:")

        # 2. Constructor
        init_args = [a.arg for a in init_method.args.args if a.arg != "self"]
        args_cpp = ", ".join(f"{param_types[a]} {a}" for a in init_args)

        # Batch 10k.3: build field initializers. Fields assigned
        # directly from constructor params use an initializer list
        # so that class-typed fields don't require a default ctor.
        # Example:
        #     Circle(Point center, double radius)
        #         : center(center), radius(radius) {}
        field_inits = []
        fields_initialized_in_body = set()
        for field_name in field_types:
            if field_name in param_types:
                field_inits.append(f"{field_name}({field_name})")
                fields_initialized_in_body.add(field_name)

        # Constructor initializer list
        # Combine parent-init (if any) with field-init (Batch 10k.3).
        if is_multi:
            parent_init = ", ".join(super_args_cpp) if super_args_cpp else ""
            all_inits = ", ".join(filter(None, [parent_init] + field_inits))
            if all_inits:
                lines.append(f"    {class_name}({args_cpp}) : {all_inits} {{")
            else:
                lines.append(f"    {class_name}({args_cpp}) {{")
        elif parent_name is not None and super_args_cpp is not None:
            parent_args = ", ".join(super_args_cpp)
            parent_init = f"{parent_name}({parent_args})"
            all_inits = ", ".join([parent_init] + field_inits)
            lines.append(f"    {class_name}({args_cpp}) : {all_inits} {{")
        elif field_inits:
            all_inits = ", ".join(field_inits)
            lines.append(f"    {class_name}({args_cpp}) : {all_inits} {{")
        else:
            lines.append(f"    {class_name}({args_cpp}) {{")

        # Body (without the super().__init__ call, and without field
        # assignments that are now handled by the initializer list).
        body_to_emit = [
            stmt for stmt in init_body
            if not (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Attribute)
                and isinstance(stmt.targets[0].value, ast.Name)
                and stmt.targets[0].value.id == "self"
                and stmt.targets[0].attr in fields_initialized_in_body
            )
        ]
        lines.extend(self._emit_method_body(body_to_emit))
        lines.append("    }")
        # 3. Other methods — virtual if parent class, override if child class
        # Is this class a parent of anything? If so, methods are `virtual`.
        is_base_class = any(
            class_name in blist for blist in self.class_bases.values()
        )

        # Do we have a parent? If so, methods are `override` when they match.
        parent_methods = set()
        for base in bases:
            parent_methods |= self.class_methods.get(base, set())

        # Track current class so `super().method()` can resolve `super`
        # to the correct parent class.
        self.current_class = class_name

        for method in other_methods:
            self._check_name(method.name, "Method name")

            # Batch 8b: __str__ -> std::string __str__() const.
            # Intercepts before normal method emission; the
            # class is added to str_classes so print/str call
            # sites can dispatch through it.
            if method.name == "__str__":
                str_args = [a for a in method.args.args if a.arg != "self"]
                if str_args:
                    raise TranspileError(
                        "__str__ takes no arguments besides self; "
                        f"got {len(str_args)}."
                    )
                if method.returns is not None:
                    ann = ast.unparse(method.returns).strip()
                    if ann != "str":
                        raise TranspileError(
                            f"__str__ must return str; got {ann}."
                        )
                str_body = self._emit_method_body(method.body)
                lines.append("")
                lines.append("    std::string __str__() const {")
                lines.extend(str_body)
                lines.append("    }")
                self.str_classes.add(class_name)
                continue

            # Batch 8a: __eq__ -> bool operator==(const T&) const.
            # Intercepts before normal method emission so the
            # signature is rewritten rather than emitted as a
            # regular method.
            if method.name == "__eq__":
                eq_args = [a for a in method.args.args if a.arg != "self"]
                if len(eq_args) != 1:
                    raise TranspileError(
                        f"__eq__ must take exactly one parameter "
                        f"besides self; got {len(eq_args)}."
                    )
                other_name = eq_args[0].arg
                self._check_name(other_name, "Parameter name")
                eq_body = self._emit_method_body(method.body)
                lines.append("")
                lines.append(
                    f"    bool operator==(const {class_name}& "
                    f"{other_name}) const {{"
                )
                lines.extend(eq_body)
                lines.append("    }")
                continue

            # Batch 8c: __add__ -> <Class> operator+(const T&) const.
            # Same-class operand only (Option a). Registered in
            # add_classes so call-site dispatch can validate.
            if method.name == "__add__":
                add_args = [a for a in method.args.args if a.arg != "self"]
                if len(add_args) != 1:
                    raise TranspileError(
                        "__add__ must take exactly one parameter "
                        f"besides self; got {len(add_args)}."
                    )
                other_name = add_args[0].arg
                self._check_name(other_name, "Parameter name")
                add_body = self._emit_method_body(method.body)
                lines.append("")
                lines.append(
                    f"    {class_name} operator+(const {class_name}& "
                    f"{other_name}) const {{"
                )
                lines.extend(add_body)
                lines.append("    }")
                self.add_classes.add(class_name)
                continue

            # Parse decorators
            decorator_names = []
            for d in method.decorator_list:
                if isinstance(d, ast.Name):
                    decorator_names.append(d.id)

            is_abstract = "abstractmethod" in decorator_names
            is_static = "staticmethod" in decorator_names
            is_classmethod = "classmethod" in decorator_names

            # Batch 8e: @classmethod + @staticmethod is ambiguous.
            if is_classmethod and is_static:
                raise TranspileError(
                    f"Combining @classmethod and @staticmethod on method "
                    f"'{method.name}' is not supported."
                )

            # Batch 8e: @classmethod -> static auto name(args) { ... }
            # The first declared param is the class parameter (e.g. `cls`);
            # inside the body it is remapped to the class name.
            if is_classmethod:
                cm_args = [a for a in method.args.args if a.arg != "self"]
                if any(a.arg == "self" for a in method.args.args):
                    raise TranspileError(
                        f"@classmethod '{method.name}' must not take `self`."
                    )
                if not cm_args:
                    raise TranspileError(
                        f"@classmethod '{method.name}' takes at least one "
                        f"argument (the class parameter, e.g. `cls`); "
                        f"got 0."
                    )
                cls_param = cm_args[0].arg
                self._check_name(cls_param, "Parameter name")
                rest_args = cm_args[1:]
                arg_parts = []
                for a in rest_args:
                    self._check_name(a.arg, "Parameter name")
                    if a.annotation is not None:
                        t = self._annot_to_cpp_type(a.annotation)
                    else:
                        t = "int"
                    arg_parts.append(f"{t} {a.arg}")
                _prev_cm_param = self._classmethod_param
                self._classmethod_param = cls_param
                body = self._emit_method_body(method.body)
                self._classmethod_param = _prev_cm_param
                lines.append("")
                lines.append(
                    f"    static auto {method.name}({', '.join(arg_parts)}) {{"
                )
                lines.extend(body)
                lines.append("    }")
                self.classmethod_names.setdefault(class_name, set()).add(method.name)
                continue

            # Batch 8d: @property getter.
            if "property" in decorator_names:
                prop_args = [a for a in method.args.args if a.arg != "self"]
                if prop_args:
                    raise TranspileError(
                        f"@property getter '{method.name}' takes no "
                        f"arguments besides self; got {len(prop_args)}."
                    )
                prop_body = self._emit_method_body(method.body)
                lines.append("")
                lines.append(f"    auto {method.name}() const {{")
                lines.extend(prop_body)
                lines.append("    }")
                self.property_getters.setdefault(class_name, set()).add(method.name)
                continue

            # Batch 8d: @x.setter for a property.
            _setter_prop = None
            for _d in method.decorator_list:
                if (isinstance(_d, ast.Attribute)
                        and _d.attr == "setter"
                        and isinstance(_d.value, ast.Name)):
                    _setter_prop = _d.value.id
                    break
            if _setter_prop is not None:
                setter_args = [a for a in method.args.args if a.arg != "self"]
                if len(setter_args) != 1:
                    raise TranspileError(
                        f"@<name>.setter '{method.name}' takes exactly "
                        f"one argument besides self; got {len(setter_args)}."
                    )
                if method.name != _setter_prop:
                    raise TranspileError(
                        f"setter method '{method.name}' must have the "
                        f"same name as its property '{_setter_prop}'."
                    )
                sp = setter_args[0]
                if sp.annotation is not None:
                    sp_type = self._annot_to_cpp_type(sp.annotation)
                else:
                    sp_type = "int"
                setter_body = self._emit_method_body(method.body)
                lines.append("")
                lines.append(f"    void {method.name}({sp_type} {sp.arg}) {{")
                lines.extend(setter_body)
                lines.append("    }")
                self.property_setters.setdefault(class_name, set()).add(_setter_prop)
                continue

            if is_abstract and is_static:
                raise TranspileError(
                    f"Combining @abstractmethod and @staticmethod on "
                    f"method '{method.name}' is not supported yet."
                )

            has_return = any(
                isinstance(s, ast.Return) and s.value is not None
                for s in ast.walk(method)
            )

            # ─── Abstract method ─────────────────────────────────
            if is_abstract:
                if method.returns is None:
                    raise TranspileError(
                        f"@abstractmethod '{method.name}' must have a "
                        f"return type annotation (e.g., `-> float`)."
                    )
                ret_type, _ = self._method_return_type(method, has_return=True)
                method_args = [
                    a.arg for a in method.args.args if a.arg != "self"
                ]
                for _a in method_args:
                    self._check_name(_a, "Parameter name")
                method_args_cpp = ", ".join(f"int {a}" for a in method_args)
                override_kw = ""
                lines.append("")
                lines.append(
                    f"    virtual {ret_type} {method.name}({method_args_cpp})"
                    f"{override_kw} = 0;"
                )
                continue

            # ─── Static method ───────────────────────────────────
            if is_static:
                # Static methods have no `self` parameter
                method_args_cpp_parts = []
                for a in method.args.args:
                    self._check_name(a.arg, "Parameter name")
                    arg_type = self._annot_to_cpp_type(a.annotation)
                    method_args_cpp_parts.append(f"{arg_type} {a.arg}")
                method_args_cpp = ", ".join(method_args_cpp_parts)

                ret_type, _ = self._method_return_type(method, has_return)

                lines.append("")
                lines.append(
                    f"    static {ret_type} {method.name}({method_args_cpp}) {{"
                )
                lines.extend(self._emit_method_body(method.body))
                lines.append("    }")
                continue

            # ─── Normal method ───────────────────────────────────
            method_args = [
                a.arg for a in method.args.args if a.arg != "self"
            ]
            for _a in method_args:
                self._check_name(_a, "Parameter name")
            method_args_cpp = ", ".join(f"int {a}" for a in method_args)

            ret_type, virtual_kw = self._method_return_type(method, has_return)
            # Batch 13d.3: infer a concrete return type for any
            # unannotated method with a `return <expr>` body. This
            # serves two purposes:
            #   1. Base-class methods that are otherwise `auto` can be
            #      made `virtual` (C++ forbids `virtual auto`).
            #   2. Child methods that override a parent method must
            #      match the parent's concrete return type (C++ rejects
            #      "conflicting return type" otherwise).
            if has_return and not virtual_kw:
                inferred = self._infer_method_return_type(method)
                if inferred is not None:
                    ret_type = inferred
                    if is_base_class:
                        virtual_kw = "virtual "
            # Emit `override` whenever we're overriding a parent method.
            # The parent method is virtual by construction (Batch 13d.1).
            override_kw = " override" if method.name in parent_methods else ""

            lines.append("")
            lines.append(
                f"    {virtual_kw}{ret_type} {method.name}({method_args_cpp})"
                f"{override_kw} {{"
            )
            lines.extend(self._emit_method_body(method.body))
            lines.append("    }")

        lines.append("};")

        # Emit static member definitions (once per class) after the struct
        for attr_name, (attr_type, attr_init) in class_attrs.items():
            lines.append(f"{attr_type} {class_name}::{attr_name} = {attr_init};")

        self._current_class = _prev_current_class
        self.classes.append("\n".join(lines))

    def _emit_method_body(self, body: List[ast.stmt]) -> List[str]:
        """
        Emit a method body (list of statements) into a fresh line buffer,
        then return those lines. Used for both __init__ and regular methods.
        """
        saved_lines = self.lines
        saved_indent = self.indent
        saved_declared = self.declared
        self.lines = []
        self.indent = 2  # 2 levels: 1 for struct, 1 for method body
        self.declared = set()  # fresh local scope

        try:
            for stmt in body:
                self.visit(stmt)
            return list(self.lines)
        finally:
            self.lines = saved_lines
            self.indent = saved_indent
            self.declared = saved_declared

    def visit_Import(self, node: ast.Import):
        """`import raylib` is the only accepted import. It flips the
        emitter into raylib mode. Nothing is emitted for it."""
        for alias in node.names:
            if alias.name == "raylib":
                self.needs_raylib = True
                return
            if alias.name == "math":
                # Batch 7a: math is always available in <cmath>.
                # No code is emitted; the flag gates math.X usage.
                self.imported_modules.add("math")
                return
            if alias.name == "random":
                # Batch 7b: random uses helpers from the preamble.
                # No code emitted; the flag gates random.X usage.
                self.imported_modules.add("random")
                return
            if alias.name == "time":
                # Batch 7c: time uses helpers from the preamble.
                self.imported_modules.add("time")
                return
        names = ", ".join(a.name for a in node.names)
        raise TranspileError(
            f"Only 'import raylib' is supported. Got: import {names}"
        )

    def visit_ImportFrom(self, node: ast.ImportFrom):
        raise TranspileError(
            f"'from ... import ...' is not supported yet. Got: "
            f"from {node.module} import ..."
        )

    def visit_Return(self, node: ast.Return):
        # If we're inside an optional-returning function and the value
        # is None, emit std::nullopt; instead of nullptr.
        if (getattr(self, "current_function", None) in self.optional_funcs):
            if node.value is None:
                self.emit("return std::nullopt;")
                return
            if (isinstance(node.value, ast.Constant)
                    and node.value.value is None):
                self.emit("return std::nullopt;")
                return
        if node.value is None:
            self.emit("return;")
        else:
            self.emit(f"return {self.expr(node.value)};")

    def visit_Pass(self, node: ast.Pass):
        """`pass` is a no-op in Python. Emit nothing."""
        pass

    def visit_Break(self, node: ast.Break):
        """`break` in a loop — C++ has the same statement.

        If we are inside a for...else, set the flag before breaking
        so the else block is skipped.
        """
        if self._for_else_stack:
            flag = self._for_else_stack[-1]
            self.emit(f"{flag} = true;")
        self.emit("break;")

    def visit_Continue(self, node: ast.Continue):
        """`continue` in a loop — C++ has the same statement."""
        self.emit("continue;")

    # ---- anything else ---------------------------------------------------
    def visit_Global(self, node):
        """`global x` — declare x as a module-level write target
        inside the current function (Batch 24). Subsequent
        assignments to x in this function target the C++ global."""
        for name in node.names:
            self.global_declared.add(name)

    def generic_visit(self, node):
        raise TranspileError(f"Unsupported syntax: {type(node).__name__}")
def _collect_bound_names(tree) -> set:
    """Batch 25: return the set of every name bound anywhere in the AST.

    Lenient — this is a whole-file analysis. A name used before it's
    assigned is allowed, matching Python's behavior for module-level
    forward references. Strict ordering is a future batch.
    """
    names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = getattr(node, "targets", None) or [node.target]
            for tgt in targets:
                for sub in ast.walk(tgt):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
        elif isinstance(node, ast.For):
            for sub in ast.walk(node.target):
                if isinstance(sub, ast.Name):
                    names.add(sub.id)
        elif isinstance(node, ast.With):
            for item in node.items:
                if item.optional_vars is not None:
                    for sub in ast.walk(item.optional_vars):
                        if isinstance(sub, ast.Name):
                            names.add(sub.id)
        elif isinstance(node, ast.FunctionDef):
            names.add(node.name)
            a = node.args
            for arg in (a.posonlyargs + a.args + a.kwonlyargs):
                names.add(arg.arg)
            if a.vararg is not None:
                names.add(a.vararg.arg)
            if a.kwarg is not None:
                names.add(a.kwarg.arg)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
                if alias.name == "raylib":
                    names.update(_RAYLIB_CONSTANTS)
        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                names.add(node.name)
        elif isinstance(node, ast.Lambda):
            a = node.args
            for arg in (a.posonlyargs + a.args + a.kwonlyargs):
                names.add(arg.arg)
            if a.vararg is not None:
                names.add(a.vararg.arg)
            if a.kwarg is not None:
                names.add(a.kwarg.arg)
    return names

def _literal_cpp_type(node):
    """Batch 13h: return the C++ type of a literal-shaped AST node,
    or None if the node isn't a compile-time-known scalar literal."""
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, bool):
            return "bool"
        if isinstance(v, int):
            return "int"
        if isinstance(v, float):
            return "double"
        if isinstance(v, str):
            return "std::string"
        return None
    if (isinstance(node, ast.UnaryOp)
            and isinstance(node.op, (ast.USub, ast.UAdd))):
        return _literal_cpp_type(node.operand)
    return None


def _scan_ctor_arg_types(tree, user_classes):
    """Batch 13h: for each user class, infer the C++ type of each
    constructor argument by scanning all ClassName(...) call sites.

    Only literal-typed args contribute. If a position receives
    conflicting literal types across call sites (e.g. one call passes
    a string, another passes an int), that position is left
    un-unified so the caller falls back to annotation-required.

    Returns { class_name: { param_index: cpp_type } }.
    """
    result = {}
    _seen_classes = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        cls = node.func.id
        if cls not in user_classes:
            continue
        _seen_classes.add(cls)
        per_class = result.setdefault(cls, {})
        for i, arg in enumerate(node.args):
            t = _literal_cpp_type(arg)
            if t is None:
                continue
            if i in per_class:
                if per_class[i] != t:
                    # Conflict: this argument position sees different
                    # literal types at different call sites. Mark
                    # as un-unifiable.
                    per_class[i] = None
            else:
                per_class[i] = t
    # Drop any positions that ended up None due to conflict.
    for cls, per_class in result.items():
        result[cls] = {k: v for k, v in per_class.items() if v is not None}

    # -----------------------------------------------------------------
    # Batch 13c (Bug #10): pass 2 — super().__init__(...) call sites.
    #
    # A base class's ctor params are often typed only via a derived
    # class calling super().__init__(name), never via a direct
    # BaseClass(...) call. Pass 1 doesn't see those because
    # node.func is an ast.Attribute, not an ast.Name.
    #
    # Strategy: walk each ClassDef. When we find a
    # super().__init__(...) call, look at each positional arg:
    #   - literal             -> its C++ type
    #   - Name matching one of the ENCLOSING class's ctor params
    #                         -> the enclosing class's inferred type
    #                            at that param position
    # Attribute the resulting per-position type to the PARENT class
    # (first base of the enclosing class), with the same conflict
    # logic as pass 1.
    # -----------------------------------------------------------------

    # { class_name: [base_name, ...] }
    _bases_map = {}
    # { class_name: { param_name: param_index_within_ctor } }
    _param_index = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        _bases_map[node.name] = [
            b.id for b in node.bases if isinstance(b, ast.Name)
        ]
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                arg_names = [a.arg for a in item.args.args]
                # arg_names[1:] drops `self`, so enumerate() already
                # starts at 0 for the first real parameter. No -1.
                _param_index[node.name] = {
                    name: i for i, name in enumerate(arg_names[1:])
                }
                break

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = _bases_map.get(node.name, [])
        if not bases:
            continue
        parent = bases[0]
        if parent not in user_classes:
            continue
        pidx = _param_index.get(node.name, {})
        child_types = result.get(node.name, {})

        for item in ast.walk(node):
            if not isinstance(item, ast.Call):
                continue
            f = item.func
            if not (isinstance(f, ast.Attribute) and f.attr == "__init__"):
                continue
            v = f.value
            if not (isinstance(v, ast.Call)
                    and isinstance(v.func, ast.Name)
                    and v.func.id == "super"):
                continue

            # We are inside `super().__init__(...)` within node.name.
            _seen_classes.add(parent)
            per_parent = result.setdefault(parent, {})
            for i, arg in enumerate(item.args):
                t = _literal_cpp_type(arg)
                if t is None and isinstance(arg, ast.Name):
                    if arg.id in pidx:
                        t = child_types.get(pidx[arg.id])
                if t is None:
                    continue
                if i in per_parent:
                    if per_parent[i] != t:
                        per_parent[i] = None
                else:
                    per_parent[i] = t

    # Re-drop None positions added by pass 2.
    for cls, per_class in result.items():
        result[cls] = {k: v for k, v in per_class.items() if v is not None}

    # Batch 13h.1: ensure every seen class is present as a key,
    # even if it has no recorded positions. Runs again after pass 2
    # so parents discovered only via super().__init__ are included.
    for cls in _seen_classes:
        result.setdefault(cls, {})
    return result


def transpile(source: str) -> str:
    """Convert InterScript source to a complete C++ translation unit."""
    tree = ast.parse(source)

    # Pass 1: register user function names and class names so calls resolve.
    # Pass 1: register user function names and class names so calls resolve.
    # Pass 1: register user function names, class names, and inheritance info.
    emitter = CppEmitter()
        # Pass 1.5: register all top-level imports BEFORE emitting any
    # class or function bodies. visit_Import only sets
    # emitter.imported_modules; the flag is read by expr()/_call_expr
    # for gating `math.X`, `random.X`, `time.X`. Previously this ran
    # in Pass 3, so `math.pi` inside a class body raised
    # "math.pi used without `import math`" (Batch 10e regression fix).
    # Hoisting matches Python semantics: imports are module-scoped.
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            emitter.visit(node)
    # Batch 25: whole-file bound-name collection.
    emitter.all_bound_names = _collect_bound_names(tree)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            emitter.user_funcs.add(node.name)
        elif isinstance(node, ast.ClassDef):
            emitter.user_funcs.add(node.name)
            emitter.user_classes.add(node.name)

            # Record all bases (single or multiple)
            base_names = []
            for b in node.bases:
                if not isinstance(b, ast.Name):
                    raise TranspileError(
                        f"Base class of '{node.name}' must be a simple name. "
                        f"Got: {ast.unparse(b)}"
                    )
                base_names.append(b.id)
            emitter.class_bases[node.name] = base_names

            # Record method names (for override detection)
            method_names = set()
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_names.add(item.name)
            emitter.class_methods[node.name] = method_names

            # Record whether this class has an explicit __init__ in source
            has_init = any(
                isinstance(item, ast.FunctionDef) and item.name == "__init__"
                for item in node.body
            )
            emitter.class_has_explicit_init[node.name] = has_init

    # Batch 13h: whole-program ctor-arg type inference. Scan every
    # ClassName(...) call for literal-typed args and unify per
    # (class, position). Consumed by visit_ClassDef below.
    # Batch 25: whole-file bound-name collection.
    emitter.all_bound_names = _collect_bound_names(tree)
    emitter.class_ctor_arg_types = _scan_ctor_arg_types(
        tree, emitter.user_classes
    )

    # Batch 27: for each function name, keep only the LAST top-level
    # `def` with that name (Python semantics). Earlier defs of the
    # same name are shadowed and skipped during Pass 2.
    _defs_by_name: dict = {}
    for _node in tree.body:
        if isinstance(_node, ast.FunctionDef):
            _defs_by_name.setdefault(_node.name, []).append(_node)
    for _name, _defs in _defs_by_name.items():
        if len(_defs) > 1:
            for _earlier in _defs[:-1]:
                emitter.shadowed_funcs.add(id(_earlier))

    # After Pass 1 completes: check for diamonds.
    for class_name, bases in emitter.class_bases.items():
        if len(bases) > 1:
            # Diamond detection: does any ancestor appear in more than
            # one base's ancestry?
            ancestors_seen = {}
            for base in bases:
                # Walk up base's ancestry
                ancestors_of_base = set()
                current = base
                while current is not None:
                    ancestors_of_base.add(current)
                    parent_list = emitter.class_bases.get(current, [])
                    current = parent_list[0] if parent_list else None
                for anc in ancestors_of_base:
                    if anc in ancestors_seen and ancestors_seen[anc] != base:
                        raise TranspileError(
                            f"Diamond inheritance detected: class '{class_name}' "
                            f"inherits from '{base}' and '{ancestors_seen[anc]}', "
                            f"which both share ancestor '{anc}'. "
                            f"Diamond inheritance is not supported."
                        )
                    ancestors_seen[anc] = base

    # Pre-pass: detect optional variables (assigned both None and a value).
    _none_assigned = set()
    _value_assigned = {}
    for _node in tree.body:
        if not isinstance(_node, ast.Assign):
            continue
        if len(_node.targets) != 1:
            continue
        if not isinstance(_node.targets[0], ast.Name):
            continue
        _name = _node.targets[0].id
        _val = _node.value
        if (isinstance(_val, ast.Constant) and _val.value is None):
            _none_assigned.add(_name)
        elif isinstance(_val, (ast.Constant, ast.UnaryOp, ast.BinOp, ast.Name)):
            if _name in _value_assigned:
                continue
            if (isinstance(_val, ast.Constant)
                    and _val.value is not None):
                v = _val.value
                if isinstance(v, bool):
                    _value_assigned[_name] = "bool"
                elif isinstance(v, int):
                    _value_assigned[_name] = "int"
                elif isinstance(v, float):
                    _value_assigned[_name] = "double"
                elif isinstance(v, str):
                    _value_assigned[_name] = "std::string"
            elif (isinstance(_val, ast.UnaryOp)
                  and isinstance(_val.operand, ast.Constant)):
                v = _val.operand.value
                if isinstance(v, int):
                    _value_assigned[_name] = "int"
                elif isinstance(v, float):
                    _value_assigned[_name] = "double"

    # Names that got both None and a value are optionals.
    for _name in _none_assigned:
        if _name in _value_assigned:
            emitter.optional_vars[_name] = _value_assigned[_name]
            emitter.use_optional = True

    # Batch 22: hoist top-level SCALAR variables to C++ global
    # scope, so functions can read them. Only names actually read
    # inside a function are hoisted — this minimizes the change
    # to emitted code for programs that don't need globals.
    # Containers stay local (their tracking in visit_Assign is
    # load-bearing and would need to run for hoisted vars too).
    _HOISTABLE = {"int", "double", "bool", "std::string"}
    _func_reads = set()
    for _fnode in tree.body:
        if not isinstance(_fnode, ast.FunctionDef):
            continue
        _params = {a.arg for a in _fnode.args.args}
        _params |= {a.arg for a in _fnode.args.kwonlyargs}
        if _fnode.args.vararg:
            _params.add(_fnode.args.vararg.arg)
        if _fnode.args.kwarg:
            _params.add(_fnode.args.kwarg.arg)
        for _sub in ast.walk(_fnode):
            if (isinstance(_sub, ast.Name)
                    and isinstance(_sub.ctx, ast.Load)
                    and _sub.id not in _params):
                _func_reads.add(_sub.id)
    # Batch 24: also collect names declared `global` in any function —
    # they need a top-level declaration so the function can write to them.
    _global_declared_names = set()
    # Batch 24.1: for globals with no top-level assignment, infer the
    # type from the assignment inside the function that declares them
    # `global`.
    _global_implied_types = {}   # name -> C++ type from a `global x` body
    for _fnode in tree.body:
        if not isinstance(_fnode, ast.FunctionDef):
            continue
        _fdeclared = set()
        for _sub in ast.walk(_fnode):
            if isinstance(_sub, ast.Global):
                _fdeclared.update(_sub.names)
        _global_declared_names.update(_fdeclared)
        for _stmt in ast.walk(_fnode):
            if not isinstance(_stmt, ast.Assign):
                continue
            if len(_stmt.targets) != 1:
                continue
            if not isinstance(_stmt.targets[0], ast.Name):
                continue
            _tname = _stmt.targets[0].id
            if _tname not in _fdeclared:
                continue
            if _tname in _global_implied_types:
                continue
            _t = emitter._infer_expr_type(_stmt.value)
            if _t in _HOISTABLE:
                _global_implied_types[_tname] = _t
    for _node in tree.body:
        if not isinstance(_node, ast.Assign):
            continue
        if len(_node.targets) != 1:
            continue
        if not isinstance(_node.targets[0], ast.Name):
            continue
        _gname = _node.targets[0].id
        if _gname not in _func_reads and _gname not in _global_declared_names:
            continue
        _gtype = emitter._infer_expr_type(_node.value)
        if _gtype in _HOISTABLE:
            emitter.global_vars[_gname] = _gtype
    # Batch 24.1: hoist names whose only assignment is inside a
    # function that declares them `global`.
    for _gname, _gtype in _global_implied_types.items():
        if _gname not in emitter.global_vars:
            emitter.global_vars[_gname] = _gtype

    # Pre-pass: detect pointer lists.
    # A list variable is a pointer list if:
    #   1. It's initialized at top level with `xs = []`
    #   2. One or more subsequent top-level statements append either
    #        a) `ptr(ClassName(...))` directly, or
    #        b) a variable bound to `ptr(ClassName(...))` earlier.
    #
    # We collect ALL appended class names and find their common
    # ancestor. If two different classes are appended, we need a
    # shared base to hold them both.

    # Step 1: map top-level `name = ptr(ClassName(...))` -> ClassName
    ptr_var_class = {}   # var name -> class name
    for _node in tree.body:
        if not isinstance(_node, ast.Assign):
            continue
        if len(_node.targets) != 1:
            continue
        if not isinstance(_node.targets[0], ast.Name):
            continue
        _value = _node.value
        if not (isinstance(_value, ast.Call)
                and isinstance(_value.func, ast.Name)
                and _value.func.id == "ptr"):
            continue
        if not _value.args:
            continue
        _inner = _value.args[0]
        if (isinstance(_inner, ast.Call)
                and isinstance(_inner.func, ast.Name)
                and _inner.func.id in emitter.user_classes):
            ptr_var_class[_node.targets[0].id] = _inner.func.id

    def _class_of_append_arg(arg):
        """Given the single argument to `.append(...)`, return the class
        name it instantiates, or None. Handles both `ptr(Cls(...))` and
        a bare Name bound to `ptr(Cls(...))` earlier."""
        # Direct: ptr(ClassName(...))
        if (isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Name)
                and arg.func.id == "ptr"
                and arg.args):
            inner = arg.args[0]
            if (isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id in emitter.user_classes):
                return inner.func.id
            return None
        # Indirect: a variable name bound to ptr(ClassName(...))
        if isinstance(arg, ast.Name):
            return ptr_var_class.get(arg.id)
        return None

    def _class_ancestors(cls):
        """Return [cls, parent, grandparent, ...] following first parents."""
        chain = [cls]
        current = cls
        while current in emitter.class_bases:
            bases = emitter.class_bases[current]
            if not bases:
                break
            current = bases[0]   # follow first parent only
            chain.append(current)
        return chain

    def _common_ancestor(classes):
        """Find the common ancestor of a set of class names."""
        if not classes:
            return None
        # Get ancestors for the first class
        chain = _class_ancestors(classes[0])
        for cls in classes[1:]:
            other = set(_class_ancestors(cls))
            chain = [c for c in chain if c in other]
        return chain[0] if chain else None

    for i, node in enumerate(tree.body):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue
        if not isinstance(node.targets[0], ast.Name):
            continue
        if not isinstance(node.value, ast.List):
            continue
        if len(node.value.elts) != 0:
            continue
        var_name = node.targets[0].id

        appended_classes = []
        for later in tree.body[i+1:]:
            if not isinstance(later, ast.Expr):
                continue
            call = later.value
            if not isinstance(call, ast.Call):
                continue
            if not isinstance(call.func, ast.Attribute):
                continue
            if call.func.attr != "append":
                continue
            if not (isinstance(call.func.value, ast.Name)
                    and call.func.value.id == var_name):
                continue
            if not call.args:
                continue
            cls = _class_of_append_arg(call.args[0])
            if cls and cls not in appended_classes:
                appended_classes.append(cls)

        if not appended_classes:
            continue

        if len(appended_classes) == 1:
            elem = appended_classes[0]
        else:
            elem = _common_ancestor(appended_classes)
            if elem is None:
                raise TranspileError(
                    f"Pointer list '{var_name}' contains incompatible "
                    f"classes: {', '.join(appended_classes)}. "
                    f"They share no common ancestor."
                )
        emitter.pointer_list_vars[var_name] = elem

    # Pass 2: emit class definitions and function bodies.
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            emitter.visit(node)  # appends to emitter.classes
        elif isinstance(node, ast.FunctionDef):
            # Batch 27: skip shadowed defs (only the LAST def of each
            # name is emitted, matching Python semantics).
            if id(node) in emitter.shadowed_funcs:
                continue
            emitter.visit(node)  # appends to emitter.functions

    # Pass 3: emit main() body.
    main_lines = []
    # First, process any `import raylib` statements so needs_raylib is set
    # before any builtin call is transpiled.
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            emitter.visit(node)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            continue
        before = len(emitter.lines)
        emitter.visit(node)
        # Emitter already indented at level 1, but we re-indent again
        # below when writing to main(). Strip one level here.
        new_lines = emitter.lines[before:]
        #print(f"[DEBUG] {type(node).__name__}: {len(emitter.lines) - before} lines")
        for line in new_lines:
            main_lines.append(line[4:] if line.startswith("    ") else line)

    # Assemble the translation unit.
    raylib_include = ['#include "raylib.h"'] if emitter.needs_raylib else []
    optional_include = ['#include <optional>'] if emitter.use_optional else []
    parts = raylib_include + optional_include + [
        '#include <string>',
        '#include <iostream>',
        '#include <utility>',
        '#include <sstream>',
        '#include <iomanip>',
        '#include <vector>',
        '#include <map>',
        '#include <algorithm>',
        '#include <cctype>',
        '#include <cmath>',
        '#include <random>',
        '#include <chrono>',
        '#include <thread>',
        '#include <set>',
        '',
        "// Helper: format a double cleanly — no trailing zeros, no trailing dot.",
        "// Used by InterScript `str()` for numeric values.",
        "std::string format_float(double value) {",
        "    std::ostringstream oss;",
        "    oss << std::setprecision(15) << value;",
        "    std::string s = oss.str();",
        "    if (s.find('.') != std::string::npos) {",
        "        s.erase(s.find_last_not_of('0') + 1);",
        "        if (!s.empty() && s.back() == '.') s.pop_back();",
        "    }",
        "    return s;",
        "}",
        "",
        "// ---- String method helpers (Batch 2a) ----",
        "static std::string str_toupper(std::string s) {",
        "    for (auto& c : s) c = (char)std::toupper((unsigned char)c);",
        "    return s;",
        "}",
        "static std::string str_tolower(std::string s) {",
        "    for (auto& c : s) c = (char)std::tolower((unsigned char)c);",
        "    return s;",
        "}",
        "static std::string str_lstrip(std::string s) {",
        "    size_t i = 0;",
        "    while (i < s.size() && std::isspace((unsigned char)s[i])) i++;",
        "    return s.substr(i);",
        "}",
        "static std::string str_rstrip(std::string s) {",
        "    size_t i = s.size();",
        "    while (i > 0 && std::isspace((unsigned char)s[i-1])) i--;",
        "    return s.substr(0, i);",
        "}",
        "static std::string str_strip(std::string s) {",
        "    return str_rstrip(str_lstrip(s));",
        "}",
        "static bool str_startswith(const std::string& s, const std::string& p) {",
        "    return s.size() >= p.size() && s.compare(0, p.size(), p) == 0;",
        "}",
        "static bool str_endswith(const std::string& s, const std::string& p) {",
        "    return s.size() >= p.size() && s.compare(s.size()-p.size(), p.size(), p) == 0;",
        "}",
        "static std::string str_replace(std::string s, const std::string& from, const std::string& to) {",
        "    if (from.empty()) return s;",
        "    size_t pos = 0;",
        "    while ((pos = s.find(from, pos)) != std::string::npos) {",
        "        s.replace(pos, from.size(), to);",
        "        pos += to.size();",
        "    }",
        "    return s;",
        "}",
        "static std::vector<std::string> str_split(const std::string& s, const std::string& sep) {",
        "    std::vector<std::string> out;",
        "    if (sep.empty()) { out.push_back(s); return out; }",
        "    size_t pos = 0, prev = 0;",
        "    while ((pos = s.find(sep, prev)) != std::string::npos) {",
        "        out.push_back(s.substr(prev, pos - prev));",
        "        prev = pos + sep.size();",
        "    }",
        "    out.push_back(s.substr(prev));",
        "    return out;",
        "}",
        "static std::string str_join(const std::string& sep, const std::vector<std::string>& xs) {",
        "    std::string out;",
        "    for (size_t i = 0; i < xs.size(); ++i) {",
        "        if (i) out += sep;",
        "        out += xs[i];",
        "    }",
        "    return out;",
        "}",
        "static int str_find(const std::string& s, const std::string& p) {",
        "    auto pos = s.find(p);",
        "    return pos == std::string::npos ? -1 : (int)pos;",
        "}",
        "static int str_count(const std::string& s, const std::string& p) {",
        "    if (p.empty()) return 0;",
        "    int n = 0;",
        "    size_t pos = 0;",
        "    while ((pos = s.find(p, pos)) != std::string::npos) {",
        "        ++n;",
        "        pos += p.size();",
        "    }",
        "    return n;",
        "}",
        "",
        "// Batch 12: input() helper. Prints an optional prompt (no trailing",
        "// newline, matching Python), reads one line from stdin, returns it",
        "// without the trailing newline. Empty prompt means no output.",
        "static std::string input_line(const std::string& prompt) {",
        "    if (!prompt.empty()) {",
        "        std::cout << prompt << std::flush;",
        "    }",
        "    std::string line;",
        "    std::getline(std::cin, line);",
        "    return line;",
        "}",
        "// ---- f-string / .format() value coercion ----",
        "static std::string is_to_string(const std::string& s) { return s; }",
        "static std::string is_to_string(const char* s) { return std::string(s); }",
        "static std::string is_to_string(int n) { return std::to_string(n); }",
        "static std::string is_to_string(double d) { return format_float(d); }",
        "static std::string is_to_string(bool b) { return b ? \"True\" : \"False\"; }",
        "static std::string is_to_string(size_t n) { return std::to_string(n); }",
        "static std::string is_to_string(long long n) { return std::to_string(n); }",
        "static std::string is_to_string(unsigned int n) { return std::to_string(n); }",

        "// ---- // (floor division) helpers ----",
        "static int is_floordiv(int a, int b) {",
        "    return (int)std::floor((double)a / (double)b);",
        "}",
        "static double is_floordiv(double a, double b) {",
        "    return std::floor(a / b);",
        "}",

        "// Batch 7b: random helpers.",
        "static std::mt19937 g_rng(",
        "    (unsigned)std::chrono::steady_clock::now()"
        ".time_since_epoch().count()"
        ");",
        "static int rand_int(int lo, int hi) {",
        "    std::uniform_int_distribution<int> dist(lo, hi);",
        "    return dist(g_rng);",
        "}",
        "static double rand_float() {",
        "    std::uniform_real_distribution<double> dist(0.0, 1.0);",
        "    return dist(g_rng);",
        "}",
        "template <typename T>",
        "static T rand_choice(const std::vector<T>& xs) {",
        "    if (xs.empty()) {",
        "        throw std::runtime_error(\"random.choice on empty list\");",
        "    }",
        "    std::uniform_int_distribution<size_t> dist(0, xs.size() - 1);",
        "    return xs[dist(g_rng)];",
        "}",
        "template <typename T>",
        "static void rand_shuffle(std::vector<T>& xs) {",
        "    std::shuffle(xs.begin(), xs.end(), g_rng);",
        "}",
        "static void rand_seed(unsigned n) {",
        "    g_rng.seed(n);",
        "}",

        "// Batch 7c: time helpers.",
        "static double time_now() {",
        "    return std::chrono::duration<double>(",
        "        std::chrono::system_clock::now().time_since_epoch()",
        "    ).count();",
        "}",
        "static void time_sleep(double seconds) {",
        "    std::this_thread::sleep_for(",
        "        std::chrono::duration<double>(seconds)",
        "    );",
        "}",

        "// vec2 (std::pair<double,double>) arithmetic helpers.",
        "// Emitted by InterScript for vec2 + vec2, vec2 - vec2, vec2 * scalar.",
        "std::pair<double, double> vec2_add(std::pair<double, double> a, std::pair<double, double> b) {",
        "    return {a.first + b.first, a.second + b.second};",
        "}",
        "std::pair<double, double> vec2_sub(std::pair<double, double> a, std::pair<double, double> b) {",
        "    return {a.first - b.first, a.second - b.second};",
        "}",
        "std::pair<double, double> vec2_scale(std::pair<double, double> v, double s) {",
        "    return {v.first * s, v.second * s};",
        "}",
        "",
        "// String repetition: s * n and n * s.",
        "// Emitted by Kofty for `\"=\" * 40`, `\"ab\" * 3`, etc.",
        "static std::string str_repeat(const std::string& s, int n) {",
        "    if (n <= 0) return \"\";",
        "    std::string out;",
        "    out.reserve(s.size() * (size_t)n);",
        "    for (int i = 0; i < n; ++i) out += s;",
        "    return out;",
        "}",
        "",
        "// Vector concatenation: a + b for std::vector<T>.",
        "template <typename T>",
        "std::vector<T> vec_concat(const std::vector<T>& a, const std::vector<T>& b) {",
        "    std::vector<T> out = a;",
        "    out.insert(out.end(), b.begin(), b.end());",
        "    return out;",
        "}",
        "",
        "// Dict pop: remove and return the value for a key.",
        "template <typename K, typename V>",
        "V dict_pop(std::map<K, V>& m, const K& key) {",
        "    V value = m[key];",
        "    m.erase(key);",
        "    return value;",
        "}",
        "",
        "// Batch 9a: f-string format spec helpers.",
        "template <typename T>",
        "std::string fmt_float(T x, int precision) {",
        "    std::ostringstream oss;",
        "    oss << std::fixed << std::setprecision(precision) << x;",
        "    return oss.str();",
        "}",
        "",
        "template <typename T>",
        "std::string fmt_int_pad(T x, int width, char pad) {",
        "    std::ostringstream oss;",
        "    oss << std::setw(width) << std::setfill(pad) << x;",
        "    return oss.str();",
        "}",
        "",
        "template <typename T>",
        "std::string fmt_align(T x, int width, char align) {",
        "    std::ostringstream oss;",
        "    if (align == '<')      oss << std::left;",
        "    else if (align == '>') oss << std::right;",
        "    else                   oss << std::internal;",
        "    oss << std::setw(width) << x;",
        "    return oss.str();",
        "}",
        "",
        "template <typename T>",
        "std::string fmt_width_float(T x, int width, int precision) {",
        "    std::ostringstream oss;",
        "    oss << std::fixed << std::setprecision(precision)",
        "        << std::setw(width) << x;",
        "    return oss.str();",
        "}",
        "",
        "// Batch 9b: f-string format spec helpers, phase 2.",
        "template <typename S>",
        "std::string str_truncate(S s, int n) {",
        "    std::string str(s);",
        "    if ((int)str.size() > n) str.resize(n);",
        "    return str;",
        "}",
        "",
        "template <typename T>",
        "std::string fmt_int_base(T x, int base, bool upper) {",
        "    std::ostringstream oss;",
        "    if (base == 16) {",
        "        if (upper) oss << std::uppercase;",
        "        oss << std::hex << x;",
        "    } else if (base == 8) {",
        "        oss << std::oct << x;",
        "    } else if (base == 2) {",
        "        unsigned long long v = (unsigned long long)x;",
        "        std::string bits;",
        "        if (v == 0) {",
        "            bits = \"0\";",
        "        } else {",
        "            while (v > 0) {",
        "                bits = (char)('0' + (v & 1)) + bits;",
        "                v >>= 1;",
        "            }",
        "        }",
        "        return bits;",
        "    } else {",
        "        oss << x;",
        "    }",
        "    return oss.str();",
        "}",
        "",
        "template <typename T>",
        "std::string fmt_int_comma(T x) {",
        "    std::string s = std::to_string(x);",
        "    bool neg = (!s.empty() && s[0] == '-');",
        "    std::string digits = neg ? s.substr(1) : s;",
        "    std::string out;",
        "    int count = 0;",
        "    for (int i = (int)digits.size() - 1; i >= 0; --i) {",
        "        out = digits[i] + out;",
        "        if (++count == 3 && i > 0) {",
        "            out = \",\" + out;",
        "            count = 0;",
        "        }",
        "    }",
        "    return neg ? \"-\" + out : out;",
        "}",
        "",
        "// Forward declarations for repr_* so the container is_to_string",
        "// overloads below can call them before their full definitions.",
        "template <typename T>",
        "std::string repr_vector(const std::vector<T>&);",
        "template <typename K, typename V>",
        "std::string repr_map(const std::map<K, V>&);",
        "template <typename T>",
        "std::string repr_set(const std::set<T>&);",
        "template <typename T1, typename T2>",
        "std::string repr_pair(const std::pair<T1, T2>&);",
        "template <typename... Ts>",
        "std::string repr_tuple(const std::tuple<Ts...>&);",
        "",
        "// Batch 10h: is_to_string overloads for containers, so that",
        "// f-strings and str() work on lists, dicts, sets, pairs, tuples.",
        "// These must appear after the repr_* definitions above.",
        "template <typename T>",
        "std::string is_to_string(const std::vector<T>& v) { return repr_vector(v); }",
        "template <typename K, typename V>",
        "std::string is_to_string(const std::map<K, V>& m) { return repr_map(m); }",
        "template <typename T>",
        "std::string is_to_string(const std::set<T>& s) { return repr_set(s); }",
        "template <typename T1, typename T2>",
        "std::string is_to_string(const std::pair<T1, T2>& p) { return repr_pair(p); }",
        "template <typename... Ts>",
        "std::string is_to_string(const std::tuple<Ts...>& t) { return repr_tuple(t); }",
        "// Batch 10a: container reprs for print(container).",
        "template <typename T>",
        "std::string repr_vector(const std::vector<T>& v) {",
        "    std::string out = \"[\";",
        "    for (size_t i = 0; i < v.size(); ++i) {",
        "        if (i > 0) out += \", \";",
        "        out += is_to_string(v[i]);",
        "    }",
        "    out += \"]\";",
        "    return out;",
        "}",
        "",
        "template <typename K, typename V>",
        "std::string repr_map(const std::map<K, V>& m) {",
        "    std::string out = \"{\";",
        "    bool first = true;",
        "    for (const auto& kv : m) {",
        "        if (!first) out += \", \";",
        "        first = false;",
        "        out += \"'\" + is_to_string(kv.first) + \"': \" + is_to_string(kv.second);",
        "    }",
        "    out += \"}\";",
        "    return out;",
        "}",
        "",
        "template <typename T>",
        "std::string repr_set(const std::set<T>& s) {",
        "    std::string out = \"{\";",
        "    bool first = true;",
        "    for (const auto& x : s) {",
        "        if (!first) out += \", \";",
        "        first = false;",
        "        out += is_to_string(x);",
        "    }",
        "    out += \"}\";",
        "    return out;",
        "}",
        "",
        "template <typename T1, typename T2>",
        "std::string repr_pair(const std::pair<T1, T2>& p) {",
        "    return \"(\" + is_to_string(p.first) + \", \" + is_to_string(p.second) + \")\";",
        "}",
        "",
        "#include <tuple>",
        "template <typename Tuple, std::size_t... I>",
        "std::string repr_tuple_impl(const Tuple& t, std::index_sequence<I...>) {",
        "    std::string out = \"(\";",
        "    std::string sep = \"\";",
        "    ((out += sep + is_to_string(std::get<I>(t)), sep = \", \"), ...);",
        "    out += \")\";",
        "    return out;",
        "}",
        "",
        "template <typename... Ts>",
        "std::string repr_tuple(const std::tuple<Ts...>& t) {",
        "    return repr_tuple_impl(t, std::index_sequence_for<Ts...>{});",
        "}",
        "",
        "// ---- Batch 10c: title / capitalize / isalpha / isdigit ----",
        "static std::string str_title(std::string s) {",
        "    bool new_word = true;",
        "    for (auto& c : s) {",
        "        if (std::isalpha((unsigned char)c)) {",
        "            if (new_word) c = (char)std::toupper((unsigned char)c);",
        "            else          c = (char)std::tolower((unsigned char)c);",
        "            new_word = false;",
        "        } else {",
        "            new_word = true;",
        "        }",
        "    }",
        "    return s;",
        "}",
        "",
        "static std::string str_capitalize(std::string s) {",
        "    bool first = true;",
        "    for (auto& c : s) {",
        "        if (first) {",
        "            c = (char)std::toupper((unsigned char)c);",
        "            first = false;",
        "        } else {",
        "            c = (char)std::tolower((unsigned char)c);",
        "        }",
        "    }",
        "    return s;",
        "}",
        "",
        "static bool str_isalpha(const std::string& s) {",
        "    if (s.empty()) return false;",
        "    for (char c : s) {",
        "        if (!std::isalpha((unsigned char)c)) return false;",
        "    }",
        "    return true;",
        "}",
        "",
        "static bool str_isdigit(const std::string& s) {",
        "    if (s.empty()) return false;",
        "    for (char c : s) {",
        "        if (!std::isdigit((unsigned char)c)) return false;",
        "    }",
        "    return true;",
        "}",
        "",
        "// List pop: remove and return the last element (Batch 8f).",
        "template <typename T>",
        "T vec_pop(std::vector<T>& v) {",
        "    if (v.empty()) {",
        "        throw std::out_of_range(\"pop from empty list\");",
        "    }",
        "    T last = v.back();",
        "    v.pop_back();",
        "    return last;",
        "}",
        "",
        "// List pop at index: remove and return element at index i (Batch 8g).",
        "// Negative indices count from the end (-1 == last element).",
        "// Batch 10b: out-of-range indices throw std::out_of_range.",
        "template <typename T>",
        "T vec_pop_at(std::vector<T>& v, int i) {",
        "    if (i < 0) i += (int)v.size();",
        "    if (i < 0 || i >= (int)v.size()) {",
        "        throw std::out_of_range(\"pop index out of range\");",
        "    }",
        "    T val = v[i];",
        "    v.erase(v.begin() + i);",
        "    return val;",
        "}",
        "",
        "// Set operations.",
        "template <typename T>",
        "std::set<T> set_op_union(const std::set<T>& a, const std::set<T>& b) {",
        "    std::set<T> out;",
        "    std::set_union(a.begin(), a.end(), b.begin(), b.end(),",
        "                   std::inserter(out, out.begin()));",
        "    return out;",
        "}",
        "template <typename T>",
        "std::set<T> set_op_intersection(const std::set<T>& a, const std::set<T>& b) {",
        "    std::set<T> out;",
        "    std::set_intersection(a.begin(), a.end(), b.begin(), b.end(),",
        "                          std::inserter(out, out.begin()));",
        "    return out;",
        "}",
        "template <typename T>",
        "std::set<T> set_op_difference(const std::set<T>& a, const std::set<T>& b) {",
        "    std::set<T> out;",
        "    std::set_difference(a.begin(), a.end(), b.begin(), b.end(),",
        "                        std::inserter(out, out.begin()));",
        "    return out;",
        "}",
        "template <typename T>",
        "std::set<T> set_op_symdiff(const std::set<T>& a, const std::set<T>& b) {",
        "    std::set<T> out;",
        "    std::set_symmetric_difference(a.begin(), a.end(), b.begin(), b.end(),",
        "                                  std::inserter(out, out.begin()));",
        "    return out;",
        "}",
        "",
        '\n\n'.join(emitter.classes),
        '',
        # Batch 22: global scalar declarations — BEFORE functions,
        # so functions that read them see the declaration.
        '\n'.join(
            f"{_t} {_n};" for _n, _t in emitter.global_vars.items()
        ),
        '',
        '\n\n'.join(emitter.functions),
        '',
        'int main() {',
    ]
    parts.extend("    " * 1 + l for l in main_lines)
    if emitter.needs_raylib:
        parts.append('    if (IsWindowReady()) CloseWindow();')
    parts.extend([
        '    return 0;',
        '}',
    ])
    return "\n".join(p for p in parts if p is not None)
