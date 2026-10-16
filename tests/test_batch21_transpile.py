"""Batch 21: list unpacking uses subscript, not std::get."""
from kofty.transpiler import transpile


def test_list_unpack_3():
    out = transpile('''
fruits = ["apple", "banana", "cherry"]
x, y, z = fruits
''')
    main = out.split("int main()")[1]
    assert "auto x = fruits[0];" in main
    assert "auto y = fruits[1];" in main
    assert "auto z = fruits[2];" in main
    assert "std::get<" not in main


def test_list_unpack_2():
    out = transpile('''
xs = [10, 20]
a, b = xs
''')
    main = out.split("int main()")[1]
    assert "auto a = xs[0];" in main
    assert "auto b = xs[1];" in main


def test_tuple_unpack_still_uses_std_get():
    out = transpile('''
t = (1, 2, 3)
a, b, c = t
''')
    main = out.split("int main()")[1]
    assert "std::get<0>(t)" in main
    assert "std::get<1>(t)" in main
    assert "std::get<2>(t)" in main


def test_pair_unpack_still_uses_first_second():
    out = transpile('''
p = (1, 2)
a, b = p
''')
    main = out.split("int main()")[1]
    assert "p.first" in main
    assert "p.second" in main
