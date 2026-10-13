"""tests/test_string_methods_transpile.py

Batch 8h: transpile-only companion to test_string_methods.py.

These tests inspect the emitted C++ directly (no exe launch), so they
are immune to the WinError 4551 WDAC flake. They do NOT replace the
runtime tests in test_string_methods.py — they coexist for redundancy
and to keep coverage on WDAC-locked machines.

Each test asserts the emitted C++ contains the expected str_* helper
call. It does NOT verify runtime semantics (that's the runtime test's
job).
"""

from kofty.transpiler import transpile


def test_upper_emits_str_toupper():
    out = transpile('s = "hello"\nprint(s.upper())\n')
    assert "str_toupper" in out


def test_lower_emits_str_tolower():
    out = transpile('s = "HELLO"\nprint(s.lower())\n')
    assert "str_tolower" in out


def test_strip_emits_str_strip():
    out = transpile('s = "  hi  "\nprint(s.strip())\n')
    assert "str_strip" in out


def test_lstrip_emits_str_lstrip():
    out = transpile('s = "  hi  "\nprint(s.lstrip())\n')
    assert "str_lstrip" in out


def test_rstrip_emits_str_rstrip():
    out = transpile('s = "  hi  "\nprint(s.rstrip())\n')
    assert "str_rstrip" in out


def test_startswith_emits_str_startswith():
    out = transpile('s = "hello"\nprint(s.startswith("he"))\n')
    assert "str_startswith" in out


def test_endswith_emits_str_endswith():
    out = transpile('s = "hello.txt"\nprint(s.endswith(".txt"))\n')
    assert "str_endswith" in out


def test_replace_emits_str_replace():
    out = transpile('s = "hello"\nprint(s.replace("l", "L"))\n')
    assert "str_replace" in out


def test_split_emits_str_split():
    out = transpile('s = "a,b,c"\nparts = s.split(",")\n')
    assert "str_split" in out


def test_join_emits_str_join():
    out = transpile('xs = ["a", "b"]\ns = ",".join(xs)\n')
    assert "str_join" in out


def test_find_emits_str_find():
    out = transpile('s = "hello"\nprint(s.find("l"))\n')
    assert "str_find" in out


def test_count_emits_str_count():
    out = transpile('s = "banana"\nprint(s.count("a"))\n')
    assert "str_count" in out


def test_chain_upper_strip_emits_both():
    out = transpile('s = "  hi  "\nprint(s.strip().upper())\n')
    assert "str_strip" in out
    assert "str_toupper" in out


def test_method_in_if_emits_endswith():
    out = transpile('s = "f.txt"\nif s.endswith(".txt"):\n    print("yes")\n')
    assert "str_endswith" in out


def test_method_on_concat_emits_upper():
    out = transpile('a = "x"\nb = "y"\ns = a + b\nprint(s.upper())\n')
    assert "str_toupper" in out


# ---- emitted preamble includes the helpers ----

def test_str_helpers_in_preamble():
    out = transpile('s = "x"\nprint(s.upper())\n')
    assert "str_toupper" in out
    assert "str_tolower" in out
    assert "str_strip" in out
