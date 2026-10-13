"""tests/test_batch9b_transpile.py

Batch 9b: f-string format specs, phase 2.

Adds:
    f"{x:}"     -> is_to_string(x)   (empty spec == no spec)
    f"{s:.3s}"  -> str_truncate(s, 3)
    f"{n:x}"    -> fmt_int_base(n, 16, false)   (lowercase hex)
    f"{n:X}"    -> fmt_int_base(n, 16, true)    (uppercase hex)
    f"{n:o}"    -> fmt_int_base(n, 8, false)    (octal)
    f"{n:b}"    -> fmt_int_base(n, 2, false)    (binary)
    f"{n:,}"    -> fmt_int_comma(n)             (1234567 -> 1,234,567)

Transpile-only. No exe launch, zero flake.
"""

import pytest

from kofty.transpiler import TranspileError, transpile


# ===========================================================================
# Empty spec
# ===========================================================================

def test_fstring_empty_spec_passthrough():
    out = transpile('x = 5\nprint(f"{x:}")\n')
    assert "is_to_string(x)" in out


def test_fstring_empty_spec_on_str():
    out = transpile('s = "hi"\nprint(f"{s:}")\n')
    assert "is_to_string(s)" in out


# ===========================================================================
# String precision .Ns
# ===========================================================================

def test_fstring_3s_truncates():
    out = transpile('s = "hello"\nprint(f"{s:.3s}")\n')
    assert "str_truncate(s, 3)" in out


def test_fstring_1s_truncates():
    out = transpile('s = "hello"\nprint(f"{s:.1s}")\n')
    assert "str_truncate(s, 1)" in out


def test_fstring_5s_truncates():
    out = transpile('s = "hello"\nprint(f"{s:.5s}")\n')
    assert "str_truncate(s, 5)" in out


# ===========================================================================
# Hex / oct / bin
# ===========================================================================

def test_fstring_lowercase_hex():
    out = transpile('n = 255\nprint(f"{n:x}")\n')
    assert "fmt_int_base(n, 16, false)" in out


def test_fstring_uppercase_hex():
    out = transpile('n = 255\nprint(f"{n:X}")\n')
    assert "fmt_int_base(n, 16, true)" in out


def test_fstring_octal():
    out = transpile('n = 8\nprint(f"{n:o}")\n')
    assert "fmt_int_base(n, 8, false)" in out


def test_fstring_binary():
    out = transpile('n = 5\nprint(f"{n:b}")\n')
    assert "fmt_int_base(n, 2, false)" in out


# ===========================================================================
# Comma thousands
# ===========================================================================

def test_fstring_comma_thousands():
    out = transpile('n = 1234567\nprint(f"{n:,}")\n')
    assert "fmt_int_comma(n)" in out


def test_fstring_comma_on_variable():
    out = transpile('a = 1000000\nprint(f"{a:,}")\n')
    assert "fmt_int_comma(a)" in out


# ===========================================================================
# In expressions / mixed
# ===========================================================================

def test_fstring_hex_in_expression():
    out = transpile('n = 15 + 1\nprint(f"{n:x}")\n')
    assert "fmt_int_base(" in out
    assert "16, false)" in out


def test_fstring_mixed_with_literal():
    out = transpile('n = 255\nprint(f"color: 0x{n:x}")\n')
    assert "color: 0x" in out
    assert "fmt_int_base(n, 16, false)" in out


def test_fstring_hex_and_decimal():
    out = transpile('n = 42\nprint(f"{n} = {n:x}")\n')
    assert "is_to_string(n)" in out
    assert "fmt_int_base(n, 16, false)" in out


def test_fstring_comma_and_text():
    out = transpile('n = 1000000\nprint(f"total: {n:,}")\n')
    assert "total: " in out
    assert "fmt_int_comma(n)" in out


# ===========================================================================
# Preamble helpers present
# ===========================================================================

def test_preamble_has_new_helpers():
    out = transpile('n = 255\nprint(f"{n:x}")\n')
    assert "fmt_int_base" in out


def test_preamble_has_str_truncate():
    out = transpile('s = "hi"\nprint(f"{s:.2s}")\n')
    assert "str_truncate" in out


# ===========================================================================
# Errors
# ===========================================================================

def test_unsupported_dollar_sign_raises():
    with pytest.raises(TranspileError):
        transpile('n = 5\nprint(f"{n:$}")\n')


def test_unsupported_percent_raises():
    with pytest.raises(TranspileError):
        transpile('x = 0.5\nprint(f"{x:.1%}")\n')
