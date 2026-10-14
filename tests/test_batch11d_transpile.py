"""Batch 11d: nested container repr. Transpile-only.

Pins the fact that nested containers flow through the correct
repr_* / is_to_string dispatch. No code changes — every case here
already works. This file exists so a future refactor of
_container_repr or the repr_* preamble helpers can't silently
regress the pattern.
"""
import pytest
from kofty.transpiler import transpile


# --- variables holding nested containers ------------------------------------

def test_print_list_of_int_pairs():
    out = transpile('''
xs = [(1, 2), (3, 4)]
print(xs)
''')
    assert "repr_vector(xs)" in out
    assert "std::pair<int, int>" in out


def test_print_list_of_3tuples():
    out = transpile('''
xs = [(1, 2, 3), (4, 5, 6)]
print(xs)
''')
    assert "repr_vector(xs)" in out
    assert "std::tuple<int, int, int>" in out


def test_print_dict_of_pairs():
    out = transpile('''
d = {"a": (1, 2), "b": (3, 4)}
print(d)
''')
    assert "repr_map(d)" in out
    assert "std::pair<int, int>" in out


def test_print_list_of_str_int_pairs():
    out = transpile('''
xs = [("x", 1), ("y", 2)]
print(xs)
''')
    assert "repr_vector(xs)" in out
    assert "std::pair<std::string, int>" in out


# --- literal (inline) nested containers -------------------------------------

def test_print_literal_list_of_pairs():
    out = transpile('print([(1, 2), (3, 4)])\n')
    assert "repr_vector(" in out
    assert "std::pair<int, int>" in out


def test_print_literal_dict_of_pairs():
    out = transpile('print({"a": (1, 2), "b": (3, 4)})\n')
    assert "repr_map(" in out


# --- str() routes through the same dispatch --------------------------------

def test_str_of_list_of_pairs():
    out = transpile('''
xs = [(1, 2), (3, 4)]
s = str(xs)
''')
    assert "repr_vector(xs)" in out


def test_str_of_dict_of_pairs():
    out = transpile('''
d = {"a": (1, 2)}
s = str(d)
''')
    assert "repr_map(d)" in out


# --- f-string also routes through the same dispatch ------------------------

def test_fstring_of_list_of_pairs():
    out = transpile('''
xs = [(1, 2), (3, 4)]
print(f"nested: {xs}")
''')
    # is_to_string on a vector dispatches to repr_vector; the f-string
    # call site should invoke is_to_string(xs).
    assert "is_to_string(xs)" in out


# --- regression: single-level containers ------------------------------------

def test_print_int_list_still_works():
    out = transpile('''
xs = [1, 2, 3]
print(xs)
''')
    assert "repr_vector(xs)" in out


def test_print_dict_still_works():
    out = transpile('''
d = {"a": 1, "b": 2}
print(d)
''')
    assert "repr_map(d)" in out
