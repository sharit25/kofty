"""tests/test_batch5a.py

Batch 5a: default arguments.

Scope:
    def f(a, b=10):            b has a default
    def f(a, b=10, c="x"):     multiple defaults
    f(1)                       b and c use defaults
    f(1, 2)                    only c uses its default
    f(1, 2, "y")               all overridden

OUT OF SCOPE (deferred to later batches):
    - *args / **kwargs
    - keyword args at the call site (f(b=2))
    - lambdas
    - mutable default args (Python footgun)
    - defaults on class methods (later batch)
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
# One default arg
# ===========================================================================

def test_default_used(tmp_path):
    assert_runs("""
        def greet(name, greeting="Hello"):
            print(greeting + ", " + name)

        greet("Alice")
    """, "Hello, Alice", tmp_path)


def test_default_overridden(tmp_path):
    assert_runs("""
        def greet(name, greeting="Hello"):
            print(greeting + ", " + name)

        greet("Bob", "Hi")
    """, "Hi, Bob", tmp_path)


def test_default_int(tmp_path):
    assert_runs("""
        def add(a, b=10):
            print(a + b)

        add(5)
        add(5, 100)
    """, "15\n105", tmp_path)


# ===========================================================================
# Multiple defaults
# ===========================================================================

def test_two_defaults_both_used(tmp_path):
    assert_runs("""
        def f(a, b=2, c=3):
            print(a * 100 + b * 10 + c)

        f(1)
    """, "123", tmp_path)


def test_two_defaults_one_overridden(tmp_path):
    assert_runs("""
        def f(a, b=2, c=3):
            print(a * 100 + b * 10 + c)

        f(1, 9)
    """, "193", tmp_path)


def test_two_defaults_both_overridden(tmp_path):
    assert_runs("""
        def f(a, b=2, c=3):
            print(a * 100 + b * 10 + c)

        f(1, 9, 8)
    """, "198", tmp_path)


# ===========================================================================
# Mixed types
# ===========================================================================

def test_default_str(tmp_path):
    assert_runs("""
        def greet(name, greeting="Hello", punctuation="!"):
            print(greeting + ", " + name + punctuation)

        greet("Alice")
        greet("Bob", "Hi")
        greet("Carol", "Hey", "?")
    """, "Hello, Alice!\nHi, Bob!\nHey, Carol?", tmp_path)


def test_default_float(tmp_path):
    assert_runs("""
        def scale(x, factor=2.0):
            print(x * factor)

        scale(5)
        scale(5, 3.0)
    """, "10\n15", tmp_path)


# ===========================================================================
# Called from within another function
# ===========================================================================

def test_default_in_call_chain(tmp_path):
    assert_runs("""
        def base(a, b=100):
            return a + b

        def wrap(x):
            return base(x)

        print(wrap(5))
        print(base(5, 200))
    """, "105\n205", tmp_path)


# ===========================================================================
# Default arg used in an expression
# ===========================================================================

def test_default_used_in_expression(tmp_path):
    assert_runs("""
        def power(base, exp=2):
            return base ** exp

        print(power(3))
        print(power(3, 3))
    """, "9\n27", tmp_path)


# ===========================================================================
# Multiple calls with different defaults
# ===========================================================================

def test_default_repeated_calls(tmp_path):
    assert_runs("""
        def tag(s, prefix="[", suffix="]"):
            print(prefix + s + suffix)

        tag("a")
        tag("b")
        tag("c", "<")
        tag("d", "<", ">")
    """, "[a]\n[b]\n<c]\n<d>", tmp_path)
