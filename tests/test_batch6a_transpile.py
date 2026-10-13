"""tests/test_batch8h Phase 4: transpile-only companion to test_batch6a.py.

Verifies the C++ emitted for match/case (literal patterns).

Emitted as an if/else-if/else chain:
    match x:
        case 1: ...
        case 2: ...
        case _: ...
->
    if (x == 1) { ... }
    else if (x == 2) { ... }
    else { ... }
"""

from kofty.transpiler import transpile


# ===========================================================================
# Basic integer match
# ===========================================================================

def test_match_int_one_case_emits_if():
    out = transpile("""
x = 1
match x:
    case 1:
        print("one")
""")
    assert "if (" in out
    assert "x == 1" in out
    # The match itself emits a single if, not an if/else chain.
    # Look for the match-specific closing brace: the case body should be
    # followed by the `}` that closes the if, then main continues.
    assert 'std::cout << "one"' in out

def test_match_int_two_cases_emits_else_if():
    out = transpile("""
x = 2
match x:
    case 1:
        print("one")
    case 2:
        print("two")
""")
    assert "if (" in out
    assert "else if" in out
    assert "x == 1" in out
    assert "x == 2" in out


def test_match_int_wildcard_emits_else():
    out = transpile("""
x = 99
match x:
    case 1:
        print("one")
    case 2:
        print("two")
    case _:
        print("other")
""")
    assert "if (" in out
    assert "else if" in out
    # Wildcard -> trailing else
    assert out.count("else") >= 2  # one else-if + one final else


def test_match_int_three_cases_emits_chain():
    out = transpile("""
x = 3
match x:
    case 1:
        print("a")
    case 2:
        print("b")
    case 3:
        print("c")
""")
    assert "x == 1" in out
    assert "x == 2" in out
    assert "x == 3" in out


# ===========================================================================
# String patterns
# ===========================================================================

def test_match_string_emits_string_compare():
    out = transpile("""
cmd = "start"
match cmd:
    case "start":
        print("starting")
    case "stop":
        print("stopping")
    case _:
        print("unknown")
""")
    assert "start" in out
    assert "stop" in out
    # String comparisons need std::string or string literals.
    assert '"start"' in out or "std::string" in out


def test_match_string_fallthrough_emits_else():
    out = transpile("""
cmd = "pause"
match cmd:
    case "start":
        print("starting")
    case "stop":
        print("stopping")
    case _:
        print("unknown")
""")
    assert "unknown" in out


# ===========================================================================
# Bool patterns
# ===========================================================================

def test_match_bool_true_emits_bool_compare():
    out = transpile("""
flag = True
match flag:
    case True:
        print("yes")
    case False:
        print("no")
""")
    assert "true" in out
    assert "false" in out


def test_match_bool_false_emits_bool_compare():
    out = transpile("""
flag = False
match flag:
    case True:
        print("yes")
    case False:
        print("no")
""")
    assert "true" in out
    assert "false" in out


# ===========================================================================
# Multiple statements per case body
# ===========================================================================

def test_match_multi_stmt_body_emits_multiple_lines():
    out = transpile("""
x = 2
match x:
    case 1:
        print("first")
        print("line 2")
    case 2:
        print("second")
        print("line 2")
""")
    assert "first" in out
    assert "second" in out
    # Both body statements must be inside the emitted block.
    assert out.count("line 2") >= 2


# ===========================================================================
# No wildcard, no match
# ===========================================================================

def test_match_no_fallthrough_emits_chain():
    out = transpile("""
x = 99
match x:
    case 1:
        print("one")
    case 2:
        print("two")
print("after")
""")
    assert "x == 1" in out
    assert "x == 2" in out


# ===========================================================================
# Match on expressions
# ===========================================================================

def test_match_on_function_result_emits_call():
    out = transpile("""
def get_code():
    return 200

match get_code():
    case 200:
        print("OK")
    case 404:
        print("Not Found")
    case _:
        print("Other")
""")
    # The matched expression is a function call.
    assert "get_code()" in out
    assert "200" in out
    assert "404" in out


# ===========================================================================
# Multiple match statements
# ===========================================================================

def test_match_twice_emits_two_chains():
    out = transpile("""
a = 1
b = 2
match a:
    case 1:
        print("a is one")
match b:
    case 2:
        print("b is two")
""")
    # Two separate if-chains.
    assert out.count("if (") >= 2
    assert "a is one" in out
    assert "b is two" in out
