"""Batch 13d.1: unannotated parent methods get `virtual` when subclassed.

Bug: Animal.speak() has no return annotation and returns a value —
_method_return_type returned ("auto", "") -> non-virtual. But a
subclass with a method of the same name got `override`, and g++
rejects overriding a non-virtual method.

(Note: 13d was already used by the *args batch — commit 1efb2d5.)
"""
from kofty.transpiler import transpile


def test_unannotated_parent_method_is_virtual_when_subclassed():
    out = transpile('''
class Animal:
    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):
        return "Woof"
''')
    assert "virtual std::string speak()" in out
    assert "std::string speak() override" in out


def test_unannotated_method_not_virtual_when_not_subclassed():
    out = transpile('''
class Standalone:
    def speak(self):
        return "..."
''')
    # Not a base class — no virtual needed.
    assert "virtual auto speak()" not in out
    assert "std::string speak()" in out


def test_annotated_parent_method_still_virtual():
    out = transpile('''
class Animal:
    def speak(self) -> str:
        return "..."

class Dog(Animal):
    def speak(self) -> str:
        return "Woof"
''')
    assert "virtual std::string speak()" in out
    assert "std::string speak() override" in out


def test_void_parent_method_still_virtual():
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
