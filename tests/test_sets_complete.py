"""Tests for set support.

Adds: literals, .add(), .remove(), .discard(), .clear(), len(),
      membership (`in`), union/intersection/difference, iteration.
"""

import pytest
from kofty.transpiler import transpile, TranspileError


def test_set_literal_int():
    out = transpile("s = {1, 2, 3}")
    assert "std::set<int>{1, 2, 3}" in out
    assert "#include <set>" in out


def test_set_literal_string():
    out = transpile('s = {"a", "b"}')
    assert "std::set<std::string>" in out


def test_set_add():
    out = transpile(
        "s = {1, 2, 3}\n"
        "s.add(4)\n"
    )
    assert "s.insert(4)" in out


def test_set_remove():
    out = transpile(
        "s = {1, 2, 3}\n"
        "s.remove(2)\n"
    )
    assert "s.erase(2)" in out


def test_set_discard():
    out = transpile(
        "s = {1, 2, 3}\n"
        "s.discard(2)\n"
    )
    assert "s.erase(2)" in out


def test_set_clear():
    out = transpile(
        "s = {1, 2, 3}\n"
        "s.clear()\n"
    )
    assert "s.clear()" in out


def test_set_len():
    out = transpile(
        "s = {1, 2, 3}\n"
        "n = len(s)\n"
    )
    assert "s.size()" in out


def test_set_membership():
    out = transpile(
        "s = {1, 2, 3}\n"
        "if 2 in s:\n"
        "    print(\"yes\")\n"
    )
    assert "s.count(2) > 0" in out


def test_set_not_in():
    out = transpile(
        "s = {1, 2, 3}\n"
        "if 5 not in s:\n"
        "    print(\"no\")\n"
    )
    assert "s.count(5)" in out


def test_set_iteration():
    out = transpile(
        "s = {1, 2, 3}\n"
        "for x in s:\n"
        "    print(x)\n"
    )
    assert "for (auto x : s)" in out


def test_set_union():
    out = transpile(
        "a = {1, 2}\n"
        "b = {2, 3}\n"
        "c = a | b\n"
    )
    assert "set_union" in out or "set_op_union" in out


def test_set_intersection():
    out = transpile(
        "a = {1, 2}\n"
        "b = {2, 3}\n"
        "c = a & b\n"
    )
    assert "set_intersection" in out or "set_op_intersection" in out


def test_set_difference():
    out = transpile(
        "a = {1, 2}\n"
        "b = {2, 3}\n"
        "c = a - b\n"
    )
    assert "set_difference" in out or "set_op_difference" in out


def test_set_symmetric_difference():
    out = transpile(
        "a = {1, 2}\n"
        "b = {2, 3}\n"
        "c = a ^ b\n"
    )
    assert "set_symmetric_difference" in out or "set_op_symdiff" in out
