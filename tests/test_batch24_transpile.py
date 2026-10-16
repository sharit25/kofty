"""Batch 24: `global x` writes to C++ global scope."""
from kofty.transpiler import transpile
import pytest

def test_global_write_without_top_level_assignment():
    out = transpile('''
def myFunc():
    global x
    x = "fantastic"

myFunc()
print("Kofty is " + x)
''')
    # The global is declared and appears before myFunc.
    assert "std::string x;" in out
    assert out.index("std::string x;") < out.index("auto myFunc()")


def test_global_write_with_top_level_assignment():
    out = transpile('''
x = "awesome"

def change():
    global x
    x = "fantastic"

change()
print("Kofty is " + x)
''')
    assert "std::string x;" in out
    main = out.split("int main()")[1]
    # Both assignments are bare (target the C++ global).
    assert 'x = "awesome";' in main
    assert "x = std::string(\"fantastic\");" in out or "x = \"fantastic\";" in out

@pytest.mark.xfail(reason="Batch 26: function-local shadows global")
def test_local_shadow_still_creates_local():
    # func_b assigns x but does NOT declare it global.
    # That x is local; it should NOT write the global.
    out = transpile('''
x = "outer"

def func_a():
    global x
    x = "changed"

def func_b():
    x = "local"
    print(x)

func_b()
func_a()
print(x)
''')
    # x is hoisted because func_a declared it global.
    assert "std::string x;" in out
    # func_b's local x still uses auto.
    func_b_body = out.split("auto func_b()")[1].split("}")[0]
    assert "auto x" in func_b_body


def test_reading_global_scalar_still_works():
    out = transpile('''
x = "awesome"

def show():
    print(x)

show()
''')
    assert "std::string x;" in out


def test_no_global_statement_unaffected():
    out = transpile('''
def hello():
    print("hi")

hello()
''')
    assert "int main()" in out
