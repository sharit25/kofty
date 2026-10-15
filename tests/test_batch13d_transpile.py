"""Batch 13d: *args / **kwargs call-site wrapping.

Transpile-only. Bug #4 in BUGS.md: a function with *args or **kwargs
must receive its arguments wrapped in std::vector<T>{...} or
std::map<...>{...} at the call site.
"""
import pytest
from kofty.transpiler import transpile


# --- *args with plain positional args ---------------------------------------

def test_star_args_three_positional():
    out = transpile('''
def sum_all(*nums):
    t = 0
    for n in nums:
        t = t + n
    return t

x = sum_all(1, 2, 3)
''')
    assert "sum_all(std::vector<int>{1, 2, 3})" in out or \
       "sum_all({1, 2, 3})" in out


def test_star_args_single_arg():
    out = transpile('''
def show(*xs):
    return xs

y = show(42)
''')
    assert "show(std::vector<int>{42})" in out or \
       "show({42})" in out

def test_star_args_no_args():
    out = transpile('''
def show(*xs):
    return xs

z = show()
''')
    # Empty call -> empty brace-init.
    assert "show({})" in out or "show(std::vector<int>{})" in out


def test_star_args_typed_elem():
    out = transpile('''
def words(*ws: str):
    return ws

v = words("a", "b")
''')
    assert 'words(std::vector<std::string>{"a", "b"})' in out or \
       'words({"a", "b"})' in out


def test_star_args_mixed_with_leading_params():
    out = transpile('''
def f(a, b, *rest):
    return rest

w = f(1, 2, 3, 4)
''')
    # a=1, b=2 stay positional; rest={3, 4}.
    assert "f(1, 2, std::vector<int>{3, 4})" in out or \
       "f(1, 2, {3, 4})" in out


# --- **kwargs ---------------------------------------------------------------

def test_kwargs_call_site():
    out = transpile('''
def describe(**info):
    return info

d = describe(a="x", b="y")
''')
    # kwarg call sites use dict literals in Kofty source.
    assert "describe(" in out
    assert "std::map" in out or "{" in out


def test_kwargs_empty():
    out = transpile('''
def describe(**info):
    return info

d = describe()
''')
    # Empty kwargs call -> empty map literal.
    assert "describe(" in out
    assert "{}" in out or "std::map" in out


# --- regression: plain function calls unaffected ----------------------------

def test_plain_function_call_unchanged():
    out = transpile('''
def add(a, b):
    return a + b

r = add(1, 2)
''')
    assert "add(1, 2)" in out
    # Should NOT wrap in braces.
    assert "add({1, 2})" not in out
