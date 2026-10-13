"""tests/test_batch8h Phase 3: transpile-only companion to test_batch5d.py.

Verifies the C++ emitted for lambdas.

Lambdas -> `[&](auto x) { return ...; }` capture-by-reference.
Single-expression bodies only. Params are untyped (auto).
"""

from kofty.transpiler import transpile


# ===========================================================================
# Basic lambda
# ===========================================================================

def test_lambda_one_param_emits_lambda():
    out = transpile("""
twice = lambda x: x * 2
print(twice(5))
""")
    # Emitted lambda: [&](auto x) { return x * 2; }
    assert "[&]" in out
    assert "auto" in out
    assert "return" in out


def test_lambda_two_params_emits_lambda():
    out = transpile("""
add = lambda a, b: a + b
print(add(3, 4))
""")
    assert "[&]" in out
    # Two auto params
    assert out.count("auto") >= 2


def test_lambda_zero_params_emits_lambda():
    out = transpile("""
f = lambda: 42
print(f())
""")
    assert "[&]" in out
    assert "42" in out


def test_lambda_no_args_with_capture_emits_capture():
    out = transpile("""
n = 100
f = lambda: n + 1
print(f())
""")
    # Capture-by-reference: [&]
    assert "[&]" in out
    assert "n" in out


# ===========================================================================
# Lambda with captures
# ===========================================================================

def test_lambda_captures_outer_emits_reference():
    out = transpile("""
base = 10
add_base = lambda x: x + base
print(add_base(5))
""")
    assert "[&]" in out
    assert "base" in out


def test_lambda_captures_string_emits_reference():
    out = transpile("""
greeting = "Hello, "
greet = lambda name: greeting + name
print(greet("Alice"))
""")
    assert "[&]" in out
    assert "greeting" in out


# ===========================================================================
# Lambda with different expression types
# ===========================================================================

def test_lambda_bool_expression_emits_comparison():
    out = transpile("""
is_even = lambda n: n % 2 == 0
print(is_even(4))
""")
    assert "[&]" in out
    # Emitted: ((n % 2) == 0) — parens around BinOp and Compare.
    assert "% 2" in out
    assert "== 0" in out


def test_lambda_comparison_emits_ternary():
    out = transpile("""
larger = lambda a, b: a if a > b else b
print(larger(3, 7))
""")
    # Ternary inside the lambda body
    assert "?" in out and ":" in out
    assert "a > b" in out


# ===========================================================================
# Multiple lambdas in one program
# ===========================================================================

def test_two_lambdas_emits_two_lambdas():
    out = transpile("""
twice = lambda x: x * 2
triple = lambda x: x * 3
print(twice(5))
print(triple(5))
""")
    # Two distinct lambda definitions
    assert out.count("[&]") >= 2


# ===========================================================================
# Lambda called many times
# ===========================================================================

def test_lambda_called_repeatedly_emits_lambda_and_calls():
    out = transpile("""
sq = lambda x: x * x
print(sq(2))
print(sq(3))
print(sq(4))
""")
    assert "[&]" in out
    # Variable `sq` is called three times; emitter must call it as `sq(...)`.
    assert "sq(" in out
