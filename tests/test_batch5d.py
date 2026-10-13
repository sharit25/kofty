"""tests/test_batch5d.py

Batch 5d: lambdas.

Design:
    x = lambda a: a * 2       -> auto x = [&](auto a) { return a * 2; };
    f = lambda a, b: a + b    -> auto f = [&](auto a, auto b) { return a + b; };

Lambdas capture all outer variables by reference ([&]). Params are
untyped (auto). Bodies are single expressions.

OUT OF SCOPE (deferred to later batches):
    - multi-statement lambda bodies
    - default args / *args / **kwargs in lambdas
    - lambdas passed directly as function arguments
    - type annotations on lambda params
    - immediate invocation: (lambda x: x*2)(5)
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
# Basic lambda
# ===========================================================================

def test_lambda_one_param(tmp_path):
    assert_runs("""
        twice = lambda x: x * 2
        print(twice(5))
    """, "10", tmp_path)


def test_lambda_two_params(tmp_path):
    assert_runs("""
        add = lambda a, b: a + b
        print(add(3, 4))
    """, "7", tmp_path)


def test_lambda_zero_params(tmp_path):
    assert_runs("""
        f = lambda: 42
        print(f())
    """, "42", tmp_path)


def test_lambda_no_args_with_capture(tmp_path):
    assert_runs("""
        n = 100
        f = lambda: n + 1
        print(f())
    """, "101", tmp_path)


# ===========================================================================
# Lambda with captures
# ===========================================================================

def test_lambda_captures_outer(tmp_path):
    assert_runs("""
        base = 10
        add_base = lambda x: x + base
        print(add_base(5))
    """, "15", tmp_path)


def test_lambda_captures_string(tmp_path):
    assert_runs("""
        greeting = "Hello, "
        greet = lambda name: greeting + name
        print(greet("Alice"))
    """, "Hello, Alice", tmp_path)


# ===========================================================================
# Lambda with different expression types
# ===========================================================================

def test_lambda_bool_expression(tmp_path):
    assert_runs("""
        is_even = lambda n: n % 2 == 0
        print(is_even(4))
        print(is_even(5))
    """, "1\n0", tmp_path)


def test_lambda_comparison(tmp_path):
    assert_runs("""
        larger = lambda a, b: a if a > b else b
        print(larger(3, 7))
        print(larger(10, 2))
    """, "7\n10", tmp_path)


# ===========================================================================
# Multiple lambdas in one program
# ===========================================================================

def test_two_lambdas(tmp_path):
    assert_runs("""
        twice = lambda x: x * 2
        triple = lambda x: x * 3
        print(twice(5))
        print(triple(5))
    """, "10\n15", tmp_path)


# ===========================================================================
# Lambda called many times
# ===========================================================================

def test_lambda_called_repeatedly(tmp_path):
    assert_runs("""
        sq = lambda x: x * x
        print(sq(2))
        print(sq(3))
        print(sq(4))
    """, "4\n9\n16", tmp_path)
