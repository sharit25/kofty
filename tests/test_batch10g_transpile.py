"""Batch 10g: set operations with inline set literals."""
from kofty.transpiler import transpile


def test_union_with_inline_literal_on_right():
    out = transpile("a = {1, 2, 3}\nb = a | {4, 5}\n")
    assert "set_op_union(a, std::set<int>{4, 5})" in out


def test_intersection_with_inline_literal_on_right():
    out = transpile("a = {1, 2, 3}\nb = a & {2, 3, 4}\n")
    assert "set_op_intersection(a, std::set<int>{2, 3, 4})" in out


def test_difference_with_inline_literal_on_right():
    out = transpile("a = {1, 2, 3}\nb = a - {1}\n")
    assert "set_op_difference(a, std::set<int>{1})" in out


def test_symdiff_with_inline_literal_on_right():
    out = transpile("a = {1, 2, 3}\nb = a ^ {3, 4}\n")
    assert "set_op_symdiff(a, std::set<int>{3, 4})" in out


def test_literal_on_left():
    out = transpile("a = {1, 2, 3}\nb = {4, 5} | a\n")
    assert "set_op_union(std::set<int>{4, 5}, a)" in out


def test_still_works_name_on_both_sides():
    out = transpile("a = {1, 2}\nb = {3, 4}\nc = a | b\n")
    assert "set_op_union(a, b)" in out
