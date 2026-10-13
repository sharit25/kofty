"""tests/test_batch4a.py

Batch 4a: enumerate() and zip() in for-loops.

Scope:
    for i, x in enumerate(xs):        -> index loop, unpack value
    for i, x in enumerate(xs, start): -> index starts at `start`
    for x, y in zip(xs, ys):          -> parallel iteration

OUT OF SCOPE (do not test here):
    - enumerate/zip outside of a for-loop
    - nested enumerate/zip
    - zip of 3+ sequences
    - enumerate of a dict/set (only lists)
    - modifying the container inside the loop
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
# enumerate
# ===========================================================================

def test_enumerate_basic(tmp_path):
    assert_runs("""
        xs = [10, 20, 30]
        for i, x in enumerate(xs):
            print(i)
            print(x)
    """, "0\n10\n1\n20\n2\n30", tmp_path)


def test_enumerate_string_list(tmp_path):
    assert_runs("""
        names = ["alice", "bob"]
        for i, n in enumerate(names):
            print(n)
    """, "alice\nbob", tmp_path)


def test_enumerate_with_start(tmp_path):
    assert_runs("""
        xs = [100, 200]
        for i, x in enumerate(xs, 1):
            print(i)
            print(x)
    """, "1\n100\n2\n200", tmp_path)


def test_enumerate_sum_indices(tmp_path):
    assert_runs("""
        xs = [5, 10, 15]
        total = 0
        for i, x in enumerate(xs):
            total = total + i * x
        print(total)
    """, "40", tmp_path)


def test_enumerate_single_element(tmp_path):
    assert_runs("""
        xs = [42]
        for i, x in enumerate(xs):
            print(i)
            print(x)
    """, "0\n42", tmp_path)


# ===========================================================================
# zip
# ===========================================================================

def test_zip_two_int_lists(tmp_path):
    assert_runs("""
        a = [1, 2, 3]
        b = [10, 20, 30]
        for x, y in zip(a, b):
            print(x + y)
    """, "11\n22\n33", tmp_path)


def test_zip_mismatched_lengths(tmp_path):
    assert_runs("""
        a = [1, 2, 3]
        b = [10, 20]
        for x, y in zip(a, b):
            print(x + y)
    """, "11\n22", tmp_path)


def test_zip_string_lists(tmp_path):
    assert_runs("""
        first = ["a", "b"]
        last = ["x", "y"]
        for f, l in zip(first, last):
            print(f + l)
    """, "ax\nby", tmp_path)


def test_zip_single_iteration(tmp_path):
    assert_runs("""
        a = [1]
        b = [100]
        for x, y in zip(a, b):
            print(x + y)
    """, "101", tmp_path)


def test_zip_shorter_first(tmp_path):
    assert_runs("""
        a = [1]
        b = [10, 20]
        for x, y in zip(a, b):
            print(x + y)
        print("done")
    """, "11\ndone", tmp_path)
