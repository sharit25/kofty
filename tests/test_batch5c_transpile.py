"""tests/test_batch8h Phase 3: transpile-only companion to test_batch5c.py.

Verifies the C++ emitted for **kwargs (variadic keyword args).

**kwargs -> std::map<std::string, std::string> (or ...<std::string, int>
with :int annotation). Call sites use dict literals.
"""

from kofty.transpiler import transpile


# ===========================================================================
# Basic **kwargs
# ===========================================================================

def test_kwargs_iterate_emits_map():
    out = transpile("""
def show(**info):
    for k, v in info.items():
        print(k)
        print(v)

show({"name": "Alice", "age": "30"})
""")
    # Emitted signature: std::map<std::string, std::string> info
    assert "std::map<std::string, std::string>" in out
    assert "info" in out


def test_kwargs_len_emits_map_size():
    out = transpile("""
def count(**info):
    return len(info)

print(count({"a": "1", "b": "2", "c": "3"}))
""")
    assert "std::map<std::string, std::string>" in out
    assert ".size()" in out


def test_kwargs_empty_emits_map():
    out = transpile("""
def count(**info):
    return len(info)

print(count({}))
""")
    assert "std::map<std::string, std::string>" in out
    assert ".size()" in out


# ===========================================================================
# **kwargs with annotation (value type = int)
# ===========================================================================

def test_kwargs_int_values_emits_int_map():
    out = transpile("""
def total(**counts: int):
    s = 0
    for v in counts.values():
        s = s + v
    return s

print(total({"a": 1, "b": 2, "c": 3}))
""")
    assert "std::map<std::string, int>" in out
    assert "counts" in out


# ===========================================================================
# **kwargs body behaves like a dict
# ===========================================================================

def test_kwargs_get_emits_map_access():
    out = transpile("""
def fetch(**data):
    return data.get("key")

print(fetch({"key": "value", "other": "x"}))
""")
    # .get() on a std::map -> .count(...) ? ... : ...
    assert "data.count" in out or ".count(" in out


def test_kwargs_membership_emits_map_count():
    out = transpile("""
def has_name(**info):
    if "name" in info:
        return 1
    return 0

print(has_name({"name": "x"}))
""")
    # in over a map -> .count(...) > 0
    assert "info.count" in out or ".count(" in out


# ===========================================================================
# **kwargs with values via .items()
# ===========================================================================

def test_kwargs_items_sorted_emits_map_iteration():
    out = transpile("""
def dump(**info):
    for k, v in info.items():
        print(k + "=" + v)

dump({"c": "3", "a": "1", "b": "2"})
""")
    # The .items() loop emits an iteration over `info`.
    assert "info" in out
    # The map type must be in the emitted signature.
    assert "std::map<std::string, std::string>" in out


# ===========================================================================
# Multiple calls, various content
# ===========================================================================

def test_kwargs_called_repeatedly_emits_map():
    out = transpile("""
def count(**info):
    return len(info)

print(count({"a": "1"}))
print(count({"a": "1", "b": "2"}))
""")
    assert "std::map<std::string, std::string>" in out
    # Both call sites must produce map literals
    assert out.count("std::map") >= 3 or out.count("{{") >= 2
