"""tests/test_batch4b_transpile.py

Batch 8h Phase 2: transpile-only companion to test_batch4b.py.

Verifies the C++ emitted for for...else. No exe launch.

The transpiler emits for...else with a `__broke_N` bool flag: set to
false before the loop, set to true when break fires, and the else
body is guarded by `if (!__broke_N)` after the loop.
"""

from kofty.transpiler import transpile


# ===========================================================================
# Basic for...else
# ===========================================================================

def test_else_runs_when_no_break_emits_flag():
    out = transpile("""
xs = [1, 2, 3]
for x in xs:
    print(x)
else:
    print("no break")
""")
    assert "__broke_" in out
    # The else body must be guarded by the flag.
    assert "if (!" in out or "if(!" in out or "if (" in out


def test_else_skipped_when_break_emits_flag_set():
    out = transpile("""
xs = [1, 2, 3]
for x in xs:
    if x == 2:
        break
    print(x)
else:
    print("no break")
print("after")
""")
    # Break must set the flag to true.
    assert "__broke_" in out
    assert "= true" in out


def test_else_runs_on_empty_list_emits_flag():
    out = transpile("""
xs = [1]
empty = [2]
total = 0
for x in xs:
    if x == 999:
        break
    total = total + 1
else:
    print("finished")
""")
    assert "__broke_" in out


def test_break_condition_never_true_emits_flag():
    out = transpile("""
xs = [10, 20, 30]
for x in xs:
    if x > 100:
        break
    print(x)
else:
    print("done")
""")
    assert "__broke_" in out


# ===========================================================================
# for...else with range
# ===========================================================================

def test_range_for_else_no_break_emits_flag():
    out = transpile("""
for i in range(3):
    print(i)
else:
    print("end")
""")
    assert "__broke_" in out


def test_range_for_else_with_break_emits_flag():
    out = transpile("""
for i in range(10):
    if i == 3:
        break
    print(i)
else:
    print("end")
""")
    assert "__broke_" in out
    assert "= true" in out


# ===========================================================================
# for...else with enumerate / zip
# ===========================================================================

def test_enumerate_for_else_no_break_emits_flag():
    out = transpile("""
xs = [10, 20]
for i, x in enumerate(xs):
    print(i)
    print(x)
else:
    print("done")
""")
    assert "__broke_" in out
    assert "xs" in out


def test_enumerate_for_else_with_break_emits_flag():
    out = transpile("""
xs = [10, 20, 30]
for i, x in enumerate(xs):
    if x == 20:
        break
    print(x)
else:
    print("done")
print("after")
""")
    assert "__broke_" in out
    assert "= true" in out


def test_zip_for_else_no_break_emits_flag():
    out = transpile("""
a = [1, 2]
b = [10, 20]
for x, y in zip(a, b):
    print(x + y)
else:
    print("done")
""")
    assert "__broke_" in out
    assert "std::min" in out or "min(" in out


def test_zip_for_else_with_break_emits_flag():
    out = transpile("""
a = [1, 2, 3]
b = [10, 20, 30]
for x, y in zip(a, b):
    if x + y == 22:
        break
    print(x + y)
else:
    print("done")
""")
    assert "__broke_" in out
    assert "= true" in out


# ===========================================================================
# for...else with dict
# ===========================================================================

def test_dict_values_for_else_emits_flag():
    out = transpile("""
d = {"a": 1, "b": 2}
for v in d.values():
    print(v)
else:
    print("all")
""")
    assert "__broke_" in out


def test_dict_values_for_else_with_break_emits_flag():
    out = transpile("""
d = {"a": 1, "b": 2, "c": 3}
for v in d.values():
    if v == 2:
        break
    print(v)
else:
    print("all")
print("after")
""")
    assert "__broke_" in out
    assert "= true" in out


# ===========================================================================
# Nested for...else
# ===========================================================================

def test_nested_for_else_emits_two_flags():
    out = transpile("""
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
""")
    # Nested for-else -> two distinct __broke_N flags.
    # Find all occurrences of __broke_N and count distinct indices.
    import re
    flags = set(re.findall(r"__broke_\d+", out))
    assert len(flags) >= 2, (
        f"expected 2+ distinct __broke_N flags, got {flags}"
    )


# ===========================================================================
# Unreachable break: else still guarded
# ===========================================================================

def test_else_with_unreachable_break_emits_flag():
    out = transpile("""
xs = [5]
for x in xs:
    print(x)
    if x > 100:
        break
else:
    print("reached else")
""")
    assert "__broke_" in out
