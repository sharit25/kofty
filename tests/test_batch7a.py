"""tests/test_batch7a.py

Batch 7a: import math.

Design:
    import math
    math.sqrt(x)      -> std::sqrt(x)
    math.pow(x, y)    -> std::pow(x, y)
    math.sin(x)       -> std::sin(x)
    math.cos(x)       -> std::cos(x)
    math.tan(x)       -> std::tan(x)
    math.floor(x)     -> std::floor(x)
    math.ceil(x)      -> std::ceil(x)
    math.fabs(x)      -> std::fabs(x)
    math.exp(x)       -> std::exp(x)
    math.log(x)       -> std::log(x)
    math.pi           -> 3.141592653589793
    math.e            -> 2.718281828459045

OUT OF SCOPE (deferred):
    - math.isnan, math.isinf, math.isfinite
    - math.atan2, math.hypot, math.fmod
    - math.log(x, base)
    - from math import ...  / import math as m
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
# Basic import + sqrt
# ===========================================================================

def test_import_math_sqrt(tmp_path):
    assert_runs("""
        import math
        x = math.sqrt(16.0)
        print(x)
    """, "4", tmp_path)


def test_sqrt_non_perfect(tmp_path):
    assert_runs("""
        import math
        print(math.sqrt(2.0))
    """, "1.41421", tmp_path)


# ===========================================================================
# pow
# ===========================================================================

def test_math_pow(tmp_path):
    assert_runs("""
        import math
        print(math.pow(2.0, 10.0))
    """, "1024", tmp_path)


# ===========================================================================
# trig
# ===========================================================================

def test_math_sin_zero(tmp_path):
    assert_runs("""
        import math
        print(math.sin(0.0))
    """, "0", tmp_path)


def test_math_cos_zero(tmp_path):
    assert_runs("""
        import math
        print(math.cos(0.0))
    """, "1", tmp_path)


# ===========================================================================
# floor / ceil
# ===========================================================================

def test_math_floor(tmp_path):
    assert_runs("""
        import math
        print(math.floor(3.7))
    """, "3", tmp_path)


def test_math_ceil(tmp_path):
    assert_runs("""
        import math
        print(math.ceil(3.2))
    """, "4", tmp_path)


# ===========================================================================
# fabs
# ===========================================================================

def test_math_fabs(tmp_path):
    assert_runs("""
        import math
        print(math.fabs(-5.5))
    """, "5.5", tmp_path)


# ===========================================================================
# exp / log
# ===========================================================================

def test_math_exp_zero(tmp_path):
    assert_runs("""
        import math
        print(math.exp(0.0))
    """, "1", tmp_path)


def test_math_log_one(tmp_path):
    assert_runs("""
        import math
        print(math.log(1.0))
    """, "0", tmp_path)


# ===========================================================================
# Constants
# ===========================================================================

def test_math_pi(tmp_path):
    assert_runs("""
        import math
        print(math.pi)
    """, "3.14159", tmp_path)


def test_math_e(tmp_path):
    assert_runs("""
        import math
        print(math.e)
    """, "2.71828", tmp_path)


# ===========================================================================
# In expressions
# ===========================================================================

def test_math_in_expression(tmp_path):
    assert_runs("""
        import math
        r = 5.0
        area = math.pi * r * r
        print(area)
    """, "78.5398", tmp_path)


def test_math_sqrt_of_sum(tmp_path):
    assert_runs("""
        import math
        a = 3.0
        b = 4.0
        print(math.sqrt(a * a + b * b))
    """, "5", tmp_path)


# ===========================================================================
# Multiple uses of math in one program
# ===========================================================================

def test_math_multiple_calls(tmp_path):
    assert_runs("""
        import math
        print(math.sqrt(4.0))
        print(math.floor(2.9))
        print(math.ceil(2.1))
    """, "2\n2\n3", tmp_path)


# ===========================================================================
# Without import — should raise a clear error
# ===========================================================================

def test_math_without_import_raises(tmp_path):
    rc, out, err = run_is("""
        x = math.sqrt(16.0)
        print(x)
    """, tmp_path)
    assert rc != 0, f"expected transpile error but got rc=0:\n{out}"
    assert "math" in err, f"error should mention 'math': {err}"
