"""tests/test_batch5c.py

Batch 5c: **kwargs (variadic keyword args).

Design:
    def f(**kw):            -> std::map<std::string, std::string> kw
    def f(**kw: int):       -> std::map<std::string, int> kw
    f({"a": "x", "b": "y"}) -> f({{"a","x"},{"b","y"}});

Python syntax `f(a=1, b=2)` is NOT supported. Dict-literal call
sites are required.

Inside the body, `kw` behaves exactly like a Python dict:
iteration over .items(), .keys(), .values(), .get(), .count via `k in kw`.

OUT OF SCOPE:
    - *args (Batch 5b — separate)
    - mixing **kwargs with regular params
    - **kwargs on class methods
    - unpacking on call: f(**d)
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
# Basic **kwargs
# ===========================================================================

def test_kwargs_iterate(tmp_path):
    assert_runs("""
        def show(**info):
            for k, v in info.items():
                print(k)
                print(v)

        show({"name": "Alice", "age": "30"})
    """, "age\n30\nname\nAlice", tmp_path)


def test_kwargs_len(tmp_path):
    assert_runs("""
        def count(**info):
            return len(info)

        print(count({"a": "1", "b": "2", "c": "3"}))
    """, "3", tmp_path)


def test_kwargs_empty(tmp_path):
    assert_runs("""
        def count(**info):
            return len(info)

        print(count({}))
    """, "0", tmp_path)


# ===========================================================================
# **kwargs with annotation (value type = int)
# ===========================================================================

def test_kwargs_int_values(tmp_path):
    assert_runs("""
        def total(**counts: int):
            s = 0
            for v in counts.values():
                s = s + v
            return s

        print(total({"a": 1, "b": 2, "c": 3}))
    """, "6", tmp_path)


# ===========================================================================
# **kwargs body behaves like a dict
# ===========================================================================

def test_kwargs_get(tmp_path):
    assert_runs("""
        def fetch(**data):
            return data.get("key")

        print(fetch({"key": "value", "other": "x"}))
    """, "value", tmp_path)


def test_kwargs_membership(tmp_path):
    assert_runs("""
        def has_name(**info):
            if "name" in info:
                return 1
            return 0

        print(has_name({"name": "x"}))
        print(has_name({"other": "y"}))
    """, "1\n0", tmp_path)


# ===========================================================================
# **kwargs with values via .items()
# ===========================================================================

def test_kwargs_items_sorted(tmp_path):
    # std::map iteration is sorted by key; the emitter relies on this.
    assert_runs("""
        def dump(**info):
            for k, v in info.items():
                print(k + "=" + v)

        dump({"c": "3", "a": "1", "b": "2"})
    """, "a=1\nb=2\nc=3", tmp_path)


# ===========================================================================
# Multiple calls, various content
# ===========================================================================

def test_kwargs_called_repeatedly(tmp_path):
    assert_runs("""
        def count(**info):
            return len(info)

        print(count({"a": "1"}))
        print(count({"a": "1", "b": "2"}))
        print(count({"a": "1", "b": "2", "c": "3"}))
    """, "1\n2\n3", tmp_path)
