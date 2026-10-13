"""tests/test_batch5b.py

Batch 5b: *args (variadic positional args).

Design:
    def f(*args):            -> std::vector<int> args
    def f(*args: str):       -> std::vector<std::string> args
    f({1, 2, 3})             -> f({1, 2, 3});

Python syntax `f(1, 2, 3)` is NOT supported. Brace-init `f({1, 2, 3})`
is the closest C++ equivalent and is what InterScript requires.

Inside the body, `args` behaves exactly like a Python list:
iteration, indexing, len(), membership.

OUT OF SCOPE:
    - kwargs (Batch 5c)
    - mixing *args with regular params (def f(a, b, *rest))
    - *args on class methods
    - unpacking on call: f(*xs)
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
# Basic *args
# ===========================================================================

def test_args_int_sum(tmp_path):
    assert_runs("""
        def sum_all(*nums):
            total = 0
            for n in nums:
                total = total + n
            return total

        print(sum_all({1, 2, 3}))
    """, "6", tmp_path)


def test_args_empty(tmp_path):
    assert_runs("""
        def count_all(*nums):
            return len(nums)

        print(count_all({}))
    """, "0", tmp_path)


def test_args_len(tmp_path):
    assert_runs("""
        def count_all(*nums):
            return len(nums)

        print(count_all({1, 2, 3, 4, 5}))
    """, "5", tmp_path)


# ===========================================================================
# *args with annotation
# ===========================================================================

def test_args_str(tmp_path):
    assert_runs("""
        def join_all(*words: str):
            result = ""
            for w in words:
                result = result + w
            return result

        print(join_all({"a", "b", "c"}))
    """, "abc", tmp_path)


def test_args_str_annotation_empty(tmp_path):
    assert_runs("""
        def join_all(*words: str):
            return len(words)

        print(join_all({}))
    """, "0", tmp_path)


# ===========================================================================
# *args body behaves like a list
# ===========================================================================

def test_args_indexing(tmp_path):
    assert_runs("""
        def first_of(*nums):
            return nums[0]

        print(first_of({10, 20, 30}))
    """, "10", tmp_path)


def test_args_membership(tmp_path):
    assert_runs("""
        def contains(*nums):
            if 5 in nums:
                return 1
            return 0

        print(contains({1, 2, 5}))
        print(contains({1, 2, 3}))
    """, "1\n0", tmp_path)


# ===========================================================================
# *args called multiple times
# ===========================================================================

def test_args_called_various_sizes(tmp_path):
    assert_runs("""
        def sum_all(*nums):
            total = 0
            for n in nums:
                total = total + n
            return total

        print(sum_all({1}))
        print(sum_all({1, 2}))
        print(sum_all({1, 2, 3}))
    """, "1\n3\n6", tmp_path)


# ===========================================================================
# *args combined with default args (Batch 5a interaction)
# ===========================================================================

def test_args_with_regular_param(tmp_path):
    assert_runs("""
        def add_all(first, *rest):
            total = first
            for n in rest:
                total = total + n
            return total

        print(add_all(10, {1, 2, 3}))
    """, "16", tmp_path)
