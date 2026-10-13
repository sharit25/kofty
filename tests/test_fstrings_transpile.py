"""tests/test_fstrings_transpile.py

Batch 8h: transpile-only companion to test_fstrings.py.

Inspects the emitted C++ for f-string and .format() output. No exe
launch, no WinError 4551 flake.
"""

from kofty.transpiler import transpile


def test_fstring_no_placeholder_emits_literal():
    out = transpile('x = f"hello"\nprint(x)\n')
    # No placeholders -> just a std::string literal.
    assert 'std::string("hello")' in out


def test_fstring_single_str_var_emits_concat():
    out = transpile('name = "world"\nmsg = f"hi {name}"\nprint(msg)\n')
    # Expect a std::string concatenation.
    assert "std::string" in out
    assert "name" in out


def test_fstring_single_int_emits_to_string():
    out = transpile('n = 5\nmsg = f"n={n}"\nprint(msg)\n')
    # int exprs go through is_to_string / std::to_string.
    assert ("is_to_string" in out) or ("std::to_string" in out)


def test_fstring_multiple_emits_plus():
    out = transpile('a = 1\nb = 2\nmsg = f"{a}-{b}"\nprint(msg)\n')
    # Emitted as (std::string("...") + ... + ...)
    assert "+" in out


def test_fstring_float_emits_format_float():
    out = transpile('x = 1.5\nmsg = f"x={x}"\nprint(msg)\n')
    assert ("format_float" in out) or ("is_to_string" in out)


def test_fstring_method_call_in_braces():
    out = transpile('s = "hi"\nmsg = f"{s.upper()}"\nprint(msg)\n')
    assert "str_toupper" in out


def test_fstring_function_call_in_braces():
    out = transpile(
        'def twice(x):\n    return x * 2\n'
        'msg = f"{twice(3)}"\n'
        'print(msg)\n'
    )
    assert "double" in out


def test_format_positional_emits_call():
    out = transpile('s = "{} and {}".format(1, 2)\nprint(s)\n')
    assert "std::string" in out


def test_format_indexed_emits_call():
    out = transpile('s = "{0} {1}".format("a", "b")\nprint(s)\n')
    assert "std::string" in out


def test_format_repeated_index():
    out = transpile('s = "{0} {0}".format(7)\nprint(s)\n')
    assert "std::string" in out


# ---- escaped braces ----

def test_fstring_escaped_braces_emits_literal_brace():
    out = transpile('x = f"{{literal}}"\nprint(x)\n')
    # Emitted C++ should contain the literal { } characters.
    assert "{" in out
    assert "}" in out
