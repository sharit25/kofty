# Kofty — Architecture and testing model

A short document explaining how the transpiler is structured, why
the current test suite misses certain classes of bugs, and what
would need to change to make "the language works" a verifiable
claim.

---

## Part 1 — How the emitter is structured

`kofty/transpiler.py` emits three sections into every `.cpp` file:

### Section A — The preamble

A fixed list of C++ helper declarations and definitions, in a
hard-coded order. Includes:

1. `#include` lines (`<string>`, `<iostream>`, `<vector>`, ...).
2. Scalar helpers: `format_float`, string methods (`str_toupper`,
   `str_strip`, ...).
3. Scalar `is_to_string` overloads (string, char*, int, double, bool).
4. Preamble templates that call `is_to_string`: `repr_vector`,
   `repr_map`, `repr_set`, `repr_pair`, `repr_tuple`.
5. Container `is_to_string` overloads (added Batch 10h) — these
   *should* go before #4 but currently don't (Bug #1).
6. Container helpers: `vec_pop`, `vec_concat`, `set_op_*`, `dict_pop`.
7. Format-spec helpers for f-strings: `fmt_float`, `fmt_int_pad`,
   `fmt_align`, ...
8. `input_line` (Batch 12).
9. `repr_*` for structured output.

The order is a Python list of one-line strings, edited by hand.
It has never been validated against C++ overload-resolution rules.

### Section B — User classes and functions

Emitted in order of appearance. Each `class Foo` becomes
`struct Foo { ... };`. Each top-level `def f()` becomes a free
function. Class field initialization, method dispatch, property
getters/setters, and inheritance all compile down to C++
constructs at this stage.

### Section C — `main()`

The top-level statements of the `.kfy` file become the body of
`int main()`. Variable declarations, control flow, calls to
user functions and preamble helpers all appear here.

### What the emitter tracks

Per-scope, in instance dictionaries on the `CppEmitter` object:

- `list_vars: dict[name, elem_type]` — names that are `std::vector<T>`.
- `dict_vars: dict[name, value_type]` — names that are `std::map<K,V>`.
- `set_vars: dict[name, elem_type]` — names that are `std::set<T>`.
- `tuple_vars: dict[name, arity]` — names that are `std::pair` or
  `std::tuple`.
- `instance_vars: dict[name, class_name]` — names that hold a user
  class instance.
- `pointer_vars: set[name]` — names that hold a raw pointer.
- `declared: set[name]` — everything declared so far in `main()`.
- `optional_vars: dict[name, T]` — names that are `std::optional<T>`.

Bug #3 comes from `declared` being a flat set that spans the whole
`main()`, mixing scopes.

---

## Part 2 — The test model

### Two tiers currently

1. **Runtime tests** (`tests/test_<feature>.py`) — use `subprocess`
   to invoke the compiled `.exe` and check stdout. Historically the
   primary tier. **Currently unusable on the development machine**
   because Windows Defender Application Control (WDAC) blocks every
   freshly-built unsigned `.exe` with `WinError 4551`.

2. **Transpile-only tests** (`tests/test_<feature>_transpile.py`) —
   call `transpile(src)` and assert on the returned C++ string.
   Introduced in Batch 8h as a workaround for the WDAC block.
   Current count: 575 tests, ~10 seconds, zero flake on this
   machine.

### What transpile-only tests can't catch

- **C++ overload-resolution failures.** Bug #1.
- **Name collisions across sections.** Bug #5.
- **Order-dependent scope issues.** Bug #3.
- **Regressions in transitive dependencies.** Bug #4 — the tests
  for `*args` still assert on the function signature containing
  `std::vector<int>`; they pass because the signature is correct
  even though the call site isn't.
- **Compile-time type mismatches.** Bugs #6, #7.

In short: **the entire compile-time class of bugs is invisible.**

### What a real test tier would look like

Three tiers, all required:

- **Tier 1 — Transpile-only.** Assert on emitted C++ shape. Fast,
  no compilation. Keeps parity tests cheap.
- **Tier 2 — Compile-only.** `transpile` → write `.cpp` → `g++
  -c -fsyntax-only`. Catches every bug in this session's list
  except Bug #2 (which needs the actual link + run to manifest).
- **Tier 3 — Compile-and-run.** `transpile` → write `.cpp` → `g++
  -o exe` → run → check stdout. Catches semantic bugs and
  regressions.

Tier 3 is blocked by WDAC on this machine. It works on Linux CI
(GitHub Actions Ubuntu runner).

---

## Part 3 — Why this session revealed seven bugs

The showcase was the first nontrivial program attempted since
`vscode_demo.kfy`, which was written six batches ago. Every
subsequent batch added features and tests but never tried to
*compose* them into a real program.

Individual feature tests check that each feature emits the right
C++ for *its own minimal case*. They don't check:

- Whether that C++ is *valid* in a larger file (ordering, overloads).
- Whether two features *interact* correctly (name reuse, type
  inference cascading).
- Whether earlier features *still work* (regressions).

The showcase is the first integration test the project has had.
It found seven bugs in one file.

**This is normal for a project at this maturity level.** Feature
development outpaces integration testing. The showcase marks the
transition to a phase where integration testing is the primary
signal.

---

## Part 4 — Structural fixes

Three changes would prevent the class of bugs we just hit.

### Fix 1 — Emit the preamble programmatically, not as a list

Replace the hard-coded list of preamble strings with a set of
named chunks and a declared dependency graph. Each chunk declares
what it needs (e.g., "repr_vector requires is_to_string overloads
for its element types"). The emitter topologically sorts the chunks
and emits them in dependency order.

This makes Bug #1 structurally impossible.

Effort: moderate. Maybe a session to design, a session to
implement, a session to migrate every helper into a chunk.

### Fix 2 — Add a `--check` flag to the CLI

`kofty foo.kfy --check` transpiles, writes the `.cpp` to a temp
file, and runs `g++ -fsyntax-only`. Returns 0 if the file parses.
Doesn't need to link or run — so it's not blocked by WDAC.

This would have caught Bugs #1, #4, #5, #6, #7 in transpile-time CI.

Effort: small. Maybe an hour.

### Fix 3 — Move integration tests into CI

Once `--check` exists, add a pytest that runs it over every file
in `examples/`. `showcase.kfy` failing `--check` would fail CI.
Fixing CI requires either:
- Publishing to GitHub and using GitHub Actions' Ubuntu runner (no
  WDAC there). This is what Release 0.1.0 is for.
- Or finding a Docker workaround on Windows.

Effort: small once CI exists. The CI itself is the bigger task.

---

## Part 5 — What to do next

Priority order:

1. **Batch 13a — fix Bug #1.** Reorder the preamble so container
   `is_to_string` overloads come before the `repr_*` templates.
   Small, self-contained, verifiable.

2. **Batch 13d — fix Bug #4.** Restore `*args` / `**kwargs`
   wrapping. Bisect to find the regression.

3. **`kofty --check` flag.** Small effort, huge return. Unlocks a
   new test tier without solving WDAC.

4. **Batch 13c — fix Bug #3.** Loop variable scoping.

5. Remaining bugs in priority order: #2, #6, #5, #7.

6. **Release 0.1.0 — GitHub Actions CI.** Once CI runs `--check`
   on `examples/showcase.kfy`, no new bug of the class found today
   can ship undetected.

7. **Preamble refactor (Fix 1).** Long-term structural fix. Worth
   doing once the easy wins are in.

The showcase stops being aspirational when items 1–6 are done.
