"""tests/test_batch8e.py

Batch 8e: @classmethod on user classes.

Design:

    class Temp:
        def __init__(self, c):
            self._c = c
        @classmethod
        def from_fahrenheit(klass, f):
            return klass((f - 32) * 5 // 9)
        @property
        def celsius(self):
            return self._c

    -> struct Temp {
           int _c;
           Temp(int c) : _c(c) {}
           static auto from_fahrenheit(int f) {
               return Temp(((f - 32) * 5 / 9));
           }
           auto celsius() const { return this->_c; }
       };

    `cls` (or the actual first-param name) is remapped to the class
    name in the classmethod body: `cls(...)` -> `Temp(...)`, `cls.x`
    -> `Temp::x`.

    Call sites `ClassName.method(args)` -> `ClassName::method(args)`,
    handled by the existing static-method dispatch (transpiler.py line
    ~1470).

Out of scope (deferred):
    - @abstractmethod + @classmethod combined
    - super() inside a classmethod
    - Classmethod inheritance polymorphism (cls always = the defining
      class, not the child class)
    - @classmethod(name) parametrized form
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
# Basic: classmethod constructs an instance via cls(...)
# ===========================================================================

def test_classmethod_basic(tmp_path):
    assert_runs("""
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
    """, "25", tmp_path)


# ===========================================================================
# Classmethod with computed args
# ===========================================================================

def test_classmethod_computed(tmp_path):
    assert_runs("""
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
    """, "100", tmp_path)


# ===========================================================================
# Classmethod calls a static method via cls.method()
# ===========================================================================

def test_classmethod_calls_static(tmp_path):
    assert_runs("""
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
    """, "10", tmp_path)


# ===========================================================================
# Classmethod returns a non-constructor value
# ===========================================================================

def test_classmethod_returns_value(tmp_path):
    assert_runs("""
        class Temp:
            def __init__(self, c):
                self._c = c
            @classmethod
            def default_celsius(klass):
                return 20

        print(Temp.default_celsius())
    """, "20", tmp_path)


# ===========================================================================
# Classmethod coexists with static and instance methods
# ===========================================================================

def test_classmethod_coexists(tmp_path):
    assert_runs("""
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
    """, "20\n7", tmp_path)


# ===========================================================================
# Classmethod called via an instance (Python allows this)
# ===========================================================================

def test_classmethod_via_instance(tmp_path):
    assert_runs("""
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
    """, "20", tmp_path)


# ===========================================================================
# @staticmethod + @classmethod combined -> reject
# ===========================================================================

def test_classmethod_with_static_raises(tmp_path):
    assert_transpile_fails("""
        class Temp:
            def __init__(self, c):
                self._c = c
            @staticmethod
            @classmethod
            def bad(klass, x):
                return klass(x)

        t = Temp.bad(5)
    """, "classmethod", tmp_path)


# ===========================================================================
# Classmethod with no args at all -> reject (needs at least cls)
# ===========================================================================

def test_classmethod_no_args_raises(tmp_path):
    assert_transpile_fails("""
        class Temp:
            def __init__(self, c):
                self._c = c
            @classmethod
            def bad():
                return 0

        x = Temp.bad()
    """, "bad", tmp_path)
