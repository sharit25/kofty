"""Batch 14: variable redeclaration (Bug #5).

Every assignment used to emit `auto name = <expr>;`. A second
assignment to the same name in main's top-level scope produced a
conflicting declaration and g++ rejected it:
    error: conflicting declaration 'auto s1'
    note: previous declaration as 'std::set<int> s1'

Fix: track top-level variable types. Rebind on subsequent
assignments (bare `name = ...`) when the type is unchanged; raise
TranspileError when the type changes.
"""
import pytest
from kofty.transpiler import transpile, TranspileError


def _main(out):
    return out.split("int main()")[1]


# --- same-type rebind: drop `auto` ------------------------------------------

def test_reassign_int_same_type():
    out = transpile('''
x = 1
x = 2
print(x)
''')
    main = _main(out)
    assert "auto x = 1;" in main
    assert "auto x = 2;" not in main
    assert "x = 2;" in main


def test_reassign_set_literal_larger():
    out = transpile('''
s = {1, 2, 3}
s = {1, 2, 3, 4}
print(s)
''')
    main = _main(out)
    assert "auto s = std::set<int>{1, 2, 3};" in main
    assert "auto s = std::set<int>{1, 2, 3, 4};" not in main
    assert "s = std::set<int>{1, 2, 3, 4};" in main


def test_reassign_list_literal():
    out = transpile('''
xs = [1, 2, 3]
xs = [4, 5, 6]
print(xs)
''')
    main = _main(out)
    assert "auto xs = std::vector<int>{1, 2, 3};" in main
    assert "auto xs = std::vector<int>{4, 5, 6};" not in main
    assert "xs = std::vector<int>{4, 5, 6};" in main

def test_reassign_string_literal():
    out = transpile('''
s = "hello"
s = "world"
print(s)
''')
    main = _main(out)
    assert 'auto s = "hello";' in main or 'auto s = std::string("hello");' in main
    assert 'auto s = "world";' not in main
    assert 'auto s = std::string("world");' not in main
    assert 's = "world";' in main or 's = std::string("world");' in main


def test_three_assignments_same_type():
    out = transpile('''
x = 1
x = 2
x = 3
print(x)
''')
    main = _main(out)
    assert "auto x = 1;" in main
    assert main.count("auto x") == 1
    assert "x = 2;" in main
    assert "x = 3;" in main


# --- regressions -------------------------------------------------------------

def test_single_assignment_still_emits_auto():
    out = transpile('x = 1\nprint(x)\n')
    main = _main(out)
    assert "auto x = 1;" in main


def test_distinct_names_no_interference():
    out = transpile('''
a = 1
b = 2
a = 3
b = 4
''')
    main = _main(out)
    assert "auto a = 1;" in main
    assert "auto b = 2;" in main
    assert "a = 3;" in main
    assert "b = 4;" in main


def test_reassign_inside_function_untouched():
    # Function-body variables are in their own scope; current
    # behavior (re-emit auto) is preserved. Multiple `auto x = ...`
    # inside a function body is a separate concern.
    out = transpile('''
def f():
    y = 1
    y = 2
    return y

print(f())
''')
    # We just want to confirm no crash and the emission is coherent.
    assert "int f()" in out or "auto f()" in out
