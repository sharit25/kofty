"""Batch 13a: preamble ordering — container is_to_string overloads
must precede the repr_* templates that use them. Transpile-only.

The test asserts on the *order* of declarations in the emitted C++.
Bug #1 in BUGS.md was a two-phase-lookup failure: repr_vector (and
friends) call is_to_string on their elements, but the container
is_to_string overloads were declared later in the file. Template
instantiation couldn't find them.
"""
import pytest
from kofty.transpiler import transpile


def _emit(src=""):
    return transpile(src if src else "x = 1\n")


def _pos(out, needle):
    i = out.find(needle)
    assert i >= 0, f"expected to find {needle!r} in emitted C++"
    return i


def test_pair_is_to_string_before_repr_vector():
    out = _emit()
    pos_pair_overload = _pos(out, "is_to_string(const std::pair<")
    pos_repr_vector = _pos(out, "std::string repr_vector(const std::vector<T>& v) {")
    assert pos_pair_overload < pos_repr_vector, (
        "container is_to_string overloads must be declared before "
        "repr_vector so template instantiation can find them"
    )


def test_vector_is_to_string_before_repr_vector():
    out = _emit()
    pos_vec_overload = _pos(out, "is_to_string(const std::vector<")
    # Look for the *definition* (ends with ") {"), not the forward
    # declaration (ends with ");").
    pos_repr_vector  = _pos(out, "std::string repr_vector(const std::vector<T>& v) {")
    assert pos_vec_overload < pos_repr_vector

def test_map_is_to_string_before_repr_map():
    out = _emit()
    pos_map_overload = _pos(out, "is_to_string(const std::map<")
    pos_repr_map = _pos(out, "std::string repr_map(const std::map<K, V>& m) {")
    assert pos_map_overload < pos_repr_map


def test_set_is_to_string_before_repr_set():
    out = _emit()
    pos_set_overload = _pos(out, "is_to_string(const std::set<")
    pos_repr_set = _pos(out, "std::string repr_set(const std::set<T>& s) {")
    assert pos_set_overload < pos_repr_set


def test_tuple_is_to_string_before_repr_tuple():
    out = _emit()
    pos_tuple_overload = _pos(out, "is_to_string(const std::tuple<")
    pos_repr_tuple = _pos(out, "std::string repr_tuple(const std::tuple<Ts...>& t) {")
    assert pos_tuple_overload < pos_repr_tuple


def test_scalar_is_to_string_still_first():
    # Regression: scalar overloads must stay ahead of everything
    # (they're the base case the container overloads eventually
    # recurse down to).
    out = _emit()
    pos_scalar = _pos(out, "is_to_string(const std::string& s)")
    pos_vector = _pos(out, "is_to_string(const std::vector<")
    assert pos_scalar < pos_vector


def test_repr_pair_still_defined():
    # We're reordering, not removing. All five repr_* helpers must
    # still be emitted.
    out = _emit()
    for name in ("repr_vector", "repr_map", "repr_set",
                 "repr_pair", "repr_tuple"):
        assert f"std::string {name}(" in out, f"{name} missing"


def test_nested_repr_still_works_at_transpile_level():
    # The bug manifests at compile time, not transpile time — but
    # this test pins the emission shape so a regression in the
    # repr dispatch is caught even without g++.
    out = transpile("xs = [(1, 2), (3, 4)]\nprint(xs)\n")
    assert "repr_vector(xs)" in out
    assert "std::pair<int, int>" in out
