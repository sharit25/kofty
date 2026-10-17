from kofty.transpiler import transpile, TranspileError
import pytest


def test_unbound_name_at_module_scope_raises():
    with pytest.raises(TranspileError, match="name 'x' is not defined"):
        transpile('print("Kofty is " + x)\n')


def test_bound_then_used_is_ok():
    out = transpile('x = "hi"\nprint(x)\n')
    assert "x" in out


def test_used_then_bound_is_ok():
    out = transpile('print(greet)\ngreet = "hi"\n')
    assert "greet" in out


def test_builtin_print_is_ok():
    transpile('print("hi")\n')


def test_module_name_is_ok():
    transpile('import math\nx = math.pi\nprint(x)\n')


def test_user_function_name_is_ok():
    transpile('def f():\n    print("hi")\n\nf()\n')


def test_user_class_name_is_ok():
    transpile(
        'class Dog:\n'
        '    def __init__(self):\n'
        '        self.name = "Rex"\n'
        '\n'
        'd = Dog()\n'
        'print(d.name)\n'
    )


def test_loop_var_is_ok():
    transpile('for i in range(3):\n    print(i)\n')


def test_function_param_is_ok():
    transpile('def f(a):\n    print(a)\n\nf(1)\n')


def test_lambda_param_is_ok():
    transpile('f = lambda x: x * 2\nprint(f(3))\n')


def test_bad_name_typo_raises():
    with pytest.raises(TranspileError, match="name 'msg' is not defined"):
        transpile('message = "hi"\nprint(msg)\n')


def test_None_true_false_ok():
    transpile('x = None\nprint(True)\nprint(False)\n')
