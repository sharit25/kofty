"""tests/test_batch8d.py

Batch 8d: @property getters + @x.setter setters on user classes.

Design:

    class Temp:
        def __init__(self, c):
            self._c = c
        @property
        def celsius(self):
            return self._c
        @celsius.setter
        def celsius(self, v):
            self._c = v

    -> struct Temp {
           int _c;
           Temp(int c) : _c(c) {}
           auto celsius() const { return this->_c; }
           void celsius(int v) { this->_c = v; }
       };

    Call-site dispatch:
      t.celsius      -> t.celsius()       (read -> getter call)
      t.celsius = 5  -> t.celsius(5);     (assign -> setter call)
      self.celsius   -> this->celsius()   (inside methods, same rule)

    Read-only property (no @x.setter): assigning raises TranspileError.

Out of scope (deferred):
    - @x.deleter
    - @property + @abstractmethod combos
    - Property inheritance across base classes
    - Properties on pointer classes (ptr(Cls(...)))
"""

import shutil
import subprocess
import sys
import textwrap

import pytest


def run_is(src: str, tmp_path) -> tuple[int, str, str]:
    if shutil.which("g++") is None:
        pytest.skip("g++ not on PATH")
    src = textwrap.dedent(src).strip() + "\n"
    is_file = tmp_path / "prog.kfy"
    is_file.write_text(src)
    result = subprocess.run(
        [sys.executable, "-m", "kofty.cli", str(is_file)],
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout, result.stderr


def assert_runs(src: str, expected_stdout: str, tmp_path):
    rc, out, err = run_is(src, tmp_path)
    assert rc == 0, f"transpile/compile failed:\nSTDERR:\n{err}\nSTDOUT:\n{out}"
    user_lines = [
        line for line in out.splitlines()
        if not line.startswith("[InterScript]")
    ]
    actual = "\n".join(user_lines).strip()
    expected = expected_stdout.strip()
    assert actual == expected, (
        f"\n--- expected ---\n{expected}\n"
        f"--- actual ---\n{actual}\n"
        f"--- raw stdout ---\n{out}\n"
        f"--- stderr ---\n{err}"
    )


def assert_transpile_fails(src: str, needle: str, tmp_path):
    rc, out, err = run_is(src, tmp_path)
    assert rc != 0, (
        f"expected transpile/compile to fail, but it succeeded.\n"
        f"STDOUT:\n{out}\nSTDERR:\n{err}"
    )
    combined = out + err
    assert needle in combined, (
        f"expected error to mention {needle!r}.\n"
        f"STDOUT:\n{out}\nSTDERR:\n{err}"
    )


# ===========================================================================
# Getter: read a backing field through @property
# ===========================================================================

def test_property_getter_basic(tmp_path):
    assert_runs("""
        class Temp:
            def __init__(self, c):
                self._c = c
            @property
            def celsius(self):
                return self._c

        t = Temp(25)
        print(t.celsius)
    """, "25", tmp_path)


# ===========================================================================
# Getter: computed value
# ===========================================================================

def test_property_getter_computed(tmp_path):
    assert_runs("""
        class Temp:
            def __init__(self, c):
                self._c = c
            @property
            def fahrenheit(self):
                return self._c * 9 // 5 + 32

        t = Temp(100)
        print(t.fahrenheit)
    """, "212", tmp_path)


# ===========================================================================
# Setter: write through @x.setter
# ===========================================================================

def test_property_setter_basic(tmp_path):
    assert_runs("""
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
    """, "30", tmp_path)


# ===========================================================================
# Setter with validation
# ===========================================================================

def test_property_setter_validation(tmp_path):
    assert_runs("""
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
        print(t.celsius)
        t.celsius = 30
        print(t.celsius)
    """, "-273\n30", tmp_path)


# ===========================================================================
# self.prop inside a method dispatches to the getter
# ===========================================================================

def test_property_read_via_self(tmp_path):
    assert_runs("""
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
    """, "42", tmp_path)


# ===========================================================================
# self.prop = v inside a method dispatches to the setter
# ===========================================================================

def test_property_write_via_self(tmp_path):
    assert_runs("""
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
        print(t.celsius)
    """, "30", tmp_path)


# ===========================================================================
# Read-only property: assignment raises
# ===========================================================================

def test_property_read_only_raises(tmp_path):
    assert_transpile_fails("""
        class Temp:
            def __init__(self, c):
                self._c = c
            @property
            def celsius(self):
                return self._c

        t = Temp(25)
        t.celsius = 30
    """, "celsius", tmp_path)


# ===========================================================================
# Setter param annotation determines the C++ type
# ===========================================================================

def test_property_setter_annotated_param(tmp_path):
    assert_runs("""
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
        print(t.celsius)
    """, "2.5", tmp_path)



# ===========================================================================
# Regression: all-private-field class must still be instantiable
# (pre-existing bug exposed by Batch 8d — see impl_batch8d.py anchor 2)
# ===========================================================================

def test_all_private_fields_class_instantiates(tmp_path):
    assert_runs("""
        class Counter:
            def __init__(self, n):
                self._n = n
            def get_n(self):
                return self._n
            def bump(self):
                self._n = self._n + 1

        c = Counter(5)
        c.bump()
        c.bump()
        print(c.get_n())
    """, "7", tmp_path)
