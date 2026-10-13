"""tests/test_batch7c.py

Batch 7c: import time.

Design:
    import time
    time.time()      -> time_now()  -- double, seconds since epoch
    time.sleep(s)    -> time_sleep(s)  -- pauses s seconds

Both are emitted as helper calls from the preamble.

OUT OF SCOPE (deferred):
    - time.ctime, time.localtime, time.gmtime
    - time.strftime, time.strptime
    - time.perf_counter, time.monotonic
    - import time as t
    - from time import ...
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


def assert_compiles_and_runs(src: str, tmp_path) -> str:
    """Run and return user stdout — for nondeterministic or timing tests."""
    rc, out, err = run_is(src, tmp_path)
    assert rc == 0, f"transpile/compile failed:\nSTDERR:\n{err}\nSTDOUT:\n{out}"
    user_lines = [
        line for line in out.splitlines()
        if not line.startswith("[InterScript]")
    ]
    return "\n".join(user_lines).strip()


def assert_runs(src: str, expected_stdout: str, tmp_path):
    actual = assert_compiles_and_runs(src, tmp_path)
    expected = expected_stdout.strip()
    assert actual == expected, (
        f"\n--- expected ---\n{expected}\n--- actual ---\n{actual}"
    )


# ===========================================================================
# time.time() -- compiles, runs, gives a positive number
# ===========================================================================

def test_time_compiles(tmp_path):
    out = assert_compiles_and_runs("""
        import time
        t = time.time()
        print("ok")
    """, tmp_path)
    assert out == "ok"


def test_time_positive(tmp_path):
    # time.time() should be > 0 (we're past 1970).
    out = assert_compiles_and_runs("""
        import time
        t = time.time()
        if t > 0.0:
            print("positive")
        else:
            print("bad")
    """, tmp_path)
    assert out == "positive"


def test_time_monotonic_increasing(tmp_path):
    # Two calls in sequence should give non-decreasing values.
    out = assert_compiles_and_runs("""
        import time
        t1 = time.time()
        t2 = time.time()
        if t2 >= t1:
            print("ok")
        else:
            print("decreased")
    """, tmp_path)
    assert out == "ok"


def test_time_arithmetic(tmp_path):
    # time.time() result should be usable in arithmetic.
    out = assert_compiles_and_runs("""
        import time
        t1 = time.time()
        t2 = time.time()
        elapsed = t2 - t1
        if elapsed >= 0.0:
            print("ok")
        else:
            print("bad")
    """, tmp_path)
    assert out == "ok"


# ===========================================================================
# time.sleep(s)
# ===========================================================================

def test_sleep_compiles(tmp_path):
    out = assert_compiles_and_runs("""
        import time
        time.sleep(0.01)
        print("done")
    """, tmp_path)
    assert out == "done"


def test_sleep_zero(tmp_path):
    out = assert_compiles_and_runs("""
        import time
        time.sleep(0.0)
        print("instant")
    """, tmp_path)
    assert out == "instant"


def test_sleep_causes_delay(tmp_path):
    # time.sleep(0.05) should give a nonzero elapsed time when measured
    # via time.time() around it. We check elapsed >= 0.04 to allow
    # scheduling slop.
    out = assert_compiles_and_runs("""
        import time
        t1 = time.time()
        time.sleep(0.05)
        t2 = time.time()
        elapsed = t2 - t1
        if elapsed >= 0.04:
            print("delayed")
        else:
            print("too fast")
    """, tmp_path)
    assert out == "delayed"


# ===========================================================================
# Without import
# ===========================================================================

def test_time_without_import_raises(tmp_path):
    rc, out, err = run_is("""
        t = time.time()
        print(t)
    """, tmp_path)
    assert rc != 0, f"expected transpile error but got rc=0:\n{out}"
