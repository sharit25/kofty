"""Batch 13h: whole-program constructor argument type inference.

When a class constructor has unannotated params that are assigned to
fields, infer the field/param C++ type by scanning all call sites of
that class for literal-typed arguments.
"""
import pytest
from kofty.transpiler import transpile, TranspileError


# --- The showcase case: Dog("Rex", "Labrador") ------------------------------

def test_dog_rex_labrador():
    out = transpile('''
class Dog:
    def __init__(self, name, breed):
        self.name = name
        self.breed = breed

d = Dog("Rex", "Labrador")
''')
    assert "std::string name" in out
    assert "std::string breed" in out


def test_person_alice():
    out = transpile('''
class Person:
    def __init__(self, name):
        self.name = name

p = Person("Alice")
''')
    assert "std::string name" in out


def test_circle_double():
    out = transpile('''
class Circle:
    def __init__(self, radius):
        self.radius = radius

c = Circle(2.5)
''')
    assert "double radius" in out


def test_counter_int():
    out = transpile('''
class Counter:
    def __init__(self, n):
        self.n = n

c = Counter(5)
''')
    assert "int n" in out


# --- Annotation takes precedence over call-site inference -------------------

def test_annotation_wins_over_inference():
    out = transpile('''
class Box:
    def __init__(self, name: str):
        self.name = name

b = Box("hello")
''')
    assert "std::string name" in out


# --- Cannot infer: raise a clear error ---------------------------------------

def test_uninferable_raises():
    """If the class IS called but no literal args are visible at
    the call site (e.g. called with a Name), and no annotation
    is given, raise."""
    with pytest.raises(TranspileError):
        transpile('''
class Dog:
    def __init__(self, name):
        self.name = name

x = "Rex"
d = Dog(x)
''')

def test_call_with_name_arg_raises():
    with pytest.raises(TranspileError):
        transpile('''
class Dog:
    def __init__(self, name):
        self.name = name

x = "Rex"
d = Dog(x)
''')


# --- Regression: default-value inference still works ------------------------

def test_default_value_still_infers():
    out = transpile('''
class Counter:
    def __init__(self, n=0):
        self.n = n

c = Counter(5)
''')
    assert "int n" in out


def test_default_str_still_infers():
    out = transpile('''
class Greeter:
    def __init__(self, greeting="hello"):
        self.greeting = greeting

g = Greeter()
''')
    assert "std::string greeting" in out
