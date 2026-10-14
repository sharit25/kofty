"""Batch 11c.2: list of 3+-tuples. Transpile-only."""
import pytest
from kofty.transpiler import transpile, TranspileError


# --- literal construction ----------------------------------------------------

def test_list_of_int_3tuples_literal():
    out = transpile('''
xs = [(1, 2, 3), (4, 5, 6)]
''')
    assert "std::tuple<int, int, int>" in out or \
           "std::tuple<int,int,int>" in out


def test_list_of_heterogeneous_3tuples_literal():
    out = transpile('''
xs = [("a", 1, True), ("b", 2, False)]
''')
    # element type is std::tuple<std::string, int, bool> (or with bool
    # possibly as int -- accept either)
    assert "std::tuple<" in out
    assert "std::string" in out


def test_list_of_4tuples_literal():
    out = transpile('''
xs = [(1, 2, 3, 4), (5, 6, 7, 8)]
''')
    assert "std::tuple<int, int, int, int>" in out or \
           "std::tuple<int,int,int,int>" in out


# --- for-unpack over list of 3-tuples ----------------------------------------

def test_for_unpack_over_list_of_3tuples():
    out = transpile('''
xs = [(1, 2, 3), (4, 5, 6)]
for a, b, c in xs:
    print(a)
''')
    assert "std::get<0>" in out
    assert "std::get<1>" in out
    assert "std::get<2>" in out


def test_for_unpack_over_list_of_4tuples():
    out = transpile('''
xs = [(1, 2, 3, 4), (5, 6, 7, 8)]
for a, b, c, d in xs:
    print(a)
''')
    assert "std::get<0>" in out
    assert "std::get<3>" in out


def test_for_unpack_str_3tuple():
    out = transpile('''
recs = [("a", 1, 2.5), ("b", 3, 4.5)]
for name, n, x in recs:
    print(name)
''')
    assert "std::get<0>" in out
    assert "std::get<2>" in out


# --- append ------------------------------------------------------------------

def test_append_3tuple_to_list_of_3tuples():
    out = transpile('''
xs = [(1, 2, 3)]
xs.append((4, 5, 6))
''')
    assert "push_back" in out


# --- regression: list of pairs still works -----------------------------------

def test_list_of_pairs_still_works():
    out = transpile('''
xs = [(1, 2), (3, 4)]
for a, b in xs:
    print(a)
''')
    assert ".first" in out
    assert ".second" in out


# --- error: mixed arities ----------------------------------------------------

def test_mixed_arities_in_list_raises():
    with pytest.raises(TranspileError):
        transpile('''
xs = [(1, 2), (1, 2, 3)]
''')
