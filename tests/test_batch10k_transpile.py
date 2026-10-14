"""Batch 10k: class-typed parameters and fields in method bodies."""
from kofty.transpiler import transpile


def test_class_param_field_access():
    out = transpile(
        "class P:\n"
        "    def __init__(self, x: int):\n"
        "        self.x = x\n"
        "def f(p: P):\n"
        "    return p.x\n"
    )
    # Field read works (this was already working; verify not broken).
    assert "p.x" in out


def test_class_param_property_access_calls_getter():
    out = transpile(
        "class P:\n"
        "    def __init__(self, x: int):\n"
        "        self.x = x\n"
        "    @property\n"
        "    def dbl(self):\n"
        "        return self.x * 2\n"
        "def f(p: P):\n"
        "    return p.dbl\n"
    )
    # Property read must emit a call, not a member-function pointer.
    assert "p.dbl()" in out
    assert "p.dbl;" not in out  # sanity: no bare reference


def test_class_param_in_fstring_dispatches_str():
    out = transpile(
        "class P:\n"
        "    def __init__(self, x: int):\n"
        "        self.x = x\n"
        "    def __str__(self):\n"
        "        return 'P'\n"
        "def f(p: P):\n"
        "    print(f'x = {p}')\n"
    )
    # f-string should call __str__(), not is_to_string(p).
    assert "p.__str__()" in out
    assert "is_to_string(p)" not in out


def test_class_param_in_fstring_with_property():
    out = transpile(
        "class P:\n"
        "    def __init__(self, x: int):\n"
        "        self.x = x\n"
        "    @property\n"
        "    def dbl(self):\n"
        "        return self.x * 2\n"
        "def f(p: P):\n"
        "    print(f'd = {p.dbl}')\n"
    )
    assert "p.dbl()" in out

def test_class_field_in_method_fstring_dispatches_str():
    out = transpile(
        "class P:\n"
        "    def __init__(self, x: int):\n"
        "        self.x = x\n"
        "    def __str__(self):\n"
        "        return 'P'\n"
        "class C:\n"
        "    def __init__(self, p: P):\n"
        "        self.p = p\n"
        "    def __str__(self):\n"
        "        return f'C({self.p})'\n"
    )
    assert "this->p.__str__()" in out
    assert "is_to_string(this->p)" not in out


def test_class_field_primitive_in_method_fstring_unchanged():
    out = transpile(
        "class C:\n"
        "    def __init__(self, n: int):\n"
        "        self.n = n\n"
        "    def __str__(self):\n"
        "        return f'C({self.n})'\n"
    )
    assert "is_to_string(this->n)" in out
