"""tests/test_batch9a_transpile.py

Batch 9a: f-string format specs.

Supported:
    f"{x:.2f}"     -> fmt_float(x, 2)
    f"{x:.3f}"     -> fmt_float(x, 3)
    f"{x:.0f}"     -> fmt_float(x, 0)
    f"{n:5d}"      -> fmt_int_pad(n, 5, ' ')
    f"{n:05d}"     -> fmt_int_pad(n, 5, '0')
    f"{x:>10}"     -> fmt_align(x, 10, '>')
    f"{x:<10}"     -> fmt_align(x, 10, '<')
    f"{x:^10}"     -> fmt_align(x, 10, '^')
    f"{x:8.2f}"    -> fmt_width_float(x, 8, 2)

Unsupported: raises TranspileError with a clear message.

Transpile-only tests. No exe launch. Zero flake.
"""

import pytest

from kofty.transpiler import TranspileError, transpile


# ===========================================================================
# Float precision .Nf
# ===========================================================================

def test_fstring_2f_emits_fmt_float():
    out = transpile('x = 3.14159\nprint(f"{x:.2f}")\n')
    assert "fmt_float(x, 2)" in out


def test_fstring_3f_emits_fmt_float():
    out = transpile('x = 3.14159\nprint(f"{x:.3f}")\n')
    assert "fmt_float(x, 3)" in out


def test_fstring_0f_emits_fmt_float():
    out = transpile('x = 3.7\nprint(f"{x:.0f}")\n')
    assert "fmt_float(x, 0)" in out


def test_fstring_1f_emits_fmt_float():
    out = transpile('x = 3.14159\nprint(f"{x:.1f}")\n')
    assert "fmt_float(x, 1)" in out


def test_fstring_2f_expression_emits_fmt_float():
    out = transpile('a = 1.0\nb = 2.0\nprint(f"{(a + b):.2f}")\n')
    # The BinOp must be emitted inside fmt_float(...).
    assert "fmt_float(" in out
    assert "2)" in out


def test_fstring_2f_method_call_emits_fmt_float():
    out = transpile('s = "3.14"\nprint(f"{float(s):.2f}")\n')
    assert "fmt_float(" in out


# ===========================================================================
# Integer width and zero-padding
# ===========================================================================

def test_fstring_5d_emits_int_pad():
    out = transpile('n = 42\nprint(f"{n:5d}")\n')
    assert "fmt_int_pad(n, 5, ' ')" in out


def test_fstring_05d_emits_zero_pad():
    out = transpile('n = 42\nprint(f"{n:05d}")\n')
    assert "fmt_int_pad(n, 5, '0')" in out


def test_fstring_3d_emits_int_pad():
    out = transpile('n = 7\nprint(f"{n:3d}")\n')
    assert "fmt_int_pad(n, 3, ' ')" in out


def test_fstring_02d_emits_zero_pad():
    out = transpile('n = 5\nprint(f"{n:02d}")\n')
    assert "fmt_int_pad(n, 2, '0')" in out


# ===========================================================================
# Alignment
# ===========================================================================

def test_fstring_gt_emits_align_right():
    out = transpile('s = "hi"\nprint(f"{s:>10}")\n')
    assert "fmt_align(s, 10, '>')" in out


def test_fstring_lt_emits_align_left():
    out = transpile('s = "hi"\nprint(f"{s:<10}")\n')
    assert "fmt_align(s, 10, '<')" in out


def test_fstring_caret_emits_align_center():
    out = transpile('s = "hi"\nprint(f"{s:^10}")\n')
    assert "fmt_align(s, 10, '^')" in out


# ===========================================================================
# Width + precision
# ===========================================================================

def test_fstring_width_precision_emits_width_float():
    out = transpile('x = 3.14159\nprint(f"{x:8.2f}")\n')
    assert "fmt_width_float(x, 8, 2)" in out


def test_fstring_width_precision_2():
    out = transpile('x = 1.5\nprint(f"{x:6.3f}")\n')
    assert "fmt_width_float(x, 6, 3)" in out


# ===========================================================================
# Mixed with literal text
# ===========================================================================

def test_fstring_with_prefix_suffix():
    out = transpile('x = 3.14159\nprint(f"pi is {x:.2f}!")\n')
    assert "pi is " in out
    assert "fmt_float(x, 2)" in out
    assert "!" in out


def test_fstring_two_specs():
    out = transpile('x = 1.5\ny = 2.5\nprint(f"{x:.1f} and {y:.2f}")\n')
    assert "fmt_float(x, 1)" in out
    assert "fmt_float(y, 2)" in out


def test_fstring_mixed_spec_and_plain():
    out = transpile('x = 3.14\nn = 5\nprint(f"{x:.2f} {n}")\n')
    assert "fmt_float(x, 2)" in out
    # Plain {n} stays is_to_string
    assert "is_to_string(n)" in out


# ===========================================================================
# Preamble helpers present
# ===========================================================================

def test_preamble_has_fmt_helpers():
    out = transpile('x = 1.0\nprint(f"{x:.2f}")\n')
    assert "fmt_float" in out
    assert "ostringstream" in out or "sstream" in out


# ===========================================================================
# Error cases
# ===========================================================================

def test_string_precision_spec_is_supported():
    # Batch 9b added .Ns -> str_truncate, so this no longer raises.
    out = transpile('s = "hello"\nprint(f"{s:.2s}")\n')
    assert "str_truncate(s, 2)" in out


def test_conversion_still_unsupported():
    with pytest.raises(TranspileError):
        transpile('x = 1\nprint(f"{x!r}")\n')
