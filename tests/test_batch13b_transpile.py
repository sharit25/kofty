"""Batch 13b: _container_repr for binops, slices, calls.

print(container_expr) must emit repr_vector / repr_set / etc.
for expressions that yield containers — not just for Names and
literals. Bug #2 in BUGS.md.
"""
import pytest
from kofty.transpiler import transpile


# --- list concat via binop ---------------------------------------------------

def test_print_list_concat_binop():
    out = transpile('''
xs = [1, 2]
ys = [3, 4]
print(xs + ys)
''')
    # Should dispatch through repr_vector, not emit raw std::cout <<
    # (xs + ys).
    main = out.split("int main()")[1]
    assert "repr_vector(" in main


def test_print_list_concat_reversed():
    out = transpile('''
xs = [1, 2]
ys = [3, 4]
print(ys + xs)
''')
    main = out.split("int main()")[1]
    assert "repr_vector(" in main


# --- set algebra via binop ---------------------------------------------------

def test_print_set_union():
    out = transpile('''
s1 = {1, 2, 3}
s2 = {3, 4, 5}
print(s1 | s2)
''')
    main = out.split("int main()")[1]
    assert "repr_set(" in main


def test_print_set_intersection():
    out = transpile('''
s1 = {1, 2, 3}
s2 = {3, 4, 5}
print(s1 & s2)
''')
    main = out.split("int main()")[1]
    assert "repr_set(" in main


def test_print_set_difference():
    out = transpile('''
s1 = {1, 2, 3}
s2 = {3, 4, 5}
print(s1 - s2)
''')
    main = out.split("int main()")[1]
    assert "repr_set(" in main


def test_print_set_symdiff():
    out = transpile('''
s1 = {1, 2, 3}
s2 = {3, 4, 5}
print(s1 ^ s2)
''')
    main = out.split("int main()")[1]
    assert "repr_set(" in main


# --- list slicing ------------------------------------------------------------

def test_print_list_slice():
    out = transpile('''
xs = [10, 20, 30, 40, 50]
print(xs[1:4])
''')
    main = out.split("int main()")[1]
    assert "repr_vector(" in main


def test_print_list_slice_open_end():
    out = transpile('''
xs = [10, 20, 30]
print(xs[1:])
''')
    main = out.split("int main()")[1]
    assert "repr_vector(" in main


# --- regression: existing behaviour not changed ------------------------------

def test_print_list_var_still_works():
    out = transpile('''
xs = [1, 2, 3]
print(xs)
''')
    assert "repr_vector(xs)" in out


def test_print_set_var_still_works():
    out = transpile('''
s = {1, 2, 3}
print(s)
''')
    assert "repr_set(s)" in out


def test_print_int_still_works():
    out = transpile('''
x = 5
print(x)
''')
    # Plain int print — must NOT wrap in repr_vector.
    # Extract the main body and check.
    main = out.split("int main()")[1] if "int main()" in out else out
    assert "repr_vector" not in main
    assert "std::cout << x" in main or "std::cout << (x)" in main
