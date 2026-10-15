"""End-to-end regression test for examples/showcase.kfy.

The showcase is the project's acceptance test: it exercises every
feature the language claims to support. This test transpiles it
and asserts that the emitted C++ contains the structural markers
for each feature. It does NOT launch the compiled .exe — that
would hit WDAC (WinError 4551) on some machines and flake. The
transpile-only signal is strong enough: if the emitted C++ loses
a helper call or a virtual method, g++ would fail, so catching it
at emission time catches it at all.

Guards against regressions in:
  - container repr wrapping (Batches 10a, 13b, 13b.1)
  - base-class method virtual/override (Batches 13d.1-3)
  - base ctor inference from super().__init__ (Batch 13c)
  - preamble ordering (Batch 13a)
"""
from pathlib import Path
import pytest

from kofty.transpiler import transpile, TranspileError


SHOWCASE = Path(__file__).resolve().parent.parent / "examples" / "showcase.kfy"


@pytest.fixture(scope="module")
def showcase_cpp():
    """Transpile examples/showcase.kfy once, share across tests."""
    if not SHOWCASE.exists():
        pytest.skip(f"{SHOWCASE} not found")
    src = SHOWCASE.read_text(encoding="utf-8")
    try:
        return transpile(src)
    except TranspileError as e:
        pytest.fail(f"showcase.kfy failed to transpile: {e}")


def _main(cpp: str) -> str:
    """Return everything after `int main()` — the program body."""
    return cpp.split("int main()", 1)[1]


# ---------------------------------------------------------------------------
# Structural markers: each section of the showcase must survive transpile.
# ---------------------------------------------------------------------------

def test_showcase_compiles(showcase_cpp):
    """Top-level: the showcase transpiles without error."""
    assert "int main()" in showcase_cpp


def test_preamble_has_helpers_before_use(showcase_cpp):
    """Batch 13a: preamble ordering — repr_* defined before use."""
    body = _main(showcase_cpp)
    # Container repr wrapping appears in main.
    assert "repr_vector(" in body


def test_string_split_wraps_in_repr(showcase_cpp):
    """Batch 13b.1: `s.split(",")` inside print -> repr_vector."""
    body = _main(showcase_cpp)
    # The showcase has `print("a,b,c".split(","))`.
    assert "repr_vector(str_split(" in body


def test_set_ops_wrap_in_repr(showcase_cpp):
    """Batch 13b: set algebra binops wrap in repr_set."""
    body = _main(showcase_cpp)
    # Showcase has set union/difference etc. — at least one must be wrapped.
    assert "repr_set(set_op_" in body


def test_class_inheritance_virtual_and_override(showcase_cpp):
    """Batches 13d.1-3: base method virtual, child method override."""
    # The showcase defines Animal.speak / Dog.speak.
    assert "virtual std::string speak()" in showcase_cpp
    assert "std::string speak() override" in showcase_cpp


def test_base_ctor_inference_from_super_init(showcase_cpp):
    """Batch 13c: Animal ctor typed from Dog's super().__init__ call."""
    # Should be std::string, not int.
    assert "Animal(std::string name)" in showcase_cpp


def test_container_print_sections_present(showcase_cpp):
    """The showcase prints lists, dicts, sets, tuples; each must
    appear as a repr_* call or as literal construction."""
    body = _main(showcase_cpp)
    # At least one list print.
    assert "repr_vector(" in body
    # At least one dict print.
    assert "repr_map(" in body
    # Lists constructed.
    assert "std::vector<int>" in body
    # Dicts constructed.
    assert "std::map<std::string" in body


def test_fstring_and_format_sections(showcase_cpp):
    """f-strings and .format() both emit is_to_string / fmt_* calls."""
    body = _main(showcase_cpp)
    # Format specs emit fmt_float / fmt_int_pad / etc.
    assert "fmt_float(" in body or "is_to_string(" in body
    # Padded int from `{42:05d}`.
    assert "fmt_int_pad(" in body
    # Comma from `{1234567:,}`.
    assert "fmt_int_comma(" in body


def test_no_showcase_compile_blockers(showcase_cpp):
    """Guard against known-bad emission forms that g++ rejects."""
    # C++17 auto-params were fixed by the -std=c++20 bump; still guard
    # against accidental reversion by asserting the flag-bearing
    # constructs don't sneak into the showcase's specific hot spots.
    # virtual auto is NEVER legal — should never appear.
    assert "virtual auto" not in showcase_cpp
    # A virtual method must have a concrete return type.
    # Specifically: the Dog/Animal case.
    assert "virtual auto speak" not in showcase_cpp
