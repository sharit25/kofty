"""Batch 23: friendly error for `global`."""
import pytest
from kofty.transpiler import transpile, TranspileError


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
