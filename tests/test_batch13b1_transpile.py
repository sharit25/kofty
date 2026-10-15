"""Batch 13b.1: extend _container_kind to recognize str_split.

Bug: print("a,b,c".split(",")) emits
    std::cout << str_split(std::string("a,b,c"), ",") << std::endl;
which g++ rejects because std::vector<std::string> has no
operator<<. The 13b fix recognized vec_concat and set_op_*, but
str_split is a container-returning builtin that wasn't on the
list. Discovered by examples/showcase.kfy line 665.
"""
import pytest
from kofty.transpiler import transpile


def _main(out):
    return out.split("int main()")[1] if "int main()" in out else out


# --- the bug ----------------------------------------------------------------

def test_print_str_split_via_method_call():
    out = transpile('print("a,b,c".split(","))\n')
    main = _main(out)
    assert "repr_vector(" in main


def test_print_str_split_via_variable():
    out = transpile('''
s = "a,b,c"
parts = s.split(",")
print(parts)
''')
    main = _main(out)
    assert "repr_vector(" in main


def test_str_split_result_assigned_not_printed_has_no_repr():
    # If the split result is stored, we shouldn't force a wrapper on
    # the store itself — only on the print.
    out = transpile('''
parts = "a,b,c".split(",")
x = parts[0]
''')
    main = _main(out)
    # No print call, so no repr_vector call site.
    assert "repr_vector(" not in main


# --- regression: 13b still works --------------------------------------------

def test_list_concat_still_wrapped():
    out = transpile('''
xs = [1, 2]
ys = [3, 4]
print(xs + ys)
''')
    assert "repr_vector(" in _main(out)


def test_set_union_still_wrapped():
    out = transpile('''
s1 = {1, 2}
s2 = {3, 4}
print(s1 | s2)
''')
    assert "repr_set(" in _main(out)


def test_list_slice_still_wrapped():
    out = transpile('''
xs = [10, 20, 30, 40]
print(xs[1:3])
''')
    assert "repr_vector(" in _main(out)


# --- regression: non-containers not wrapped ---------------------------------

def test_print_plain_string_no_repr():
    out = transpile('print("hello")\n')
    assert "repr_vector(" not in _main(out)


def test_print_plain_int_no_repr():
    out = transpile('print(42)\n')
    assert "repr_vector(" not in _main(out)
