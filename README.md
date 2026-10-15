Set-Location C:\InterScript-Language
$readme = @'
<p align="center">
  <img src="kofty.svg" alt="Kofty" width="128">
</p>
# Kofty

A Python-subset language that transpiles to C++ and compiles to a
native executable with plain `g++`. Console programs only — no GUI,
no Raylib.

    foo.kfy  ->  kofty/transpiler.py  ->  build/foo.cpp  ->  g++  ->  build/foo.exe
                   (Python AST -> C++ strings)

Kofty is a small, expressive language: everything Python-ish you'd
want for a console program — functions, classes, lists, dicts, sets,
tuples, f-strings with format specs, match/case, exceptions, and more
— but the output is a standalone native binary.

## Install

    pip install kofty

Or from source (development mode):

    git clone https://github.com/sharit25/kofty
    cd kofty
    pip install -e .

## Quick start

Create `hello.kfy`:

    print("Hello, world!")

Compile and run:

    kofty hello.kfy

Output:

    Hello, world!

## CLI

    kofty <file.kfy>              # transpile, compile, run
    kofty <file.kfy> --emit-only  # write C++ but do not compile
    kofty <file.kfy> --out <dir>  # output directory (default: build)
    kofty --version

## What Kofty supports

**Types:** `int`, `float`, `str`, `bool`, `None` (via `std::optional`),
plus `list`, `dict`, `set`, `tuple`.

**Control flow:** `if` / `elif` / `else`, `while`, `for i in range(N)`,
`for x in xs`, `break`, `continue`, `pass`, `for...else`.

**Comprehensions of iteration:** `enumerate`, `zip`.

**Pattern matching:** `match` / `case` with literal patterns.

**Exceptions:** `raise`, `try` / `except` (catch-all).

**Functions:** default args, `*args`, `**kwargs`, lambdas.

**Classes:** `__init__`, methods, field inference, single and multiple
inheritance, `super()`, `@staticmethod`, `@abstractmethod`,
`@classmethod`, `@property` / `@x.setter`, `__eq__`, `__str__`,
`__add__`.

**Strings:** `.upper()`, `.lower()`, `.strip()` / `.lstrip()` /
`.rstrip()`, `.startswith()` / `.endswith()`, `.replace()`, `.split()`,
`.join()`, `.find()`, `.count()`, `.title()`, `.capitalize()`,
`.isalpha()`, `.isdigit()`.

**f-strings** with format specs: `f"{x:.2f}"`, `f"{n:05d}"`,
`f"{n:x}"`, `f"{big:,}"`, `f"{s:.5s}"`, alignment (`>N`, `<N`, `^N`).

**Standard library (partial):**

- `import math` — `sqrt`, `pow`, `sin`, `cos`, `tan`, `floor`, `ceil`,
  `fabs`, `exp`, `log`, `pi`, `e`
- `import random` — `random()`, `randint(a, b)`, `choice(xs)`,
  `shuffle(xs)`, `seed(n)`
- `import time` — `time()`, `sleep(s)`

**Containers:** full list/dict/set/tuple support — indexing (including
negative), slicing, iteration, and common methods.

See [ROADMAP.md](ROADMAP.md) for the full feature matrix and what's
still missing.

## Requirements

- Python 3.10+
- A C++17 compiler on PATH — MinGW `g++` on Windows works well
  (MSYS2 UCRT64 is what we test on)

## Examples

See the `examples/` directory. A few highlights:

- `console_hello.kfy` — the minimal program
- `oop_complete.kfy` — full class hierarchy demo
- `fstring_advanced.kfy` — format spec showcase
- `print_container.kfy` — printing lists, dicts, sets, tuples

## Development

    python check.py                              # syntax check
    python -m pytest tests/ -q -k "transpile"    # fast, no exe launch
    python -m pytest tests/ -q                   # full suite (slower)

Note: on Windows machines with Application Control policies enabled,
launching freshly-built executables may be blocked by the OS
(`WinError 4551`). The transpile-only test layer avoids this.

## License

MIT — see [LICENSE](LICENSE).
'@

[System.IO.File]::WriteAllText("$PWD\README.md", $readme, (New-Object System.Text.UTF8Encoding $false))
Write-Host "README.md replaced."

# Kofty

A small Python-subset language that compiles to C++ and runs on
the command line. Write `.kfy` files; get native executables.

    print("Hello, Kofty!")

## Install

    pip install kofty

Until Kofty is published on PyPI, install from source:

    git clone https://github.com/sharit25/kofty
    cd kofty
    pip install -e .

Requires Python 3.11+ and `g++` on PATH.

## Quick start

    mkdir myproject && cd myproject
    kofty init
    # Write hello.kfy in your editor
    kofty hello.kfy

`kofty init` writes VS Code project files so `Ctrl+Shift+B` builds
and runs the focused `.kfy` file.

## What works

See `examples/showcase.kfy` for a tour of every feature the
language supports. Note: the showcase is currently **aspirational**
— it exercises the full intended feature set, some of which isn't
implemented or has bugs. See `BUGS.md` for the exact list and
`SHOWCASE_STATUS.md` for the workflow.

For a demo that runs today, see `examples/vscode_demo.kfy`.

Highlights that work right now:

- ints, floats, strings, bools, None
- lists, dicts, sets, tuples, unpacking
- `for`/`while`/`break`/`continue`, `for...else`
- `enumerate`, `zip`
- classes with `__init__`, methods, `__str__`, `__eq__`, `__add__`
- `@property` / `@x.setter`, `@classmethod`, `@staticmethod`
- inheritance and `super()`
- f-strings with format specs, `.format()`
- `match`/`case`, `try`/`except`
- `import math`, `import random`, `import time`
- `input()` for console I/O

## What doesn't work yet

See `BUGS.md` for the current list. Highlights:

- nested containers in `print()` (compile error — Bug #1)
- `print()` on an expression that returns a container (Bug #2)
- reusing a variable name for a loop and a plain assignment (Bug #3)
- `*args` / `**kwargs` at call sites (Bug #4)
- variable redeclaration with a different type (Bug #5)
- list methods on function parameters (Bug #6)
- unannotated constructor parameters holding strings (Bug #7)

## Documentation

- `HANDOFF.md` — full session journal, current state, how to resume.
- `ARCHITECTURE.md` — how the emitter works, why the test suite
  misses certain bugs.
- `BUGS.md` — known bugs and gaps.
- `SHOWCASE_STATUS.md` — status of the aspirational showcase.
- `ROADMAP.manual.md` — long-term direction.

## Development

    python check.py                       # parse all Python files
    python -m pytest tests/ -q -k "transpile"   # fast test layer
    python generate_roadmap.py            # regenerate ROADMAP.md

The full suite (`python -m pytest tests/ -q`) includes runtime
tests that compile and execute `.exe` files. On some Windows
machines, WDAC blocks freshly-built executables (`WinError 4551`).
See `ARCHITECTURE.md` §"The test model".

## License

MIT.
