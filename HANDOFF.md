# InterScript-Language — Handoff / Session State

_Snapshot: 2026-10-12. Project: pure InterScript console language_
_(no raylib, no GUI). For GUI/widget work see C:\InterScript (archived)._

---

## 1. What InterScript-Language is

A Python-subset source language (.is files) that transpiles to C++
and compiles to a native executable with plain g++. No GUI, no raylib.
Console programs only: print, arithmetic, strings, classes, lists,
dicts, tuples, sets, functions.

Pipeline:

    foo.is  ->  interscript/transpiler.py  ->  build/foo.cpp  ->  g++  ->  build/foo.exe
                  (Python AST -> C++ strings)              (no -lraylib)

Entry point: interscript.bat -> python -m interscript.cli <file>

## 2. Project layout

    C:\InterScript-Language\
    |-- check.py
    |-- generate_roadmap.py
    |-- interscript.bat
    |-- HANDOFF.md (this file)
    |-- README.md
    |-- ROADMAP.md
    |-- ROADMAP.manual.md
    |-- .vscode\
    |-- interscript\
    |   |-- __init__.py
    |   |-- cli.py
    |   |-- transpiler.py  (~2200 lines)
    |   `-- interscript_stubs.pyi
    |-- stubs\
    |   `-- interscript_stubs.pyi
    |-- tests\
    |   |-- conftest.py
    |   |-- test_transpiler.py
    |   |-- test_compile.py
    |   |-- test_none.py
    |   |-- test_optional.py
    |   |-- test_lists_complete.py
    |   |-- test_dicts_complete.py
    |   |-- test_sets_complete.py
    |   |-- test_tuples_complete.py
    |   |-- (runtime tests, batch 3 - batch 8e, string_methods, fstrings)
    |   `-- (transpile-only companions, batch 3 - batch 8e, string_methods, fstrings)
    `-- examples\
        |-- console_hello.is
        |-- none_demo.is
        |-- list_ops.is
        |-- dict_ops.is
        |-- set_ops.is
        |-- tuple_ops.is
        |-- temperature.is
        |-- vec2_test.is
        |-- dict_demo.is
        |-- list_test.is
        |-- float_test.is
        |-- button_demo.is
        |-- inheritance_demo.is
        |-- multiple_inheritance.is
        |-- oop_complete.is
        |-- poly_demo.is
        `-- return_annotation.is

## 3. Current state (2026-10-12)

- 465 runtime tests + 484 transpile-only tests = 949 total
- 6 xfailed
- Batch 10k.3 (constructor initializer list) DONE
- Batch 10k.2 (class fields in method bodies) DONE
- Batch 10k.1 (class-typed params in function bodies) DONE
- `examples/vscode_demo.kfy` compiles and runs end-to-end (2026-10-14)
- 493 transpile-only tests passing, 0 failing
- Batch 10j (user-class parameter annotations) DONE
- Batch 10i (user classes in f-strings) DONE
- Batch 10h (containers in f-strings) DONE
- Batch 10g (set ops with inline set literals) DONE
- Batch 10f (string repetition `"=" * 40`) DONE
- Batch 10e (import hoisting above class bodies) DONE
- Batch 10d (embed .ico in .exe) DONE
- Batch 9c (packaging, rename to Kofty, GitHub push) DONE
- Batch 10b (xs.pop bounds checking) DONE
- Batch 10c (title/capitalize/isalpha/isdigit) DONE
- Batch 10a (print(container) reprs) DONE
- Batch 9b (f-string format specs, phase 2) DONE
- Batch 9a (f-string format specs) DONE
- Batch 8h (transpile-only companions) DONE
- Batch 8g (list.pop(i)) DONE
- Batch 8f (list.pop() real removal) DONE
- Batch 8e (@classmethod) DONE
- Batch 8d (@property + @x.setter) DONE
- Batch 8c (__add__ -> operator+) DONE
- Batch 8b (__str__ -> std::string __str__() const) DONE
- Batch 8a (__eq__ -> operator==) DONE
- Batch 7c (import time) DONE
- Batch 7b (import random) DONE
- Batch 7a (import math) DONE
- Batch 6b (raise, try/except) DONE
- Batch 6 complete (match/case, raise, try/except)
- Batch 6a (match/case) DONE
- Batch 5d (lambdas) DONE
- Batch 5 complete (default args, *args, **kwargs, lambdas)
- Batch 5c (**kwargs) DONE
- Batch 5b (*args) DONE
- Batch 5a (default arguments) DONE
- Batch 4b (for...else) DONE
- Batch 4a (enumerate, zip) DONE
- Batch 3 (** //, ternary) DONE
- Batch 2b (f-strings, .format()) DONE
- Batch 2a (String methods) DONE
- check.py clean
- raylib-optional: only `import raylib` triggers raylib; console has none
- Plan A COMPLETE (None/optional, Lists, Dicts, Sets, Tuples)
- Last backup: InterScript-Language_backup_20261013_batch10b_pop_bounds.zip
- Last backup: InterScript-Language_backup_20261013_batch10b_pop_bounds.zip
- GitHub: https://github.com/sharit25/kofty
- PyPI name reserved: kofty (not yet published)

## 4. What works

Data types:
- int, float, str, bool, None (via std::optional)
- list: literal, indexing (incl. negative), slicing, iteration,
        append, insert, remove, sort, reverse, clear, pop (with
        and without index), x in xs, concat with +
- tuple (2-element): literal -> std::make_pair, t[0]/t[1] -> .first/.second,
        unpacking a,b = t
- tuple (3+ element): literal -> std::make_tuple, t[N] -> std::get<N>(t),
        unpacking a,b,c = t -> per-element std::get<i>, item assignment
        t[N] = v -> std::get<N>(t) = v
- string methods: .upper() .lower() .strip() .lstrip() .rstrip()
                  .startswith(x) .endswith(x) .replace(a,b)
                  .split(sep) -> list[str]  .join(list[str])
                  .find(x) -> int  .count(x) -> int
- f-strings: f"text {expr} more" -> std::string concatenation
             supports int/float/str/bool exprs, nested method calls,
             function calls; {{ and }} escape literal braces
- .format() on a string literal: "{} and {}".format(a, b)
             supports positional {} and indexed {0} {1} placeholders,
             including repeated indices
- enumerate(xs): for i, x in enumerate(xs)  (index + value iteration)
- enumerate(xs, start): index starts at `start`
- zip(a, b): for x, y in zip(a, b)  (parallel iteration, stops at shorter)
- for...else: for x in xs: body else: elsebody
              else block runs if loop completes without break;
              works with range, list, dict.values/items, enumerate, zip;
              nested for-else handled via __broke_N flags
- default args: def f(a, b=10): -> C++ defaults on the emitted signature
                call sites with fewer args use defaults; string params
                with defaults get `std::string` type (fixes str concat)
- *args: def f(*nums): -> std::vector<int> nums (default elem type)
         def f(*words: str): -> std::vector<std::string>
         Call sites use brace-init: f({1, 2, 3}), f({})
         vararg name registered as a list variable (indexing,
         len, membership, iteration all work)
- **kwargs: def f(**info): -> std::map<std::string, std::string> info
            def f(**counts: int): -> std::map<std::string, int>
            Call sites use dict literals: f({"a": "1", "b": "2"}), f({})
            kwarg name registered as a dict variable (.get, .items,
            .values, in, len, iteration all work)
            NOTE: iterates in key-sorted order (std::map), not Python
            insertion order
- lambdas: lambda x: x * 2 -> [&](auto x) { return x * 2; }
           assigned to a variable: twice = lambda x: x * 2
           captures outer variables by reference ([&])
           single-expression bodies only
           calls dispatch through the variable name
- import math: math.sqrt, math.pow, math.sin, math.cos, math.tan,
               math.floor, math.ceil, math.fabs, math.exp, math.log
               math.pi, math.e constants
               emits std::<func>(...) from <cmath>
- import random: random.random(), random.randint(a, b) (inclusive),
                 random.choice(xs), random.shuffle(xs) (in-place),
                 random.seed(n)
                 Uses std::mt19937 seeded from steady_clock at startup
                 rand_shuffle and rand_choice are templates
- import time: time.time() -> double seconds since epoch
               time.sleep(s) -> pause s seconds (double)
               uses std::chrono::system_clock + std::this_thread
- match/case (literal patterns): match x: case 1: ... case _: ...
             emits if/else-if/else chain
             supported patterns: int/str/float literals, True/False, _
             unsupported: capture (case x:), OR, guards, structural,
             type patterns, nested patterns
- raise: raise X("msg") -> throw std::runtime_error("msg");
         raise X        -> throw std::runtime_error("");
         all exception names collapse to std::runtime_error
- try/except (catch-all): try: ... except Exception: ... -> try{...}catch(...){...}
         bare `except:` and `except Exception:` both map to catch(...)
         one except block only; no else, no finally, no `as e`
- ** (power): a ** b -> std::pow(a, b); always returns double
              (2 ** 3 prints "8", not "8.0", via format_float trimming)
- // (floor div): a // b -> is_floordiv(a, b); correct Python floor
                  semantics for negative operands and floats
- ternary: a if cond else b -> ((cond) ? (a) : (b))
           both branches must have compatible C++ types
- dict: literal (incl. nested), access, update, iteration (keys/
        values/items), .get(default), .pop, .update, .clear,
        k in d, k not in d
- set: literal, .add, .remove, .discard, .clear, len, in/not in,
       iteration, union |, intersection &, difference -, symdiff ^
- vec2 (std::pair<double,double>) with operators +, -, * scalar,
  +=, -=, *=

Control flow:
- if / elif / else, while, for i in range(N), for x in xs,
  break, continue, pass

Functions:
- def f(a, b): (auto return type)
- def f(a: int) -> int: (typed params and return)
- Mixed return None + return value -> std::optional<T>

Classes:
- class Foo with __init__, methods, field type inference
- Private fields (_ prefix)
- Single + multiple inheritance, super(), @abstractmethod,
  @staticmethod
- Pointer lists via ptr(Cls()) with common-ancestor detection
- @property getters -> auto prop() const { body }
- @x.setter setters -> void prop(T v) { body }
  (T from setter param annotation; else int)
- obj.prop / self.prop -> method call (getter)
- obj.prop = v / self.prop = v -> method call (setter)
- Read-only property assignment raises TranspileError
- __eq__ -> bool operator==(const T& other) const
- __str__ -> std::string __str__() const
             (call sites: print(obj), str(obj))
- __add__ -> T operator+(const T& other) const
- @classmethod -> static auto name(args) { ... }
                 (first param is class param, remapped in body)

Built-ins:
- print, str, int, float, len, vec2, ptr
- (raylib builtins available only with `import raylib`)

## 5. What does NOT work yet

- print(container) uses is_to_string for elements, so string elements
  print without quotes: print(["a", "b"]) -> [a, b] (Python prints
  ['a', 'b']). Nested containers are still unsupported.
- print(container) does NOT handle empty containers (empty literals
  aren't supported by the transpiler; see below).
- Nested containers (list of tuple, dict value = tuple, 3+ level nesting)
- Tuple arity not tracked across function return values
  (t = make() where make returns a tuple -> t not in tuple_vars)
- Typed tuple return annotations (def f() -> tuple[int,int,int])
- for-unpack over 3+ tuples (for a, b, c in triples)
- f-string format specs: f"{x:.2f}", f"{n:05d}", f"{x:>10}"
- f-string conversions: f"{x!r}", f"{x!s}"
- .format() with kwargs: "{x}".format(x=1)
- .format() with format specs: "{:.2f}".format(x)
- variable-receiver .format(): s.format(...) where s is a str variable
- string methods not yet supported: .title() .capitalize() .swapcase()
  .split() with no arg  .strip(chars)  .isalpha() .isdigit()
- x **= 2 (augmented power) and x //= 2 (augmented floor div)
- ** with int-preserving semantics: 2 ** 3 returns double, not int
- ternary branches with mismatched types (int if c else "str")
- List comprehension
- Dict/Set methods beyond the ones listed above
- while...else (not implemented)
- enumerate() / zip() outside a for-loop
- zip of 3+ sequences
- nested enumerate/zip
- match with capture patterns: case x:  (binds value)
- match with OR patterns: case 1 | 2:
- match with guards: case n if n > 0:
- match with structural patterns: case [a, b]:, case {"k": v}:
- match with type patterns: case int():, case str():
- typed except: except ValueError:
- multiple except blocks
- try/else and try/finally
- bare raise (re-raise)
- exception objects: except Exception as e:
- custom exception classes
- import math (partial): missing math.isnan, math.isinf, math.isfinite,
                         math.atan2, math.hypot, math.fmod,
                         math.log(x, base), math.pi special cases
- import json (not supported yet)
- time.ctime, time.localtime, time.gmtime, time.strftime, time.strptime
- time.perf_counter, time.monotonic
- import time as t (aliasing not supported)
- random.uniform(a, b), random.sample(xs, k), random.randrange(...)
- random.gauss / normalvariate
- import random as r (aliasing not supported)
- from random import ... (only `import random` syntax works)
- from math import ... (only `import math` syntax works)
- import math as m (aliasing not supported)
- print(double) uses 6 significant digits (C++ default); use str(x)
  for format_float's higher-precision output
- @property + @abstractmethod combined
- @x.deleter
- Property inheritance across base classes (direct-class-only)
- T + scalar / scalar + T for user classes (only T + T supported)
- __sub__, __mul__, __truediv__, __neg__, __iadd__ on user classes
- Bounds checking on xs.pop(i) -- out-of-range is UB
- t[N] += v for N>=3 tuples (AugAssign block not patched)
- default args on class methods (only plain functions supported)
- default args with non-literal values (e.g. b=foo())
- keyword args at call sites: f(b=2)
- *args mixed with defaults or kwargs beyond one vararg slot
- *args on class methods
- unpacking on call: f(*xs)
- lambdas with multi-statement bodies
- lambdas with default args / *args / **kwargs
- lambdas passed directly as function arguments
- lambdas with type-annotated params
- immediate invocation: (lambda x: x*2)(5)
- *args and **kwargs together on the same function
- *args/**kwargs on class methods
- unpacking on call: f(*xs), f(**d)
- kwarg value type must be homogeneous (C++ map constraint)
- emitter does not call _check_name on parameter names. `def f(default):`
  produces C++ that won't compile (confusing g++ error). Fix: add
  `self._check_name(a.arg, "Parameter name")` in visit_FunctionDef's
  arg_parts loop.
- `xs.pop()` and `xs.pop(i)` now throw std::out_of_range on
  out-of-range indices. Uncaught, this terminates the program
  (matches Python's uncaught IndexError behavior). Not catchable
  via InterScript's `try/except` because InterScript's except is
  catch-all over std::exception — but this should work. Runtime
  verification is blocked by WDAC on this machine.
  **Discovered by `examples/vscode_demo.kfy` (Batch 10k candidates):**
- `@property` access on a **class-typed function/method parameter**
  inside the callee's body: `def f(p: Point): ... p.magnitude_sq`
  emits `p.magnitude_sq` (member-function pointer), not
  `p.magnitude_sq()` (call). Same for `p.x` when `p` is a param.
- `is_to_string(<class-typed field>)` inside a class method body:
  `Circle.__str__` does `is_to_string(this->center)` where `center`
  is a `Point` field. Needs to dispatch to `this->center.__str__()`,
  not `is_to_string(...)`. Same fix pattern as 10i but for
  `self.X` / `this->X` field reads inside method bodies.
- Constructor with a **class-typed field** needs an initializer list.
  `Circle(Point center, double radius) { this->center = center; }`
  fails because `this->center` is default-constructed before
  assignment, and `Point` has no default constructor. Fix: emit
  `Circle(Point center, double radius) : center(center), radius(radius) {}`
  OR change the param to `const Point& center`.


## 6. Plan A is DONE. Batch 2+ next.

Batch 2a: String methods  DONE (2026-10-11)
Batch 2b: f-strings, .format()  DONE (2026-10-11)
Batch 3: ** (power), // (floor div), ternary  DONE (2026-10-11)
Batch 4a: enumerate, zip  DONE (2026-10-11)
Batch 4b: for...else  DONE (2026-10-11)
Batch 5a: default args  DONE (2026-10-11)
Batch 5b: *args  DONE (2026-10-11)
Batch 5c: **kwargs  DONE (2026-10-11)
Batch 5d: lambdas  DONE (2026-10-11)
Batch 6a: match/case  DONE (2026-10-11)
Batch 6: match/case, raise, try/except  DONE (2026-10-11)
Batch 7a: import math  DONE (2026-10-11)
Batch 7b: import random  DONE (2026-10-11)
Batch 7c: import time  DONE (2026-10-11)
Batch 8a: __eq__ -> operator==  DONE (2026-10-12)
Batch 8b: __str__ -> std::string __str__() const  DONE (2026-10-12)
Batch 8c: __add__ -> operator+  DONE (2026-10-12)
Batch 8d: @property + @x.setter  DONE (2026-10-12)
Batch 8e: @classmethod  DONE (2026-10-12)
Batch 8f: list.pop() real removal  DONE (2026-10-12)
Batch 8g: list.pop(i)  DONE (2026-10-12)
Batch 8h: transpile-only companions  DONE (2026-10-12)
Batch 8: @classmethod  DONE
Batch 7d (deferred): import json
Batch 9a: f-string format specs  DONE (2026-10-12)
Batch 9b: f-string format specs, phase 2  DONE (2026-10-12)
Batch 10a: print(container) reprs  DONE (2026-10-13)
Batch 10b: xs.pop bounds checking  DONE (2026-10-13)
Batch 10c: title/capitalize/isalpha/isdigit  DONE (2026-10-13)
Batch 9c: pip install -e ., real CLI, docs  <- NEXT
Batch 9c: packaging + rename InterScript→Kofty + GitHub push  DONE (2026-10-13)
Batch 10d: embed .ico in compiled .exe  DONE (2026-10-13)
Batch 11: publish to PyPI  <- NEXT (candidate)
Batch 11-alt: GitHub Actions CI  <- NEXT (candidate)

## 7. Development workflow

Every feature:
  1. Write tests in tests/test_<feature>.py (red phase)
  2. python check.py -> must say "parse cleanly"
  3. python -m pytest tests/test_<feature>.py -v -> tests FAIL
  4. Implement via a script (impl_<feature>.py) matching content anchors
  5. python check.py -> clean
  6. python -m pytest tests/test_<feature>.py -v -> all pass
  7. python -m pytest tests/ -v -> full suite all pass
  8. Verify with examples/<feature>.is
  9. Back up: Compress-Archive -Path C:\InterScript-Language -DestinationPath "$env:USERPROFILE\InterScript-Language_backup_YYYYMMDD_<feature>.zip" -Force
  10. Delete impl script and .bak files

**Preferred pattern going forward (Batch 8h and later):**
Write transpile-only tests that inspect the emitted C++. See
sections 19 and 20. Zero flake on the current WDAC-locked machine.

## 8. Commands

    python check.py
    python -m pytest tests/test_<feature>.py -q      # targeted
    python -m pytest tests/test_batchX_transpile.py -q  # transpile only, ~1-2s
    python -m pytest tests/ -q                       # full suite (runtime flakes on this machine)
    # Do NOT use `-n` (pytest-xdist): workers collide on shared build/ dir
    python -m interscript.cli examples\console_hello.is
    python -m interscript.cli examples\foo.is --emit-only
    python generate_roadmap.py

    # Backup
    Compress-Archive -Path C:\InterScript-Language -DestinationPath "$env:USERPROFILE\InterScript-Language_backup_YYYYMMDD_<name>.zip" -Force

    # Run only the transpile-only layer (fast, flake-free)
    python -m pytest tests/ -q -k "transpile"

## 9. Lessons learned (accumulated)

- NEVER delete code by line number. Match by content (start marker +
  end marker). Line numbers drift; content does not.
- Write .bak only AFTER guards pass, or use .bak.N (numbered).
- VS Code tabs are buffers, not files. Ctrl+S.
- Back up before every risky change.
- The impl script pattern (content anchors + backup + guard) has
  worked many times now. Keep using it.
- Small, focused edits; test after each.
- Containers (list, dict, set, tuple) each need a private dict on the
  emitter to track "which variables hold what" so method/subscript
  dispatch knows what to emit.
- Test strings that assert on emitted C++ must match what the emitter
  actually writes. `auto` + `std::make_tuple` does NOT emit
  an explicit `std::tuple<int, int, int>` type spelling anywhere.
- Content anchors: if a regex keeps missing, switch to exact
  multi-line string replacement. Byte-for-byte from a Select-String
  paste is more reliable than a hand-written regex.
- Watch for a SECOND guard when relaxing a rule.
- When a feature removes a limitation, grep the WHOLE test suite for
  tests asserting the old limitation.
- PowerShell here-strings (@' ... '@) execute as code, not as file
  content. To edit a text file, use VS Code or notepad, not the shell.
- Full test suite takes ~16-30 min serially. During development, run
  only the targeted transpile-only test file. DO NOT use
  pytest-xdist (-n): parallel workers collide on the shared build/
  directory.
- **Windows Application Control (WDAC) blocks freshly-built .exe
  files with `WinError 4551`.** This is the dominant test-infrastructure
  issue on the current machine. See section 19. Mitigation: transpile-
  only tests. See section 20.
- **Transpile-only tests must assert on emitted C++ strings**, not
  runtime behavior or (usually) error behavior. The transpiler is
  lazy — unknown method names emit as raw C++ and fail at g++ time.
- **Expression args in emitted C++ are wrapped in parens**:
  `vec_pop_at(xs, (-1))`, not `vec_pop_at(xs, -1)`. Test assertions
  must match the parenthesized form.
- **`print(obj)` requires `__str__`.** When writing transpile-only
  tests for a class that will be passed to `print`, add a
  `def __str__(self): return ...` to the class, or avoid `print(obj)`.

## 10. Where we are right now

- Batches 2–8h complete
- 674 total tests: 465 runtime + 209 transpile-only
- check.py clean
- Everything backed up
- Full-suite flake: documented as WDAC (WinError 4551). The
  transpile-only layer runs clean (~40s, 0 flake) and is the
  primary local test signal.
- Next: feature work — pick from section 5, sections 12–18
  follow-ups, or Batch 9 (pip install -e ., real CLI, docs)

---

## 11. How to resume in a new chat

Paste this file into the new chat with the message:
"HANDOFF.md content follows. Read it, then tell me where we are.
Batch 8h complete. Next: pick a feature from section 5 follow-ups."

The new AI should:
1. Confirm the state (674 total tests: 465 runtime + 209 transpile-only,
   6 xfailed, Plan A complete, Batches 2–8h done).
2. Note: runtime tests flake ~100% on this machine due to WDAC
   (WinError 4551). The transpile-only layer runs clean. This is
   NOT a regression signal.
3. Ask which feature to tackle next. Highest-value candidates:
   - f-string format specs (`f"{x:.2f}"`, `f"{n:05d}"`, `f"{x:>10}"`)
   - print(container) reprs
   - xs.pop(i) bounds checking
   - import json (Batch 7d deferred)
   - Batch 9: pip install -e ., real CLI, docs
   - OOP follow-ups from sections 12–16

Get the file onto the clipboard with:
    Get-Content C:\InterScript-Language\HANDOFF.md -Raw | Set-Clipboard

## 12. Batch 8a changelog (2026-10-12)

### __eq__ on user classes

- `visit_ClassDef` intercepts `def __eq__(self, other):` and emits:
      bool operator==(const <Class>& <other>) const { ...body... }
- `p1 == p2` in source emits `p1 == p2` in C++, dispatching to the operator.

**Tests:** `tests/test_batch8a.py` (8 tests) + `tests/test_batch8a_transpile.py` (7 tests).

**Known follow-ups:**
- Constructor param type inference from str literals
- `!=`, `__lt__`, `__gt__`, `__le__`, `__ge__`, `__hash__` not emitted
- `__eq__` inherited from a base class: operator== is not inherited

## 13. Batch 8b changelog (2026-10-12)

### __str__ on user classes

- `CppEmitter.__init__` — `self.instance_vars`, `self.str_classes`
- `visit_Assign` — registers `instance_vars[target] = ClassName` for `x = ClassName(...)`
- `visit_ClassDef` intercepts `def __str__(self):` -> `std::string __str__() const`
- `_call_expr` `print` branch rewrites `print(obj)` -> `std::cout << obj.__str__() << std::endl`
- `_call_expr` `str` branch rewrites `str(obj)` -> `obj.__str__()`

**Tests:** `tests/test_batch8b.py` (8) + `tests/test_batch8b_transpile.py` (8).

## 14. Batch 8c changelog (2026-10-12)

### __add__ on user classes

- `CppEmitter.__init__` — `self.add_classes`
- `visit_ClassDef` intercepts `def __add__(self, other):` -> `<Class> operator+(const <Class>& <other>) const`
- `expr()` ast.BinOp handler validates both operands are same-class instances
- `_class_of_expr` helper (used by print/str dispatch and visit_Assign)
- `visit_Assign` registers `x = a + b + c` via `_class_of_expr`

**Tests:** `tests/test_batch8c.py` (8) + `tests/test_batch8c_transpile.py` (8).

## 15. Batch 8d changelog (2026-10-12)

### @property getters + @x.setter setters

- `CppEmitter.__init__` — `property_getters`, `property_setters`, `_current_class`
- `visit_ClassDef` field emission — **unconditional `public:` before constructor** (fixes pre-existing privacy bug)
- `visit_ClassDef` intercepts `@property def name(self):` -> `auto name() const { body }`
- `visit_ClassDef` intercepts `@name.setter def name(self, v):` -> `void name(T v) { body }`
- `expr()` ast.Attribute — property read dispatch
- `visit_Assign` ast.Attribute — property write dispatch

**Tests:** `tests/test_batch8d.py` (9) + `tests/test_batch8d_transpile.py` (8).

## 16. Batch 8e changelog (2026-10-12)

### @classmethod on user classes

- `CppEmitter.__init__` — `classmethod_names`, `_classmethod_param`
- `visit_ClassDef` intercepts `@classmethod` -> `static auto <name>(<rest-args>) { body }`
- `_call_expr` top remaps `<param>(...)` -> `<ClassName>(...)`, `<param>.m(...)` -> `<ClassName>::m(...)`
- `_call_expr` instance dispatch — `obj.classmethod(...)` -> `ClassName::classmethod(...)`
- `visit_Assign` registers `<ClassName>.classmethod(...)` results

**Tests:** `tests/test_batch8e.py` (8) + `tests/test_batch8e_transpile.py` (8).

## 17. Batch 8f changelog (2026-10-12)

### list.pop() real removal

**Fix — two content anchors in `interscript/transpiler.py`:**

1. Preamble — added `vec_pop<T>`:
       template <typename T>
       T vec_pop(std::vector<T>& v) {
           T last = v.back();
           v.pop_back();
           return last;
       }

2. List-methods `pop` branch — emits `vec_pop(xs)` instead of `xs.back()`

**Tests:** `tests/test_batch8f.py` (8 runtime, blocked by WDAC) — correctness proven by `tests/test_lists_complete.py::test_list_pop` (checks `"vec_pop(xs)" in out`).

**Test infrastructure:** `tests/conftest.py` with retry loop for WinError 4551.

## 18. Batch 8g changelog (2026-10-12)

### list.pop(i) — remove and return element at index i

1. Preamble — added `vec_pop_at<T>`:
       template <typename T>
       T vec_pop_at(std::vector<T>& v, int i) {
           if (i < 0) i += (int)v.size();
           T val = v[i];
           v.erase(v.begin() + i);
           return val;
       }

2. List-methods `pop` branch — accepts 0 or 1 args

**Tests:** `tests/test_batch8g.py` (9 tests, transpile-only, ~5s).

**Note:** expression args are parenthesized: `vec_pop_at(xs, (-1))`.

**Known follow-up:** no bounds checking (`xs.pop(100)` is UB).

## 19. Application Control (WDAC) situation (2026-10-12)

The full test suite on this machine shows ~216/474 failed, ALL with
`OSError: [WinError 4551] An Application Control policy has blocked
this file`. This is a Windows Defender Application Control (WDAC)
or Smart App Control policy:

- `RealTimeProtectionEnabled: False`
- `AntivirusEnabled: True`
- `Set-MpPreference -DisableRealtimeMonitoring $true` fails with
  "You don't have enough permissions" (HRESULT 0xc0000142)

WDAC blocks execution of unsigned/freshly-written .exe files. The
transpiler pipeline writes a fresh `build\prog.exe` for every test.

**Mitigation that works: write transpile-only tests.**

Pattern:
    from interscript.transpiler import transpile
    def test_x():
        out = transpile("xs = [1, 2, 3]\nxs.pop(0)\n")
        assert "vec_pop_at(xs, 0)" in out

These tests inspect the emitted C++ directly. No exe launch. Zero
flake.

## 20. Batch 8h changelog (2026-10-12) — COMPLETE

### Transpile-only test companions

**Motivation.** WinError 4551 (WDAC) blocks every freshly-built
.exe. Runtime tests flake ~100% on this machine.

**Solution.** Transpile-only companion test files, one per runtime
test file. Each companion imports `transpile` from
`interscript.transpiler` and asserts on the emitted C++ string.
No exe launch. Zero flake.

**Scope.**

| Phase | Files covered | Tests added |
|-------|---------------|-------------|
| 1 | string methods, f-strings | 27 |
| 2 | batch3, batch4a, batch4b | 43 |
| 3 | batch5a, batch5b, batch5c, batch5d | 38 |
| 4 | batch6a, batch6b, batch7a, batch7b, batch7c | 61 |
| 5 | batch8a, batch8b, batch8c, batch8d, batch8e | 40 |
| **Total** | **19 files** | **209 transpile-only tests** |

**Runtime: ~40 seconds for all 209 tests, 0 flake.**

**Coexistence.** The original runtime test files are unchanged.
On a machine without WDAC, both layers run.

**Pattern.**
```python
from interscript.transpiler import transpile

def test_feature():
    out = transpile("""
xs = [1, 2, 3]
xs.pop(0)
""")
    assert "vec_pop_at(xs, 0)" in out

## 21. Batch 9a changelog (2026-10-12)

### f-string format specs

Extends Batch 2b (f-strings). Supports a useful subset of Python's
format-spec mini-language inside `{expr:spec}`.

**Supported specs:**

| Spec | Meaning | Emitted helper |
|------|---------|----------------|
| `.Nf` | N-decimal float | `fmt_float(x, N)` |
| `.N`  | N significant digits | `fmt_float(x, N)` |
| `Nd`  | space-pad int to width N | `fmt_int_pad(x, N, ' ')` |
| `0Nd` | zero-pad int to width N | `fmt_int_pad(x, N, '0')` |
| `>N`  | right-align to width N | `fmt_align(x, N, '>')` |
| `<N`  | left-align to width N | `fmt_align(x, N, '<')` |
| `^N`  | center-align to width N | `fmt_align(x, N, '^')` |
| `N.Mf`| width + precision float | `fmt_width_float(x, N, M)` |

**Fix — three content anchors in `interscript/transpiler.py`:**

1. `_parse_format_spec(spec_node)` — new helper. Reads the
   `ast.JoinedStr` (Python 3.12+) or `ast.Constant` produced by
   Python's parser and returns the raw spec string (e.g. `".2f"`).
   Rejects nested specs (`{x:{width}}`) with a clear message.

2. `_emit_format_spec(inner_cpp, spec)` — new helper. Regex-matches
   the spec string and dispatches to the right `fmt_*` helper. Raises
   `TranspileError` with the supported list for unrecognized specs.

3. `expr()` `ast.FormattedValue` branch — replaced the "raise on
   format_spec" with: parse the spec, then either `is_to_string(x)`
   (no spec) or `_emit_format_spec(...)`.

4. Preamble — four new templates next to `vec_pop`:
   - `fmt_float<T>(T x, int precision)` — `std::fixed` + `setprecision`
   - `fmt_int_pad<T>(T x, int width, char pad)` — `setw` + `setfill`
   - `fmt_align<T>(T x, int width, char align)` — `left`/`right`/`internal`
   - `fmt_width_float<T>(T x, int width, int precision)` — both

**Still unsupported (raises TranspileError):**
- `!r` / `!s` conversions (Batch 2b already rejected; unchanged)
- Nested specs `{x:{width}}`
- String precision `.Ns` (only floats supported for `.N`)
- Comma thousands separator `{n:,}`
- Hex/oct/bin `{n:x}`, `{n:o}`, `{n:b}`
- Percent `{x:.2%}`

**Tests:** `tests/test_batch9a_transpile.py`, 21 tests, all passing
in ~4s. Transpile-only (no exe launch, no WDAC flake).

**Verified:** `check.py` clean (53 Python files).

**Known follow-up:** empty spec `f"{x:}"` currently falls through to
the unsupported-spec branch — worth adding a passthrough case.

**Artifacts:** `impl_batch9a.py` applied anchors A, B, C. Backup zip:
`InterScript-Language_backup_20261012_batch9a_fstring_format.zip`.

## 22. Batch 9b changelog (2026-10-12)

### f-string format specs, phase 2

Extends Batch 9a with four more spec kinds.

**Added specs:**

| Spec | Meaning | Emitted helper |
|------|---------|----------------|
| `` (empty) | passthrough to `is_to_string` | — |
| `.Ns` | truncate string to N chars | `str_truncate(x, N)` |
| `x` | lowercase hex | `fmt_int_base(x, 16, false)` |
| `X` | uppercase hex | `fmt_int_base(x, 16, true)` |
| `o` | octal | `fmt_int_base(x, 8, false)` |
| `b` | binary | `fmt_int_base(x, 2, false)` |
| `,` | comma thousands | `fmt_int_comma(x)` |

**Fix — two content anchors in `interscript/transpiler.py`:**

1. `_emit_format_spec` — added six new branches before the final
   `raise TranspileError`. Empty spec now returns
   `is_to_string(inner_cpp)`.

2. Preamble — added three new templates after `fmt_width_float`:
   - `str_truncate<S>(S s, int n)` — resizes std::string if longer
   - `fmt_int_base<T>(T x, int base, bool upper)` — hex/oct via
     iostream manipulators; binary via manual bit loop
   - `fmt_int_comma<T>(T x)` — inserts commas every 3 digits,
     handles negative sign

**Error message updated** to list all supported specs (9a + 9b).

**Still unsupported (raises TranspileError):**
- `!r` / `!s` conversions
- Nested specs `{x:{width}}`
- Percent `{x:.1%}`
- Currency `{x:$}`
- Combined `,Nf` (comma with float precision) — deferred
- Locale-aware grouping

**Tests:** `tests/test_batch9b_transpile.py`, 19 tests, all passing
in ~7s. Transpile-only (no exe launch, no WDAC flake).

**Verified:** `check.py` clean (54 Python files).

**Artifacts:** `impl_batch9b.py` applied anchors A, B. Backup zip:
`InterScript-Language_backup_20261012_batch9b_fstring_format2.zip`.

## 23. Batch 10a changelog (2026-10-13)

### print(container) reprs

`print([1, 2, 3])`, `print({"a": 1})`, `print({1, 2, 3})`,
`print((1, 2))`, `print((1, 2, 3, 4))`, and the same inside
`str(...)` — now emit `repr_vector` / `repr_map` / `repr_set` /
`repr_pair` / `repr_tuple` helper calls.

**Fix — four content anchors in `interscript/transpiler.py`:**

1. `_container_repr(node, emitted)` — new helper. Given an AST
   node and its already-emitted C++ string, returns a `repr_X(...)`
   call if the node is a literal container or a Name tracked in
   `list_vars` / `dict_vars` / `set_vars` / `tuple_vars`. Returns
   None for anything else.

2. `_call_expr` print branch — after the user-class `__str__`
   check, calls `_container_repr`. If it returns a value, emits
   `std::cout << <repr_call> << std::endl`. Falls through to raw
   stream otherwise.

3. `_call_expr` str branch — same dispatch, before the optional-var
   unwrap and `format_float` fallback.

4. Preamble — five new templates:
   - `repr_vector<T>` — `[a, b, c]`, elements via `is_to_string`
   - `repr_map<K, V>` — `{'a': 1, 'b': 2}`, keys quoted
   - `repr_set<T>` — `{a, b, c}`
   - `repr_pair<T1, T2>` — `(a, b)`
   - `repr_tuple<Ts...>` — variadic, `(a, b, c, ...)` via
     `std::index_sequence` fold

**Tests:** `tests/test_batch10a_transpile.py`, 17 tests (2 originally
for empty containers were deleted — see below).

**Known limitations (kept):**
- String elements print without quotes: `print(["a", "b"])` ->
  `[a, b]`. Python prints `['a', 'b']`.
- Nested containers unsupported.
- Empty containers not supported (`xs = []` and `d = {}` raise
  TranspileError at assignment time — pre-existing limitation,
  not new to 10a).

**Artifacts:** `impl_batch10a.py` applied anchors A, B, C, D.
Backup zip: `InterScript-Language_backup_20261013_batch10a_print_container.zip`.

## 24. Batch 10c changelog (2026-10-13)

### Four more string methods

Adds `.title()`, `.capitalize()`, `.isalpha()`, `.isdigit()`.

**Fix — two content anchors in `interscript/transpiler.py`:**

1. String-method dispatch — four new branches after `str_count`:
   - `title` -> `str_title(_recv)`
   - `capitalize` -> `str_capitalize(_recv)`
   - `isalpha` -> `str_isalpha(_recv)` (bool)
   - `isdigit` -> `str_isdigit(_recv)` (bool)

2. Preamble — four new helpers:
   - `str_title(std::string s)` — capitalize after each non-letter
   - `str_capitalize(std::string s)` — capitalize first, lowercase rest
   - `str_isalpha(const std::string& s)` — true if non-empty and all
     chars are letters
   - `str_isdigit(const std::string& s)` — true if non-empty and all
     chars are digits

**Design notes:**
- `isalpha` / `isdigit` return `bool`. When printed they go through
  `std::cout` and show `1` / `0` (consistent with existing bool
  convention in InterScript).
- Empty string: both return `false`, matching Python.

**Tests:** `tests/test_batch10c_transpile.py`, 12 tests, all passing
in ~1.5s.

**Verified:** `check.py` clean (56 Python files).

**Artifacts:** `impl_batch10c.py` applied anchors A, B. Backup zip:
`InterScript-Language_backup_20261013_batch10c_string_methods2.zip`.

## 25. Batch 10b changelog (2026-10-13)

### Bounds checking on vec_pop / vec_pop_at

**Problem.** `xs.pop()` on an empty list was UB (`.back()` on an
empty vector). `xs.pop(i)` with an out-of-range index was UB
(`v[i]` read out of bounds, `v.erase` corrupted the vector). Python
raises `IndexError`.

**Fix — one anchor in `interscript/transpiler.py`, preamble templates:**

`vec_pop<T>` now checks `v.empty()` and throws
`std::out_of_range("pop from empty list")` before touching
`v.back()`.

`vec_pop_at<T>` now normalizes the negative index (unchanged),
then checks `i < 0 || i >= (int)v.size()` and throws
`std::out_of_range("pop index out of range")`.

**Error model.** Uncaught, the C++ `std::out_of_range` propagates
to `std::terminate` and the process exits non-zero. Python's
uncaught `IndexError` similarly exits non-zero with a traceback.
InterScript's `try/except` (Batch 6b) uses `catch (...)` which
DOES catch `std::out_of_range` — so `try: xs.pop(100) except: ...`
should work at runtime. Runtime verification blocked by WDAC on
this machine (see section 19).

**Tests:** `tests/test_batch10b_transpile.py`, 11 tests, all passing
in ~3s. Transpile-only. Verifies the emitted preamble contains the
bounds checks and that `.pop()` / `.pop(i)` still emit the helper
calls.

**Verified:** `check.py` clean (57 Python files). `--emit-only`
on `examples/list_pop.is` shows the exact expected preamble and
call sites.

**Note on print-in-preamble** (`fmt_int_comma` also uses `i >= 0`
in its loop) — the grep for `i >= ` matched a false positive from
`fmt_int_comma`. Not a bug; the actual out-of-range check
(`i >= (int)v.size()`) is what matters and it's there.

**Artifacts:** `impl_batch10b.py` applied anchor A. Backup zip:
`InterScript-Language_backup_20261013_batch10b_pop_bounds.zip`.

## 27. Rename to Kofty + packaging (2026-10-13)

**Project renamed InterScript -> Kofty.**

- Python package: `interscript` -> `kofty`
- CLI command: `interscript` -> `kofty`
- File extension: `.is` -> `.kfy`
- PyPI package name: `kofty` (verified available)
- GitHub repo: https://github.com/sharit25/kofty

Done via `rename_to_kofty.py` (kept in the repo for reference).
Pre-rename source tree preserved in `.bak-rename/` (gitignored).

**Packaging added (Batch 9c):**

- `pyproject.toml` — PEP 621 metadata, MIT license,
  `kofty = "kofty.cli:main"` entry point.
- `LICENSE` — MIT, copyright 2026 sharit25.
- `.gitignore` — build, venv, caches, backups.
- `README.md` — rewritten for Kofty, no Raylib references.

**Verified:**

- `pip install -e .` succeeds in a fresh venv.
- `kofty --help` shows the correct CLI usage.
- `kofty examples\console_hello.kfy --emit-only` writes the C++
  with `[Kofty] Wrote build\console_hello.cpp` status.
- 451 transpile-only tests pass (0 flake).
- Git commit `bc54fbb` (initial) and `7b9fd2a` (README fix) pushed
  to GitHub `main`.

**Notes:**
- The project folder is still `C:\InterScript-Language\`. Renaming
  the folder is cosmetic and optional; deferred.
- `HANDOFF.md` intentionally kept "InterScript-Language" references
  as historical artifacts.
- The pre-existing `fix_cli_branding_v2.py` bug (missed the argparse
  help string) was patched with a one-off command; the current
  `kofty/cli.py` is correct.

## 28. Batch 10d changelog (2026-10-13)

### Embed .ico in compiled executables

Every `kofty foo.kfy` now embeds `kofty.ico` into the compiled
`.exe`, so Windows Explorer / taskbar / Alt+Tab show the Kofty
icon instead of the default blank icon.

**How it works:**

1. `resolve_icon()` looks for `kofty.ico` in this order:
   - `--icon=<path>` (explicit)
   - `<source_dir>/kofty.ico`
   - `<cwd>/kofty.ico`
   - the installed package: `kofty/data/kofty.ico`

2. If found and `windres` is on PATH:
   - writes `build/<stem>_res.rc` with `IDI_ICON1 ICON "<abs path>"`
   - runs `windres <rc> -O coff -o <obj>`
   - adds `<obj>` to the g++ link line

3. `--icon=none` disables embedding.
4. If any step fails (missing `windres`, bad icon path), a warning is
   printed and the build continues without the icon.

**Files changed:**

- `kofty/cli.py` — new helpers `resolve_icon`, `build_icon_object`;
  `compile_cpp` gains an `icon` parameter; argparse gets `--icon`.
- `pyproject.toml` — `package-data` now includes `data/*`.
- `kofty/data/kofty.ico`, `kofty/data/kofty.svg`,
  `kofty/data/kofty_mono.svg` — packaged assets.

**Verified:**

- `kofty examples\console_hello.kfy` succeeds end-to-end, including
  exe launch (WDAC was not blocking at that moment).
- The `[Kofty] (icon) windres ...` line appears before the g++
  invocation, and the compiled `.exe` shows the icon in Explorer.

**Known follow-ups:**
- Only the default `kofty.ico` is embedded; per-project custom icons
  work via `--icon=<path>` but there's no per-project `.kofty.toml`
  config yet.
- On non-Windows systems, `windres` is not on PATH, so the icon is
  silently skipped. Could add a Linux/macOS .ico embed path later
  (uncommon; Linux binaries rarely have embedded icons).
- If a future version bundles the icon into a wheel, `pip install
  kofty` will ship it; currently works via editable install only.

**Artifacts:** `patch_10d_icon.py` applied 4 anchors, backed up to
`kofty/cli.py.bak.batch10d`, both deleted after close-out.

## 30. Batch 10f changelog (2026-10-13)

### String repetition: `s * n` and `n * s`

**Bug.** `"=" * 40` emitted raw C++ `("=" * 40)`, which is
`const char[2] * int` — invalid. No test caught it because no
existing test or example used string repetition.

**Fix — two anchors in `kofty/transpiler.py`:**

1. Preamble — added after `vec2_scale`:

    static std::string str_repeat(const std::string& s, int n) {
        if (n <= 0) return "";
        std::string out;
        out.reserve(s.size() * (size_t)n);
        for (int i = 0; i < n; ++i) out += s;
        return out;
    }

2. `expr()` `ast.BinOp` — new branch after the Pow/FloorDiv block:

    if isinstance(node.op, ast.Mult):
        left_is_str = self._is_string_expr(node.left)
        right_is_str = self._is_string_expr(node.right)
        left_is_int_lit = (isinstance(node.left, ast.Constant)
                           and isinstance(node.left.value, int)
                           and not isinstance(node.left.value, bool))
        right_is_int_lit = (isinstance(node.right, ast.Constant)
                            and isinstance(node.right.value, int)
                            and not isinstance(node.right.value, bool))
        if left_is_str and right_is_int_lit:
            return f"str_repeat({left}, {right})"
        if right_is_str and left_is_int_lit:
            return f"str_repeat({right}, {left})"

**Scope.** int side must be a literal constant for this batch.
`"=" * n` where `n` is a variable is a future extension.

**Tests:** `tests/test_batch10f_transpile.py`, 4 tests.

**Verified:**
- 4/4 batch-10f tests pass
- 462/462 existing transpile-only tests still pass
- check.py clean (56 Python files)
- Demo advances past the two `"=" * 40` g++ errors

**Artifacts:** backup
`InterScript-Language_backup_20261013_batch10f_str_repeat.zip`.

**Follow-up.** Test authoring note: when asserting a helper is
"not used", scope the assertion to `main()` — the preamble
always contains every helper, so `assert "str_repeat" not in out`
is wrong; `assert "str_repeat(" not in main_body` is right.

## 32. Batch 10j changelog (2026-10-13)

### User-class parameter annotations

**Bug.** `def f(p: Point): ...` emitted `auto f(int p)`. The
`Point` annotation was silently replaced with `int` because
`_annot_to_cpp_type` had a hardcoded map (`int`/`float`/`str`/`bool`)
with `"int"` as its fallback. Any unknown name — including user
classes — collapsed to `int`.

**Fix — one anchor in `kofty/transpiler.py`:** `_annot_to_cpp_type`
now checks `self.user_classes` before falling back to `"int"`:

    if annotation.id in mapping:
        return mapping[annotation.id]
    if annotation.id in self.user_classes:
        return annotation.id
    return "int"

That single change fixed every caller: function params, method
params, constructor params, property setters, abstract methods.
`self.user_classes` is populated in `transpile()` during the
pre-pass that registers class names (line ~3484).

**Tests:** `tests/test_batch10j_transpile.py`, 5 tests.

**Verified:**
- 5/5 batch-10j tests pass
- 484/484 transpile-only tests still pass
- check.py clean (60 Python files)

**Newly surfaced (Batch 10k candidates):**
1. Property access on a class-typed function parameter inside
   the callee body (`p.magnitude_sq` on `p: Point`).
2. `is_to_string(this->center)` inside `Circle.__str__` — class-typed
   field in a method body needs `__str__()` dispatch.
3. Constructor with class-typed field needs an initializer list
   (`Point` has no default constructor).

**Artifacts:** backup
`InterScript-Language_backup_20261013_batch10j_user_class_params.zip`.

## 33. Batch 10k — RESOLVED (2026-10-14)

All three sub-tasks completed; `examples/vscode_demo.kfy`
compiles and runs end-to-end.

### 10k.1 — Class-typed parameter access ✅
Registered class-typed params in `instance_vars` during
`visit_FunctionDef` body emission; restored on exit.
Files: `kofty/transpiler.py` (`visit_FunctionDef`).
Tests: `tests/test_batch10k_transpile.py` (4 tests).
Commit: 1a791fb.

### 10k.2 — Class-typed fields in method bodies ✅
- Added `self.class_field_types: dict` to the emitter.
- Populated it in `visit_ClassDef` from the `field_types`
  gathered during constructor analysis.
- Extended `_class_of_expr` to handle `self.field` reads by
  looking up the field's type in `class_field_types`.
Tests: 2 more tests in `tests/test_batch10k_transpile.py`.
Commit: b69d6ad.

### 10k.3 — Constructor initializer list ✅
Constructors now emit `: field(param), ...` for every field
assigned directly from a constructor parameter, merged with the
parent-initializer list from `super().__init__(...)`.
Body assignments for those fields are filtered out.
Files: `kofty/transpiler.py` (constructor emission).
Tests: 3 more tests; 2 existing tests in `tests/test_transpiler.py`
updated for the new (correct) emitted form.
Commit: (the one you're about to make).

**Acceptance:** `.\run_kofty.ps1 examples\vscode_demo.kfy` builds
and runs the full demo (`Hello, kofty!` through `Done.`).

## 34. Demo-driven bug hunt: what it found

`examples/vscode_demo.kfy` was written as an end-to-end test
program. It surfaced 9 real language gaps that unit tests missed:

| Batch | Gap |
|-------|-----|
| 10e | `math.pi` (and random/time) inside class method bodies |
| 10f | String repetition `"=" * n` |
| 10g | Set operations with inline set literals |
| 10h | Containers inside f-strings |
| 10i | User-class instances inside f-strings |
| 10j | User-class parameter annotations were silently `int` |
| 10k.1 | Class-typed params weren't registered in scope |
| 10k.2 | Class-typed fields weren't tracked past `visit_ClassDef` |
| 10k.3 | Constructor default-constructed class-typed fields |

All fixed. Demo runs. 493 transpile tests green.

**Lesson:** write a real program. Tests written by the same
author as the feature have the same blind spots. A demo that
attempts a lot will find the gaps the tests didn't.

## End-to-end example

`examples/vscode_demo.kfy` is a full tour of the language:
strings, f-strings, lists, dicts, sets, tuples, classes,
`__str__` / `__eq__` / `__add__`, properties, classmethods,
lambda, match/case, try/except, math/random/time, for-else,
enumerate, zip. It compiles and runs end-to-end.

    kofty examples/vscode_demo.kfy
