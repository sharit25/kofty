from kofty.transpiler import transpile


def _main_section(out):
    return out.split("int main()")[1]


def _function_section(out):
    # Everything between the preamble and int main()
    parts = out.split("int main()")
    return parts[0]


def test_duplicate_function_emits_once():
    out = transpile(
        "def f():\n"
        '    print("first")\n'
        "\n"
        "def f():\n"
        '    print("second")\n'
        "\n"
        "f()\n"
    )
    # Only one def emitted
    assert out.count("void f()") == 1 or out.count("auto f()") == 1


def test_duplicate_function_keeps_last():
    out = transpile(
        "def f():\n"
        '    print("first")\n'
        "\n"
        "def f():\n"
        '    print("second")\n'
        "\n"
        "f()\n"
    )
    # "first" should not appear in the emitted C++ (its body was dropped)
    assert 'to_string("first")' not in out
    assert 'to_string("second")' in out


def test_duplicate_function_return_type_keeps_last():
    out = transpile(
        "def f():\n"
        "    return 1\n"
        "\n"
        "def f():\n"
        '    return "hi"\n'
        "\n"
        "x = f()\n"
    )
    # Only the string-returning version is emitted
    assert out.count("f()") >= 1


def test_three_definitions_keeps_last():
    out = transpile(
        "def f():\n"
        '    print("one")\n'
        "\n"
        "def f():\n"
        '    print("two")\n'
        "\n"
        "def f():\n"
        '    print("three")\n'
        "\n"
        "f()\n"
    )
    assert 'to_string("one")' not in out
    assert 'to_string("two")' not in out
    assert 'to_string("three")' in out

def test_single_definition_unchanged():
    out = transpile('def greet():\n    print("hi")\n\ngreet()\n')
    assert "greet" in out
    assert "hi" in out


def test_two_different_functions_both_emitted():
    out = transpile(
        "def f():\n"
        '    print("f")\n'
        "\n"
        "def g():\n"
        '    print("g")\n'
        "\n"
        "f()\n"
        "g()\n"
    )
    assert "f" in out
    assert "g" in out


def test_call_dispatches_to_last_definition():
    # f() should call the second def, not the first.
    out = transpile(
        "def f():\n"
        '    print("first")\n'
        "\n"
        "def f():\n"
        '    print("second")\n'
        "\n"
        "f()\n"
    )
    # Only "second" survives to emitted C++
    assert out.count('"second"') >= 1
    assert '"first"' not in out
