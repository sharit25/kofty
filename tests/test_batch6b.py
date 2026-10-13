"""tests/test_batch6b.py

Batch 6b: raise statement and try/except (catch-all only).

Design:
    raise ValueError("msg")   -> throw std::runtime_error("msg");
    raise SomeError("msg")    -> throw std::runtime_error("msg");
    raise SomeError           -> throw std::runtime_error("");

    try:
        risky()
    except Exception:
        print("caught")
    -> try { risky(); } catch (...) { print("caught"); }

Bare `except:` and `except Exception:` both map to `catch (...)`.

OUT OF SCOPE (deferred):
    - typed except:      except ValueError:
    - multiple excepts
    - else: / finally:
    - bare raise (re-raise)
    - custom exception classes
    - exception objects (e.value, e.args)
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
# raise + try/except with raise
# ===========================================================================

def test_try_no_exception(tmp_path):
    assert_runs("""
        try:
            print("in try")
        except Exception:
            print("caught")
        print("after")
    """, "in try\nafter", tmp_path)


def test_try_with_raise(tmp_path):
    assert_runs("""
        try:
            raise Exception("boom")
        except Exception:
            print("caught")
        print("after")
    """, "caught\nafter", tmp_path)


def test_try_bare_except(tmp_path):
    assert_runs("""
        try:
            raise Exception("x")
        except:
            print("caught")
        print("after")
    """, "caught\nafter", tmp_path)


def test_try_raise_custom_name(tmp_path):
    assert_runs("""
        try:
            raise ValueError("bad value")
        except Exception:
            print("value error caught")
        print("after")
    """, "value error caught\nafter", tmp_path)


def test_try_raise_no_message(tmp_path):
    assert_runs("""
        try:
            raise RuntimeError
        except Exception:
            print("caught")
    """, "caught", tmp_path)


# ===========================================================================
# Nested try
# ===========================================================================

def test_try_nested(tmp_path):
    assert_runs("""
        try:
            print("outer try")
            try:
                raise Exception("inner")
            except Exception:
                print("inner caught")
        except Exception:
            print("outer caught")
        print("done")
    """, "outer try\ninner caught\ndone", tmp_path)


# ===========================================================================
# try with multiple statements
# ===========================================================================

def test_try_multi_stmt(tmp_path):
    assert_runs("""
        try:
            print("a")
            print("b")
            print("c")
        except Exception:
            print("caught")
    """, "a\nb\nc", tmp_path)


# ===========================================================================
# try with function call
# ===========================================================================

def test_try_with_function(tmp_path):
    assert_runs("""
        def risky(x):
            if x < 0:
                raise Exception("negative")
            print("ok")

        try:
            risky(-1)
        except Exception:
            print("caught")
        try:
            risky(5)
        except Exception:
            print("caught")
    """, "caught\nok", tmp_path)


# ===========================================================================
# raise at top level (not caught) — should still compile
# ===========================================================================

def test_raise_in_function_not_caught(tmp_path):
    assert_runs("""
        def will_fail():
            raise Exception("nope")

        print("before")
        try:
            will_fail()
        except Exception:
            print("caught")
        print("after")
    """, "before\ncaught\nafter", tmp_path)


# ===========================================================================
# try in a loop
# ===========================================================================

def test_try_in_loop(tmp_path):
    assert_runs("""
        for i in range(3):
            try:
                if i == 1:
                    raise Exception("skip")
                print(i)
            except Exception:
                print("caught")
    """, "0\ncaught\n2", tmp_path)


# ===========================================================================
# Empty try body (edge case)
# ===========================================================================

def test_try_pass(tmp_path):
    assert_runs("""
        try:
            pass
        except Exception:
            print("caught")
        print("after")
    """, "after", tmp_path)


# ===========================================================================
# try/except where except body is empty
# ===========================================================================

def test_except_pass(tmp_path):
    assert_runs("""
        try:
            raise Exception("x")
        except Exception:
            pass
        print("after")
    """, "after", tmp_path)
