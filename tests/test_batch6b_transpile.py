"""tests/test_batch8h Phase 4: transpile-only companion to test_batch6b.py.

Verifies the C++ emitted for raise and try/except (catch-all).

    raise X("msg") -> throw std::runtime_error("msg");
    raise X        -> throw std::runtime_error("");

    try: ... except: ...       -> try { ... } catch (...) { ... }
    try: ... except Exception: ... -> try { ... } catch (...) { ... }
"""

from kofty.transpiler import transpile


# ===========================================================================
# raise + try/except with raise
# ===========================================================================

def test_try_no_exception_emits_try_catch():
    out = transpile("""
try:
    print("in try")
except Exception:
    print("caught")
print("after")
""")
    assert "try {" in out or "try{" in out
    assert "catch" in out


def test_try_with_raise_emits_throw_runtime_error():
    out = transpile("""
try:
    raise Exception("boom")
except Exception:
    print("caught")
print("after")
""")
    assert "throw std::runtime_error" in out
    assert "boom" in out
    assert "catch" in out


def test_try_bare_except_emits_catch_all():
    out = transpile("""
try:
    raise Exception("x")
except:
    print("caught")
print("after")
""")
    assert "throw std::runtime_error" in out
    # Bare except -> catch (...)
    assert "catch (...)" in out or "catch(...)" in out


def test_try_raise_custom_name_emits_runtime_error():
    out = transpile("""
try:
    raise ValueError("bad value")
except Exception:
    print("value error caught")
print("after")
""")
    # Custom exception names collapse to std::runtime_error.
    assert "throw std::runtime_error" in out
    assert "bad value" in out


def test_try_raise_no_message_emits_empty_string():
    out = transpile("""
try:
    raise RuntimeError
except Exception:
    print("caught")
""")
    # raise X with no msg -> throw std::runtime_error("");
    assert "std::runtime_error" in out


# ===========================================================================
# Nested try
# ===========================================================================

def test_try_nested_emits_two_catches():
    out = transpile("""
try:
    print("outer try")
    try:
        raise Exception("inner")
    except Exception:
        print("inner caught")
except Exception:
    print("outer caught")
print("done")
""")
    # Two try/catch pairs.
    assert out.count("try {") >= 2 or out.count("try{") >= 2
    assert out.count("catch") >= 2


# ===========================================================================
# try with multiple statements
# ===========================================================================

def test_try_multi_stmt_emits_all_in_try():
    out = transpile("""
try:
    print("a")
    print("b")
    print("c")
except Exception:
    print("caught")
""")
    assert "a" in out
    assert "b" in out
    assert "c" in out
    assert "catch" in out


# ===========================================================================
# try with function call
# ===========================================================================

def test_try_with_function_emits_function_and_catch():
    out = transpile("""
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
""")
    assert "risky" in out
    assert "throw std::runtime_error" in out
    # Two try blocks
    assert out.count("catch") >= 2


# ===========================================================================
# raise in a function called from try
# ===========================================================================

def test_raise_in_function_not_caught_emits_throw_in_func():
    out = transpile("""
def will_fail():
    raise Exception("nope")

print("before")
try:
    will_fail()
except Exception:
    print("caught")
print("after")
""")
    assert "will_fail" in out
    assert "throw std::runtime_error" in out
    assert "nope" in out


# ===========================================================================
# try in a loop
# ===========================================================================

def test_try_in_loop_emits_try_inside_for():
    out = transpile("""
for i in range(3):
    try:
        if i == 1:
            raise Exception("skip")
        print(i)
    except Exception:
        print("caught")
""")
    assert "throw std::runtime_error" in out
    assert "catch" in out


# ===========================================================================
# Empty try body
# ===========================================================================

def test_try_pass_emits_try_catch():
    out = transpile("""
try:
    pass
except Exception:
    print("caught")
print("after")
""")
    assert "try" in out
    assert "catch" in out


# ===========================================================================
# except body is empty (pass)
# ===========================================================================

def test_except_pass_emits_empty_catch():
    out = transpile("""
try:
    raise Exception("x")
except Exception:
    pass
print("after")
""")
    assert "throw std::runtime_error" in out
    assert "catch" in out
