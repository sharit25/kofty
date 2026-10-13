"""Batch 10f: string repetition (`"=" * 40`)."""
from kofty.transpiler import transpile


def test_str_times_int():
    out = transpile('s = "=" * 40\n')
    assert "str_repeat(\"=\", 40)" in out


def test_int_times_str():
    out = transpile('s = 40 * "="\n')
    assert "str_repeat(\"=\", 40)" in out


def test_uses_in_print():
    out = transpile('print("=" * 40)\n')
    assert "str_repeat" in out


def test_still_works_for_int_mult():
    # Regular int multiplication must not be turned into str_repeat.
    # Note: `str_repeat` is always defined in the preamble (unused
    # helpers are harmless dead code), so we check the *call site*
    # in main(), not the whole output.
    out = transpile('x = 3 * 4\n')
    main_body = out.split("int main()", 1)[1]
    assert "str_repeat(" not in main_body
    assert "3 * 4" in main_body
