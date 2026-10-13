"""tests/test_string_methods.py

Batch 2a: String methods.

Scope:
    .upper()           .lower()
    .strip()           .lstrip()          .rstrip()
    .startswith(x)     .endswith(x)
    .replace(a, b)
    .split(sep)        .join(xs)
    .find(x)           .count(x)

OUT OF SCOPE (do not test here):
    - f-strings (Batch 2b)
    - .format()      (Batch 2b)
    - .split() with no arg (whitespace split)
    - .strip(chars) / .lstrip(chars) / .rstrip(chars) with arg
    - .title() .capitalize() .swapcase() .zfill() .center() .ljust() .rjust()
    - .isalpha() .isdigit() .isalnum() .isspace() etc.
    - regex, .partition, .rsplit
"""

import shutil
import subprocess
import sys
import textwrap

import pytest


# ---------------------------------------------------------------------------
# Helper: compile + run an .is snippet, return (returncode, stdout, stderr).
# Uses the real CLI so we exercise the same path users do.
# ---------------------------------------------------------------------------
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
    # Filter out the CLI's status lines (they start with "[InterScript] ").
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
# 1. .upper()
# ---------------------------------------------------------------------------
def test_upper(tmp_path):
    assert_runs("""
        s = "hello"
        print(s.upper())
    """, "HELLO", tmp_path)


# ---------------------------------------------------------------------------
# 2. .lower()
# ---------------------------------------------------------------------------
def test_lower(tmp_path):
    assert_runs("""
        s = "HELLO World"
        print(s.lower())
    """, "hello world", tmp_path)


# ---------------------------------------------------------------------------
# 3. .strip()
# ---------------------------------------------------------------------------
def test_strip(tmp_path):
    assert_runs("""
        s = "  spaced  "
        print(s.strip())
    """, "spaced", tmp_path)


# ---------------------------------------------------------------------------
# 4. .lstrip()
# ---------------------------------------------------------------------------
def test_lstrip(tmp_path):
    assert_runs("""
        s = "  spaced  "
        print(s.lstrip())
    """, "spaced  ", tmp_path)


# ---------------------------------------------------------------------------
# 5. .rstrip()
# ---------------------------------------------------------------------------
def test_rstrip(tmp_path):
    assert_runs("""
        s = "  spaced  "
        print(s.rstrip())
    """, "  spaced", tmp_path)


# ---------------------------------------------------------------------------
# 6. .startswith()
# ---------------------------------------------------------------------------
def test_startswith_true(tmp_path):
    assert_runs("""
        s = "hello world"
        print(s.startswith("hello"))
    """, "1", tmp_path)


def test_startswith_false(tmp_path):
    assert_runs("""
        s = "hello world"
        print(s.startswith("world"))
    """, "0", tmp_path)


# ---------------------------------------------------------------------------
# 7. .endswith()
# ---------------------------------------------------------------------------
def test_endswith_true(tmp_path):
    assert_runs("""
        s = "hello world"
        print(s.endswith("world"))
    """, "1", tmp_path)


def test_endswith_false(tmp_path):
    assert_runs("""
        s = "hello world"
        print(s.endswith("hello"))
    """, "0", tmp_path)


# ---------------------------------------------------------------------------
# 8. .replace(a, b)
# ---------------------------------------------------------------------------
def test_replace(tmp_path):
    assert_runs("""
        s = "a-b-c"
        print(s.replace("-", "+"))
    """, "a+b+c", tmp_path)


def test_replace_no_match(tmp_path):
    assert_runs("""
        s = "hello"
        print(s.replace("x", "y"))
    """, "hello", tmp_path)


# ---------------------------------------------------------------------------
# 9. .split(sep) -- returns list of strings
# ---------------------------------------------------------------------------
def test_split_comma(tmp_path):
    assert_runs("""
        s = "a,b,c"
        parts = s.split(",")
        print(parts[0])
        print(parts[1])
        print(parts[2])
    """, "a\nb\nc", tmp_path)


def test_split_len(tmp_path):
    assert_runs("""
        s = "one two three"
        parts = s.split(" ")
        print(len(parts))
    """, "3", tmp_path)


# ---------------------------------------------------------------------------
# 10. .join(xs) -- sep.join(list of strings)
# ---------------------------------------------------------------------------
def test_join(tmp_path):
    assert_runs("""
        xs = ["a", "b", "c"]
        s = ",".join(xs)
        print(s)
    """, "a,b,c", tmp_path)


# ---------------------------------------------------------------------------
# 11. .find(x) -- returns index, or -1
# ---------------------------------------------------------------------------
def test_find_found(tmp_path):
    assert_runs("""
        s = "hello world"
        print(s.find("world"))
    """, "6", tmp_path)


def test_find_not_found(tmp_path):
    assert_runs("""
        s = "hello world"
        print(s.find("xyz"))
    """, "-1", tmp_path)


# ---------------------------------------------------------------------------
# 12. .count(x)
# ---------------------------------------------------------------------------
def test_count(tmp_path):
    assert_runs("""
        s = "banana"
        print(s.count("a"))
    """, "3", tmp_path)


def test_count_none(tmp_path):
    assert_runs("""
        s = "banana"
        print(s.count("z"))
    """, "0", tmp_path)


# ---------------------------------------------------------------------------
# 13. Chaining: methods on results of other methods
# ---------------------------------------------------------------------------
def test_chain_upper_strip(tmp_path):
    assert_runs("""
        s = "  hello  "
        print(s.strip().upper())
    """, "HELLO", tmp_path)


# ---------------------------------------------------------------------------
# 14. In an expression (not just assigned)
# ---------------------------------------------------------------------------
def test_method_in_if(tmp_path):
    assert_runs("""
        s = "hello.txt"
        if s.endswith(".txt"):
            print("text file")
        else:
            print("other")
    """, "text file", tmp_path)


# ---------------------------------------------------------------------------
# 15. Methods on a variable assigned from input/other expression
# ---------------------------------------------------------------------------
def test_method_on_concat(tmp_path):
    assert_runs("""
        a = "hello"
        b = " world"
        s = a + b
        print(s.upper())
    """, "HELLO WORLD", tmp_path)
