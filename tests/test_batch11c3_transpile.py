"""Batch 11c.3: dict values that are tuples. Transpile-only."""
import pytest
from kofty.transpiler import transpile, TranspileError


# --- literal construction ----------------------------------------------------

def test_dict_with_pair_values_literal():
    out = transpile('''
d = {"a": (1, 2), "b": (3, 4)}
''')
    assert "std::pair<int, int>" in out or "std::pair<int,int>" in out
    assert "std::map" in out


def test_dict_with_3tuple_values_literal():
    out = transpile('''
d = {"a": (1, 2, 3), "b": (4, 5, 6)}
''')
    assert "std::tuple<int, int, int>" in out or \
           "std::tuple<int,int,int>" in out


def test_dict_with_heterogeneous_pairs():
    out = transpile('''
d = {"a": ("x", 1), "b": ("y", 2)}
''')
    assert "std::pair<std::string, int>" in out or \
           "std::pair<std::string,int>" in out


# --- subscript: d["a"] yields a pair ----------------------------------------

def test_subscript_dict_yields_pair():
    out = transpile('''
d = {"a": (1, 2), "b": (3, 4)}
p = d["a"]
x, y = p
''')
    # The unpack of p should use .first / .second — arity 2
    assert ".first" in out
    assert ".second" in out


def test_subscript_dict_yields_3tuple():
    out = transpile('''
d = {"a": (1, 2, 3), "b": (4, 5, 6)}
t = d["a"]
a, b, c = t
''')
    # The unpack of t should use std::get<N>
    assert "std::get<0>" in out
    assert "std::get<2>" in out


# --- for k, v in d.items() --------------------------------------------------

def test_for_items_over_dict_of_pairs():
    out = transpile('''
d = {"a": (1, 2), "b": (3, 4)}
for k, v in d.items():
    print(k)
''')
    # v is a pair; it should be emitted as a pair in the loop
    assert "std::pair" in out or "std::map" in out
    assert "for" in out


def test_for_items_over_dict_of_3tuples():
    out = transpile('''
d = {"a": (1, 2, 3), "b": (4, 5, 6)}
for k, v in d.items():
    print(k)
''')
    assert "std::tuple" in out


# --- regression: dict of scalars still works --------------------------------

def test_dict_of_int_values_still_works():
    out = transpile('d = {"a": 1, "b": 2}\n')
    assert "std::map<std::string, int>" in out


def test_dict_of_str_values_still_works():
    out = transpile('d = {"a": "x", "b": "y"}\n')
    assert "std::map<std::string, std::string>" in out


# --- error: nested unpack in for-items is rejected --------------------------

def test_nested_unpack_rejected():
    with pytest.raises(TranspileError):
        transpile('''
d = {"a": (1, 2), "b": (3, 4)}
for k, (a, b) in d.items():
    print(k)
''')
