"""Batch 10i: user classes in f-strings dispatch to __str__."""
from kofty.transpiler import transpile


def test_user_class_in_fstring_uses_str_method():
    out = transpile(
        "class P:\n"
        "    def __str__(self):\n"
        "        return \"P\"\n"
        "p = P()\n"
        "print(f\"x = {p}\")\n"
    )
    assert "p.__str__()" in out
    # Must not fall through to the primitive overloads:
    assert "is_to_string(p)" not in out


def test_user_class_from_method_call_in_fstring():
    out = transpile(
        "class P:\n"
        "    def __str__(self):\n"
        "        return \"P\"\n"
        "    @classmethod\n"
        "    def origin(cls):\n"
        "        return P()\n"
        "o = P.origin()\n"
        "print(f\"o = {o}\")\n"
    )
    assert "o.__str__()" in out


def test_user_class_from_add_in_fstring():
    out = transpile(
        "class P:\n"
        "    def __str__(self):\n"
        "        return \"P\"\n"
        "    def __add__(self, other):\n"
        "        return self\n"
        "a = P()\n"
        "b = P()\n"
        "print(f\"c = {a + b}\")\n"
    )
    # The BinOp result is a user-class instance; should dispatch
    # to __str__ on the produced expression.
    assert ".__str__()" in out


def test_primitive_in_fstring_still_uses_is_to_string():
    out = transpile("x = 5\nprint(f\"x = {x}\")\n")
    assert "is_to_string(x)" in out


def test_string_in_fstring_unchanged():
    out = transpile("s = \"hi\"\nprint(f\"s = {s}\")\n")
    assert "is_to_string(s)" in out
