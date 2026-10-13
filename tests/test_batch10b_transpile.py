"""tests/test_batch10b_transpile.py

Batch 10b: bounds checking on vec_pop / vec_pop_at.

The transpiled C++ now throws std::out_of_range on:
    xs.pop()   when xs is empty
    xs.pop(i)  when i is out of range (after negative normalization)

Tests inspect the emitted preamble for the bounds checks, and check
that .pop() / .pop(i) call sites still emit the helpers. Runtime
verification of the throw itself is blocked by WDAC on this machine
(see HANDOFF section 19).

Transpile-only. No exe launch. Zero flake.
"""

from kofty.transpiler import transpile


# ===========================================================================
# Preamble carries the bounds checks
# ===========================================================================

def test_vec_pop_preamble_has_empty_check():
    out = transpile('xs = [1, 2, 3]\nxs.pop()\n')
    # The helper must guard against empty vectors.
    assert "v.empty()" in out
    assert "out_of_range" in out


def test_vec_pop_at_preamble_has_range_check():
    out = transpile('xs = [1, 2, 3]\nxs.pop(0)\n')
    # The helper must guard against out-of-range index.
    assert "i < 0 || i >=" in out or "i >= (int)v.size()" in out
    assert "out_of_range" in out


def test_vec_pop_at_normalizes_negative():
    out = transpile('xs = [1, 2, 3]\nxs.pop(-1)\n')
    # The negative-index normalization must still be present.
    assert "i += (int)v.size()" in out


# ===========================================================================
# Call sites still emit the helpers
# ===========================================================================

def test_pop_no_args_still_emits_vec_pop():
    out = transpile('xs = [1, 2, 3]\nxs.pop()\n')
    assert "vec_pop(xs)" in out


def test_pop_index_still_emits_vec_pop_at():
    out = transpile('xs = [1, 2, 3]\nxs.pop(0)\n')
    assert "vec_pop_at(xs, 0)" in out


def test_pop_negative_index_still_emits_vec_pop_at():
    out = transpile('xs = [1, 2, 3]\nxs.pop(-1)\n')
    assert "vec_pop_at(xs, (-1))" in out


def test_pop_result_assigned_still_works():
    out = transpile('xs = [1, 2, 3]\nx = xs.pop()\nprint(x)\n')
    assert "vec_pop(xs)" in out


def test_pop_in_expression_still_works():
    out = transpile('xs = [1, 2, 3]\nprint(xs.pop())\n')
    assert "vec_pop(xs)" in out


# ===========================================================================
# Error message wording
# ===========================================================================

def test_pop_error_message_mentions_empty():
    out = transpile('xs = [1, 2, 3]\nxs.pop()\n')
    assert "empty" in out


def test_pop_at_error_message_mentions_out_of_range():
    out = transpile('xs = [1, 2, 3]\nxs.pop(0)\n')
    assert "out of range" in out


# ===========================================================================
# Still rejects 2+ args at transpile time (Batch 8g behavior preserved)
# ===========================================================================

def test_pop_too_many_args_still_rejected():
    import pytest
    from kofty.transpiler import TranspileError
    with pytest.raises(TranspileError):
        transpile('xs = [1, 2, 3]\nxs.pop(0, 1)\n')
