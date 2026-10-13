"""Tests for `None` support in InterScript.

None is currently unsupported as a value. This adds:
  - `x = None`         -> `auto x = nullptr;`
  - `return None`      -> `return nullptr;`
  - `x is None`        -> `(x == nullptr)`
  - `x is not None`    -> `(x != nullptr)`
  - `def f(x=None)`    -> default argument nullptr
"""

from kofty.transpiler import transpile, TranspileError


def test_none_literal():
    out = transpile("x = None")
    assert "auto x = nullptr;" in out


def test_none_return():
    out = transpile(
        "def f():\n"
        "    return None\n"
    )
    assert "return nullptr;" in out


def test_none_is_check():
    out = transpile(
        "x = None\n"
        "if x is None:\n"
        "    print(\"empty\")\n"
    )
    assert "if ((x == nullptr)) {" in out


def test_none_is_not_check():
    out = transpile(
        "x = None\n"
        "if x is not None:\n"
        "    print(\"set\")\n"
    )
    assert "if ((x != nullptr)) {" in out


def test_none_equality():
    out = transpile(
        "x = None\n"
        "if x == None:\n"
        "    print(\"empty\")\n"
    )
    assert "if ((x == nullptr)) {" in out


def test_none_in_expression():
    # A None-returning function used in a conditional
    out = transpile(
        "def get():\n"
        "    return None\n"
        "v = get()\n"
        "if v is None:\n"
        "    print(\"nothing\")\n"
    )
    assert "return nullptr;" in out
    assert "if ((v == nullptr)) {" in out

def test_negative_literals_in_list():
    out = transpile("xs = [-1, -2, -3]")
    # Emitter wraps unary minus in parens: {(-1), (-2), (-3)}
    # Either form is valid C++.
    assert "std::vector<int>" in out
    assert "-1" in out
    assert "-2" in out
    assert "-3" in out


def test_mixed_sign_literals_in_list():
    out = transpile("xs = [-1.5, 2.5, -3.0]")
    assert "std::vector<double>" in out
