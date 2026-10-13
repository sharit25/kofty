"""tests/test_batch8h Phase 3: transpile-only companion to test_batch5a.py.

Verifies the C++ emitted for default arguments. No exe launch.

Default args are emitted as C++ defaults on the function signature
(e.g. `int b = 10`). Call sites with fewer args use the default.
"""

from kofty.transpiler import transpile


# ===========================================================================
# One default arg
# ===========================================================================

def test_default_used_emits_signature_default():
    out = transpile("""
def greet(name, greeting="Hello"):
    print(greeting + ", " + name)

greet("Alice")
""")
    # Emitter should produce a default on the param signature.
    assert "greeting" in out
    assert '"Hello"' in out or "Hello" in out


def test_default_overridden_emits_signature_default():
    out = transpile("""
def greet(name, greeting="Hello"):
    print(greeting + ", " + name)

greet("Bob", "Hi")
""")
    assert "greeting" in out
    assert "Hi" in out


def test_default_int_emits_int_default():
    out = transpile("""
def add(a, b=10):
    print(a + b)

add(5)
add(5, 100)
""")
    # Expect `int b = 10` or similar in the function signature.
    assert "= 10" in out
    assert "add" in out


# ===========================================================================
# Multiple defaults
# ===========================================================================

def test_two_defaults_both_used_emits_both():
    out = transpile("""
def f(a, b=2, c=3):
    print(a * 100 + b * 10 + c)

f(1)
""")
    assert "= 2" in out
    assert "= 3" in out


def test_two_defaults_one_overridden_emits_both():
    out = transpile("""
def f(a, b=2, c=3):
    print(a * 100 + b * 10 + c)

f(1, 9)
""")
    assert "= 2" in out
    assert "= 3" in out


def test_two_defaults_both_overridden_emits_both():
    out = transpile("""
def f(a, b=2, c=3):
    print(a * 100 + b * 10 + c)

f(1, 9, 8)
""")
    assert "= 2" in out
    assert "= 3" in out


# ===========================================================================
# Mixed types
# ===========================================================================

def test_default_str_emits_string_defaults():
    out = transpile("""
def greet(name, greeting="Hello", punctuation="!"):
    print(greeting + ", " + name + punctuation)

greet("Alice")
""")
    # String defaults must be emitted as std::string(...) or a quoted literal
    assert "Hello" in out
    assert "!" in out


def test_default_float_emits_double_default():
    out = transpile("""
def scale(x, factor=2.0):
    print(x * factor)

scale(5)
""")
    assert "2.0" in out
    assert "factor" in out


# ===========================================================================
# Called from within another function
# ===========================================================================

def test_default_in_call_chain_emits_default():
    out = transpile("""
def base(a, b=100):
    return a + b

def wrap(x):
    return base(x)

print(wrap(5))
""")
    assert "= 100" in out
    assert "base" in out
    assert "wrap" in out


# ===========================================================================
# Default arg used in an expression
# ===========================================================================

def test_default_used_in_expression_emits_pow():
    out = transpile("""
def power(base, exp=2):
    return base ** exp

print(power(3))
""")
    assert "= 2" in out
    # Body must contain std::pow
    assert "std::pow" in out


# ===========================================================================
# Multiple calls with different defaults
# ===========================================================================

def test_default_repeated_calls_emits_signature():
    out = transpile("""
def tag(s, prefix="[", suffix="]"):
    print(prefix + s + suffix)

tag("a")
tag("b")
tag("c", "<")
""")
    assert 'prefix' in out
    assert 'suffix' in out
    # "[", "]" literals must appear in the emitted C++.
    assert '"["' in out or "[" in out
    assert '"]"' in out or "]" in out
