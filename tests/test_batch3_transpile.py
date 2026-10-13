"""tests/test_batch3_transpile.py

Batch 8h Phase 2: transpile-only companion to test_batch3.py.

Verifies the C++ emitted for **, //, and ternary. No exe launch,
immune to WinError 4551.
"""

from kofty.transpiler import transpile


# ===========================================================================
# **  (power)
# ===========================================================================

def test_pow_int_int_emits_std_pow():
    out = transpile("x = 2 ** 3\nprint(x)\n")
    assert "std::pow(2, 3)" in out


def test_pow_var_emits_std_pow():
    out = transpile("a = 5\nb = 2\nprint(a ** b)\n")
    assert "std::pow(a, b)" in out


def test_pow_float_base_emits_std_pow():
    out = transpile("x = 2.0 ** 3\nprint(x)\n")
    assert "std::pow(2.0, 3)" in out


def test_pow_zero_exp_emits_std_pow():
    out = transpile("print(7 ** 0)\n")
    assert "std::pow(7, 0)" in out


def test_pow_in_expression_nests_std_pow():
    out = transpile("print(1 + 2 ** 3)\n")
    assert "std::pow(2, 3)" in out


def test_pow_with_parens_emits_std_pow():
    out = transpile("print((1 + 2) ** 3)\n")
    assert "std::pow((1 + 2), 3)" in out


# ===========================================================================
# //  (floor div)
# ===========================================================================

def test_floordiv_positive_emits_is_floordiv():
    out = transpile("print(7 // 2)\n")
    assert "is_floordiv(7, 2)" in out


def test_floordiv_exact_emits_is_floordiv():
    out = transpile("print(8 // 2)\n")
    assert "is_floordiv(8, 2)" in out


def test_floordiv_negative_dividend_emits_is_floordiv():
    out = transpile("print(-7 // 2)\n")
    assert "is_floordiv((-7), 2)" in out or "is_floordiv(-7, 2)" in out


def test_floordiv_negative_divisor_emits_is_floordiv():
    out = transpile("print(7 // -2)\n")
    assert "is_floordiv(7, (-2))" in out or "is_floordiv(7, -2)" in out


def test_floordiv_both_negative_emits_is_floordiv():
    out = transpile("print(-7 // -2)\n")
    assert "is_floordiv" in out


def test_floordiv_floats_emits_is_floordiv():
    out = transpile("print(7.5 // 2.0)\n")
    assert "is_floordiv(7.5, 2.0)" in out


def test_floordiv_vars_emits_is_floordiv():
    out = transpile("a = 17\nb = 5\nprint(a // b)\n")
    assert "is_floordiv(a, b)" in out


# ===========================================================================
# ternary  (a if cond else b)
# ===========================================================================

def test_ternary_int_true_emits_ternary():
    out = transpile("x = 5\nprint(x if x > 0 else 0)\n")
    # C++ ternary: ((cond) ? (a) : (b))
    assert "?" in out and ":" in out
    assert "x > 0" in out


def test_ternary_int_false_emits_ternary():
    out = transpile("x = -5\nprint(x if x > 0 else 0)\n")
    assert "?" in out and ":" in out


def test_ternary_str_emits_ternary():
    out = transpile('n = 3\nprint("odd" if n % 2 == 1 else "even")\n')
    assert "?" in out and ":" in out


def test_ternary_in_assignment_emits_ternary():
    out = transpile("a = 10\nb = 20\nm = a if a < b else b\nprint(m)\n")
    assert "?" in out and ":" in out
    assert "a < b" in out


def test_ternary_nested_emits_two_ternaries():
    out = transpile('x = 5\ny = "pos" if x > 0 else ("zero" if x == 0 else "neg")\nprint(y)\n')
    # Two ? : constructs -> at least two `?` chars
    assert out.count("?") >= 2
    assert out.count(":") >= 2


def test_ternary_arithmetic_arms_emits_ternary():
    out = transpile("n = 4\nprint(n * 2 if n > 0 else n * -1)\n")
    assert "?" in out and ":" in out
    assert "n * 2" in out
