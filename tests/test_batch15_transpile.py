"""Batch 15: int(x) / float(x) parse string variables.

Fix surfaced by examples/user_input.kfy: int(age_str) emitted
(int)age_str, which is an invalid C++ cast from std::string to
int. Now any Name argument routes through std::stoi / std::stod.
"""
from kofty.transpiler import transpile


def test_int_of_named_variable_uses_stoi():
    out = transpile("""
s = input("num: ")
n = int(s)
print(n)
""")
    assert "std::stoi(s)" in out


def test_float_of_named_variable_uses_stod():
    out = transpile("""
s = input("num: ")
n = float(s)
print(n)
""")
    assert "std::stod(s)" in out


def test_int_of_input_direct_still_uses_stoi():
    out = transpile('n = int(input("n: "))\n')
    assert "std::stoi(input_line(" in out


def test_float_of_input_direct_still_uses_stod():
    out = transpile('n = float(input("n: "))\n')
    assert "std::stod(input_line(" in out


def test_int_of_literal_still_uses_c_cast():
    out = transpile('n = int(42)\n')
    assert "(int)42" in out


def test_float_of_literal_still_uses_c_cast():
    out = transpile('n = float(3.14)\n')
    assert "(double)3.14" in out
