"""tests/test_batch8b.py

Batch 8b: __str__ on user classes.

Design (Option 2 — named method, special-cased call sites):

    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        def __str__(self):
            return f"({self.x}, {self.y})"

    -> struct Point {
           int x;
           int y;
           Point(int x, int y) : x(x), y(y) {}
           std::string __str__() const {
               return (std::string("(") + ...);  // whatever the body emits
           }
       };

    Call-site rewriting (in _call_expr):
      print(obj)     ->  std::cout << obj.__str__() << std::endl;
      str(obj)       ->  obj.__str__()

    Strictness:
      - If print(obj) / str(obj) is used on a class with no __str__,
        raise TranspileError naming the class.
      - __str__ may be written with no annotation (emitter emits
        std::string) or with `-> str` (accepted). `-> <other>` is an
        error.

OUT OF SCOPE (deferred):
    - __repr__
    - __str__ on classes with a base class that also defines __str__
    - __str__ for print() of containers containing user objects
    - implicit C++ conversion operator (deliberately not used — see
      handoff Batch 8b design note)
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
# Basic: __str__ returns a literal
# ===========================================================================

def test_str_literal(tmp_path):
    assert_runs("""
        class Greeter:
            def __init__(self):
                pass
            def __str__(self):
                return "hello"

        g = Greeter()
        print(g)
    """, "hello", tmp_path)


# ===========================================================================
# __str__ uses self.field
# ===========================================================================

def test_str_uses_field(tmp_path):
    assert_runs("""
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __str__(self):
                return f"({self.x}, {self.y})"

        p = Point(3, 4)
        print(p)
    """, "(3, 4)", tmp_path)


# ===========================================================================
# str(obj) builtin routes through __str__
# ===========================================================================

def test_str_via_builtin(tmp_path):
    assert_runs("""
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __str__(self):
                return f"({self.x}, {self.y})"

        p = Point(1, 2)
        print(str(p))
    """, "(1, 2)", tmp_path)


# ===========================================================================
# Concatenation: "prefix: " + str(obj)
# ===========================================================================

def test_str_concat(tmp_path):
    assert_runs("""
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __str__(self):
                return f"({self.x}, {self.y})"

        p = Point(5, 6)
        print("point: " + str(p))
    """, "point: (5, 6)", tmp_path)


# ===========================================================================
# Multiple instances -> distinct output
# ===========================================================================

def test_str_multiple_instances(tmp_path):
    assert_runs("""
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
    """, "(1, 1)\n(2, 2)", tmp_path)


# ===========================================================================
# __str__ alongside other methods
# ===========================================================================

def test_str_alongside_other_methods(tmp_path):
    assert_runs("""
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
    """, "Counter(6)", tmp_path)


# ===========================================================================
# Missing __str__ -> transpile error naming the class
# ===========================================================================

def test_str_missing_raises(tmp_path):
    assert_transpile_fails("""
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        p = Point(1, 2)
        print(p)
    """, "Point", tmp_path)


# ===========================================================================
# Optional -> str annotation is accepted
# ===========================================================================

def test_str_annotation_str(tmp_path):
    assert_runs("""
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def __str__(self) -> str:
                return f"({self.x}, {self.y})"

        p = Point(7, 8)
        print(p)
    """, "(7, 8)", tmp_path)
