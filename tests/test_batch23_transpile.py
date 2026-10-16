"""Batch 23: friendly error for `global`."""
import pytest
from kofty.transpiler import transpile, TranspileError


def test_global_raises_clear_error():
    with pytest.raises(TranspileError) as e:
        transpile('''
x = "awesome"

def change():
    global x
    x = "fantastic"

change()
''')
    msg = str(e.value)
    assert "global" in msg
    assert "not supported" in msg
    assert "return value" in msg


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
