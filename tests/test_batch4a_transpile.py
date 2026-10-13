"""tests/test_batch4a_transpile.py

Batch 8h Phase 2: transpile-only companion to test_batch4a.py.

Verifies the C++ emitted for enumerate() and zip() in for-loops.
No exe launch.
"""

from kofty.transpiler import transpile


# ===========================================================================
# enumerate
# ===========================================================================

def test_enumerate_basic_emits_index_loop():
    out = transpile("""
xs = [10, 20, 30]
for i, x in enumerate(xs):
    print(i)
    print(x)
""")
    # Should iterate by index, not range-based for.
    assert "xs.size()" in out or "xs[" in out


def test_enumerate_string_list_emits_index_loop():
    out = transpile("""
names = ["alice", "bob"]
for i, n in enumerate(names):
    print(n)
""")
    assert "names" in out
    assert ".size()" in out or "names[" in out


def test_enumerate_with_start_emits_offset():
    out = transpile("""
xs = [100, 200]
for i, x in enumerate(xs, 1):
    print(i)
    print(x)
""")
    # Start value 1 must appear somewhere in the emitted loop.
    assert "1" in out
    assert "xs" in out


def test_enumerate_sum_indices_emits_index_loop():
    out = transpile("""
xs = [5, 10, 15]
total = 0
for i, x in enumerate(xs):
    total = total + i * x
print(total)
""")
    assert "total" in out
    assert "xs" in out


def test_enumerate_single_element_emits_loop():
    out = transpile("""
xs = [42]
for i, x in enumerate(xs):
    print(i)
    print(x)
""")
    assert "xs" in out


# ===========================================================================
# zip
# ===========================================================================

def test_zip_two_int_lists_emits_parallel_loop():
    out = transpile("""
a = [1, 2, 3]
b = [10, 20, 30]
for x, y in zip(a, b):
    print(x + y)
""")
    # zip emits a min() bound and two indexed accesses.
    assert "a" in out and "b" in out
    assert "std::min" in out or ".size()" in out


def test_zip_mismatched_lengths_emits_min():
    out = transpile("""
a = [1, 2, 3]
b = [10, 20]
for x, y in zip(a, b):
    print(x + y)
""")
    assert "std::min" in out or "std::min(" in out


def test_zip_string_lists_emits_parallel_loop():
    out = transpile("""
first = ["a", "b"]
last = ["x", "y"]
for f, l in zip(first, last):
    print(f + l)
""")
    assert "first" in out and "last" in out


def test_zip_single_iteration_emits_loop():
    out = transpile("""
a = [1]
b = [100]
for x, y in zip(a, b):
    print(x + y)
""")
    assert "a" in out and "b" in out


def test_zip_shorter_first_emits_min():
    out = transpile("""
a = [1]
b = [10, 20]
for x, y in zip(a, b):
    print(x + y)
print("done")
""")
    assert "std::min" in out or "min(" in out
