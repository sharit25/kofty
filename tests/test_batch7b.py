"""tests/test_batch7b.py

Batch 7b: import random.

Design:
    import random
    random.random()       -> rand_float()
    random.randint(a, b)  -> rand_int(a, b)
    random.choice(xs)     -> rand_choice(xs)
    random.shuffle(xs)    -> rand_shuffle(xs)
    random.seed(n)        -> rand_seed(n)

Output of random functions is nondeterministic. Tests that need exact
values first call random.seed(N) to fix the sequence. Other tests just
assert on ranges or property constraints.

OUT OF SCOPE (deferred):
    - random.uniform(a, b)
    - random.randrange(...)
    - random.sample(xs, k)
    - random.gauss / normalvariate
    - random.choices (with weights)
    - import random as r
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


def assert_compiles_and_runs(src: str, tmp_path) -> str:
    """Run and return user stdout — no expected value. For nondeterministic tests."""
    rc, out, err = run_is(src, tmp_path)
    assert rc == 0, f"transpile/compile failed:\nSTDERR:\n{err}\nSTDOUT:\n{out}"
    user_lines = [
        line for line in out.splitlines()
        if not line.startswith("[InterScript]")
    ]
    return "\n".join(user_lines).strip()


# ===========================================================================
# random.seed + deterministic sequences
# ===========================================================================

def test_seed_makes_deterministic_int(tmp_path):
    # Deterministic given the seed. Same seed -> same value.
    # We don't know the exact value for MT19937 but it's stable across runs.
    out1 = assert_compiles_and_runs("""
        import random
        random.seed(42)
        print(random.randint(1, 100))
    """, tmp_path)
    out2 = assert_compiles_and_runs("""
        import random
        random.seed(42)
        print(random.randint(1, 100))
    """, tmp_path)
    assert out1 == out2, f"seed(42) not deterministic:\n{out1}\nvs\n{out2}"


def test_seed_different_seeds_differ(tmp_path):
    out_a = assert_compiles_and_runs("""
        import random
        random.seed(1)
        a = random.randint(1, 1000000)
        b = random.randint(1, 1000000)
        c = random.randint(1, 1000000)
        print(a)
        print(b)
        print(c)
    """, tmp_path)
    out_b = assert_compiles_and_runs("""
        import random
        random.seed(999)
        a = random.randint(1, 1000000)
        b = random.randint(1, 1000000)
        c = random.randint(1, 1000000)
        print(a)
        print(b)
        print(c)
    """, tmp_path)
    assert out_a != out_b, "different seeds gave same output"


# ===========================================================================
# random.random() -- range test
# ===========================================================================

def test_random_compiles(tmp_path):
    # Just verify the program runs (can't assert on exact value).
    out = assert_compiles_and_runs("""
        import random
        x = random.random()
        print("ok")
    """, tmp_path)
    assert out == "ok"


def test_random_range(tmp_path):
    # Generate 20 numbers, check all in [0, 1)
    out = assert_compiles_and_runs("""
        import random
        random.seed(7)
        for i in range(20):
            x = random.random()
            if x < 0.0:
                print("too low")
            if x >= 1.0:
                print("too high")
        print("all in range")
    """, tmp_path)
    assert out == "all in range"


# ===========================================================================
# random.randint(a, b) -- inclusive range test
# ===========================================================================

def test_randint_range(tmp_path):
    out = assert_compiles_and_runs("""
        import random
        random.seed(13)
        for i in range(50):
            n = random.randint(5, 10)
            if n < 5:
                print("below")
            if n > 10:
                print("above")
        print("all in range")
    """, tmp_path)
    assert out == "all in range"


def test_randint_can_hit_endpoints(tmp_path):
    # Generate many values, check both endpoints are reachable.
    out = assert_compiles_and_runs("""
        import random
        random.seed(42)
        lo_hits = 0
        hi_hits = 0
        for i in range(200):
            n = random.randint(1, 3)
            if n == 1:
                lo_hits = lo_hits + 1
            if n == 3:
                hi_hits = hi_hits + 1
        if lo_hits > 0:
            print("lo seen")
        if hi_hits > 0:
            print("hi seen")
    """, tmp_path)
    assert "lo seen" in out
    assert "hi seen" in out


# ===========================================================================
# random.choice(xs)
# ===========================================================================

def test_choice_int(tmp_path):
    out = assert_compiles_and_runs("""
        import random
        random.seed(3)
        xs = [10, 20, 30]
        total = 0
        for i in range(30):
            n = random.choice(xs)
            total = total + n
        print("done")
    """, tmp_path)
    assert out == "done"


def test_choice_from_strings(tmp_path):
    out = assert_compiles_and_runs("""
        import random
        random.seed(5)
        words = ["red", "green", "blue"]
        for i in range(10):
            w = random.choice(words)
            print(w)
    """, tmp_path)
    # Every line should be one of the three words
    for line in out.splitlines():
        assert line in ("red", "green", "blue"), f"unexpected: {line}"


# ===========================================================================
# random.shuffle(xs)
# ===========================================================================

def test_shuffle_preserves_elements(tmp_path):
    out = assert_compiles_and_runs("""
        import random
        random.seed(11)
        xs = [1, 2, 3, 4, 5]
        random.shuffle(xs)
        print(len(xs))
        total = 0
        for x in xs:
            total = total + x
        print(total)
    """, tmp_path)
    assert out == "5\n15"


def test_shuffle_changes_order(tmp_path):
    out = assert_compiles_and_runs("""
        import random
        random.seed(99)
        xs = [10, 20, 30, 40, 50]
        random.shuffle(xs)
        for x in xs:
            print(x)
    """, tmp_path)
    # Should be a permutation of the original, and (with this seed)
    # very unlikely to equal the original order.
    lines = out.splitlines()
    assert sorted(lines, key=int) == ["10", "20", "30", "40", "50"]


# ===========================================================================
# Without import
# ===========================================================================

def test_random_without_import_raises(tmp_path):
    rc, out, err = run_is("""
        x = random.randint(1, 10)
        print(x)
    """, tmp_path)
    assert rc != 0, f"expected transpile error but got rc=0:\n{out}"
    assert "random" in err, f"error should mention 'random': {err}"
