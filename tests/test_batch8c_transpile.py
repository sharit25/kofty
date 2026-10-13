"""tests/test_batch8h Phase 5b: transpile-only companion to test_batch8c.py.

Verifies the C++ emitted for __add__ on user classes.

    def __add__(self, other): ...  ->  <Class> operator+(const <Class>& other) const
"""

from kofty.transpiler import transpile


# ===========================================================================
# Basic: __add__ emits operator+
# ===========================================================================

def test_add_fields_sum_emits_operator():
    out = transpile("""
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __add__(self, other):
        return Vec(self.x + other.x, self.y + other.y)

a = Vec(1, 2)
b = Vec(3, 4)
c = a + b
""")
    assert "operator+" in out
    # The signature must be Vec operator+(const Vec& ...) const
    assert "const Vec&" in out


def test_add_identity_emits_operator():
    out = transpile("""
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __add__(self, other):
        return Vec(self.x + other.x, self.y + other.y)

a = Vec(5, 7)
z = Vec(0, 0)
d = a + z
""")
    assert "operator+" in out


def test_add_chain_emits_operator():
    out = transpile("""
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __add__(self, other):
        return Vec(self.x + other.x, self.y + other.y)

a = Vec(1, 1)
b = Vec(2, 2)
c = Vec(3, 3)
d = a + b + c
""")
    assert "operator+" in out
    # Chain: at least two + operators in the C++ expression.
    assert out.count("+") >= 2


def test_add_multiple_instances_emits_single_operator():
    out = transpile("""
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __add__(self, other):
        return Vec(self.x + other.x, self.y + other.y)
    def __str__(self):
        return f"({self.x}, {self.y})"

a = Vec(1, 1)
b = Vec(10, 20)
c = Vec(100, 200)
print(a + b)
print(b + c)
print(c + a)
""")
    # __add__ defined once, so only one operator+ definition.
    assert out.count("operator+") == 1


# ===========================================================================
# __add__ alongside other dunders
# ===========================================================================

def test_add_with_eq_and_other_methods_emits_all():
    out = transpile("""
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __add__(self, other):
        return Vec(self.x + other.x, self.y + other.y)
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    def scale(self, k):
        self.x = self.x * k
        self.y = self.y * k

a = Vec(1, 2)
b = Vec(3, 4)
c = a + b
if c == Vec(4, 6):
    print("ok")
c.scale(2)
print(c.x)
""")
    assert "operator+" in out
    assert "operator==" in out
    assert "scale" in out


# ===========================================================================
# Missing __add__ -> TranspileError
# ===========================================================================

def test_add_missing_raises():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError) as exc:
        transpile("""
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y

a = Vec(1, 2)
b = Vec(3, 4)
c = a + b
""")
    assert "Vec" in str(exc.value)


# ===========================================================================
# Different classes -> TranspileError
# ===========================================================================

def test_add_different_classes_raises():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError):
        transpile("""
class Foo:
    def __init__(self, n):
        self.n = n
    def __add__(self, other):
        return Foo(self.n + other.n)

class Bar:
    def __init__(self, n):
        self.n = n
    def __add__(self, other):
        return Bar(self.n + other.n)

f = Foo(1)
b = Bar(2)
c = f + b
""")


# ===========================================================================
# Result reused: c = a + b, then c + a
# ===========================================================================

def test_add_result_reused_emits_registered():
    out = transpile("""
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __add__(self, other):
        return Vec(self.x + other.x, self.y + other.y)

a = Vec(1, 2)
b = Vec(3, 4)
c = a + b
d = c + a
print(d.x)
""")
    # c must be registered as a Vec so c + a uses operator+.
    assert "operator+" in out
