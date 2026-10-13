"""Tests for std::optional support.

InterScript maps Python's "value or None" pattern to C++'s
std::optional<T>. Triggered by:
  - a function that returns both None and a value
  - a variable assigned both None and a value
"""

from kofty.transpiler import transpile, TranspileError


# ============================================================
# Function returns
# ============================================================

def test_function_mixed_returns_uses_optional():
    out = transpile(
        "def find(xs, target):\n"
        "    for x in xs:\n"
        "        if x == target:\n"
        "            return x\n"
        "    return None\n"
    )
    assert "std::optional<int>" in out
    assert "return std::nullopt;" in out


def test_optional_function_includes_optional_header():
    out = transpile(
        "def f(x):\n"
        "    if x > 0:\n"
        "        return x\n"
        "    return None\n"
    )
    assert "#include <optional>" in out


def test_optional_return_annotation_int():
    out = transpile(
        "def f(x: int) -> int:\n"
        "    if x > 0:\n"
        "        return x\n"
        "    return None\n"
    )
    # Explicit int annotation + None -> still becomes optional<int>
    assert "std::optional<int> f(int x)" in out


def test_function_only_none_returns_not_optional():
    out = transpile(
        "def f():\n"
        "    return None\n"
    )
    # Only None returns: not an optional, plain return
    assert "return nullptr;" in out
    assert "std::optional" not in out.split("int main")[0]


# ============================================================
# Variable tracking
# ============================================================

def test_variable_none_then_int_becomes_optional():
    out = transpile(
        "x = None\n"
        "x = 5\n"
    )
    assert "std::optional<int> x;" in out


def test_variable_none_then_string_becomes_optional():
    out = transpile(
        "x = None\n"
        "x = \"hello\"\n"
    )
    assert "std::optional<std::string> x;" in out


def test_variable_only_none_stays_nullptr():
    out = transpile(
        "x = None\n"
        "if x is None:\n"
        "    print(\"empty\")\n"
    )
    # Only None: plain nullptr, no optional
    assert "auto x = nullptr;" in out


# ============================================================
# `is None` / `is not None` on optionals
# ============================================================

def test_optional_is_none_check():
    out = transpile(
        "x = None\n"
        "x = 5\n"
        "if x is None:\n"
        "    print(\"empty\")\n"
    )
    assert "if ((!x.has_value())) {" in out


def test_optional_is_not_none_check():
    out = transpile(
        "x = None\n"
        "x = 5\n"
        "if x is not None:\n"
        "    print(\"set\")\n"
    )
    assert "if ((x.has_value())) {" in out


# ============================================================
# Accessing the value
# ============================================================

def test_optional_in_str_uses_value():
    out = transpile(
        "x = None\n"
        "x = 5\n"
        "s = str(x)\n"
    )
    # str() on an optional unwraps with .value()
    assert "format_float(x.value())" in out


# ============================================================
# End-to-end
# ============================================================

def test_optional_full_example():
    out = transpile(
        "def find(xs, target):\n"
        "    for x in xs:\n"
        "        if x == target:\n"
        "            return x\n"
        "    return None\n"
        "\n"
        "result = find([1, 2, 3], 5)\n"
        "if result is None:\n"
        "    print(\"not found\")\n"
        "else:\n"
        "    print(\"found: \" + str(result))\n"
    )
    assert "std::optional<int> find" in out
    assert "return std::nullopt;" in out
    assert ".has_value()" in out or ".value()" in out
