"""tests/test_batch3.py

Batch 3: ** (power), // (floor div), ternary (a if c else b).

Scope decisions (locked):
    **  -> std::pow(a, b); always returns double. 2**3 prints "8", not "8.0",
          because format_float trims trailing ".0".
    //  -> is_floordiv(a, b); C++ helpers overload on int/double.
          Python floor semantics: -7 // 2 == -4.
    ?:  -> C++ ternary ((cond) ? (a) : (b)). Both arms must have compatible
          types; mixing int and str is a compile error (documented limitation).

OUT OF SCOPE (do not test here):
    - int-preserving ** (2**3 staying int)
    - comparison chains with ternary
    - ternary with tuple/list/dict arms
    - augmented ** (x **= 2)
    - augmented // (x //= 2)
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
# **  (power)
# ===========================================================================

def test_pow_int_int(tmp_path):
    assert_runs("""
        x = 2 ** 3
        print(x)
    """, "8", tmp_path)


def test_pow_var(tmp_path):
    assert_runs("""
        a = 5
        b = 2
        print(a ** b)
    """, "25", tmp_path)


def test_pow_float_base(tmp_path):
    assert_runs("""
        x = 2.0 ** 3
        print(x)
    """, "8", tmp_path)


def test_pow_zero_exp(tmp_path):
    assert_runs("""
        print(7 ** 0)
    """, "1", tmp_path)


def test_pow_in_expression(tmp_path):
    assert_runs("""
        print(1 + 2 ** 3)
    """, "9", tmp_path)


def test_pow_with_parens(tmp_path):
    assert_runs("""
        print((1 + 2) ** 3)
    """, "27", tmp_path)


# ===========================================================================
# //  (floor div)
# ===========================================================================

def test_floordiv_positive(tmp_path):
    assert_runs("""
        print(7 // 2)
    """, "3", tmp_path)


def test_floordiv_exact(tmp_path):
    assert_runs("""
        print(8 // 2)
    """, "4", tmp_path)


def test_floordiv_negative_dividend(tmp_path):
    assert_runs("""
        print(-7 // 2)
    """, "-4", tmp_path)


def test_floordiv_negative_divisor(tmp_path):
    assert_runs("""
        print(7 // -2)
    """, "-4", tmp_path)


def test_floordiv_both_negative(tmp_path):
    assert_runs("""
        print(-7 // -2)
    """, "3", tmp_path)


def test_floordiv_floats(tmp_path):
    assert_runs("""
        print(7.5 // 2.0)
    """, "3", tmp_path)


def test_floordiv_vars(tmp_path):
    assert_runs("""
        a = 17
        b = 5
        print(a // b)
    """, "3", tmp_path)


# ===========================================================================
# ternary  (a if cond else b)
# ===========================================================================

def test_ternary_int_true(tmp_path):
    assert_runs("""
        x = 5
        print(x if x > 0 else 0)
    """, "5", tmp_path)


def test_ternary_int_false(tmp_path):
    assert_runs("""
        x = -5
        print(x if x > 0 else 0)
    """, "0", tmp_path)


def test_ternary_str(tmp_path):
    assert_runs("""
        n = 3
        print("odd" if n % 2 == 1 else "even")
    """, "odd", tmp_path)


def test_ternary_in_assignment(tmp_path):
    assert_runs("""
        a = 10
        b = 20
        m = a if a < b else b
        print(m)
    """, "10", tmp_path)


def test_ternary_nested(tmp_path):
    assert_runs("""
        x = 5
        y = "pos" if x > 0 else ("zero" if x == 0 else "neg")
        print(y)
    """, "pos", tmp_path)


def test_ternary_arithmetic_arms(tmp_path):
    assert_runs("""
        n = 4
        print(n * 2 if n > 0 else n * -1)
    """, "8", tmp_path)
