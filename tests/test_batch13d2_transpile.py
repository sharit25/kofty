"""Batch 13d.2: base-class methods with inferable returns get a
concrete return type, not `virtual auto` (which C++ forbids).

After 13d.1 forced `virtual` on base methods, unannotated methods
with a `return <expr>` body were emitted as `virtual auto ...`,
which g++ rejects. 13d.2 infers a concrete return type from the
body when possible; falls back to `auto` (and skips `virtual` AND
`override`) when not.
"""
from kofty.transpiler import transpile


def test_string_return_inferred_for_base_method():
    out = transpile('''
class Animal:
    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):
        return "Woof"
''')
    # Concrete return type inferred; not `virtual auto`.
    assert "virtual std::string speak()" in out
    assert "std::string speak() override" in out
    assert "virtual auto" not in out


def test_int_return_inferred_for_base_method():
    out = transpile('''
class Base:
    def value(self):
        return 42

class Child(Base):
    def value(self):
        return 7
''')
    assert "virtual int value()" in out
    assert "int value() override" in out


def test_double_return_inferred_for_base_method():
    out = transpile('''
class Base:
    def ratio(self):
        return 3.14

class Child(Base):
    def ratio(self):
        return 2.71
''')
    assert "virtual double ratio()" in out


def test_void_base_method_still_works():
    # No return value at all — the void path still works.
    out = transpile('''
class Base:
    def run(self):
        print("base")

class Child(Base):
    def run(self):
        print("child")
''')
    assert "virtual void run()" in out
    assert "void run() override" in out


def test_uninferable_base_method_falls_back_to_auto_no_virtual():
    # `x` is a local variable — we don't track it, so inference
    # should fail and the method stays `auto`, non-virtual.
    out = transpile('''
class Base:
    def compute(self, x):
        return x

class Child(Base):
    def compute(self, x):
        return x
''')
    assert "virtual auto compute()" not in out
    # Should be non-virtual auto, and NOT marked override.
    assert "auto compute() override" not in out


def test_non_base_class_unannotated_method_still_auto():
    # Not a base class — no virtual needed. Keeps existing behavior.
    out = transpile('''
class Standalone:
    def compute(self):
        return 42
''')
    assert "virtual " not in out
    assert "int compute()" in out
