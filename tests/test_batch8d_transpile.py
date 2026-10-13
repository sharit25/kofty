"""tests/test_batch8h Phase 5b: transpile-only companion to test_batch8d.py.

Verifies the C++ emitted for @property getters and @x.setter setters.

    @property def celsius(self): return self._c
      -> auto celsius() const { return this->_c; }

    @celsius.setter def celsius(self, v): self._c = v
      -> void celsius(int v) { this->_c = v; }

    t.celsius      -> t.celsius()
    t.celsius = 5  -> t.celsius(5);
    self.celsius   -> this->celsius()
    self.celsius = v -> this->celsius(v);
"""

from kofty.transpiler import transpile


# ===========================================================================
# Getter
# ===========================================================================

def test_property_getter_basic_emits_getter():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @property
    def celsius(self):
        return self._c

t = Temp(25)
print(t.celsius)
""")
    # Getter emitted as `auto celsius() const`
    assert "celsius()" in out
    assert "const" in out
    # Read site must dispatch to method call.
    assert "t.celsius()" in out


def test_property_getter_computed_emits_getter():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @property
    def fahrenheit(self):
        return self._c * 9 // 5 + 32

t = Temp(100)
print(t.fahrenheit)
""")
    assert "fahrenheit()" in out
    # Computation must appear (is_floordiv).
    assert "is_floordiv" in out


# ===========================================================================
# Setter
# ===========================================================================

def test_property_setter_basic_emits_setter():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @property
    def celsius(self):
        return self._c
    @celsius.setter
    def celsius(self, v):
        self._c = v

t = Temp(25)
t.celsius = 30
print(t.celsius)
""")
    # Setter signature: void celsius(int v)
    assert "void celsius" in out
    # Write site dispatches to setter call.
    assert "t.celsius(30)" in out


def test_property_setter_validation_emits_setter_body():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @property
    def celsius(self):
        return self._c
    @celsius.setter
    def celsius(self, v):
        if v < -273:
            self._c = -273
        else:
            self._c = v

t = Temp(25)
t.celsius = -500
""")
    assert "void celsius" in out
    # The validation `if (v < -273)` must appear.
    assert "-273" in out


# ===========================================================================
# self.prop read / write inside methods
# ===========================================================================

def test_property_read_via_self_emits_getter_call():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @property
    def celsius(self):
        return self._c
    def describe(self):
        return self.celsius * 2

t = Temp(21)
print(t.describe())
""")
    # Inside the method, self.celsius -> this->celsius()
    assert "this->celsius()" in out


def test_property_write_via_self_emits_setter_call():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @property
    def celsius(self):
        return self._c
    @celsius.setter
    def celsius(self, v):
        self._c = v
    def bump(self):
        self.celsius = self.celsius + 10

t = Temp(20)
t.bump()
""")
    # Inside bump, both read and write dispatch through methods.
    assert "this->celsius(" in out


# ===========================================================================
# Read-only property assignment -> TranspileError
# ===========================================================================

def test_property_read_only_raises():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError) as exc:
        transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @property
    def celsius(self):
        return self._c

t = Temp(25)
t.celsius = 30
""")
    # Error message must mention the property name.
    assert "celsius" in str(exc.value)


# ===========================================================================
# Setter param annotation -> C++ type
# ===========================================================================

def test_property_setter_annotated_param_emits_double():
    out = transpile("""
class Temp:
    def __init__(self, c: float):
        self._c = c
    @property
    def celsius(self):
        return self._c
    @celsius.setter
    def celsius(self, v: float):
        self._c = v

t = Temp(1.0)
t.celsius = 2.5
""")
    # Setter must take a double, not int.
    assert "void celsius(double" in out


# ===========================================================================
# Regression: all-private-field class
# ===========================================================================

def test_all_private_fields_class_emits_public():
    out = transpile("""
class Counter:
    def __init__(self, n):
        self._n = n
    def get_n(self):
        return self._n
    def bump(self):
        self._n = self._n + 1

c = Counter(5)
c.bump()
print(c.get_n())
""")
    # The class must expose public members (constructor + methods).
    assert "public:" in out
    # The constructor must be publicly accessible.
    assert "Counter(int" in out
