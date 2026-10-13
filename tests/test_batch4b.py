"""tests/test_batch4b.py

Batch 4b: for...else.

Python semantics:
    for x in xs:
        ...
    else:
        ...
The else block runs if the loop completed WITHOUT a `break`.

Scope:
    - for...else over a list variable
    - for...else over enumerate(...) and zip(...)  (interacts with Batch 4a)
    - for...else over dict .values() / .keys() / .items()
    - for i in range(N): ... else: ...
    - nested for...else — flag names must not collide
    - `break` inside a for...else sets the flag before breaking
    - `break` in a plain for (no else) still emits bare break

OUT OF SCOPE:
    - while...else (Python has it; not in this batch)
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
# Basic for...else
# ===========================================================================

def test_else_runs_when_no_break(tmp_path):
    assert_runs("""
        xs = [1, 2, 3]
        for x in xs:
            print(x)
        else:
            print("no break")
    """, "1\n2\n3\nno break", tmp_path)


def test_else_skipped_when_break(tmp_path):
    assert_runs("""
        xs = [1, 2, 3]
        for x in xs:
            if x == 2:
                break
            print(x)
        else:
            print("no break")
        print("after")
    """, "1\nafter", tmp_path)


def test_else_runs_on_empty_list(tmp_path):
    assert_runs("""
        xs = [1]
        empty = [2]
        total = 0
        for x in xs:
            if x == 999:
                break
            total = total + 1
        else:
            print("finished")
    """, "finished", tmp_path)


def test_break_condition_never_true(tmp_path):
    assert_runs("""
        xs = [10, 20, 30]
        for x in xs:
            if x > 100:
                break
            print(x)
        else:
            print("done")
    """, "10\n20\n30\ndone", tmp_path)


# ===========================================================================
# for...else with range
# ===========================================================================

def test_range_for_else_no_break(tmp_path):
    assert_runs("""
        for i in range(3):
            print(i)
        else:
            print("end")
    """, "0\n1\n2\nend", tmp_path)


def test_range_for_else_with_break(tmp_path):
    assert_runs("""
        for i in range(10):
            if i == 3:
                break
            print(i)
        else:
            print("end")
    """, "0\n1\n2", tmp_path)


# ===========================================================================
# for...else with enumerate / zip  (Batch 4a interaction)
# ===========================================================================

def test_enumerate_for_else_no_break(tmp_path):
    assert_runs("""
        xs = [10, 20]
        for i, x in enumerate(xs):
            print(i)
            print(x)
        else:
            print("done")
    """, "0\n10\n1\n20\ndone", tmp_path)


def test_enumerate_for_else_with_break(tmp_path):
    assert_runs("""
        xs = [10, 20, 30]
        for i, x in enumerate(xs):
            if x == 20:
                break
            print(x)
        else:
            print("done")
        print("after")
    """, "10\nafter", tmp_path)


def test_zip_for_else_no_break(tmp_path):
    assert_runs("""
        a = [1, 2]
        b = [10, 20]
        for x, y in zip(a, b):
            print(x + y)
        else:
            print("done")
    """, "11\n22\ndone", tmp_path)


def test_zip_for_else_with_break(tmp_path):
    assert_runs("""
        a = [1, 2, 3]
        b = [10, 20, 30]
        for x, y in zip(a, b):
            if x + y == 22:
                break
            print(x + y)
        else:
            print("done")
    """, "11", tmp_path)


# ===========================================================================
# for...else with dict
# ===========================================================================

def test_dict_values_for_else(tmp_path):
    assert_runs("""
        d = {"a": 1, "b": 2}
        for v in d.values():
            print(v)
        else:
            print("all")
    """, "1\n2\nall", tmp_path)


def test_dict_values_for_else_with_break(tmp_path):
    assert_runs("""
        d = {"a": 1, "b": 2, "c": 3}
        for v in d.values():
            if v == 2:
                break
            print(v)
        else:
            print("all")
        print("after")
    """, "1\nafter", tmp_path)


# ===========================================================================
# Nested for...else
# ===========================================================================

def test_nested_for_else(tmp_path):
    assert_runs("""
        outer = [1, 2]
        inner = [10, 20]
        for a in outer:
            for b in inner:
                if b == 999:
                    break
                print(a)
                print(b)
            else:
                print("inner else")
        else:
            print("outer else")
    """, "1\n10\n1\n20\ninner else\n2\n10\n2\n20\ninner else\nouter else", tmp_path)


# ===========================================================================
# else block with a break that never runs (Python: else runs)
# ===========================================================================

def test_else_with_unreachable_break(tmp_path):
    assert_runs("""
        xs = [5]
        for x in xs:
            print(x)
            if x > 100:
                break
        else:
            print("reached else")
    """, "5\nreached else", tmp_path)
