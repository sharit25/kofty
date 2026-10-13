"""tests/test_batch6a.py

Batch 6a: match/case (literal patterns only).

Design:
    match x:
        case 1: ...       -> if (x == 1) { ... }
        case 2: ...       -> else if (x == 2) { ... }
        case _: ...       -> else { ... }

Supported pattern kinds:
    - integer literals:  case 1:
    - string literals:   case "hello":
    - bool literals:     case True: / case False:
    - wildcard:          case _:

OUT OF SCOPE (deferred):
    - OR patterns:       case 1 | 2:
    - guards:            case n if n > 0:
    - capture patterns:  case x:      (binds the value)
    - structural:        case [a, b]: case {"k": v}:
    - type patterns:     case int(): case str():
    - nested patterns
    - multiple statements in a match body (indented block) - SUPPORTED actually
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


# ===========================================================================
# Basic integer match
# ===========================================================================

def test_match_int_one_case(tmp_path):
    assert_runs("""
        x = 1
        match x:
            case 1:
                print("one")
    """, "one", tmp_path)


def test_match_int_two_cases(tmp_path):
    assert_runs("""
        x = 2
        match x:
            case 1:
                print("one")
            case 2:
                print("two")
    """, "two", tmp_path)


def test_match_int_wildcard(tmp_path):
    assert_runs("""
        x = 99
        match x:
            case 1:
                print("one")
            case 2:
                print("two")
            case _:
                print("other")
    """, "other", tmp_path)


def test_match_int_three_cases(tmp_path):
    assert_runs("""
        x = 3
        match x:
            case 1:
                print("a")
            case 2:
                print("b")
            case 3:
                print("c")
    """, "c", tmp_path)


# ===========================================================================
# String patterns
# ===========================================================================

def test_match_string(tmp_path):
    assert_runs("""
        cmd = "start"
        match cmd:
            case "start":
                print("starting")
            case "stop":
                print("stopping")
            case _:
                print("unknown")
    """, "starting", tmp_path)


def test_match_string_fallthrough(tmp_path):
    assert_runs("""
        cmd = "pause"
        match cmd:
            case "start":
                print("starting")
            case "stop":
                print("stopping")
            case _:
                print("unknown")
    """, "unknown", tmp_path)


# ===========================================================================
# Bool patterns
# ===========================================================================

def test_match_bool_true(tmp_path):
    assert_runs("""
        flag = True
        match flag:
            case True:
                print("yes")
            case False:
                print("no")
    """, "yes", tmp_path)


def test_match_bool_false(tmp_path):
    assert_runs("""
        flag = False
        match flag:
            case True:
                print("yes")
            case False:
                print("no")
    """, "no", tmp_path)


# ===========================================================================
# Multiple statements per case body
# ===========================================================================

def test_match_multi_stmt_body(tmp_path):
    assert_runs("""
        x = 2
        match x:
            case 1:
                print("first")
                print("line 2")
            case 2:
                print("second")
                print("line 2")
    """, "second\nline 2", tmp_path)


# ===========================================================================
# No wildcard, no match
# ===========================================================================

def test_match_no_fallthrough(tmp_path):
    assert_runs("""
        x = 99
        match x:
            case 1:
                print("one")
            case 2:
                print("two")
        print("after")
    """, "after", tmp_path)


# ===========================================================================
# Match on expressions
# ===========================================================================

def test_match_on_function_result(tmp_path):
    assert_runs("""
        def get_code():
            return 200

        match get_code():
            case 200:
                print("OK")
            case 404:
                print("Not Found")
            case _:
                print("Other")
    """, "OK", tmp_path)


# ===========================================================================
# Multiple match statements
# ===========================================================================

def test_match_twice(tmp_path):
    assert_runs("""
        a = 1
        b = 2
        match a:
            case 1:
                print("a is one")
        match b:
            case 2:
                print("b is two")
    """, "a is one\nb is two", tmp_path)
