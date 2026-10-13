"""tests/test_batch10c_transpile.py

Batch 10c: four more string methods.

Adds:
    s.title()       -> str_title(s)
    s.capitalize()  -> str_capitalize(s)
    s.isalpha()     -> str_isalpha(s)  (bool)
    s.isdigit()     -> str_isdigit(s)  (bool)

Transpile-only. No exe launch. Zero flake.
"""

from kofty.transpiler import transpile


# ===========================================================================
# .title()
# ===========================================================================

def test_title_emits_str_title():
    out = transpile('s = "hello world"\nprint(s.title())\n')
    assert "str_title(s)" in out


def test_title_on_literal():
    out = transpile('print("hello world".title())\n')
    assert "str_title(" in out


def test_title_on_concat():
    out = transpile('a = "hello"\nb = " world"\nprint((a + b).title())\n')
    assert "str_title(" in out


# ===========================================================================
# .capitalize()
# ===========================================================================

def test_capitalize_emits_str_capitalize():
    out = transpile('s = "hello world"\nprint(s.capitalize())\n')
    assert "str_capitalize(s)" in out


def test_capitalize_on_literal():
    out = transpile('print("hello".capitalize())\n')
    assert "str_capitalize(" in out


# ===========================================================================
# .isalpha()
# ===========================================================================

def test_isalpha_emits_str_isalpha():
    out = transpile('s = "hello"\nprint(s.isalpha())\n')
    assert "str_isalpha(s)" in out


def test_isalpha_in_if():
    out = transpile('s = "abc"\nif s.isalpha():\n    print("yes")\n')
    assert "str_isalpha(s)" in out


# ===========================================================================
# .isdigit()
# ===========================================================================

def test_isdigit_emits_str_isdigit():
    out = transpile('s = "123"\nprint(s.isdigit())\n')
    assert "str_isdigit(s)" in out


def test_isdigit_in_if():
    out = transpile('s = "42"\nif s.isdigit():\n    print("num")\n')
    assert "str_isdigit(s)" in out


# ===========================================================================
# Chains
# ===========================================================================

def test_title_after_strip():
    out = transpile('s = "  hi  "\nprint(s.strip().title())\n')
    assert "str_strip" in out
    assert "str_title" in out


def test_title_after_lower():
    out = transpile('s = "HELLO WORLD"\nprint(s.lower().title())\n')
    assert "str_tolower" in out
    assert "str_title" in out


# ===========================================================================
# Preamble helpers present
# ===========================================================================

def test_preamble_has_all_four_helpers():
    out = transpile('s = "hi"\nprint(s.title())\n')
    assert "str_title" in out
    assert "str_capitalize" in out
    assert "str_isalpha" in out
    assert "str_isdigit" in out
