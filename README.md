<p align="center">
  <img src="kofty.svg" alt="Kofty" width="128">
</p>

# Kofty

A Python-subset language that transpiles to C++ and compiles to a
native executable with plain `g++`. Console programs only.

    foo.kfy  ->  kofty/transpiler.py  ->  build/foo.cpp  ->  g++  ->  build/foo.exe

## Install

    pip install kofty

Or from source:

    git clone https://github.com/sharit25/kofty
    cd kofty
    pip install -e .

Requires Python 3.10+ and a C++20 compiler (GCC 10+ or Clang 16+)
on PATH. On Windows, MSYS2 UCRT64 is the tested toolchain.

## Quick start

    print("Hello, Kofty!")

Save as `hello.kfy`, then:

    kofty hello.kfy

## CLI

    kofty <file.kfy>              # transpile, compile, run
    kofty <file.kfy> --emit-only  # write C++ but do not compile
    kofty <file.kfy> --out <dir>  # output directory (default: build)
    kofty init                    # write .vscode/tasks.json + settings.json
    kofty --version

## Language support

**Types:** `int`, `float`, `str`, `bool`, `None`, `list`, `dict`,
`set`, `tuple`.

**Control flow:** `if` / `elif` / `else`, `while`, `for ... in range`,
`for x in xs`, `break`, `continue`, `for...else`, `enumerate`, `zip`,
`match` / `case`, `try` / `except`.

**Functions:** defaults, `*args`, `**kwargs`, lambdas.

**Classes:** `__init__`, methods, single and multiple inheritance,
`super()`, `@staticmethod`, `@classmethod`, `@abstractmethod`,
`@property` / `@x.setter`, `__eq__`, `__str__`, `__add__`.

**Strings:** `.upper()`, `.lower()`, `.strip()`, `.startswith()`,
`.endswith()`, `.replace()`, `.split()`, `.join()`, `.find()`,
`.count()`, `.title()`, `.capitalize()`, `.isalpha()`, `.isdigit()`.

**f-strings** with format specs: `f"{x:.2f}"`, `f"{n:05d}"`,
`f"{n:x}"`, `f"{big:,}"`, `f"{s:.5s}"`, alignment (`>N`, `<N`, `^N`).

**Module scope:** module-level scalars and containers are visible
inside functions. `global x` for writes. Local assignment shadows.

**Builtins:** `print`, `input`, `str`, `int`, `float`, `bool`, `len`,
`list`, `tuple`, `dict`, `set`, `range`, `enumerate`, `zip`, `vec2`,
`ptr`.

**Standard library (partial):**

- `import math` - `sqrt`, `pow`, `sin`, `cos`, `tan`, `floor`, `ceil`,
  `fabs`, `exp`, `log`, `pi`, `e`
- `import random` - `random()`, `randint(a, b)`, `choice(xs)`,
  `shuffle(xs)`, `seed(n)`
- `import time` - `time()`, `sleep(s)`

## Examples

`examples/showcase.kfy` is the full tour - it exercises every
feature listed above and runs end-to-end.

`examples/console_hello.kfy` is the minimal program.

## Known limitations

- Nested containers in literals (e.g. `[[1, 2], [3, 4]]`) - compile error.
- `type(x)`, `isinstance(x, T)` - rejected by design (static transpiler).
- Complex numbers, bytes, memoryview - not supported.
- List comprehensions - not supported.

See `HANDOFF.md` for the full feature matrix and current state.

## Development

    python check.py                              # parse-check all Python files
    python -m pytest tests/ -q -k "transpile"    # fast, no exe launch
    python -m pytest tests/ -q                   # full suite (slower)

On Windows machines with Application Control policies, freshly-built
executables may be blocked by the OS (`WinError 4551`). The
transpile-only test layer avoids this.

## License

MIT - see [LICENSE](LICENSE).
