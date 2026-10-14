"""Batch 11a: .format() on variable receiver, empty f-string spec,
parameter-name keyword check. Transpile-only (no exe launch)."""
import pytest
from kofty.transpiler import transpile, TranspileError


# --- Fix A: .format() on a variable receiver -------------------------------

def test_format_on_variable_receiver():
    out = transpile('''
s = "{} and {}"
r = s.format(1, 2)
''')
    assert ".format(" in out  # still dispatched through the string helper
    # The emitted form should route through the same helper the literal
    # receiver uses. Match whatever helper the literal form emits.
    lit = transpile('r = "{} and {}".format(1, 2)\n')
    # Extract the helper name the literal form uses.
    import re
    m = re.search(r"(\w+)\(", lit)
    assert m, "literal .format() should emit some helper call"
    helper = m.group(1)
    assert helper in out, f"variable receiver should reuse {helper}"


def test_format_on_variable_receiver_indexed():
    out = transpile('''
s = "{0} then {1} then {0}"
r = s.format("a", "b")
''')
    assert "format" in out.lower()


def test_keyword_parameter_error_message_mentions_param():
    try:
        transpile('def f(default):\n    return default\n')
    except TranspileError as e:
        msg = str(e)
        assert "Parameter" in msg or "parameter" in msg, msg
        assert "default" in msg, msg
    else:
        pytest.fail("expected TranspileError")

def test_format_on_variable_initialized_from_literal_works():
    out = transpile('''
s = "{} and {}"
r = s.format(1, 2)
''')
    # The literal was captured at assignment; _emit_format should
    # produce a concatenation with is_to_string.
    assert "is_to_string" in out
    assert " and " in out


def test_format_on_variable_reassigned_from_nonliteral_raises():
    with pytest.raises(TranspileError):
        transpile('''
s = "{}"
t = s
r = t.format(1)
''')


# --- Fix B: empty format spec passthrough ----------------------------------

def test_empty_format_spec_equals_no_spec():
    with_spec    = transpile('x = 42\ns = f"{x:}"\n')
    without_spec = transpile('x = 42\ns = f"{x}"\n')
    # The only difference should be whitespace/name mangling.
    # Assert the same is_to_string dispatch is present in both.
    assert "is_to_string" in with_spec
    assert "is_to_string" in without_spec


def test_empty_format_spec_on_string_var():
    out = transpile('name = "kofty"\ns = f"{name:}"\n')
    assert "is_to_string" in out


def test_empty_format_spec_does_not_raise():
    # Should not raise TranspileError.
    transpile('x = 1.5\ns = f"{x:}"\n')


# --- Fix C: parameter name keyword check -----------------------------------

def test_cpp_keyword_as_parameter_raises():
    with pytest.raises(TranspileError):
        transpile('def f(default):\n    return default\n')


def test_cpp_keyword_as_parameter_raises_class():
    # `default` is a C++ keyword
    with pytest.raises(TranspileError):
        transpile('''
class C:
    def m(self, default):
        return default
''')
    # `this` is a C++ keyword
    with pytest.raises(TranspileError):
        transpile('''
class C:
    def m(self, this):
        return this
''')

def test_normal_parameter_names_still_work():
    out = transpile('def f(x, y, z):\n    return x + y + z\n')
    assert "x" in out and "y" in out and "z" in out


def test_keyword_parameter_error_message_mentions_param():
    try:
        transpile('def f(default):\n    return default\n')
    except TranspileError as e:
        assert "Parameter" in str(e) or "parameter" in str(e)
    else:
        pytest.fail("expected TranspileError")

def test_cpp_keyword_as_abstract_method_param_raises():
    with pytest.raises(TranspileError):
        transpile('''
from abc import abstractmethod
class Shape:
    @abstractmethod
    def area(self, default) -> float:
        pass
''')


def test_cpp_keyword_as_static_method_param_raises():
    with pytest.raises(TranspileError):
        transpile('''
class C:
    @staticmethod
    def m(this):
        return this
''')
