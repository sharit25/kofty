
---

## 2 — Save as `C:\InterScript-Language\SHOWCASE_STATUS.md`

```markdown
# Showcase status

`examples/showcase.kfy` is the **aspirational** end-to-end test for
Kofty. It exercises every feature the language claims to support,
in one file.

**It does not compile yet.** Seven bugs block it — see `BUGS.md`.

## What "aspirational" means here

The showcase is written as if the language worked fully. It is
*not* doctored to avoid the broken features. When the seven bugs
in `BUGS.md` are fixed, the showcase should compile and run
end-to-end without changes.

Until then, running `kofty showcase.kfy` will fail at the first
broken feature it hits. The failure is the to-do list.

## What the current demo does

`examples/vscode_demo.kfy` is the *running* demo. It exercises a
subset of Kofty's features that are known to work end-to-end.
It's the file to show someone who wants to see Kofty run today.

## Status of the seven blockers

| # | Feature | Blocks |
|---|---------|--------|
| 1 | `is_to_string` container overload ordering | `print(xs)` where `xs` is nested |
| 2 | `_container_repr` for binops / calls / slices | `print(a + b)`, `print(s1 \| s2)`, `print(xs[1:4])` |
| 3 | Loop variable leakage into `declared` | reusing a variable name for a loop and a plain var |
| 4 | `*args` / `**kwargs` call-site wrapping | `sum_all(1, 2, 3)` |
| 5 | Variable redeclaration with different type | `d = {}; ...; d = SomeClass()` |
| 6 | List methods on function parameters | `def f(xs): xs.pop()` |
| 7 | Unannotated ctor param type inference | `class C: def __init__(self, name): ...` with string call site |

## Suggested workflow

1. Fix Bug #1 (Batch 13a).
2. Run `kofty showcase.kfy`; it will fail at the next bug.
3. Fix that bug (13b, 13c, ...).
4. Repeat until it runs.
5. Move the aspirational showcase into a CI test tier that
   compiles and runs it.

## Do not "fix" the showcase by removing features

The temptation when a section fails is to comment out the broken
line. **Don't.** The showcase is the contract — it says what Kofty
is supposed to do. Every time we strip a feature to make it run,
we lose the reminder that the feature is broken.

If you need a *runnable* demo, extend `examples/vscode_demo.kfy`
or write a second file. Keep the showcase aspirational.
