"""Batch 11c.1: list of pairs (2-tuples). Transpile-only."""
import pytest
from kofty.transpiler import transpile, TranspileError


# --- literal construction ----------------------------------------------------

def test_list_of_int_pairs_literal():
    out = transpile('''
xs = [(1, 2), (3, 4)]
''')
    assert "std::pair<int, int>" in out or "std::pair<int,int>" in out


def test_list_of_str_int_pairs_literal():
    out = transpile('''
xs = [("a", 1), ("b", 2)]
''')
    assert "std::pair<std::string, int>" in out or \
           "std::pair<std::string,int>" in out


def test_list_of_int_str_pairs_literal():
    out = transpile('''
xs = [(1, "a"), (2, "b")]
''')
    assert "std::pair<int, std::string>" in out or \
           "std::pair<int,std::string>" in out


# --- for-unpack over list of pairs -------------------------------------------

def test_for_unpack_over_list_of_pairs():
    out = transpile('''
xs = [(1, 2), (3, 4)]
for a, b in xs:
    print(a)
''')
    assert ".first" in out
    assert ".second" in out


def test_for_unpack_str_int():
    out = transpile('''
pairs = [("a", 1), ("b", 2)]
for k, v in pairs:
    print(k)
''')
    assert ".first" in out
    assert ".second" in out


# --- append ------------------------------------------------------------------

def test_append_pair_to_list_of_pairs():
    out = transpile('''
xs = [(1, 2)]
xs.append((3, 4))
''')
    assert "push_back" in out
    assert "make_pair" in out


# --- subscript gives a pair --------------------------------------------------

def test_subscript_list_of_pairs_gives_pair():
    out = transpile('''
xs = [(1, 2), (3, 4)]
y = xs[0]
print(y)
''')
    assert "xs[0]" in out


# --- regression: single-element lists still work -----------------------------

def test_single_level_int_list_still_works():
    out = transpile('xs = [1, 2, 3]\n')
    assert "std::vector<int>" in out


def test_single_level_str_list_still_works():
    out = transpile('xs = ["a", "b"]\n')
    assert "std::vector<std::string>" in out


def test_single_level_for_loop_still_works():
    out = transpile('''
xs = [1, 2, 3]
for x in xs:
    print(x)
''')
    assert "for (auto x : xs)" in out
