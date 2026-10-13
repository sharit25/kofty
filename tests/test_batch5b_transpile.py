"""tests/test_batch8h Phase 3: transpile-only companion to test_batch5b.py.

Verifies the C++ emitted for *args (variadic positional args).

*args -> std::vector<int> (or std::vector<std::string> with :str).
Call sites use brace-init: f({1, 2, 3}) -> f({1, 2, 3});
"""

from kofty.transpiler import transpile


# ===========================================================================
# Basic *args
# ===========================================================================

def test_args_int_sum_emits_vector():
    out = transpile("""
def sum_all(*nums):
    total = 0
    for n in nums:
        total = total + n
    return total

print(sum_all({1, 2, 3}))
""")
    # Emitted signature must contain std::vector<int>
    assert "std::vector<int>" in out
    assert "nums" in out


def test_args_empty_emits_vector_and_size():
    out = transpile("""
def count_all(*nums):
    return len(nums)

print(count_all({}))
""")
    assert "std::vector<int>" in out
    assert ".size()" in out


def test_args_len_emits_vector_size():
    out = transpile("""
def count_all(*nums):
    return len(nums)

print(count_all({1, 2, 3, 4, 5}))
""")
    assert "std::vector<int>" in out
    assert ".size()" in out


# ===========================================================================
# *args with annotation
# ===========================================================================

def test_args_str_emits_vector_string():
    out = transpile("""
def join_all(*words: str):
    result = ""
    for w in words:
        result = result + w
    return result

print(join_all({"a", "b", "c"}))
""")
    assert "std::vector<std::string>" in out
    assert "words" in out


def test_args_str_annotation_empty_emits_vector_string():
    out = transpile("""
def join_all(*words: str):
    return len(words)

print(join_all({}))
""")
    assert "std::vector<std::string>" in out
    assert ".size()" in out


# ===========================================================================
# *args body behaves like a list
# ===========================================================================

def test_args_indexing_emits_subscript():
    out = transpile("""
def first_of(*nums):
    return nums[0]

print(first_of({10, 20, 30}))
""")
    # Indexing a vector -> nums[0]
    assert "nums[0]" in out or "nums.at(0)" in out


def test_args_membership_emits_find():
    out = transpile("""
def contains(*nums):
    if 5 in nums:
        return 1
    return 0

print(contains({1, 2, 5}))
""")
    # in over a vector -> std::find(...) != .end()
    assert "std::find" in out
    assert "nums" in out


# ===========================================================================
# *args called multiple times
# ===========================================================================

def test_args_called_various_sizes_emits_signature():
    out = transpile("""
def sum_all(*nums):
    total = 0
    for n in nums:
        total = total + n
    return total

print(sum_all({1}))
print(sum_all({1, 2}))
""")
    assert "std::vector<int>" in out
    # Brace-init call sites
    assert "{1}" in out or "std::vector<int>{1}" in out


# ===========================================================================
# *args combined with regular param
# ===========================================================================

def test_args_with_regular_param_emits_signature():
    out = transpile("""
def add_all(first, *rest):
    total = first
    for n in rest:
        total = total + n
    return total

print(add_all(10, {1, 2, 3}))
""")
    # Signature: add_all(int first, std::vector<int> rest)
    assert "first" in out
    assert "std::vector<int>" in out
    assert "rest" in out
