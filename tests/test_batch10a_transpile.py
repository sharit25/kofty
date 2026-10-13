"""tests/test_batch10a_transpile.py

Batch 10a: print(container) reprs.

Targets:
    print([1, 2, 3])       -> repr_vector([...])
    print((1, 2))          -> repr_pair((...))
    print((1, 2, 3))       -> repr_tuple((...))
    print({"a": 1})        -> repr_map({...})
    print({1, 2, 3})       -> repr_set({...})

And the same for str(container).

Transpile-only. No exe launch. Zero flake.
"""

from kofty.transpiler import transpile


# ===========================================================================
# print(list)
# ===========================================================================

def test_print_list_literal_emits_repr_vector():
    out = transpile('print([1, 2, 3])\n')
    assert "repr_vector" in out


def test_print_list_variable_emits_repr_vector():
    out = transpile('xs = [1, 2, 3]\nprint(xs)\n')
    assert "repr_vector(xs)" in out



def test_print_list_of_strings_emits_repr_vector():
    out = transpile('xs = ["a", "b"]\nprint(xs)\n')
    assert "repr_vector(xs)" in out


# ===========================================================================
# print(dict)
# ===========================================================================

def test_print_dict_literal_emits_repr_map():
    out = transpile('print({"a": 1, "b": 2})\n')
    assert "repr_map" in out


def test_print_dict_variable_emits_repr_map():
    out = transpile('d = {"a": 1, "b": 2}\nprint(d)\n')
    assert "repr_map(d)" in out


# ===========================================================================
# print(set)
# ===========================================================================

def test_print_set_literal_emits_repr_set():
    out = transpile('print({1, 2, 3})\n')
    assert "repr_set" in out


def test_print_set_variable_emits_repr_set():
    out = transpile('s = {1, 2, 3}\nprint(s)\n')
    assert "repr_set(s)" in out


# ===========================================================================
# print(tuple)
# ===========================================================================

def test_print_pair_emits_repr_pair():
    out = transpile('t = (1, 2)\nprint(t)\n')
    assert "repr_pair(t)" in out


def test_print_tuple3_emits_repr_tuple():
    out = transpile('t = (1, 2, 3)\nprint(t)\n')
    assert "repr_tuple(t)" in out


def test_print_tuple4_emits_repr_tuple():
    out = transpile('t = (1, 2, 3, 4)\nprint(t)\n')
    assert "repr_tuple(t)" in out


# ===========================================================================
# str(container) -- same dispatch
# ===========================================================================

def test_str_list_variable_emits_repr_vector():
    out = transpile('xs = [1, 2, 3]\nprint(str(xs))\n')
    assert "repr_vector(xs)" in out


def test_str_dict_variable_emits_repr_map():
    out = transpile('d = {"a": 1}\nprint(str(d))\n')
    assert "repr_map(d)" in out


# ===========================================================================
# Preamble has the four helpers
# ===========================================================================

def test_preamble_has_repr_vector():
    out = transpile('xs = [1]\nprint(xs)\n')
    assert "repr_vector" in out


def test_preamble_has_repr_map():
    out = transpile('d = {"a": 1}\nprint(d)\n')
    assert "repr_map" in out


def test_preamble_has_repr_set():
    out = transpile('s = {1}\nprint(s)\n')
    assert "repr_set" in out


def test_preamble_has_repr_pair():
    out = transpile('t = (1, 2)\nprint(t)\n')
    assert "repr_pair" in out


def test_preamble_has_repr_tuple():
    out = transpile('t = (1, 2, 3)\nprint(t)\n')
    assert "repr_tuple" in out
