"""Tests for complete dictionary support.

Adds: iteration (keys, values, items), .get(), .pop(), .update(),
      .clear(), membership (`in`), nested dicts.
"""

import pytest
from kofty.transpiler import transpile, TranspileError


# ============================================================
# Iteration
# ============================================================

def test_dict_iterate_keys_default():
    out = transpile(
        'd = {"a": 1, "b": 2}\n'
        "for k in d:\n"
        "    print(k)\n"
    )
    assert "for (auto& [" in out
    assert ": d)" in out


def test_dict_iterate_keys_explicit():
    out = transpile(
        'd = {"a": 1, "b": 2}\n'
        "for k in d.keys():\n"
        "    print(k)\n"
    )
    assert "for (auto& [" in out
    assert ": d)" in out


def test_dict_iterate_values():
    out = transpile(
        'd = {"a": 1, "b": 2}\n'
        "for v in d.values():\n"
        "    print(v)\n"
    )
    # values: bind _ to key, v to value
    assert "for (auto& [" in out
    assert ": d)" in out


def test_dict_iterate_items():
    out = transpile(
        'd = {"a": 1, "b": 2}\n'
        "for k, v in d.items():\n"
        "    print(k)\n"
    )
    assert "for (auto& [k, v] : d)" in out


# ============================================================
# .get()
# ============================================================

def test_dict_get_with_default():
    out = transpile(
        'd = {"a": 1}\n'
        "x = d.get(\"b\", 0)\n"
    )
    assert "d.count(" in out
    assert "d[\"b\"]" in out


def test_dict_get_no_default():
    out = transpile(
        'd = {"a": 1}\n'
        "x = d.get(\"a\")\n"
    )
    assert "d.count(" in out


# ============================================================
# .pop(), .update(), .clear()
# ============================================================

def test_dict_pop():
    out = transpile(
        'd = {"a": 1, "b": 2}\n'
        "x = d.pop(\"a\")\n"
    )
    assert "dict_pop" in out or ".erase(" in out


def test_dict_update():
    out = transpile(
        'd = {"a": 1}\n'
        'other = {"b": 2}\n'
        "d.update(other)\n"
    )
    assert "d.insert(other.begin(), other.end())" in out


def test_dict_clear():
    out = transpile(
        'd = {"a": 1}\n'
        "d.clear()\n"
    )
    assert "d.clear()" in out


# ============================================================
# Membership
# ============================================================

def test_dict_in():
    out = transpile(
        'd = {"a": 1}\n'
        'if "a" in d:\n'
        "    print(\"yes\")\n"
    )
    assert "d.count(" in out
    assert "> 0" in out


def test_dict_not_in():
    out = transpile(
        'd = {"a": 1}\n'
        'if "b" not in d:\n'
        "    print(\"no\")\n"
    )
    assert "d.count(" in out


# ============================================================
# Nested dicts
# ============================================================

def test_nested_dict_literal():
    out = transpile(
        'd = {"a": {"x": 1, "y": 2}}\n'
    )
    # Should emit a nested std::map
    assert "std::map" in out
    assert "std::map<std::string, std::map<std::string, int>>" in out


def test_nested_dict_access():
    out = transpile(
        'd = {"a": {"x": 1}}\n'
        'v = d["a"]["x"]\n'
    )
    assert 'd["a"]["x"]' in out
