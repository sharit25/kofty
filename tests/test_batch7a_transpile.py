"""tests/test_batch8h Phase 4: transpile-only companion to test_batch7a.py.

Verifies the C++ emitted for `import math`.

math.sqrt(x) -> std::sqrt(x), etc.
math.pi -> 3.141592653589793, math.e -> 2.718281828459045.
"""

from kofty.transpiler import transpile


# ===========================================================================
# Basic import + sqrt
# ===========================================================================

def test_math_sqrt_emits_std_sqrt():
    out = transpile("""
import math
x = math.sqrt(16.0)
print(x)
""")
    assert "std::sqrt" in out
    assert "<cmath>" in out or "<math.h>" in out


def test_sqrt_non_perfect_emits_std_sqrt():
    out = transpile("""
import math
print(math.sqrt(2.0))
""")
    assert "std::sqrt(2.0)" in out


# ===========================================================================
# pow
# ===========================================================================

def test_math_pow_emits_std_pow():
    out = transpile("""
import math
print(math.pow(2.0, 10.0))
""")
    assert "std::pow(2.0, 10.0)" in out


# ===========================================================================
# trig
# ===========================================================================

def test_math_sin_zero_emits_std_sin():
    out = transpile("""
import math
print(math.sin(0.0))
""")
    assert "std::sin(0.0)" in out


def test_math_cos_zero_emits_std_cos():
    out = transpile("""
import math
print(math.cos(0.0))
""")
    assert "std::cos(0.0)" in out


# ===========================================================================
# floor / ceil
# ===========================================================================

def test_math_floor_emits_std_floor():
    out = transpile("""
import math
print(math.floor(3.7))
""")
    assert "std::floor(3.7)" in out


def test_math_ceil_emits_std_ceil():
    out = transpile("""
import math
print(math.ceil(3.2))
""")
    assert "std::ceil(3.2)" in out


# ===========================================================================
# fabs
# ===========================================================================

def test_math_fabs_emits_std_fabs():
    out = transpile("""
import math
print(math.fabs(-5.5))
""")
    assert "std::fabs" in out


# ===========================================================================
# exp / log
# ===========================================================================

def test_math_exp_zero_emits_std_exp():
    out = transpile("""
import math
print(math.exp(0.0))
""")
    assert "std::exp(0.0)" in out


def test_math_log_one_emits_std_log():
    out = transpile("""
import math
print(math.log(1.0))
""")
    assert "std::log(1.0)" in out


# ===========================================================================
# Constants
# ===========================================================================

def test_math_pi_emits_literal():
    out = transpile("""
import math
print(math.pi)
""")
    # math.pi -> 3.141592653589793 (or similar literal)
    assert "3.14" in out or "M_PI" in out


def test_math_e_emits_literal():
    out = transpile("""
import math
print(math.e)
""")
    assert "2.71" in out or "M_E" in out


# ===========================================================================
# In expressions
# ===========================================================================

def test_math_in_expression_emits_multiple_uses():
    out = transpile("""
import math
r = 5.0
area = math.pi * r * r
print(area)
""")
    assert "3.14" in out or "M_PI" in out
    assert "r" in out


def test_math_sqrt_of_sum_emits_nested():
    out = transpile("""
import math
a = 3.0
b = 4.0
print(math.sqrt(a * a + b * b))
""")
    assert "std::sqrt" in out
    # The inner expression a * a + b * b must appear.
    assert "a * a" in out or "a*a" in out


# ===========================================================================
# Multiple uses of math in one program
# ===========================================================================

def test_math_multiple_calls_emits_three_calls():
    out = transpile("""
import math
print(math.sqrt(4.0))
print(math.floor(2.9))
print(math.ceil(2.1))
""")
    assert "std::sqrt" in out
    assert "std::floor" in out
    assert "std::ceil" in out


# ===========================================================================
# Without import - should raise a clear error
# ===========================================================================

def test_math_without_import_raises():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError):
        transpile("""
x = math.sqrt(16.0)
print(x)
""")
