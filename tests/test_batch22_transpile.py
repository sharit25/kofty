"""Batch 22: top-level scalars read from functions are hoisted."""
from kofty.transpiler import transpile


def test_function_reads_top_level_string():
    out = transpile('''
x = "awesome"

def myFunc():
    print("Kofty is " + x)

myFunc()
''')
    assert "std::string x;" in out
    # Declaration appears before myFunc.
    assert out.index("std::string x;") < out.index("auto myFunc()")


def test_function_reads_top_level_int():
    out = transpile('''
count = 5

def show():
    print(count)

show()
''')
    assert "int count;" in out
    assert out.index("int count;") < out.index("auto show()")


def test_top_level_not_read_by_function_NOT_hoisted():
    # Nothing reads `x` from a function, so no hoist.
    out = transpile('''
x = 42
print(x)
''')
    assert "int x;" not in out
    main = out.split("int main()")[1]
    assert "auto x = 42;" in main


def test_list_NOT_hoisted_even_if_read():
    # Containers stay local — no hoist yet.
    out = transpile('''
xs = [1, 2, 3]

def show():
    print(xs)

show()
''')
    # No global declaration for xs.
    before_main = out.split("int main()")[0]
    assert "std::vector<int> xs;" not in before_main
