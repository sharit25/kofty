## Planned phases

### Phase D2 — Lists
### Phase D1.5 — Class field type inference (✅ COMPLETE)

- Constructor parameter annotations (`: int`, `: float`, `: str`, `: bool`)
  drive both field types and constructor parameter types.
- Field types infer from literal assignments:
  - `self.x = 5` → `int`
  - `self.s = "hi"` → `std::string`
  - `self.p = vec2(...)` → `std::pair<double, double>`
  - `self.l = [1,2,3]` → `std::vector<int>`
- Fallback: unannotated parameters and uninferable fields default to `int`.

### Phase D3a — Single inheritance (✅ COMPLETE)

- `class Child(Parent):` emits `struct Child : Parent { ... };`
- `super().__init__(args)` calls parent constructor via C++
  initializer list: `Child(args) : Parent(parent_args) { ... }`
- `super().__init__()` must be the **first statement** of a subclass `__init__`
- `virtual` emitted on `void` methods (auto-returning methods can't be virtual in C++)
- `override` emitted on child methods that match parent methods
- Inherited fields and methods work through C++ inheritance

**Known limitations:**
- Methods with `auto` return type cannot be `virtual` (would need return
  type annotations — future D3e)
- Multiple inheritance raises a clear error (Phase D3c)
- `super().method()` for non-init methods is Phase D3b

- **D2a.** List literals `[1, 2, 3]` → `std::vector<int>`
- **D2b.** `for x in list` iteration
- **D2c.** `len(xs)`, `xs.append(x)`

### Feature — Dictionaries (✅ COMPLETE — basic)

**Supported:**
- Dict literals: `d = {"name": "Alice", "city": "Paris"}`
- All values must be the same type (int, double, str, bool)
- All keys must be string literals
- Access: `x = d["key"]`
- Update: `d["key"] = new_value`
- Add new key: `d["new_key"] = value`
- Empty dict `{}` errors with a clear message

**Emits:** `std::map<std::string, T>` with all values of type T.

**Not yet supported (future sessions):**
- Iteration: `for k in d.keys()`, `for v in d.values()`
- Nested dicts: `d["a"]["b"]`
- Methods: `.get()`, `.pop()`, `.update()`, `.clear()`
- Non-string keys
- Mixed value types

### Phase D3e — Method return type annotations (✅ COMPLETE)
- Methods can annotate their return type:
  ```python
  def get_value(self) -> int:
      return self.value
### Phase D3b — `super().method()` and class attributes (✅ COMPLETE)

- `super().method(args)` inside a child method emits `Parent::method(args)`
- `super().method()` errors clearly if the parent lacks that method
- Class-level assignments (`count = 0` inside class body) become `static`
  members:
  - `static int count;` inside the struct
  - `int Counter::count = 0;` outside the struct (definition)
  - String class attributes wrap in `std::string(...)` for the definition
- `ClassName.attr` at top level emits `ClassName::attr`

### Phase D3d — Abstract methods and static methods (✅ COMPLETE)

**Abstract methods:**
- `@abstractmethod` on a method with a return annotation:
  ```python
  class Shape:
      @abstractmethod
      def area(self) -> float:
          pass

### Phase D3c — Multiple inheritance (✅ COMPLETE)

- `class Child(Parent1, Parent2):` supported (non-virtual C++ inheritance)
- **Diamond inheritance is rejected** with a clear error. If two parents
  share an ancestor, the transpiler detects it in a post-Pass-1 graph walk.
- **Parent constructors must be called explicitly** as the first N
  statements of `__init__`, in the same order as the base list:
  ```python
  class Duck(Walkable, Swimmable):
      def __init__(self, name: str, depth: int):
          Walkable.__init__(self, name)
          Swimmable.__init__(self, depth)

### Phase D4 — Dictionaries
- `{"key": value}` → `std::map`

### Phase E — Control flow
- `match` / `switch`

### Phase F — String functions
- `len()`, substring, string methods

### Phase G — Editor experience
- Proper `.is` package + Pylance stubs (removes `# pyright` pragma)

## Long-term goal: Godot-style game framework

A small game framework with:
1. **`vec2`** ✅ (done)
2. **Class field type inference** — allow fields of type `std::string`, `std::pair`, etc.
3. **Operator overloading** — `pos + vel`, `vel * dt`
4. **Lists** — iterate over entities
5. **Node base class** — `start()`, `update(dt)`, `draw()`
6. **Collision system** — engine-level collision
7. **Scene tree** — parent/child nodes

## Known limitations

- Class fields are always `int`. Tuples and strings in fields don't work.
- No lists, dicts, or `for x in xs` iteration.
- No inheritance or callbacks.
- Type tracking is limited — the transpiler doesn't know variable types.
- No imports; every program is a single file.
- Windows only — no Linux/macOS/Android export.
- No debugger beyond `print()`.
- Console input (`input()`) not implemented.

## Development workflow

Every feature follows this cycle:

1. **Write tests** in `tests/test_transpiler.py` describing new behavior.
2. **Run** `python check.py` → must say "parse cleanly".
3. **Run** `python -m pytest tests/ -v` → new tests should FAIL.
4. **Implement** in `kofty/transpiler.py`.
5. **Run** `python check.py` again → must be clean.
6. **Run** pytest → all tests should PASS.
7. **Verify end-to-end** with an `examples/*.is` demo.
8. **Back up** before the next feature.

## Backup locations

Check `%USERPROFILE%\InterScript_backup_*.zip` for the latest backup.

## Lessons learned

- **VS Code auto-indent can corrupt pastes.** Always run `python check.py`
  after any file edit. Create files with `code <full-path>`, not the
  Explorer's New File button.
- **C++ "most vexing parse":** `Ball ball();` declares a function.
  Use brace init `Ball ball{};` — the transpiler already does.
- **Raylib's `DrawText` needs `const char*`.** The transpiler wraps
  non-literal string args in `std::string(...).c_str()`.
- **`auto` can't be used for struct members.** Class fields are `int`
  for now.
- **Declare variables before using them.** C++ requires declaration
  before use; the transpiler preserves source order.
- **`Expand-Archive -Force`** overwrites matching files but does not
  delete extra files. Always back up before restoring.

# Kofty — Manual Roadmap

Long-term direction, updated by hand. For the auto-generated batch
history, see `ROADMAP.md`. For current bugs, see `BUGS.md`.

## Immediate (next 2–3 sessions)

**Fix the seven bugs in `BUGS.md`.** In priority order:

1. **13a — Bug #1** (is_to_string overload ordering).
2. **13d — Bug #4** (`*args` / `**kwargs` call-site regression).
3. **`kofty --check` CLI flag** — enables compile-only test tier
   without needing WDAC workaround.
4. **13c — Bug #3** (loop variable scoping).
5. **13b, 13f, 13e, 13g** — the remaining bugs.

When all seven are fixed, `examples/showcase.kfy` compiles and
runs end-to-end.

## Next (after the bug fixes)

**Release 0.1.0.**

- GitHub Actions CI: run `kofty --check` on every `.kfy` file in
  `examples/` on every push.
- Publish to PyPI: `pip install kofty` works for anyone.
- Version bump, tag, GitHub release.

This is the milestone that turns Kofty from "a repo on my machine"
into "a published language."

## Then

**Structural fix: programmatic preamble.** See `ARCHITECTURE.md`
Part 4, Fix 1. Replace the hand-ordered list of preamble chunks
with a dependency graph. Makes Bug #1 (and its class) structurally
impossible.

**Test tier upgrade: compile-and-run.** Once CI exists and runs on
Linux (no WDAC), enable the runtime test tier again. Bring back the
465 runtime tests that are currently unusable on the dev machine.

## Long-term (post-1.0)

Features that are deferred but wanted:

- **Nested containers, deep.** List of lists, dict of dicts, 3+
  levels. Currently only 2 levels work.
- **Chained subscript:** `xs[0][0]`.
- **List comprehensions.**
- **`import json`.**
- **`datetime` module.**
- **Real module system** — `import x as y`, `from x import y`.
  Currently `math` / `random` / `time` are three hardcoded names.
- **Empty container literals:** `xs = []`, `d = {}`. Requires type
  annotation or deferred type check.
- **First-class functions:** passing a function as an argument.
  `def apply(f, x): return f(x)` currently fails.
- **Exception hierarchy:** custom exception classes, typed
  `except ValueError:`.

## Won't do

- GUI / graphics. Kofty is a console language. Raylib support was
  removed in the InterScript → Kofty rename.
- Python compatibility at the library level. Kofty implements a
  subset of Python syntax and semantics, not the CPython API.
- Garbage collection. C++ RAII is the memory model.
- Async / await.

## Design principles

1. **Console-only.** No GUI, no graphics.
2. **Subset, not superset.** If Python doesn't do it, Kofty doesn't
   either — unless there's a strong C++-idiomatic reason.
3. **Fail at transpile time when possible.** Prefer
   `TranspileError` with a clear message over a confusing g++
   error. This is aspirational; Bug #7 violates it today.
4. **Integration tests are the contract.** A feature is not done
   when its unit test passes; it's done when it appears in a real
   program that compiles and runs.
5. **One bug, one batch.** No combining unrelated fixes. Serial
   verification catches interactions.
