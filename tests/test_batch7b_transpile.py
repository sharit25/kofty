"""tests/test_batch8h Phase 4b: transpile-only companion to test_batch7b.py.

Verifies the C++ emitted for `import random`.

random.random()      -> rand_float()
random.randint(a, b) -> rand_int(a, b)
random.choice(xs)    -> rand_choice(xs)
random.shuffle(xs)   -> rand_shuffle(xs)
random.seed(n)       -> rand_seed(n)

These tests inspect the emitted C++ only — no exe launch, so they
are immune to the WDAC flake. The runtime tests in test_batch7b.py
verify actual randomness behavior.
"""

from kofty.transpiler import transpile


# ===========================================================================
# random.seed
# ===========================================================================

def test_seed_emits_rand_seed():
    out = transpile("""
import random
random.seed(42)
print(random.randint(1, 100))
""")
    assert "rand_seed(42)" in out


def test_seed_different_seeds_emit_different_literals():
    out_a = transpile("""
import random
random.seed(1)
print(random.randint(1, 100))
""")
    out_b = transpile("""
import random
random.seed(999)
print(random.randint(1, 100))
""")
    assert "rand_seed(1)" in out_a
    assert "rand_seed(999)" in out_b


# ===========================================================================
# random.random()
# ===========================================================================

def test_random_emits_rand_float():
    out = transpile("""
import random
x = random.random()
print("ok")
""")
    assert "rand_float()" in out


def test_random_range_emits_rand_float_in_loop():
    out = transpile("""
import random
random.seed(7)
for i in range(20):
    x = random.random()
    print(x)
""")
    assert "rand_float()" in out
    assert "rand_seed(7)" in out


# ===========================================================================
# random.randint(a, b)
# ===========================================================================

def test_randint_emits_rand_int():
    out = transpile("""
import random
random.seed(13)
for i in range(50):
    n = random.randint(5, 10)
    print(n)
""")
    assert "rand_int(5, 10)" in out


def test_randint_can_hit_endpoints_emits_rand_int():
    out = transpile("""
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
print(lo_hits)
print(hi_hits)
""")
    assert "rand_int(1, 3)" in out
    # Endpoints 1 and 3 must appear literally in the emitted call.
    assert "(1, 3)" in out


# ===========================================================================
# random.choice(xs)
# ===========================================================================

def test_choice_int_emits_rand_choice():
    out = transpile("""
import random
random.seed(3)
xs = [10, 20, 30]
n = random.choice(xs)
print(n)
""")
    assert "rand_choice(xs)" in out


def test_choice_from_strings_emits_rand_choice():
    out = transpile("""
import random
random.seed(5)
words = ["red", "green", "blue"]
for i in range(10):
    w = random.choice(words)
    print(w)
""")
    assert "rand_choice(words)" in out


# ===========================================================================
# random.shuffle(xs)
# ===========================================================================

def test_shuffle_preserves_elements_emits_rand_shuffle():
    out = transpile("""
import random
random.seed(11)
xs = [1, 2, 3, 4, 5]
random.shuffle(xs)
print(len(xs))
""")
    assert "rand_shuffle(xs)" in out


def test_shuffle_changes_order_emits_rand_shuffle():
    out = transpile("""
import random
random.seed(99)
xs = [10, 20, 30, 40, 50]
random.shuffle(xs)
for x in xs:
    print(x)
""")
    assert "rand_shuffle(xs)" in out
    # The rand_shuffle template helper must be in the preamble.
    assert "rand_shuffle" in out


# ===========================================================================
# Preamble includes the random helpers
# ===========================================================================

def test_preamble_includes_random_helpers():
    out = transpile("""
import random
random.seed(1)
x = random.random()
print(x)
""")
    # All four helper names must appear at least once in the file.
    assert "rand_seed" in out
    assert "rand_float" in out


# ===========================================================================
# Without import - should raise
# ===========================================================================

def test_random_without_import_raises():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError):
        transpile("""
x = random.randint(1, 10)
print(x)
""")
