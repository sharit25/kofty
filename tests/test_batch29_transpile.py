from kofty.transpiler import transpile, TranspileError
import pytest


def test_list_from_tuple():
    out = transpile('xs = list((1, 2, 3))\n')
    assert "std::vector<int>{1, 2, 3}" in out


def test_list_from_tuple_strings():
    out = transpile('xs = list(("a", "b", "c"))\n')
    assert "std::vector<std::string>" in out


def test_list_from_list_literal():
    out = transpile('xs = list([1, 2, 3])\n')
    assert "std::vector<int>{1, 2, 3}" in out


def test_tuple_from_list_literal():
    out = transpile('t = tuple([1, 2])\n')
    assert "std::make_pair(1, 2)" in out


def test_tuple_from_3_element_list():
    out = transpile('t = tuple([1, 2, 3])\n')
    assert "std::make_tuple(1, 2, 3)" in out


def test_set_from_tuple():
    out = transpile('s = set((1, 2, 3))\n')
    assert "std::set<int>{1, 2, 3}" in out


def test_set_from_list_literal():
    out = transpile('s = set([1, 2, 3])\n')
    assert "std::set<int>" in out


def test_dict_from_dict_literal():
    out = transpile('d = dict({"a": 1, "b": 2})\n')
    assert "std::map<std::string, int>" in out


def test_bool_from_int():
    out = transpile('b = bool(5)\n')
    assert "(bool)(5)" in out


def test_bool_from_variable():
    out = transpile('x = 5\nb = bool(x)\n')
    assert "(bool)(x)" in out


def test_list_with_no_args_raises():
    with pytest.raises(TranspileError, match="list\\(\\) requires exactly 1"):
        transpile('xs = list()\n')


def test_tuple_with_no_args_raises():
    with pytest.raises(TranspileError, match="tuple\\(\\) requires exactly 1"):
        transpile('t = tuple()\n')


def test_set_with_no_args_raises():
    with pytest.raises(TranspileError, match="set\\(\\) requires exactly 1"):
        transpile('s = set()\n')


def test_dict_with_no_args_raises():
    with pytest.raises(TranspileError, match="dict\\(\\) with 0 arguments"):
        transpile('d = dict()\n')


def test_dict_with_kwargs_raises():
    # dict(a=1, b=2) is a Call with keywords, not positional args.
    # Batch 5c kwargs are for function DEFS, not call sites.
    with pytest.raises(TranspileError):
        transpile('d = dict(a=1, b=2)\n')


def test_list_of_strings_used_in_loop():
    out = transpile(
        'xs = list(("a", "b", "c"))\n'
        'for x in xs:\n'
        '    print(x)\n'
    )
    assert "std::vector<std::string>" in out
    assert "for (auto x : xs)" in out


def test_bool_in_comparison():
    out = transpile('b = bool(1)\nif b:\n    print("yes")\n')
    assert "(bool)(1)" in out
