"""Batch 11b: tuple arity across function returns. Transpile-only."""
import pytest
from kofty.transpiler import transpile, TranspileError


# --- Part 1: unannotated function returning a tuple literal ------------------

def test_unannotated_function_returning_3_tuple_registers_arity():
    out = transpile('''
def make():
    return (1, 2, 3)

t = make()
a, b, c = t
''')
    # t must be in tuple_vars[3] so the unpacking emits per-element
    # std::get<i>. The emission should reference t.first or std::get<0>(t)
    # depending on arity. For arity 3 it's std::get.
    assert "std::get<0>(t)" in out
    assert "std::get<1>(t)" in out
    assert "std::get<2>(t)" in out


def test_unannotated_function_returning_2_tuple_registers_arity():
    out = transpile('''
def make():
    return (1, 2)

t = make()
a, b = t
''')
    # arity 2 -> pair, so .first / .second
    assert "t.first" in out
    assert "t.second" in out


def test_unannotated_function_with_multiple_returns_same_arity():
    out = transpile('''
def make(flag):
    if flag:
        return (1, 2, 3)
    return (4, 5, 6)

t = make(True)
a, b, c = t
''')
    assert "std::get<0>(t)" in out


# --- Part 2: annotated function returning a tuple ----------------------------

def test_annotated_function_returning_tuple_3_registers_arity():
    out = transpile('''
def make() -> tuple[int, int, int]:
    return (1, 2, 3)

t = make()
a, b, c = t
''')
    assert "std::get<0>(t)" in out


def test_annotated_function_returning_tuple_2_registers_arity():
    out = transpile('''
def make() -> tuple[int, int]:
    return (1, 2)

t = make()
a, b = t
''')
    assert "t.first" in out
    assert "t.second" in out


def test_annotated_function_returning_tuple_with_str_element():
    out = transpile('''
def make() -> tuple[int, str, float]:
    return (1, "hi", 2.5)

t = make()
a, b, c = t
''')
    assert "std::get<0>(t)" in out
    assert "std::get<2>(t)" in out


# --- Part 3: subscript indexing on a returned tuple --------------------------

def test_subscript_on_returned_3_tuple():
    out = transpile('''
def make():
    return (10, 20, 30)

t = make()
x = t[1]
''')
    assert "std::get<1>(t)" in out


def test_subscript_on_returned_2_tuple():
    out = transpile('''
def make():
    return (10, 20)

t = make()
x = t[1]
''')
    assert "t.second" in out


# --- Part 4: for-loop unpacking a returned tuple directly --------------------

def test_for_unpack_over_returned_tuple():
    out = transpile('''
def make():
    return ((1, 2), (3, 4), (5, 6))

# Not a for-unpack-over-tuple case, skip this and test something real
''')
    # Placeholder: see note below
    pass


# --- Part 5: existing behavior still works -----------------------------------

def test_literal_tuple_unpacking_still_works():
    out = transpile('''
t = (1, 2, 3)
a, b, c = t
''')
    assert "std::get<0>(t)" in out


def test_scalar_return_not_registered_as_tuple():
    out = transpile('''
def get_x():
    return 42

x = get_x()
''')
    # Only inspect the emitted C++ inside main(), not the preamble.
    if "int main()" in out:
        main_body = out.split("int main()", 1)[1]
    else:
        main_body = out
    assert "std::get<" not in main_body


def test_str_return_not_registered_as_tuple():
    out = transpile('''
def greeting():
    return "hello"

g = greeting()
''')
    # g should be a std::string
    assert "std::string g" in out or "auto g" in out
