# tests/test_batch13c_transpile.py
from kofty.transpiler import transpile


def _main(out):
    return out.split("int main()")[1]


def test_base_ctor_param_inferred_from_super_init():
    out = transpile('''
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed

d = Dog("Rex", "Labrador")
''')
    # Animal's constructor should have `std::string name`, not `int name`.
    assert "Animal(std::string name)" in out


def test_base_ctor_param_inferred_from_super_init_pair():
    out = transpile('''
class Base:
    def __init__(self, a, b):
        self.a = a
        self.b = b

class Child(Base):
    def __init__(self, a, b):
        super().__init__(a, b)

c = Child("x", "y")
''')
    assert "Base(std::string a, std::string b)" in out


def test_base_ctor_still_int_when_args_are_int():
    out = transpile('''
class Base:
    def __init__(self, n):
        self.n = n

class Child(Base):
    def __init__(self, n):
        super().__init__(n)

c = Child(42)
''')
    assert "Base(int n)" in out


def test_derived_class_ctor_still_inferred():
    out = transpile('''
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed

d = Dog("Rex", "Labrador")
''')
    # Dog's own ctor should still be `std::string name, std::string breed`
    assert "Dog(std::string name, std::string breed)" in out
