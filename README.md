# InterScript

A Python-subset language that transpiles to C++ and links against Raylib.
Write simple `.is` files, get native Windows executables.

    foo.kfy  ->  transpiler.py  ->  build/foo.cpp  ->  g++ + raylib  ->  build/foo.exe

## Quick start

    python -m kofty.cli examples\hello.kfy

Or with the batch wrapper:

    interscript examples\hello.kfy

## CLI

    interscript <file.kfy>              # transpile, compile, run
    interscript <file.kfy> --emit-only  # write C++ but do not compile
    interscript <file.kfy> --out <dir>  # output directory (default: build)
    interscript --version

## Requirements

- Python 3.10+
- g++ (MinGW on Windows; MSYS2 UCRT64 works)
- Raylib installed at C:\raylib (override with RAYLIB_INCLUDE / RAYLIB_LIB env vars)

## Tests

    python check.py                    # py_compile every Python file
    python -m pytest tests/ -v         # 165 tests

## Docs

- HANDOFF.md        -- full project state, architecture, current work
- ROADMAP.md        -- auto-generated roadmap (facts from source)
- ROADMAP.manual.md -- human-written notes and plans

## What works

Classes, single and multiple inheritance (diamond rejected), abstract
and static methods, method return annotations, private fields,
pointer lists with ancestor detection, dictionaries, vec2 as
std::pair, lists with iteration and append, tuple unpacking.

See HANDOFF.md section 3 for the complete feature list.

## Examples

`examples/` contains demo programs covering each feature:

- `hello.kfy`             -- minimal raylib window
- `styled_widgets.kfy`    -- OOP widget framework with buttons and labels
- `pong.kfy`, `pong_oop.kfy` -- Pong game (procedural and OOP)
- `target_blaster.kfy`    -- small arcade game
- `inheritance_demo.kfy`  -- single and multiple inheritance
- `dict_demo.kfy`         -- dictionary syntax
- `list_test.kfy`         -- list iteration
- `vec2_test.kfy`         -- vec2 arithmetic

Run any of them with:

    python -m kofty.cli examples\<name>.is
