"""Batch 10j: user-class parameter annotations."""
from kofty.transpiler import transpile


def test_function_param_with_user_class_annotation():
    out = transpile(
        "class P:\n"
        "    def __init__(self, x: int):\n"
        "        self.x = x\n"
        "def f(p: P):\n"
        "    return p.x\n"
    )
    assert "f(P p)" in out
    assert "f(int p)" not in out


def test_function_param_with_class_annotation_uses_field():
    out = transpile(
        "class P:\n"
        "    def __init__(self, x: int):\n"
        "        self.x = x\n"
        "def g(p: P):\n"
        "    return p.x * 2\n"
    )
    # Field access on the param must work
    assert "p.x" in out


def test_constructor_param_with_user_class_annotation():
    out = transpile(
        "class P:\n"
        "    def __init__(self, x: int):\n"
        "        self.x = x\n"
        "class C:\n"
        "    def __init__(self, center: P, y: int):\n"
        "        self.center = center\n"
        "        self.y = y\n"
    )
    assert "C(P center, int y)" in out
    assert "C(int center, int y)" not in out


def test_primitive_annotations_unchanged():
    out = transpile(
        "def f(a: int, b: float, s: str, flag: bool):\n"
        "    return a\n"
    )
    assert "f(int a, double b, std::string s, bool flag)" in out


def test_no_annotation_defaults_to_auto():
    out = transpile("def f(x):\n    return x\n")
    assert "auto f(auto x)" in out
