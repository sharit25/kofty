"""tests/test_fstrings.py

Batch 2b: f-strings and .format().

Scope:
    f"literal"                   -> "literal"
    f"{expr}"                    -> str(expr)
    f"prefix {expr} suffix"      -> "prefix " + str(expr) + " suffix"
    f"{a}{b}"                    -> str(a) + str(b)
    f"{a + b}"                   -> str(a + b)
    f"{{literal braces}}"        -> "{literal braces}"
    "{} and {}".format(a, b)     -> positional substitution
    "{0} {1} {0}".format(a, b)   -> indexed substitution

OUT OF SCOPE (do not test here):
    - format specs: f"{x:.2f}"   "{:05d}"   "{:>10}"
    - conversions:  f"{x!r}"     f"{x!s}"
    - kwargs:       "{x}".format(x=1)
    - nested braces in .format()
    - f-string with newline: f"{x}\n"
"""

import shutil
import subprocess
import sys
import textwrap

import pytest


def run_is(src: str, tmp_path) -> tuple[int, str, str]:
    if shutil.which("g++") is None:
        pytest.skip("g++ not on PATH")
    src = textwrap.dedent(src).strip() + "\n"
    is_file = tmp_path / "prog.kfy"
    is_file.write_text(src)
    result = subprocess.run(
        [sys.executable, "-m", "kofty.cli", str(is_file)],
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout, result.stderr


def assert_runs(src: str, expected_stdout: str, tmp_path):
    rc, out, err = run_is(src, tmp_path)
    assert rc == 0, f"transpile/compile failed:\nSTDERR:\n{err}\nSTDOUT:\n{out}"
    user_lines = [
        line for line in out.splitlines()
        if not line.startswith("[InterScript]")
    ]
    actual = "\n".join(user_lines).strip()
    expected = expected_stdout.strip()
    assert actual == expected, (
        f"\n--- expected ---\n{expected}\n"
        f"--- actual ---\n{actual}\n"
        f"--- raw stdout ---\n{out}\n"
        f"--- stderr ---\n{err}"
    )


# ---------------------------------------------------------------------------
# 1. f-string: no placeholders (just a prefixed literal)
# ---------------------------------------------------------------------------
def test_fstring_no_placeholder(tmp_path):
    assert_runs("""
        s = f"hello"
        print(s)
    """, "hello", tmp_path)


# ---------------------------------------------------------------------------
# 2. f-string: single expression, string value
# ---------------------------------------------------------------------------
def test_fstring_single_str_var(tmp_path):
    assert_runs("""
        name = "world"
        s = f"Hello, {name}!"
        print(s)
    """, "Hello, world!", tmp_path)


# ---------------------------------------------------------------------------
# 3. f-string: single expression, integer value
# ---------------------------------------------------------------------------
def test_fstring_single_int(tmp_path):
    assert_runs("""
        x = 42
        s = f"x={x}"
        print(s)
    """, "x=42", tmp_path)


# ---------------------------------------------------------------------------
# 4. f-string: multiple expressions
# ---------------------------------------------------------------------------
def test_fstring_multiple(tmp_path):
    assert_runs("""
        a = 3
        b = 5
        s = f"{a} + {b} = {a + b}"
        print(s)
    """, "3 + 5 = 8", tmp_path)


# ---------------------------------------------------------------------------
# 5. f-string: adjacent expressions with no separator
# ---------------------------------------------------------------------------
def test_fstring_adjacent(tmp_path):
    assert_runs("""
        a = "foo"
        b = "bar"
        s = f"{a}{b}"
        print(s)
    """, "foobar", tmp_path)


# ---------------------------------------------------------------------------
# 6. f-string: leading and trailing literals
# ---------------------------------------------------------------------------
def test_fstring_wrapped(tmp_path):
    assert_runs("""
        n = 7
        s = f"before {n} after"
        print(s)
    """, "before 7 after", tmp_path)


# ---------------------------------------------------------------------------
# 7. f-string: escaped braces
# ---------------------------------------------------------------------------
def test_fstring_escaped_braces(tmp_path):
    assert_runs("""
        s = f"{{literal}}"
        print(s)
    """, "{literal}", tmp_path)


# ---------------------------------------------------------------------------
# 8. f-string: float value
# ---------------------------------------------------------------------------
def test_fstring_float(tmp_path):
    assert_runs("""
        pi = 3.14
        s = f"pi = {pi}"
        print(s)
    """, "pi = 3.14", tmp_path)


# ---------------------------------------------------------------------------
# 9. f-string: expression that is a method call
# ---------------------------------------------------------------------------
def test_fstring_method_call(tmp_path):
    assert_runs("""
        s = f"{'hello'.upper()}"
        print(s)
    """, "HELLO", tmp_path)


# ---------------------------------------------------------------------------
# 10. f-string: expression that is a function call
# ---------------------------------------------------------------------------
def test_fstring_function_call(tmp_path):
    assert_runs("""
        def twice(x: int) -> int:
            return x * 2
        s = f"doubled: {twice(21)}"
        print(s)
    """, "doubled: 42", tmp_path)

# ---------------------------------------------------------------------------
# 11. .format() positional {}
# ---------------------------------------------------------------------------
def test_format_positional(tmp_path):
    assert_runs("""
        s = "{} and {}".format("cats", "dogs")
        print(s)
    """, "cats and dogs", tmp_path)


# ---------------------------------------------------------------------------
# 12. .format() with int argument
# ---------------------------------------------------------------------------
def test_format_int(tmp_path):
    assert_runs("""
        s = "n = {}".format(99)
        print(s)
    """, "n = 99", tmp_path)


# ---------------------------------------------------------------------------
# 13. .format() with indexed placeholders
# ---------------------------------------------------------------------------
def test_format_indexed(tmp_path):
    assert_runs("""
        s = "{0} + {1} = {2}".format(2, 3, 5)
        print(s)
    """, "2 + 3 = 5", tmp_path)


# ---------------------------------------------------------------------------
# 14. .format() with repeated index
# ---------------------------------------------------------------------------
def test_format_repeated_index(tmp_path):
    assert_runs("""
        s = "{0}-{1}-{0}".format("a", "b")
        print(s)
    """, "a-b-a", tmp_path)


# ---------------------------------------------------------------------------
# 15. f-string concatenated with another string
# ---------------------------------------------------------------------------
def test_fstring_plus_string(tmp_path):
    assert_runs("""
        n = 5
        s = f"n={n}" + "!"
        print(s)
    """, "n=5!", tmp_path)
