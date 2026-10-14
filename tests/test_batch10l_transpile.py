"""Batch 10l: int / int must produce float (Python true division).

Python's `/` is always true division: `7 / 3` is 2.333...
C++'s `/` on two ints is integer division: `7 / 3` is 2.
Kofty must emit a cast when both operands are int-typed.
"""
from kofty.transpiler import transpile


def test_int_div_int_literals_cast_to_double():
    out = transpile("x = 7 / 3\n")
    main = out.split("int main()", 1)[1]
    assert "(7 / 3)" not in main
    assert "double" in main


def test_int_div_int_via_variables_cast_to_double():
    out = transpile("a = 7\nb = 3\nprint(f\"{a / b}\")\n")
    main = out.split("int main()", 1)[1]
    assert "(a / b)" not in main
    assert "double" in main


def test_int_div_int_in_fstring():
    out = transpile('print(f"{7 / 3}")\n')
    main = out.split("int main()", 1)[1]
    assert "(7 / 3)" not in main
    assert "double" in main


def test_float_div_float_unchanged():
    out = transpile("x = 5.0 / 2.0\n")
    assert "(5.0 / 2.0)" in out


def test_float_div_int_unchanged():
    out = transpile("x = 5.0 / 2\n")
    main = out.split("int main()", 1)[1]
    assert "(5.0 / 2)" in main


def test_int_div_float_unchanged():
    out = transpile("x = 5 / 2.0\n")
    main = out.split("int main()", 1)[1]
    assert "(5 / 2.0)" in main


def test_floordiv_still_uses_is_floordiv():
    # `//` must not be affected — it keeps the is_floordiv helper.
    out = transpile("x = 7 // 3\n")
    assert "is_floordiv(7, 3)" in out
