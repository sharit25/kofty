"""tests/test_batch8h Phase 5b: transpile-only companion to test_batch8e.py.

Verifies the C++ emitted for @classmethod.

    @classmethod
    def make(klass, c): ...
      -> static auto make(int c) { ... }

    Body remapping:
        klass(c)          -> <ClassName>(c)
        klass.method(...) -> <ClassName>::method(...)

    Call sites:
        ClassName.method(...)  -> ClassName::method(...)
        obj.method(...)        -> ClassName::method(...)  (via instance)
"""

from kofty.transpiler import transpile


# ===========================================================================
# Basic
# ===========================================================================

def test_classmethod_basic_emits_static():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @classmethod
    def make(klass, c):
        return klass(c)
    @property
    def celsius(self):
        return self._c

t = Temp.make(25)
print(t.celsius)
""")
    # Emitted as static member function.
    assert "static auto make" in out
    # Body: `klass(c)` remapped to `Temp(c)`.
    assert "Temp(" in out
    # Call site: `Temp.make(25)` -> `Temp::make(25)`.
    assert "Temp::make(25)" in out


def test_classmethod_computed_emits_static():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @classmethod
    def from_fahrenheit(klass, f):
        return klass((f - 32) * 5 // 9)
    @property
    def celsius(self):
        return self._c

t = Temp.from_fahrenheit(212)
print(t.celsius)
""")
    assert "static auto from_fahrenheit" in out
    # Body uses is_floordiv for `// 9`.
    assert "is_floordiv" in out
    # Call site uses ::
    assert "Temp::from_fahrenheit(212)" in out


def test_classmethod_calls_static_emits_class_scope():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @staticmethod
    def twice(x):
        return x * 2
    @classmethod
    def make_doubled(klass, x):
        return klass(klass.twice(x))
    @property
    def celsius(self):
        return self._c

t = Temp.make_doubled(5)
print(t.celsius)
""")
    assert "static auto make_doubled" in out
    # `klass.twice(x)` must be remapped to `Temp::twice(x)`.
    assert "Temp::twice" in out


def test_classmethod_returns_value_emits_static():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @classmethod
    def default_celsius(klass):
        return 20

print(Temp.default_celsius())
""")
    assert "static auto default_celsius" in out
    # No args in the emitted signature except from the class param.
    assert "default_celsius()" in out or "default_celsius()" in out


# ===========================================================================
# Coexistence
# ===========================================================================

def test_classmethod_coexists_emits_all_three():
    out = transpile("""
class Calc:
    def __init__(self, n):
        self.n = n
    @staticmethod
    def add(a, b):
        return a + b
    @classmethod
    def make_default(klass):
        return klass(10)
    def twice(self):
        return self.n * 2

c = Calc.make_default()
print(c.twice())
print(Calc.add(3, 4))
""")
    # Static, classmethod, instance method all present.
    assert "static auto make_default" in out
    assert "static auto add" in out
    # `twice` is a normal method, not static.
    assert "auto twice" in out


# ===========================================================================
# Classmethod via instance
# ===========================================================================

def test_classmethod_via_instance_emits_class_scope():
    out = transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @classmethod
    def make(klass, c):
        return klass(c)
    @property
    def celsius(self):
        return self._c

t = Temp(10)
t2 = t.make(20)
print(t2.celsius)
""")
    # `t.make(20)` must dispatch to `Temp::make(20)`.
    assert "Temp::make(20)" in out


# ===========================================================================
# Errors
# ===========================================================================

def test_classmethod_with_static_raises():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError) as exc:
        transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @staticmethod
    @classmethod
    def bad(klass, x):
        return klass(x)

t = Temp.bad(5)
""")
    assert "classmethod" in str(exc.value)


def test_classmethod_no_args_raises():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError) as exc:
        transpile("""
class Temp:
    def __init__(self, c):
        self._c = c
    @classmethod
    def bad():
        return 0

x = Temp.bad()
""")
    assert "bad" in str(exc.value)
