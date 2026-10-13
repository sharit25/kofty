"""Tests for complete list support.

Adds: .pop, .insert, .remove, .sort, .reverse, .clear,
      `in`, negative indexing, slicing, list concat.
"""
import pytest
from kofty.transpiler import transpile, TranspileError


# ============================================================
# Methods
# ============================================================

def test_list_pop():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "x = xs.pop()\n"
    )
    # Batch 8f: pop() dispatches through the vec_pop template helper,
    # which reads back(), pops_back(), and returns the value.
    assert "vec_pop(xs)" in out


def test_list_insert():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "xs.insert(0, 9)\n"
    )
    assert "xs.insert(xs.begin() + 0, 9)" in out


def test_list_insert_variable_index():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "i = 1\n"
        "xs.insert(i, 99)\n"
    )
    assert "xs.insert(xs.begin() + i, 99)" in out


def test_list_remove():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "xs.remove(2)\n"
    )
    assert "std::find" in out and "erase" in out


def test_list_sort():
    out = transpile(
        "xs = [3, 1, 2]\n"
        "xs.sort()\n"
    )
    assert "std::sort(xs.begin(), xs.end())" in out


def test_list_reverse():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "xs.reverse()\n"
    )
    assert "std::reverse(xs.begin(), xs.end())" in out


def test_list_clear():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "xs.clear()\n"
    )
    assert "xs.clear()" in out


# ============================================================
# Membership
# ============================================================

def test_list_membership():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "if 2 in xs:\n"
        "    print(\"yes\")\n"
    )
    assert "std::find" in out and "xs.end()" in out


def test_list_not_in():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "if 5 not in xs:\n"
        "    print(\"no\")\n"
    )
    assert "std::find" in out and "xs.end()" in out
    # not in -> !=
    assert "!=" in out


# ============================================================
# Negative indexing
# ============================================================

def test_list_negative_index():
    out = transpile(
        "xs = [10, 20, 30]\n"
        "last = xs[-1]\n"
    )
    assert "xs[xs.size() - 1]" in out


def test_list_negative_index_2():
    out = transpile(
        "xs = [10, 20, 30]\n"
        "second_last = xs[-2]\n"
    )
    assert "xs[xs.size() - 2]" in out


# ============================================================
# Slicing
# ============================================================

def test_list_slice_simple():
    out = transpile(
        "xs = [1, 2, 3, 4, 5]\n"
        "mid = xs[1:3]\n"
    )
    # Check for std::vector construction from iterators
    assert "std::vector<int>(xs.begin() + 1, xs.begin() + 3)" in out


# ============================================================
# Concat
# ============================================================

def test_list_concat():
    out = transpile(
        "a = [1, 2]\n"
        "b = [3, 4]\n"
        "c = a + b\n"
    )
    assert "vec_concat" in out or "std::vector<int> c" in out


# ============================================================
# Errors
# ============================================================

def test_list_insert_wrong_arity():
    with pytest.raises(TranspileError, match="insert"):
        transpile(
            "xs = [1, 2, 3]\n"
            "xs.insert(0)\n"
        )
