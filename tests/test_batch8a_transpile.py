"""tests/test_batch8h Phase 5a: transpile-only companion to test_batch8a.py.

Verifies the C++ emitted for __eq__ on user classes.

    def __eq__(self, other): ...   ->   bool operator==(const T& other) const
"""

from kofty.transpiler import transpile


POINT_SRC_TEMPLATE = """
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

p1 = Point(3, 4)
p2 = Point(3, 4)
if p1 == p2:
    print("equal")
"""


# ===========================================================================
# Basic: __eq__ emits operator==
# ===========================================================================

def test_eq_true_emits_operator():
    out = transpile(POINT_SRC_TEMPLATE)
    # Emitter turns __eq__ into: bool operator==(const Point& <name>) const
    assert "operator==" in out
    assert "Point" in out


def test_eq_false_emits_operator():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

p1 = Point(3, 4)
p2 = Point(3, 5)
if p1 == p2:
    print("equal")
""")
    assert "operator==" in out


def test_eq_different_first_field_emits_operator():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

p1 = Point(9, 4)
p2 = Point(3, 4)
if p1 == p2:
    print("equal")
""")
    assert "operator==" in out


# ===========================================================================
# Comparison uses p1 == p2 in emitted C++
# ===========================================================================

def test_eq_result_printed_emits_comparison():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

p1 = Point(1, 2)
p2 = Point(1, 2)
print(p1 == p2)
""")
    # The comparison must be emitted as `p1 == p2` in the print statement.
    assert "p1 == p2" in out or "(p1 == p2)" in out


# ===========================================================================
# Parameter name independence
# ===========================================================================

def test_eq_param_named_rhs_emits_operator():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __eq__(self, rhs):
        return self.x == rhs.x and self.y == rhs.y

p1 = Point(1, 2)
p2 = Point(1, 2)
if p1 == p2:
    print("yes")
""")
    assert "operator==" in out
    # The parameter name must appear in the emitted signature.
    assert "rhs" in out


# ===========================================================================
# Multiple instances
# ===========================================================================

def test_eq_multiple_instances_emits_single_operator():
    out = transpile("""
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

a = Point(1, 1)
b = Point(1, 1)
c = Point(2, 2)
if a == b:
    print("ab equal")
if b == c:
    print("bc equal")
if a == c:
    print("ac equal")
""")
    # __eq__ is emitted once, regardless of how many comparisons.
    assert out.count("operator==") == 1


# ===========================================================================
# __eq__ alongside other methods
# ===========================================================================

def test_eq_alongside_other_methods_emits_both():
    out = transpile("""
class Counter:
    def __init__(self, n):
        self.n = n
    def __eq__(self, other):
        return self.n == other.n
    def increment(self):
        self.n = self.n + 1

c1 = Counter(5)
c2 = Counter(5)
c1.increment()
if c1 == c2:
    print("equal")
""")
    assert "operator==" in out
    # increment should still be emitted as a normal method.
    assert "increment" in out
