"""tests/test_batch8a.py

Batch 8a: __eq__ on user classes.

Design:
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        def __eq__(self, other):
            return self.x == other.x and self.y == other.y

    -> struct Point {
           int x;
           int y;
           Point(int x, int y) : x(x), y(y) {}
           bool operator==(const Point& other) const {
               return (this->x == other.x) && (this->y == other.y);
           }
       };

    Then `p1 == p2` in the source compiles to `p1 == p2` in C++, which
    dispatches to the operator.

OUT OF SCOPE (deferred):
    - != -- only __eq__ is emitted
    - __lt__, __gt__, __le__, __ge__
    - __hash__
    - __eq__ with mixed-type parameter (int, etc.)
    - __eq__ on classes with a base class that also defines __eq__
"""

import shutil
import subprocess
import sys
import textwrap

import pytest


def run_is(src: str, tmp_path) -> tuple[int, str, str]:
    if shutil.which("g++") is None:
        pytest.skip("g++ not on PATH")
    src = textwrap.dedent(src).strip() + "\n"
    is_file = tmp_path / "prog.kfy"
    is_file.write_text(src)
    result = subprocess.run(
        [sys.executable, "-m", "kofty.cli", str(is_file)],
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout, result.stderr


def assert_runs(src: str, expected_stdout: str, tmp_path):
    rc, out, err = run_is(src, tmp_path)
    assert rc == 0, f"transpile/compile failed:\nSTDERR:\n{err}\nSTDOUT:\n{out}"
    user_lines = [
        line for line in out.splitlines()
        if not line.startswith("[InterScript]")
    ]
    actual = "\n".join(user_lines).strip()
    expected = expected_stdout.strip()
    assert actual == expected, (
        f"\n--- expected ---\n{expected}\n"
        f"--- actual ---\n{actual}\n"
        f"--- raw stdout ---\n{out}\n"
        f"--- stderr ---\n{err}"
    )


# ===========================================================================
# Basic: equality
# ===========================================================================

def test_eq_true(tmp_path):
    assert_runs("""
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
        else:
            print("not equal")
    """, "equal", tmp_path)


def test_eq_false(tmp_path):
    assert_runs("""
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
        else:
            print("not equal")
    """, "not equal", tmp_path)


def test_eq_different_first_field(tmp_path):
    assert_runs("""
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
        else:
            print("not equal")
    """, "not equal", tmp_path)


# ===========================================================================
# Truthy/falsy result
# ===========================================================================

def test_eq_result_printed(tmp_path):
    # Print the boolean result directly.
    assert_runs("""
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __eq__(self, other):
                return self.x == other.x and self.y == other.y

        p1 = Point(1, 2)
        p2 = Point(1, 2)
        print(p1 == p2)
    """, "1", tmp_path)


# ===========================================================================
# Different parameter name
# ===========================================================================

def test_eq_param_named_rhs(tmp_path):
    assert_runs("""
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
    """, "yes", tmp_path)


# ===========================================================================
# String fields
# ===========================================================================

@pytest.mark.xfail(
    reason="constructor param type inference: `self.name = name` gives no "
           "type signal, so `name` is emitted as `int` and `Named(\"alice\")` "
           "fails to compile. Pre-existing, unrelated to __eq__. "
           "Tracked as: constructor param inference from str literals.",
    strict=True,
)
def test_eq_string_fields(tmp_path):
    assert_runs("""
        class Named:
            def __init__(self, name):
                self.name = name
            def __eq__(self, other):
                return self.name == other.name

        a = Named("alice")
        b = Named("alice")
        c = Named("bob")
        if a == b:
            print("same")
        if a == c:
            print("same")
        else:
            print("different")
    """, "same\ndifferent", tmp_path)

# ===========================================================================
# Multiple instances
# ===========================================================================

def test_eq_multiple_instances(tmp_path):
    assert_runs("""
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
        else:
            print("bc not equal")
        if a == c:
            print("ac equal")
        else:
            print("ac not equal")
    """, "ab equal\nbc not equal\nac not equal", tmp_path)


# ===========================================================================
# __eq__ on a class that also has other methods
# ===========================================================================

def test_eq_alongside_other_methods(tmp_path):
    assert_runs("""
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
        else:
            print("not equal")
    """, "not equal", tmp_path)
