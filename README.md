Set-Location C:\InterScript-Language
$readme = @'
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
