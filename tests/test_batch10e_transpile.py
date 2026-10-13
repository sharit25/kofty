"""Batch 10e: register imports before emitting class bodies.

Regression: `math.pi` (and random.*/time.*) inside a class method
raised "used without `import math`" because visit_Import ran in a
later pass than visit_ClassDef.
"""
from kofty.transpiler import transpile


def test_math_pi_in_class_method():
    out = transpile(
        "import math\n"
        "class C:\n"
        "    def area(self):\n"
        "        return math.pi\n"
    )
    assert "3.141592653589793" in out


def test_math_e_in_class_method():
    out = transpile(
        "import math\n"
        "class C:\n"
        "    def e(self):\n"
        "        return math.e\n"
    )
    assert "2.718281828459045" in out


def test_math_call_in_class_method():
    out = transpile(
        "import math\n"
        "class C:\n"
        "    def s(self):\n"
        "        return math.sqrt(2)\n"
    )
    assert "std::sqrt" in out


def test_math_in_property():
    out = transpile(
        "import math\n"
        "class C:\n"
        "    @property\n"
        "    def x(self):\n"
        "        return math.pi\n"
    )
    assert "3.141592653589793" in out


def test_random_in_class_method():
    out = transpile(
        "import random\n"
        "class C:\n"
        "    def r(self):\n"
        "        return random.random()\n"
    )
    assert "rand_float()" in out


def test_time_in_class_method():
    out = transpile(
        "import time\n"
        "class C:\n"
        "    def t(self):\n"
        "        return time.time()\n"
    )
    assert "time_now()" in out


def test_import_after_class_still_works():
    # Python allows imports anywhere at module level; Kofty should too.
    out = transpile(
        "class C:\n"
        "    def area(self):\n"
        "        return math.pi\n"
        "import math\n"
    )
    assert "3.141592653589793" in out
