"""Batch 10h: is_to_string overloads for containers."""
from kofty.transpiler import transpile


def test_is_to_string_vector_overload_present():
    out = transpile("xs = [1, 2, 3]\nprint(xs)\n")
    assert "is_to_string(const std::vector<T>&" in out


def test_is_to_string_map_overload_present():
    out = transpile('d = {"a": 1}\nprint(d)\n')
    assert "is_to_string(const std::map<K, V>&" in out


def test_is_to_string_set_overload_present():
    out = transpile("s = {1, 2, 3}\nprint(s)\n")
    assert "is_to_string(const std::set<T>&" in out


def test_is_to_string_pair_overload_present():
    out = transpile("t = (1, 2)\nprint(t)\n")
    assert "is_to_string(const std::pair<T1, T2>&" in out


def test_is_to_string_tuple_overload_present():
    out = transpile("t = (1, 2, 3)\nprint(t)\n")
    assert "is_to_string(const std::tuple<Ts...>&" in out
