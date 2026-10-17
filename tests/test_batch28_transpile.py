from kofty.transpiler import transpile


def test_list_read_from_function():
    out = transpile(
        'xs = [1, 2, 3]\n'
        'def show():\n'
        '    print(xs)\n'
        'show()\n'
    )
    assert "std::vector<int> xs;" in out


def test_list_string_read_from_function():
    out = transpile(
        'names = ["a", "b"]\n'
        'def show():\n'
        '    print(names)\n'
        'show()\n'
    )
    assert "std::vector<std::string> names;" in out


def test_dict_read_from_function():
    out = transpile(
        'd = {"a": 1}\n'
        'def show():\n'
        '    print(d)\n'
        'show()\n'
    )
    assert "std::map<std::string, int> d;" in out


def test_set_read_from_function():
    out = transpile(
        's = {1, 2, 3}\n'
        'def show():\n'
        '    print(s)\n'
        'show()\n'
    )
    assert "std::set<int> s;" in out


def test_tuple_read_from_function():
    out = transpile(
        't = (1, 2)\n'
        'def show():\n'
        '    print(t)\n'
        'show()\n'
    )
    assert "std::pair<int, int> t;" in out


def test_list_iteration_inside_function():
    out = transpile(
        'xs = [1, 2, 3]\n'
        'def show():\n'
        '    for x in xs:\n'
        '        print(x)\n'
        'show()\n'
    )
    assert "for (auto x : xs)" in out


def test_list_not_read_not_hoisted():
    out = transpile('xs = [1, 2, 3]\nprint(xs)\n')
    # No global declaration if no function reads it
    preamble = out.split("int main()")[0]
    assert "std::vector<int> xs;" not in preamble


def test_scalar_still_hoisted():
    out = transpile(
        'x = "hi"\n'
        'def show():\n'
        '    print(x)\n'
        'show()\n'
    )
    assert "std::string x;" in out


def test_mixed_scalar_and_container():
    out = transpile(
        'x = 42\n'
        'xs = [1, 2, 3]\n'
        'def show():\n'
        '    print(x)\n'
        '    print(xs)\n'
        'show()\n'
    )
    assert "int x;" in out
    assert "std::vector<int> xs;" in out


def test_bare_assignment_not_auto():
    out = transpile(
        'xs = [1, 2, 3]\n'
        'def show():\n'
        '    print(xs)\n'
        'show()\n'
    )
    main = out.split("int main()")[1]
    # In main, hoisted container uses bare `xs = ...;` (no `auto` redeclaration)
    assert "xs = std::vector<int>{1, 2, 3};" in main
    assert "auto xs = std::vector<int>" not in main
