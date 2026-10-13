"""tests/test_batch8h Phase 5a: transpile-only companion to test_batch8b.py.

Verifies the C++ emitted for __str__ on user classes.

    def __str__(self): ...  ->  std::string __str__() const

    print(obj)  ->  std::cout << obj.__str__() << std::endl
    str(obj)    ->  obj.__str__()

    print(obj) with no __str__ -> TranspileError naming the class.
"""

from kofty.transpiler import transpile


# ===========================================================================
# Basic: __str__ returns a literal
# ===========================================================================

def test_str_literal_emits_str_method():
    out = transpile("""
class Greeter:
    def __init__(self):
        pass
    def __str__(self):
        return "hello"

g = Greeter()
print(g)
""")
    # Emitter renames __str__ to a normal method `__str__()` (with the
    # double-underscore name kept as-is, C++ allows leading underscores).
    assert "__str__" in out
    assert "std::string" in out


# ===========================================================================
# print(obj) dispatches through __str__
# ===========================================================================

def test_str_uses_field_emits_dispatch():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __str__(self):
        return f"({self.x}, {self.y})"

p = Point(3, 4)
print(p)
""")
    # print(p) must be rewritten to use __str__().
    assert "__str__()" in out
    assert "std::cout" in out


# ===========================================================================
# str(obj) builtin
# ===========================================================================

def test_str_via_builtin_emits_str_call():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __str__(self):
        return f"({self.x}, {self.y})"

p = Point(1, 2)
print(str(p))
""")
    assert "__str__()" in out


# ===========================================================================
# Concatenation: "prefix: " + str(obj)
# ===========================================================================

def test_str_concat_emits_string_concat():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __str__(self):
        return f"({self.x}, {self.y})"

p = Point(5, 6)
print("point: " + str(p))
""")
    assert "point: " in out
    assert "__str__()" in out


# ===========================================================================
# Multiple instances
# ===========================================================================

def test_str_multiple_instances_emits_single_method():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __str__(self):
        return f"({self.x}, {self.y})"

a = Point(1, 1)
b = Point(2, 2)
print(a)
print(b)
""")
    # __str__ is a method on the class; only one definition.
    assert out.count("std::string __str__()") == 1
    # Two print call sites, both rewritten.
    assert out.count("__str__()") >= 3


# ===========================================================================
# __str__ alongside other methods
# ===========================================================================

def test_str_alongside_other_methods_emits_both():
    out = transpile("""
class Counter:
    def __init__(self, n):
        self.n = n
    def increment(self):
        self.n = self.n + 1
    def __str__(self):
        return f"Counter({self.n})"

c = Counter(5)
c.increment()
print(c)
""")
    assert "increment" in out
    assert "__str__" in out


# ===========================================================================
# Missing __str__ -> TranspileError naming the class
# ===========================================================================

def test_str_missing_raises():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError) as exc:
        transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
print(p)
""")
    # Error message must mention the class name.
    assert "Point" in str(exc.value)


# ===========================================================================
# Optional -> str annotation accepted
# ===========================================================================

def test_str_annotation_str_emits_str_method():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

p = Point(7, 8)
print(p)
""")
    assert "__str__" in out
    assert "std::string" in out
