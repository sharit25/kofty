"""tests/test_batch8c.py

Batch 8c: __add__ on user classes.

Design (Option a — same-class operand only, mirroring 8a/8b):

    class Vec:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        def __add__(self, other):
            return Vec(self.x + other.x, self.y + other.y)

    -> struct Vec {
           int x;
           int y;
           Vec(int x, int y) : x(x), y(y) {}
           Vec operator+(const Vec& other) const {
               return Vec((this->x + other.x), (this->y + other.y));
           }
       };

    Then `v1 + v2` in source compiles to `v1 + v2` in C++, dispatching
    to operator+.

    Call-site rule: both operands must be Names in instance_vars of the
    same class. Otherwise: TranspileError.

OUT OF SCOPE (deferred):
    - T + scalar (int/float/str)
    - scalar + T (reflected __radd__)
    - T + <different-class>
    - __sub__, __mul__, __truediv__, __neg__
    - __iadd__ (augmented a += b)
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


def assert_transpile_fails(src: str, needle: str, tmp_path):
    rc, out, err = run_is(src, tmp_path)
    assert rc != 0, (
        f"expected transpile/compile to fail, but it succeeded.\n"
        f"STDOUT:\n{out}\nSTDERR:\n{err}"
    )
    combined = out + err
    assert needle in combined, (
        f"expected error to mention {needle!r}.\n"
        f"STDOUT:\n{out}\nSTDERR:\n{err}"
    )


# ===========================================================================
# Basic: a + b produces a new instance with summed fields
# ===========================================================================

def test_add_fields_sum(tmp_path):
    assert_runs("""
        class Vec:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __add__(self, other):
                return Vec(self.x + other.x, self.y + other.y)
            def __str__(self):
                return f"({self.x}, {self.y})"

        a = Vec(1, 2)
        b = Vec(3, 4)
        c = a + b
        print(c)
    """, "(4, 6)", tmp_path)


# ===========================================================================
# Identity: adding zero gives the same field values
# ===========================================================================

def test_add_identity(tmp_path):
    assert_runs("""
        class Vec:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __add__(self, other):
                return Vec(self.x + other.x, self.y + other.y)
            def __str__(self):
                return f"({self.x}, {self.y})"

        a = Vec(5, 7)
        z = Vec(0, 0)
        print(a + z)
    """, "(5, 7)", tmp_path)


# ===========================================================================
# Chain: (a + b) + c
# ===========================================================================

def test_add_chain(tmp_path):
    assert_runs("""
        class Vec:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __add__(self, other):
                return Vec(self.x + other.x, self.y + other.y)
            def __str__(self):
                return f"({self.x}, {self.y})"

        a = Vec(1, 1)
        b = Vec(2, 2)
        c = Vec(3, 3)
        d = a + b + c
        print(d)
    """, "(6, 6)", tmp_path)


# ===========================================================================
# Multiple instances, different results
# ===========================================================================

def test_add_multiple_instances(tmp_path):
    assert_runs("""
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
    """, "(11, 21)\n(110, 220)\n(101, 201)", tmp_path)


# ===========================================================================
# __add__ alongside other dunders and methods
# ===========================================================================

def test_add_with_eq_and_other_methods(tmp_path):
    assert_runs("""
        class Vec:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __add__(self, other):
                return Vec(self.x + other.x, self.y + other.y)
            def __eq__(self, other):
                return self.x == other.x and self.y == other.y
            def __str__(self):
                return f"({self.x}, {self.y})"
            def scale(self, k):
                self.x = self.x * k
                self.y = self.y * k

        a = Vec(1, 2)
        b = Vec(3, 4)
        c = a + b
        if c == Vec(4, 6):
            print("correct")
        else:
            print("wrong")
        c.scale(2)
        print(c)
    """, "correct\n(8, 12)", tmp_path)


# ===========================================================================
# Missing __add__ -> transpile error naming the class
# ===========================================================================

def test_add_missing_raises(tmp_path):
    assert_transpile_fails("""
        class Vec:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        a = Vec(1, 2)
        b = Vec(3, 4)
        c = a + b
    """, "Vec", tmp_path)


# ===========================================================================
# Different classes -> transpile error
# ===========================================================================

def test_add_different_classes_raises(tmp_path):
    assert_transpile_fails("""
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
    """, "Foo", tmp_path)


# ===========================================================================
# Result reused: c = a + b, then c + a
# ===========================================================================

def test_add_result_reused(tmp_path):
    assert_runs("""
        class Vec:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __add__(self, other):
                return Vec(self.x + other.x, self.y + other.y)
            def __str__(self):
                return f"({self.x}, {self.y})"

        a = Vec(1, 2)
        b = Vec(3, 4)
        c = a + b
        d = c + a
        print(d)
    """, "(5, 8)", tmp_path)
