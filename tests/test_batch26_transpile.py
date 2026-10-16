"""Batch 26: function-local variable shadows module-level."""
from kofty.transpiler import transpile


def test_local_shadows_module_level():
    out = transpile('''
x = "awesome"

def myfunc():
    x = "fantastic"
    print("Kofty is " + x)

myfunc()
print("Kofty is " + x)
''')
    assert "std::string x;" in out
    func_body = out.split("auto myfunc()")[1].split("}")[0]
    assert "auto x" in func_body
    main = out.split("int main()")[1]
    assert "x = std::string(\"awesome\");" in main or 'x = "awesome";' in main


def test_global_still_writes_module_level():
    out = transpile('''
def change():
    global x
    x = "changed"

change()
print(x)
''')
    assert "std::string x;" in out
    func_body = out.split("auto change()")[1].split("}")[0]
    assert "auto x" not in func_body


def test_no_module_level_x_still_works():
    out = transpile('''
def hello():
    msg = "hi"
    print(msg)

hello()
''')
    assert "int main()" in out


def test_all_four_tutorial_examples_pass():
    out2 = transpile('''
x = "awesome"

def function():
    print("Kofty is " + x)

function()
''')
    assert "std::string x;" in out2

    out3 = transpile('''
def myfunc():
    global x
    x = "fantastic"

myfunc()
print("Kofty is " + x)
''')
    assert "std::string x;" in out3

    out4 = transpile('''
x = "awesome"

def function():
    global x
    x = "fantastic"

function()
print("Kofty is " + x)
''')
    assert "std::string x;" in out4
