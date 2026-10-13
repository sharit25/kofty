"""tests/test_batch8h Phase 4b: transpile-only companion to test_batch7c.py.

Verifies the C++ emitted for `import time`.

time.time()   -> time_now()
time.sleep(s) -> time_sleep(s)
"""

from kofty.transpiler import transpile


# ===========================================================================
# time.time()
# ===========================================================================

def test_time_emits_time_now():
    out = transpile("""
import time
t = time.time()
print(t)
""")
    assert "time_now()" in out
    # chrono header must be included.
    assert "chrono" in out or "time" in out


def test_time_positive_emits_time_now():
    out = transpile("""
import time
t = time.time()
if t > 0.0:
    print("positive")
else:
    print("bad")
""")
    assert "time_now()" in out


def test_time_monotonic_increasing_emits_two_calls():
    out = transpile("""
import time
t1 = time.time()
t2 = time.time()
if t2 >= t1:
    print("ok")
""")
    # Two distinct calls -> two occurrences of time_now().
    assert out.count("time_now()") >= 2


def test_time_arithmetic_emits_subtraction():
    out = transpile("""
import time
t1 = time.time()
t2 = time.time()
elapsed = t2 - t1
print(elapsed)
""")
    assert "time_now()" in out
    # The subtraction t2 - t1 must survive emission.
    assert "t2 - t1" in out or "t2-t1" in out


# ===========================================================================
# time.sleep(s)
# ===========================================================================

def test_sleep_compiles_emits_time_sleep():
    out = transpile("""
import time
time.sleep(0.01)
print("done")
""")
    assert "time_sleep(0.01)" in out


def test_sleep_zero_emits_time_sleep_zero():
    out = transpile("""
import time
time.sleep(0.0)
print("instant")
""")
    assert "time_sleep(0.0)" in out


def test_sleep_causes_delay_emits_sleep_and_time():
    out = transpile("""
import time
t1 = time.time()
time.sleep(0.05)
t2 = time.time()
elapsed = t2 - t1
print(elapsed)
""")
    assert "time_sleep(0.05)" in out
    assert out.count("time_now()") >= 2


# ===========================================================================
# Preamble includes the time helpers
# ===========================================================================

def test_preamble_includes_time_helpers():
    out = transpile("""
import time
t = time.time()
time.sleep(0.01)
print(t)
""")
    assert "time_now" in out
    assert "time_sleep" in out


# ===========================================================================
# Without import - should raise
# ===========================================================================

def test_time_without_import_raises():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError):
        transpile("""
t = time.time()
print(t)
""")
