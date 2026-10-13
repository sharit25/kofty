"""tests/test_batch8g.py

Batch 8g: list.pop(i) — remove and return element at index i.

Uses transpile-only checks (emit C++ and inspect the string). These
tests never launch a compiled .exe, so they are immune to the
Application Control / WinError 4551 flake that affects the runtime
tests in tests/test_batch8f.py.
"""

import pytest

from kofty.transpiler import TranspileError, transpile


def test_pop_at_zero():
    out = transpile("xs = [1, 2, 3]\nx = xs.pop(0)\n")
    assert "vec_pop_at(xs, 0)" in out


def test_pop_at_one():
    out = transpile("xs = [1, 2, 3]\nx = xs.pop(1)\n")
    assert "vec_pop_at(xs, 1)" in out


def test_pop_at_variable():
    out = transpile("xs = [1, 2, 3]\ni = 1\nx = xs.pop(i)\n")
    assert "vec_pop_at(xs, i)" in out


def test_pop_at_negative():
    out = transpile("xs = [1, 2, 3]\nx = xs.pop(-1)\n")
    assert "vec_pop_at(xs, (-1))" in out


def test_pop_at_expression():
    out = transpile("xs = [1, 2, 3]\nx = xs.pop(1 + 1)\n")
    assert "vec_pop_at(xs, (1 + 1))" in out


def test_pop_no_args_still_works():
    out = transpile("xs = [1, 2, 3]\nx = xs.pop()\n")
    assert "vec_pop(xs)" in out


def test_pop_at_bare_statement():
    out = transpile("xs = [1, 2, 3]\nxs.pop(0)\n")
    assert "vec_pop_at(xs, 0)" in out


def test_pop_too_many_args_raises():
    with pytest.raises(TranspileError):
        transpile("xs = [1, 2, 3]\nx = xs.pop(0, 1)\n")


def test_vec_pop_at_template_emitted():
    out = transpile("xs = [1]\nxs.pop(0)\n")
    assert "vec_pop_at" in out
