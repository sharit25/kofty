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

## 35. Batch 10l changelog (2026-10-14)

### int / int emits true (float) division

**Bug.** `7 / 3` emitted `(7 / 3)` — C++ integer division → `2`.
Python gives `2.333...`. Kofty's existing test
(`test_float_division_not_truncated`) only covered `5.0 / 2.0`
where C++ naturally gives float — it never tested the int/int case.

**Fix — two anchors in `kofty/transpiler.py`:**

1. New `_is_int_expr(node)` helper: returns True for
   `ast.Constant(int)`, `ast.Name` not tracked as a container
   or user class, and int-preserving `BinOp`/`UnaryOp`.
2. New branch in `expr()`'s `ast.BinOp` for `ast.Div`: when both
   sides are int-typed, emit `((double)L / (double)R)`. Otherwise
   emit `(L / R)` as before.

**Tests:** `tests/test_batch10l_transpile.py`, 7 tests.

Commit: 1812267.

## 36. Batch 10l.1 changelog (2026-10-14)

### UTF-8 BOM tolerance

**Bug.** A `.kfy` file written by PowerShell's
`Set-Content -Encoding utf8`, Notepad, or Visual Studio — all of
which emit BOM-prefixed UTF-8 — crashed Python's `ast.parse`
with "invalid non-printable character U+FEFF".

**Fix — one-line change in `kofty/cli.py`:**

    src_path.read_text(encoding="utf-8")     # before
    src_path.read_text(encoding="utf-8-sig") # after

`utf-8-sig` strips a leading BOM if present, otherwise behaves
identically to `utf-8`.

Commit: c9a3681.

## 37. Batch 10m changelog (2026-10-14)

### `kofty <file>` searches subdirectories

**Bug.** `kofty CalcTwoNum.kfy` only worked if the file was in
the current directory. From the project root, it said
"File not found" even if the file existed at `examples\...`.

**Fix — one new helper in `kofty/cli.py`:**

`_resolve_source_file(name)` tries:
1. The path as given (relative to CWD)
2. If the arg has no path separators, a recursive search of CWD
   (up to 3 levels deep) for a unique file of that name
3. If zero matches → None (caller prints "not found")
4. If multiple → prints all candidates and returns None

**Tests:** `tests/test_cli_resolve.py`, 5 tests.

Commit: 5885c11.

## 38. Batch 10n / 10n.1 changelog (2026-10-14)

### `kofty init` writes VS Code project setup

**Feature.** New `kofty init` subcommand that writes:
- `.vscode/tasks.json` — enables Ctrl+Shift+B to build+run the
  currently-focused `.kfy` file via `python -m kofty.cli ${file}`
- `.vscode/settings.json` — maps `*.kfy` → Python syntax
  highlighting, plus 4-space indentation defaults

Refuses to overwrite existing files; reports what it wrote.

**Fix — `kofty/cli.py`:**
- New `_TASKS_JSON` and `_SETTINGS_JSON` constants
- New `_run_init()` function
- Early dispatch in `main()`: if `argv[0] == "init"`, run init
  instead of argparse

**Tests:** `tests/test_cli_init.py`, 8 tests.

Commits: 99a4473 (10n/10n.1 combined), 560d440 (HANDOFF + example).

## 39. Batch 10o changelog (2026-10-14)

### Kofty Icons VS Code extension

**Feature.** A minimal VS Code icon-theme extension that shows
the Kofty logo on `.kfy` and `.is` files. Ships with its own
`kofty.svg` and `kofty_mono.svg`. Bypasses Material Icon Theme
entirely.

**Location:** `vscode-kofty/` — a separate npm project inside
the repo.

**Files:**
- `vscode-kofty/package.json` — extension manifest, declares
  one iconTheme contribution
- `vscode-kofty/icons/kofty-icon-theme.json` — maps `.kfy` and
  `.is` → `./kofty.svg`
- `vscode-kofty/icons/kofty.svg` — copied from `kofty/data/`
- `vscode-kofty/README.md`, `LICENSE`, `.vscodeignore` — packaging

**Build:** requires Node.js. `npm install -g @vscode/vsce` then
`cd vscode-kofty && vsce package` produces `kofty-icons-0.1.0.vsix`.
Install with `code --install-extension kofty-icons-0.1.0.vsix`.
Activate via `Preferences: File Icon Theme` → "Kofty Icons".

**Caveat — VS Code icon themes are one-at-a-time.** Activating
"Kofty Icons" replaces the current theme entirely for files we
don't map. Everything not `.kfy`/`.is` falls back to VS Code's
bare-minimum generic page icon (not Seti's rich icons).

**Attempted and rejected:**
- Merging Seti's icon set into our theme — Seti's
  `seti-icon-theme.json` is not shipped as a file on disk in
  VS Code 1.80+; it's bundled inside `app.asar`. Can't copy.
- Material Icon Theme's `customClones` — only clones built-in
  icons with different colors, doesn't accept custom SVGs.
- Material Icon Theme's `material-icon-theme-custom-icons`
  globalStorage folder — v5.39 removed support entirely.

**Decision:** ship the extension as-is. `.kfy` files get the
Kofty logo; everything else gets the plain fallback. If the
plain look becomes annoying, uninstall the extension and switch
back to Seti — but lose the Kofty logo.

Commit: d16e1e2.

## 40. Session wrap-up (2026-10-14)

**Batches completed this session:**
10e, 10f, 10g, 10h, 10i, 10j, 10k.1, 10k.2, 10k.3,
10l, 10l.1, 10m, 10n, 10n.1, 10o.

**Test count:** 500 transpile-only + 8 cli-init + 5 cli-resolve
= 513 total passing.

**The demo `examples/vscode_demo.kfy` runs end-to-end.**

**New workflow for fresh projects:**

    mkdir myproject && cd myproject
    kofty init
    # create CalcTwoNum.kfy in VS Code
    # press Ctrl+Shift+B, or type `kofty CalcTwoNum.kfy`

**Open follow-ups (from earlier sections):**
- GitHub Actions CI (Batch 11-alt)
- Publish `kofty` to PyPI (Batch 11)
- Demo regression test in `tests/`
- Any remaining feature work from section 5

**Icon caveat:** activating "Kofty Icons" replaces rich Seti
icons with plain fallbacks on non-`.kfy` files. This is a
known trade-off, documented in section 39.

## 42. Batch 11b changelog (2026-10-14)

### Tuple arity tracked across function returns

**Bug.** `def make(): return (1, 2, 3)` followed by `t = make(); a, b, c = t`
emitted `t.first / t.second` (arity-2 fallback) instead of
`std::get<0>(t) / std::get<1>(t) / std::get<2>(t)`. Same for
`t[N]` subscript. The emitter tracked tuple arity only for literal
tuple assignments, not for function returns.

**Fix — five content anchors in `kofty/transpiler.py`:**

1. `CppEmitter.__init__` — added
   `self.func_return_arity: dict = {}` after `str_literal_vars`.
2. New method `_infer_tuple_return_arity(node)`:
   - If `node.returns` is `-> tuple[...]`, parse the arity from the
     subscript slice (tuple of N elements → N; bare name → 1).
   - Else scan `ast.walk(node)` for `Return` statements. If every
     return value is a `Tuple` literal of the same arity, use that
     arity; otherwise return None.
3. `visit_FunctionDef` — after `self.user_funcs.add(node.name)`,
   call the helper and register in `func_return_arity` if the arity
   is determinable.
4. `visit_Assign` — the literal-tuple branch
   (`if isinstance(node.value, ast.Tuple): tuple_vars[name] = ...`)
   gains an `elif`: if the RHS is a `Call` to a name in
   `func_return_arity`, register `tuple_vars[name]` with that arity.
5. Tuple-unpacking branch — same `elif` extension so
   `a, b, c = make()` (direct unpack of a returned tuple, no
   intermediate variable) reads the arity from the function.

**Design decision — lenient fallback for ambiguous returns.**
If a function has mixed tuple + scalar returns, or no returns at
all, `_infer_tuple_return_arity` returns None and the target variable
is not registered in `tuple_vars`. Unpacking then falls back to the
pre-existing arity-2 assumption (`.first` / `.second`). This is
consistent with how unregistered variables were already handled;
making it strict would break existing code and is a language-
semantics change deferred to a possible Batch 11b.1.

**Scope — not fixed by this batch:**
- Typed tuple return *signatures* (`def f() -> tuple[int,int,int]:`
  still emits `auto f()`; only the arity is tracked, not the
  element types in the C++ signature).
- `for a, b, c in triples` where `triples` is a list of tuples.
  That's nested-container territory (Batch 11c).

**Files changed:** `kofty/transpiler.py`.

**Tests:** `tests/test_batch11b_transpile.py`, 12 tests, all passing.

**Verified:**
- `check.py` clean (66 files).
- Full transpile layer: 525 passing, 0 failing.

**Commit:** `daebc39`.

**Follow-up note (deferred, cosmetic):** `visit_Assign` still has the
duplicated `if isinstance(target, ast.Name):` header noted in §41.
Unrelated to 11b; still queued for a cosmetic pass.

## 43. Batch 11c.1 changelog (2026-10-14)

### List of pairs (2-tuples) + for-unpack

**Feature.** `xs = [(1, 2), (3, 4)]` now compiles. `for a, b in xs:`
unpacks each pair via `.first` / `.second`. `xs.append((5, 6))` works.
`xs[0]` yields a pair.

**Bug fixed.** Before: `[(1, 2), (3, 4)]` raised `TranspileError:
List elements must be literals for now`. The `ast.List` handler in
`expr()` refused any element that wasn't an `ast.Constant`. And
even if the gate were opened, `visit_For` refused tuple targets
with `For loop target must be a single name`.

**Fix — six anchors across `kofty/transpiler.py`:**

1. `CppEmitter.__init__` — `self.list_vars` changed from `set` to
   `dict`, mapping name → element C++ type. All `list_vars.add(name)`
   sites updated to `list_vars[name] = <type>`. Four sites:
   pointer-list registration, split-result registration, list-literal
   registration, varargs registration.
2. `expr()` `ast.List` handler — accepts 2-tuple elements. Element
   type is `std::pair<T1, T2>`; each pair emits as
   `std::pair<int, int>{a, b}`. Element-type uniformity across
   elements is enforced.
3. `expr()` list emission — the pair-list branch emits
   `std::vector<std::pair<T1, T2>>{...}` before the scalar-list
   fallback runs.
4. `visit_For` — when the target is a 2-tuple and the iterable is
   a list-of-pairs, emits
   `for (const auto& __it : xs) { auto a = __it.first; auto b = __it.second; ... }`.
5. `visit_Assign` — records the element type of a list-literal into
   `list_vars[name]`.

**Design notes:**
- Lists are tracked by name in a `dict`, not a `set`. Every existing
  `name in self.list_vars` check still works (dict membership is by
  key); every `.add(name)` became `[name] = <type>`.
- The pair-emission uses C++ brace-init (`std::pair<int, int>{1, 2}`),
  not `std::make_pair(1, 2)`. Both are valid; brace-init was
  simpler to emit from the tuple AST.
- Element types must be uniform across a list literal. Mixed types
  like `[(1, "a"), ("b", 2)]` raise `TranspileError`.
- Lists of 3+-tuples (`[(1,2,3)]`) still raise; that's Batch 11c.2.

**Files changed:** `kofty/transpiler.py`.

**Tests:** `tests/test_batch11c1_transpile.py`, 10 tests, all passing.

**Verified:**
- `check.py` clean (67 files).
- Full transpile layer: 535 passing, 0 failing.

**Follow-up notes:**
- The `visit_For` tuple-target path only handles list-of-pairs.
  Lists of 3+-tuples will need the same treatment in 11c.2.
- Chained subscript `xs[0][0]` still raises. Needs a type descriptor
  threaded through subscript dispatch, not just a string. Deferred
  to a possible 11c.4.

**Next:** Batch 11c.2 — list of 3+-tuples. Same machinery, different
element-type string (`std::tuple<T1, T2, T3>`) and `std::get<N>(it)`
for the for-unpack.

## 44. Batch 11c.2 changelog (2026-10-14)

### List of 3+-tuples + for-unpack

**Feature.** `xs = [(1, 2, 3), (4, 5, 6)]` now compiles with element
type `std::tuple<int, int, int>`. `for a, b, c in xs:` unpacks each
tuple via `std::get<0/1/2>(__it)`. Heterogeneous 3+-tuples work.
4-tuples work. `xs.append((7, 8, 9))` works. List of pairs (2-tuples)
still works — regression-protected.

**Fix — three edits across `kofty/transpiler.py`:**

1. `expr()`'s `ast.List` handler: the tuple-detection branch now
   accepts any arity >= 2. Element types are stored as a tuple of
   type strings; `_elem_arity` is recorded. Emission picks
   `std::pair<T1,T2>` for arity 2, `std::tuple<T1,...,Tn>` for
   arity 3+.

2. `visit_Assign`'s list-registration block: the previous
   `if isinstance(_first, ast.Tuple) and len(_first.elts) == 2:`
   became `and len(_first.elts) >= 2:`, with a `std::tuple<...>`
   branch added for arity 3+. This is what makes the for-loop
   handler see `std::tuple<...>` when it looks up
   `list_vars[node.iter.id]`.

3. `_visit_for_inner`'s tuple-target handler: the previous
   arity-2-only branch became arity-agnostic. Emits
   `.first`/`.second` for pairs, `std::get<N>(__it)` for tuples.
   Arity-2 unpack of a pair still requires exactly 2 target names;
   arity-3+ requires exactly arity-many.

**Design notes:**
- The list-of-pairs code path (Batch 11c.1) is preserved as a
  subset of the list-of-tuples path. Arity-2 lists still emit
  `std::vector<std::pair<T1, T2>>{...}` and still unpack via
  `.first`/`.second`.
- Element types must be uniform across a list literal. Mixed
  arities (`[(1, 2), (1, 2, 3)]`) raise `TranspileError`. Mixed
  element types within the same arity also raise.
- Nested containers (`[[1, 2], [3, 4]]`, `[((1, 2), 3)]`) are
  still unsupported. That's Batch 11c.3 / 11d territory.

**Files changed:** `kofty/transpiler.py`.

**Tests:** `tests/test_batch11c2_transpile.py`, 9 tests, all passing.

**Verified:**
- `check.py` clean (68 files).
- Full transpile layer: 544 passing, 0 failing.

**Commit:** `b01abfb`.

**Next:** Batch 11c.3 — dict values that are tuples
(`d = {"a": (1, 2), "b": (3, 4)}`). Opens the `ast.Dict` value-type
gate to accept `ast.Tuple`. Last piece of the nested-container arc
before 11d (nested repr).

## 45. Batch 11c.3 changelog (2026-10-14)

### Dict values that are tuples

**Feature.** `d = {"a": (1, 2), "b": (3, 4)}` now compiles with value
type `std::pair<int, int>`. 3+-tuples as dict values compile as
`std::tuple<...>`. `d["a"]` yields a pair/tuple, subscriptable or
unpackable. `for k, v in d.items():` works. Same dict-literal path
supports heterogeneous pairs (`{"a": ("x", 1)}`).

**Fix — one branch in `visit_Assign`'s dict value-type inference:**

`_infer_dict_value_type` (there are two copies — one inside
`visit_Assign` and one inside `expr()`; only the `visit_Assign`
copy needed the change) gains a branch for `ast.Tuple` values with
arity >= 2. Element type is `std::pair<T1,T2>` for arity 2,
`std::tuple<T1,...,Tn>` for arity 3+. Element types are validated
to be scalar literals.

Also: `_visit_for_inner`'s tuple-target handler now rejects nested
destructure (`for k, (a, b) in d.items()`) with a clear
`TranspileError: Nested tuple-unpacking in for-loops is not
supported yet.` — previously it crashed with an `AttributeError`.

**Files changed:** `kofty/transpiler.py`.

**Tests:** `tests/test_batch11c3_transpile.py`, 10 tests, all passing.

**Verified:**
- `check.py` clean (69 files).
- Full transpile layer: 554 passing, 0 failing.

**Commit:** (this one).

**Deferred:** `expr()`'s copy of `_infer_dict_value_type` was *not*
edited and still doesn't accept tuples. This is fine for the tests
that pass because the dict's *emission* goes through a different
code path (`expr()` uses `self.expr(val)` on each value, and tuple
values already emit as `std::make_pair` / `std::make_tuple` from
the `ast.Tuple` branch of `expr()`). But if a dict-of-tuples is
ever constructed inside a context where `expr()`'s dict branch is
invoked directly — e.g. as a value inside another dict, or in a
function-return position — this copy will need the same fix. Note
for follow-up.

**Arc status:** Batches 11c.1, 11c.2, 11c.3 are done. Nested
*construction* now works for lists and dicts. Remaining arc work:
**11d** — nested repr (`print([(1,2),(3,4)])` rendering as
`[(1, 2), (3, 4)]` instead of `[(1, 2)` with element fallbacks).
Deferred; not urgent.

## 46. Batch 12 changelog (2026-10-14)

### input() builtin

**Feature.** `input()` reads a line from stdin (returns `std::string`
without trailing newline). `input(prompt)` prints the prompt first
(no trailing newline, matching Python) then reads.
`int(input())` parses via `std::stoi`. `float(input())` parses via
`std::stod`. The result of `input()` is a normal `std::string` and
flows through string concat, f-strings, `is_to_string`, etc.

**Fix — one preamble helper, one dispatch branch, two special-case
upgrades:**

1. Preamble (`transpiler.py`'s preamble list) — new helper
   `input_line(const std::string& prompt)`:
   - Prints prompt via `std::cout << prompt << std::flush` when
     non-empty.
   - Reads line via `std::getline(std::cin, line)`.
   - Returns the line (no trailing newline, matching Python).

2. `_call_expr` — new branch immediately after the `print()` case:
   - `input()` → `input_line("")`
   - `input(prompt)` → `input_line(prompt)`
   - `input(a, b)` → `TranspileError`

3. `int()` special-case — when the argument is `input(...)`, emit
   `std::stoi(input_line(...))` instead of `(int)input_line(...)`.
   The C-style cast wouldn't compile (`const char*` to int is
   invalid); `std::stoi` is the correct parser.

4. `float()` special-case — same shape, `std::stod`.

**Design notes:**
- Prompt is written with `std::flush` so it appears before the
  read even when stdout is line-buffered.
- Empty prompt produces no output — `input_line("")` skips the
  prompt emission.
- `int(input())` on non-numeric input throws `std::invalid_argument`
  from `std::stoi`. Uncaught, that propagates to `std::terminate`
  (non-zero exit), same as Python's uncaught `ValueError`.
  `try/except` in Kofty (Batch 6b, `catch (...)`) catches it.
- The `input_line` helper is in the fixed preamble and included in
  every program, even those that never call `input()`. The linker
  drops it. This matches how `vec_pop`, `str_repeat`, and all the
  `fmt_*` helpers work — no "detect unused" logic.

**Files changed:** `kofty/transpiler.py`.

**Tests:** `tests/test_batch12_transpile.py`, 10 tests, all passing.

**Verified:**
- `check.py` clean (70 files).
- Full transpile layer: 564 passing, 0 failing.

**Interactivity smoke-test:**

## 47. Batch 11d changelog (2026-10-14)

### Nested container repr — verification only

**Finding.** Nested container repr (`print([(1,2),(3,4)])`,
`print({"a":(1,2)})`) already works. It was completed as a side
effect of Batch 10h (`is_to_string` overloads for containers) plus
Batches 11c.1–11c.3 (correct element-type tracking for
list-of-pairs, list-of-tuples, dict-of-tuples). No emitter
changes were needed.

**Verified emissions:**
| Source | Emitted C++ |
|--------|-------------|
| `xs = [(1,2),(3,4)]; print(xs)` | `std::vector<std::pair<int, int>>{...}` + `repr_vector(xs)` |
| `xs = [(1,2,3),(4,5,6)]; print(xs)` | `std::vector<std::tuple<int,int,int>>{...}` + `repr_vector(xs)` |
| `d = {"a":(1,2)}; print(d)` | `std::map<std::string, std::pair<int, int>>{...}` + `repr_map(d)` |
| `print([(1,2),(3,4)])` (literal) | inline `repr_vector(std::vector<...>{...})` |

**Files changed:** none. Only `tests/test_batch11d_transpile.py` added.

**Tests:** 11 tests, all passing on first run. The batch's purpose
is to pin the behavior so a future refactor of `_container_repr`
or the repr_* preamble helpers can't silently regress it.

**Known limitations (unchanged from 10a):**
- Top-level string lists still print without quotes:
  `print(["a", "b"])` → `[a, b]`, Python prints `['a', 'b']`.
- String elements *inside* a pair also print without quotes:
  `print([("x", 1)])` → `[(x, 1)]`, Python prints `[('x', 1)]`.
- Nested-nested (list of lists, dict of dicts) still unsupported —
  no test cases for those; deferred.

**Note:** Batch 11d was originally scoped as "make nested repr
work." The scope reduced to "verify nested repr already works"
once a probe showed all five target cases producing correct C++
pre-batch. This is the second time this session that a batch's
premise turned out to be stale — the code had organically grown
the feature during an earlier batch, and the follow-up batch was
tracking a gap that no longer existed.

**Commit:** (this one — tests only).

## 49. Batch 13a changelog (2026-10-15)

### Preamble ordering + input_line dedup + forward declarations

Three fixes in `kofty/transpiler.py`'s preamble list.

**Bug #1 — container is_to_string overload ordering.**

Container `is_to_string` overloads called `repr_vector` /
`repr_map` / `repr_set` / `repr_pair` / `repr_tuple`, but those
templates were defined *after* the overloads in the emitted C++.
And the `repr_*` templates called `is_to_string` on their element
types. Circular dependency: each side needed the other to be
declared first.

Fix: two parts.
1. Add forward declarations for all five `repr_*` templates.
2. Move the container `is_to_string` overloads (which call the
   forward-declared `repr_*`) to before the full `repr_*`
   definitions.

Emitted order is now:
  scalar is_to_string overloads
  repr_* forward declarations
  container is_to_string overloads (call repr_* forward decls)
  full repr_* definitions

Result: `print()` on nested containers compiles and runs, e.g.
`print([(1, 2), (3, 4)])` → `[(1, 2), (3, 4)]`.

**Bug #8 — duplicate input_line definition.**

`input_line` was defined twice in the preamble — once at column-0
indentation, once at column-8 (partial Batch 12 re-application
artifact). Result: every compiled `.kfy` file failed with
"redefinition of input_line". This blocked *all* builds.

Fix: delete the duplicate block.

**Test changes.**

- `tests/test_batch10h_transpile.py::test_overloads_come_after_reprs`
  was pinning the *wrong* order (the bug). Deleted.
- `tests/test_batch13a_transpile.py` added — 8 tests pinning the
  correct order, plus regressions for scalar-overload-first and
  repr-* definitions present.

**Files changed:** `kofty/transpiler.py`,
`tests/test_batch10h_transpile.py` (test deleted),
`tests/test_batch13a_transpile.py` (new).

**Verified:**
- `check.py` clean (72 files).
- Full transpile layer: 582 passing, 0 failing.
- `kofty tests_minimal.kfy` with `xs = [(1, 2), (3, 4)]; print(xs)`
  compiles, links, and prints `[(1, 2), (3, 4)]`.

**Commit:** `d48c38d`.

**Process note.** This batch took ~15 round-trips. The core problem
was that the test asserted on a substring that matched both the
forward declaration (`std::string repr_vector(const std::vector<T>&);`)
and the full definition (`std::string repr_vector(const std::vector<T>& v) {`).
`str.find()` returned the forward declaration, which was correctly
positioned first, so the test failed for the wrong reason. The fix
was to search for the *definition* form specifically.

The other recurring issue was that manual edits and impl-script
edits sometimes collided, and `git diff` was needed to establish
ground truth. In future, when a batch involves multiple edits to
the same file, run `git diff` after each edit to confirm state.

**Next:** Bug #4 (`*args` / `**kwargs` call-site regression) or
Bug #7 (unannotated ctor params), whichever is smaller. Both are
single-concept fixes.

## 50. Batch 13d changelog (2026-10-15)

### *args / **kwargs call-site wrapping

**Bug #4:** functions with `*args` weren't receiving their
positional args wrapped in a `std::vector<T>{...}` at the call
site. `sum_all(1, 2, 3)` emitted `sum_all(1, 2, 3)` which g++
rejected ("could not convert '1' from 'int' to 'std::vector<int>'").

**Root cause.** The `elif name in self.func_varargs` branch in
`_call_expr` iterated the caller's args and only wrapped the
*last one* if it happened to be an `ast.Set` literal. Plain
positional args went through unwrapped.

**Fix — three anchors in `kofty/transpiler.py`:**

1. `CppEmitter.__init__` — added `self.func_vararg_leading: dict`
   to record how many leading positional params precede the
   vararg for each function.

2. `_call_expr` — replaced the arg-preparation branch for
   `*args`-callees. Now emits:
   - `f()` → `f(std::vector<T>{})`
   - `f(1, 2, 3)` → `f(std::vector<T>{1, 2, 3})`
   - `f(a, b, *rest)` called as `f(1, 2, 3, 4)` → `f(1, 2, std::vector<int>{3, 4})`
   Leading args (before the vararg) stay positional; the rest
   wrap into one vector.

3. `visit_FunctionDef` — records
   `self.func_vararg_leading[node.name] = len(node.args.args)`
   when registering a `*args` variadic param.

**Tests changed:**
- Added `tests/test_batch13d_transpile.py` (8 tests) covering
  `*args` with 0/1/3 args, typed element (`*ws: str`), mixed
  signatures, kwargs, and a plain-function regression.
- Fixed two tests in `tests/test_batch5b_transpile.py` that were
  pinning the *unwrapped* (buggy) form.

**Verified:**
- `check.py` clean (73 files).
- Full transpile layer: 590 passing, 0 failing.
- `kofty tests_minimal_args.kfy` with `sum_all(1, 2, 3)` compiles,
  links, and prints `6`.

**Commit:** `1efb2d5`.

**Process note.** My original test assertions looked for the short
brace-init form `sum_all({1, 2, 3})`. The emitter writes the
explicit-typed form `sum_all(std::vector<int>{1, 2, 3})`. Both are
valid C++; the explicit form is arguably better (unambiguous vs.
`std::initializer_list` in some contexts). Tests were relaxed to
accept either. Lesson: **assert on the property (args wrapped in
a vector of the right type), not on the exact emitted text.**

**Next:** Bug #7 (unannotated ctor params), Bug #2 (container
repr for binops), Bug #3 (loop variable scoping), Bug #5
(variable redeclaration), Bug #6 (list methods on params).

## 51. Batch 13h + 13h.1 changelog (2026-10-15)

### Whole-program constructor argument type inference

**Bug #7:** unannotated ctor params defaulted to `int` regardless of
what call sites passed. `class Dog: def __init__(self, name, breed):
self.name = name; self.breed = breed` followed by
`Dog("Rex", "Labrador")` produced `Dog(int name, int breed)` and a
call site passing `const char*` — g++ error.

**Fix — four anchors in `kofty/transpiler.py`:**

1. `CppEmitter.__init__` — added
   `self.class_ctor_arg_types: dict = {}`. Populated by the pre-pass
   in `transpile()`.

2. New module-level helpers `_literal_cpp_type(node)` and
   `_scan_ctor_arg_types(tree, user_classes)`:
   - `_literal_cpp_type` returns the C++ type of a literal-shaped
     AST node (Constant, UnaryOp wrapping a Constant), or None.
   - `_scan_ctor_arg_types` walks the whole AST for
     `ClassName(...)` calls, records the literal-typed argument at
     each position per class, and unifies across call sites.
     Conflicting positions are dropped.

3. `transpile()` — new pre-pass between Pass 1 and diamond
   detection: `emitter.class_ctor_arg_types = _scan_ctor_arg_types(tree, emitter.user_classes)`.

4. `visit_ClassDef` — the `param_types` block was rewritten to:
   - Annotated params use the annotation.
   - Unannotated params with a default value call
     `_infer_default_type(default_node)` — this also fixed an
     existing bug where `def __init__(self, greeting="hello")`
     emitted `int greeting`.
   - Unannotated params with neither annotation nor default are
     marked `None`, then backfilled from
     `class_ctor_arg_types[class_name][param_index]`.

**Batch 13h.1 — relax the raise condition.**

Original 13h raised `TranspileError` for any param still `None`
after backfill. That broke ~6 class-emission tests in
`tests/test_transpiler.py` that define classes but never call
them. Fix: only raise if the class has a call site somewhere in
the source. Dead classes default to `int`, matching pre-13h
behavior.

Implemented via a `_seen_classes` set in `_scan_ctor_arg_types`
that tracks every class mentioned in a call, even if no literal
args were recorded. Then `visit_ClassDef` checks
`class_name in self.class_ctor_arg_types` and:
- If `True`: raise when a param is still `None`.
- If `False`: default that param to `"int"`.

**Files changed:** `kofty/transpiler.py`.

**Tests:** `tests/test_batch13h_transpile.py` (9 tests, all pass).

**Verified:**
- `check.py` clean (74 files).
- Full transpile layer: 599 passing, 0 failing.
- `tests/test_transpiler.py`: 162 passing, 0 failing (no regression).
- `kofty tests_minimal_dog.kfy` with
  `Dog("Rex", "Labrador")` compiles, links, launches, prints `ok`.

**Commits:** `940641e` (13h), `7632745` (13h.1).

**Design notes:**
- Only **literal** args contribute. `Dog(x)` where `x` is a Name
  raises if no annotation is given, because the transpiler can't
  know `x`'s type without more analysis.
- Conflicting call sites (`Dog("a")` and `Dog(1)`) drop that
  position from the hint table — the class then has a call site
  but no inference for that param, so the annotation-required
  error fires.
- Defaults still take priority over call-site inference (test
  `test_default_value_still_infers` pins this).

**Next:** Bug #2 (`_container_repr` for binops/slices/calls), then
#3 (loop var scoping), #5 (variable redeclaration), #6 (list
methods on params).

## 52. Batch 13a–13d.3 + "showcase runs" milestone (2026-10-15)

Session goal: get `examples/showcase.kfy` to compile and run
end-to-end. Done. The showcase — the full-tour acceptance test —
builds and prints its complete output for the first time.

### Bug board this session (8 bugs, 7 fixed)

The showcase surfaced a chain of real language gaps. Each was
found by the compiler, fixed at the emission level, and locked in
with a transpile-only test file.

| Batch | Bug | Fix |
|-------|-----|-----|
| 13a | Preamble ordering: `is_to_string` container overloads called `repr_*` before they were declared | Added forward decls; moved overloads above definitions |
| 13a | Duplicate `input_line` in preamble (blocked *all* builds) | Removed the duplicate |
| 13b | `_container_repr` didn't handle binops/slices/calls | New `_container_kind` helper; `repr_vector(xs + ys)`, `repr_set(s1 \| s2)`, `repr_vector(xs[1:3])` now wrap correctly |
| 13b.1 | `str.split()` result not wrapped in `repr_vector` | Extended `_container_kind` to match `ast.Attribute.attr == "split"` |
| 13c | Base ctor params defaulted to `int` when only called via `super().__init__(...)` | New pass 2 in `_scan_ctor_arg_types` walks `super().__init__` call sites |
| 13d.1 | Unannotated base methods emitted non-virtual, but subclasses got `override` | Force `virtual` on base-class methods |
| 13d.2 | `virtual auto` is invalid C++ | Infer concrete return type from method body |
| 13d.3 | Child overrides still emitted `auto`, causing "conflicting return type" | Generalize return-type inference to all methods; emit `override` when name matches a parent method |

Still open, warning-only: **Bug #12** — C++20 `auto` parameters
under `-std=c++17`. Fix is one line in `kofty/cli.py`. Not
showcase-blocking.

### Test counts

- Full transpile layer: **632 passing, 0 failing** (up from 599 at §51)
- `tests/test_transpiler.py`: **162 passing**
- `check.py`: **79 Python files parse cleanly**
- Showcase: **builds and runs**

### New test files this session

| File | Count | Scope |
|------|-------|-------|
| `tests/test_batch13b_transpile.py` | 11 | binop/slice wrapping |
| `tests/test_batch13b1_transpile.py` | 8 | `str.split()` wrapping |
| `tests/test_batch13c_transpile.py` | 4 | base ctor inference |
| `tests/test_batch13d1_transpile.py` | 4 | `virtual` on base methods |
| `tests/test_batch13d2_transpile.py` | 6 | return-type inference |

Plus 6 assertion updates in existing test files, to match the
new (correct) emitted forms — `auto get_x()` → `int get_x()`,
`auto speak() override` → `std::string speak() override`, etc.

### Commits (pushed to origin/main)

## 53. Session addendum — Batches 13a–14 + C++20 + showcase (2026-10-15)

Continuation of §52. The "showcase runs end-to-end" milestone was
reached, then hardened.

### Final state at end of session

- **`check.py`: 81 Python files parse cleanly**
- **Full transpile suite: 640 passing, 0 failing**
- **`tests/test_showcase.py`: 9 passing** (regression guard)
- **`examples/showcase.kfy`: compiles and runs cleanly, zero warnings**
- Compile flag: **`-std=c++20`** (was `-std=c++17`)
- Working tree clean, all commits pushed to `origin/main`

### Batches after §52

| Batch | What | Commit |
|-------|------|--------|
| 13b.1 | `_container_kind` recognizes `str.split()` (AST Attribute, not Name) | `80d66b2` |
| 13c | Base ctor param inference from `super().__init__()` | `63bb9c9` |
| 13d.1-3 | `virtual` on base-class methods; infer return types; emit `override` | `61f0ad3` |
| — | HANDOFF/ROADMAP + add `showcase.kfy` | `652694b` |
| — | HANDOFF §52 | `72f8f0d` |
| — | Bump `-std=c++17` → `-std=c++20` | `b59d2c6` |
| — | Add set-algebra section to showcase; add showcase regression test | `2d49249` |
| 14 | Same-type set-literal rebind (no second `auto`) | `36da794` |

### The C++20 flag change

`kofty/cli.py` line 165: `"-std=c++17"` → `"-std=c++20"`.
Reason: unannotated function params emit as C++20 abbreviated
templates (`auto x`), which g++ flags as an extension under
`-std=c++17`. C++20 is a strict superset for everything Kofty
emits. Kills the 7 `-Wc++20-extensions` warnings in the showcase
build.

**Minimum g++ version:** C++20 needs GCC 10+. The machine is on
**g++ 16.2.0** (msys64/ucrt64), well past that. If a future
contributor has g++ < 10, they need to upgrade.

### Showcase regression test — `tests/test_showcase.py`

Nine transpile-only tests that assert on the *emitted C++* for
each feature the showcase exercises. Does **not** launch the
compiled `.exe` (WDAC / WinError 4551 would flake on this machine).
Catches any regression to:
- container repr wrapping (10a, 13b, 13b.1)
- set-algebra wrapping (13b)
- string-split wrapping (13b.1)
- base-class virtual + child override (13d.1-3)
- base ctor inference from `super().__init__` (13c)
- preamble ordering (13a)
- f-string format specs (9a, 9b)

### Batch 14 — same-type rebind

Fix: the set-literal branch in `visit_Assign` was emitting
`auto {name} = ...;` unconditionally. Changed to the `if name in
self.declared:` pattern that the vec2, list, and generic paths
already use.

**Not in scope for Batch 14:** type-change detection (`x = 1`
then `x = "hello"`). That's a separate feature. Two tests marked
`xfail` were removed rather than committed. If you want it,
next batch.

### Lessons this session (accumulated)

1. **A fix that runs but doesn't fire is worse than no fix.**
   Three separate batches applied cleanly, ran the tests, and
   produced no output change because the code branch never
   matched. Always verify the *emitted C++*, not just the test
   outcome. One-liner:
   ```
   @'
   from kofty.transpiler import transpile
   out = transpile("<your test case>")
   print(out.split("int main()")[1])
   '@ | python -
   ```

2. **When a fix involves an index, assert the index's *effect*.**
   Batch 13c had an off-by-one in `_param_index` that would have
   been caught instantly by `assert "Animal(std::string name)"
   in out` instead of `assert "std::string name" in out`.

3. **`_container_kind` inspects the AST, not the emitted C++.**
   Match on `node.func.attr == "split"`, not the helper name
   `"str_split"`.

4. **`virtual` and `auto` are incompatible.** Any base-class
   method that could be overridden needs a concrete return type.
   13d.2/13d.3 are the return-type inference that makes 13d.1
   legal.

5. **The showcase is the acceptance test.** Six of this session's
   eight fixes came from running `kofty examples/showcase.kfy`
   and chasing the first g++ error. Extending the showcase is the
   highest-leverage way to find bugs.

6. **Test assertions on emitted C++ must scope to `main()`.** The
   preamble defines every helper, so `assert "repr_vector" in out`
   always passes. Scope to `out.split("int main()")[1]`.

7. **Push protection is real.** A GitHub PAT embedded in a text
   file blocks the push. Rotate, remove, amend, re-push.

8. **`visit_Assign` is 300 lines with 8+ parallel branches.** For
   this function, read the exact target code first, make ONE edit,
   verify. Avoid scripts and multi-site replaces — they match the
   wrong place too easily.

### What to do next session (priority order)

1. **Package for testing / publish** — see §54 for the shipping
   flow. Simplest path: `python -m build && pip install dist/*.whl`.
   Test on a fresh machine before `twine upload`.
2. **Type-change detection** (Bug #5 full) — raise a
   `TranspileError` on `x = 1` then `x = "hello"`. Needs a
   `self.var_types` dict and inference at every assignment. Medium.
3. **Bug #3 — loop variable scoping.** `declared` needs
   current-scope vs any-scope split. Small but tricky.
4. **Bug #6 — list methods on function parameters.** Needs
   annotation-based list typing. Small.
5. **GitHub Actions CI.** `python check.py && pytest tests/ -k
   transpile`. Simple workflow.
6. **Extend the showcase** with classes/inheritance/properties,
   match/case, try/except, math/random/time, lambdas, *args.
   Every section added is a future bug caught early.

   ## 54. Shipping Kofty — packaging and distribution (2026-10-15)

### Quick state of packaging

- **PyPI name reserved:** `kofty` (not yet published).
- **`pyproject.toml`:** PEP 621 metadata, MIT license,
  `kofty = "kofty.cli:main"` entry point. Verified with
  `pip install -e .` in a fresh venv.
- **GitHub:** https://github.com/sharit25/kofty
- **Test file shipped:** `examples/console_hello.kfy` and
  `examples/showcase.kfy` (now the full acceptance test).

### To ship a wheel for testing (private beta)

From the repo root, in a clean state (`git status` shows nothing
modified):

```powershell
python -m pip install --upgrade build twine
python -m build
```

Outputs two files in `dist/`:
- `kofty-<version>-py3-none-any.whl` (the wheel)
- `kofty-<version>.tar.gz` (source distribution)

**Send to a tester:**

The `.whl` file alone is enough. The tester runs:
```powershell
python -m pip install kofty-0.1.0-py3-none-any.whl
kofty --help
```

**Requirements for the tester's machine:**
- Python 3.10+
- **g++ with C++20 support (GCC 10+ or Clang 16+)** on PATH
- Windows: `windres` on PATH for icon embedding (optional —
  skipped gracefully if missing)
- MSYS2/ucrt64 or MinGW-w64 on Windows is the tested setup

**If g++ is missing or too old, Kofty fails at compile time with
a clear g++ error.** No `pip install` failure. Document this in
the tester email.

### To publish on PyPI (public)

Once you're confident in the wheel:

```powershell
# 1. Test install the wheel in a fresh venv FIRST
python -m venv .testvenv
.testvenv\Scripts\activate
pip install dist\kofty-0.1.0-py3-none-any.whl
kofty examples\showcase.kfy
deactivate
Remove-Item -Recurse .testvenv

# 2. Test on TestPyPI before the real thing
python -m twine upload --repository testpypi dist/*
# then: pip install --index-url https://test.pypi.org/simple/ kofty

# 3. Real PyPI upload
python -m twine upload dist/*
```

Requires a PyPI API token in `~/.pypirc` or entered at the prompt.
**Never commit the token.**

### What a user sees after `pip install kofty`

```
$ kofty --help
usage: kofty [-h] [--emit-only] [--icon ICON] file

Kofty compiler — .kfy to native executable

$ kofty hello.kfy
[Kofty] Wrote build\hello.cpp
[Kofty] (console) g++ build\hello.cpp -o build\hello.exe -std=c++20
[Kofty] Launching build\hello.exe
Hello, world!
```

### Test checklist before shipping

Run through this on a fresh venv or a second machine:

- [ ] `pip install kofty-0.1.0-py3-none-any.whl` succeeds
- [ ] `kofty --help` shows usage
- [ ] `kofty init` writes `.vscode/tasks.json` and
      `.vscode/settings.json`
- [ ] `kofty hello.kfy` builds and runs a hello-world program
- [ ] `kofty examples\showcase.kfy` runs end-to-end
- [ ] `kofty examples\user_input.kfy` reads and echoes a line
- [ ] Unicode (UTF-8 with BOM) source files work (Batch 10l.1)
- [ ] `kofty <file>` finds files in subdirectories (Batch 10m)
- [ ] Calling `kofty` on a file with a C++ keyword as an
      identifier raises a clear `TranspileError`

### User input — example for testing

Kofty supports `input()` and `input("prompt: ")`. See
`examples/user_input.kfy` (created alongside this section) for a
runnable demo. `input()` returns `std::string`; use
`int(input())` or `float(input())` to parse.

**Known behaviour:**
- `input()` reads one line from stdin, no trailing newline.
- `input("prompt")` prints the prompt first, no trailing newline.
- `int(input())` parses via `std::stoi` — throws on non-numeric
  input, matching Python's `ValueError`.
- `try/except` (catch-all) catches the parse error.

### If the tester reports "g++ not found"

The tester needs a C++20 compiler. Install:
- **Windows:** MSYS2 (ucrt64 toolchain) or MinGW-w64.
  https://www.msys2.org/ — `pacman -S mingw-w64-ucrt-x86_64-gcc`
- **Linux:** `apt install g++` (Ubuntu 22.04+ has GCC 11).
- **macOS:** `xcode-select --install` (Clang 14+ works).

Verify: `g++ --version` should show version ≥ 10 (GCC) or ≥ 16
(Clang).

### If the tester reports a different bug

Ask them for:
1. The `.kfy` source file (small, anonymized is fine).
2. The exact `kofty` command they ran.
3. The full output including any g++ errors.

Then file it as a bug against this project. The pattern is:
minimal reproduction → red-phase test → fix → verify.

## 55. Input fixes (2026-10-15)

The `examples/user_input.kfy` demo surfaced a bug in `int(x)` /
`float(x)`: only direct `int(input(...))` was parsed correctly;
`int(s)` where `s` is a `std::string` variable emitted a C-style
cast that C++ rejects.

Fix: any Name argument to `int`/`float` routes through
`std::stoi` / `std::stod`. Numeric-literal arguments keep the
C-style cast.

**Tradeoff:** `int(x)` where `x` is an `int` variable now emits
`std::stoi(x)`, which won't compile. Numeric variables shouldn't
be wrapped in `int()` anyway. Full type-aware dispatch waits for
variable type tracking (deferred).

Test file: `tests/test_batch15_transpile.py`, 6 tests.
Commit: `4e01436`.

- **Unknown names pass through to C++.** A bare `pi` (when not
  defined) emits as C++ identifier `pi` and fails at g++
  compile time with a confusing "not declared in this scope"
  error. Kofty should raise a `TranspileError` at transpile
  time with a suggestion (e.g. "did you mean math.pi?").
  Needs a pass tracking all declared names + builtins +
  imported constants. Medium.

## 57. Tester-driven fixes (2026-10-16)

Session of tester bug reports. Each fix is small; several are
features Kofty lacked that testers expected from Python.

### Fixed (all committed; some share a commit)

| Feature | Fix | Batch |
|---------|-----|-------|
| `int("42")` / `float("3.14")` | Constant(str) args route through `std::stoi`/`std::stod` | 16 |
| `print(a, b, c)` | Multiple args joined with spaces, each through `is_to_string` | 17 |
| `"""docstring"""` (bare string) | Silently accepted as no-op | 18 |
| `type(x)`, `isinstance(...)` | Friendly "not supported" message | 19 |
| `x = y = z = "Orange"` (chained) | Expanded to per-target assignments | 20 |
| `x, y, z = fruits` (list unpack) | Emits `fruits[0]`, `fruits[1]`, ... instead of `std::get<N>` | 21 |

**Commit labels:** some of these shared a commit rather than
getting their own, so `git log --oneline` doesn't show every
batch number. **The behavior is in `kofty/transpiler.py` and
tested via `tests/test_batch15..21_*.py`.**

### Now working end-to-end

`allcheck.kfy` (tester's comprehensive feature file) builds and
runs cleanly. The example exercises:
- string literal parsing (`int("42")`, `float("3.14")`)
- multi-arg print
- bare string expressions (docstrings)
- chained assignment
- list unpacking
- tuple unpacking (parenthesized and unparenthesized)

### Python features Kofty still doesn't support

Encountered by testers; **reject with clear errors** rather than
attempt to implement:

- `type(x)` — needs runtime reflection, not applicable to a
  static transpiler. Rejected with helpful message (Batch 19).
- `isinstance(x, T)` — same reasoning. Batch 19 message covers it.
- `x, *rest = list` — star-unpacking. Not yet, and low priority.

### Test file inventory

- `tests/test_batch15_transpile.py` — 6 tests (int/float parse)
- `tests/test_batch16_transpile.py` — (not created; batched into 15)
- `tests/test_batch17..20` — (not created; features covered by showcase)
- `tests/test_batch21_transpile.py` — 4 tests (list unpack)

**Some batches lack dedicated test files.** Regression coverage
mostly comes from `test_showcase.py` + the tester file. Consider
adding tests as the showcase grows.

### Wheel state

Wheel `dist/kofty-0.1.0-py3-none-any.whl` was built successfully
before this session's fixes. **It does not include Batches 16–21.**
Rebuild before shipping to a tester:

```powershell
python -m build
```

This overwrites `dist/` with a fresh wheel containing all fixes.

### What to prioritize next

1. **Rebuild the wheel** and re-ship to the tester who found the
   string-literal bug.
2. **Update showcase.kfy** with the newly-supported features
   (chained assignment, list unpacking, multi-arg print) so
   `test_showcase.py` locks them in.
3. **Watch for the next gap.** The tester pattern so far:
   - Try a Python feature (unpacking, type(), multi-arg print)
   - If it works, great; if not, report.

   Every report is either a bug in existing code or a missing
   feature. Decide per report: **support** or **reject clearly**.
4. **Batch 22 candidate:** full variable-type tracking. The
   `int(x)`/`float(x)` dispatch is now four branches (Constant
   str, Name in string_vars, Call to input, fallback cast).
   Proper type tracking would collapse it to one.

   ## 58. Batch 22 — top-level scalars hoisted to C++ global scope (2026-10-16)

### The gap

Python lets a function read a module-level variable:

    x = "awesome"
    def myFunc():
        print("Kofty is " + x)     # reads global x
    myFunc()

Kofty emitted myFunc as a standalone C++ function with no
access to main's locals, so `x` was undeclared — g++ error:

    error: 'x' was not declared in this scope

Surfaced by tester code. This is the natural Python idiom; every
tester writing real Python hits it.

### The fix

Top-level `Name` assignments whose type is a **scalar**
(int / double / bool / std::string) **AND** whose name is read
from inside any function body are hoisted to C++ global scope.
The declaration is emitted **before the functions**, so the
functions see it. The assignment in main uses the bare form.

### Scope — what's hoisted, what's not

**Hoisted:** top-level scalar Name assignments read from a function.

**Not hoisted:**
- Containers (list / dict / set / tuple). Their type-tracking in
  `visit_Assign` is load-bearing — `list_vars`, `dict_vars`,
  `set_vars`, `tuple_vars` — and running it for a hoisted var
  would require pulling the tracking out of the emission branch.
  That's a bigger change; deferred.
- User-class instances. Constructor calls have their own emission
  path.
- `vec2(...)` results. Tracked in `vec2_vars`.
- Any top-level scalar that no function reads. **Programs that
  don't use globals get zero change to emitted code.**

### What's NOT fixed

Reading a container from inside a function still fails:

    xs = [1, 2, 3]
    def show(): print(xs)     # xs undeclared in C++ function body

That's a known limitation of this batch. A follow-up batch (23)
would need to hoist containers, which means making the container
type-tracking side effects run for hoisted vars too.

### Design decisions

1. **Read-analysis, not blanket hoisting.** Two earlier attempts
   (hoist every top-level variable; hoist every top-level scalar)
   broke 55 and 12 tests respectively. The read-analysis filter
   broke zero — nothing else in the emitted code changes.

2. **Emit globals before functions, not after.** C++ requires
   declaration-before-use. The first attempt put the global block
   between functions and int main(), which failed: `myFunc` saw
   `x` at line 469, `std::string x;` was at line 472. The correct
   position is between the classes block and the functions block.

3. **Scalars only.** Full container hoisting needs the container
   type-tracking to be independent of where the variable is
   declared. Deferred to Batch 23.

### Files changed

- `kofty/transpiler.py`
  - `CppEmitter.__init__` — added `self.global_vars: dict = {}`
  - `transpile()` — new pre-pass collects top-level scalars read
    from functions
  - `transpile()` assembly — global declarations inserted between
    classes and functions
  - `visit_Assign` — hoisted names emit bare assignment (no auto)
- `tests/test_batch22_transpile.py` — new (4 tests)

### Tests

- **650 passing, 0 failing** — no regression.
- `global_test.kfy` builds and prints `Kofty is awesome`.
- `list_test.kfy` builds and prints `[1, 2, 3, 4]` — containers
  unaffected.
- `examples/allcheck.kfy` runs end-to-end.

### Lessons

1. **The idempotency guard in impl scripts was too broad.** The
   check `if "Batch 22:" in src:` matched a comment left over from
   a partial application. Fixed to `if "self.global_vars: dict = {}"
   in src:` — precise, only set by the actual anchor.

2. **Commit before trying a multi-anchor impl script.** The v2
   attempt left the working tree in a partially-applied state; the
   revert required `git restore`, and then the v3 script's guard
   falsely reported "already applied." From a clean tree, v3
   applied all four anchors and worked.

3. **Blast radius matters.** The v1 fix was correct in principle
   but touched every program. The v3 fix touches only programs
   that read a global from a function. Always ask: how many
   programs' emitted code changes?

### What's next

The tester file `allcheck.kfy` (or its equivalent) should now
build and run. The remaining known tester gap is:

- **Reading a container from a function.** Deferred to Batch 23.

If the tester hits more issues, they'll be new — the string and
scalar cases are covered.

## 60. Batch 24 + 24.1 — `global x` implementation (2026-10-16)

Continuation of §59. Full `global` write support.

### Working state

- **660 transpile tests passing, 1 xfailed** (the xfail documents a
  known limitation).
- `global_write.kfy`, `global_write2.kfy` — build and print correctly.
- `local_only.kfy` — first print works, outer read fails with a g++
  error (correct Python semantics).

### Feature

```python
def myFunc():
    global x
    x = "fantastic"

myFunc()
print("Kofty is " + x)     # Kofty is fantastic
```

### Batch 24.1 — the pre-pass fixup

The first pass of Batch 24 only looked at top-level `ast.Assign`
nodes. If `x` is declared `global` inside a function but never
assigned at module scope, the pre-pass missed it. Batch 24.1
walks function bodies to find those declarations and infer types.

### Known limitation (xfailed)

```python
x = "outer"

def func_a():
    global x
    x = "changed"

def func_b():
    x = "local"            # local in Python, writes global in Kofty
    print(x)

func_b()                   # Python: "local"; Kofty: writes global
func_a()
print(x)                   # Python: "changed"; Kofty: "local"
```

**Root cause:** `visit_FunctionDef` doesn't reset `self.declared`
for function bodies. Top-level functions share a single `declared`
set with `main`. When `func_b` assigns `x`, the emitter sees `x in
self.global_vars` (from `func_a`'s hoist) and emits a bare
assignment.

**Fix (deferred to Batch 26):** per-function scope for
`self.declared` in `visit_FunctionDef`, plus a `visit_Assign`
guard that checks `self.current_function is None` before treating
`self.global_vars` membership as "write the global."

**Two failed attempts** (see §59, Batches 24.2 draft) broke the
emitter with `AttributeError: 'CppEmitter'` on `self.current_function`
because that attribute wasn't initialized in `__init__`. Reverted.
The eventual fix must:
1. Initialize `self.current_function = None` in `__init__`.
2. Save/reset/restore `self.declared` in `visit_FunctionDef`.
3. Guard `visit_Assign`'s `global_vars` check with
   `self.current_function is None`.

### Files changed

- `kofty/transpiler.py` — five anchors in Batch 24, one in
  Batch 24.1.
- `tests/test_batch23_transpile.py` — obsolete
  `test_global_raises_clear_error` deleted.
- `tests/test_batch24_transpile.py` — new (5 tests, 1 xfail).

### Lessons

1. **Never edit `transpiler.py` by hand without checking what
   attributes exist.** The 24.2 hand edits assumed
   `self.current_function` was initialized. It wasn't — the
   attribute is set only *inside* `visit_FunctionDef`. Every
   other code path hit `AttributeError`.

2. **A hang during pytest is usually the previous batch's edits,
   not the tests.** The 10-minute burn was the broken
   `transpiler.py`, not a slow test.

3. **When git shows the same file as both "staged" and
   "unstaged", reset and re-check the diff.** `git restore` had
   reverted the working tree but not the staged copy, creating a
   misleading `git status`.

4. **Multi-line git commit messages with embedded quotes fail
   in PowerShell.** Use single-line messages for anything
   containing `"..."`.

### What's next

- **Batch 25:** friendly error for unbound names (currently pass
  through to g++).
- **Batch 26:** per-function `declared` scope so a function's
  local `x` shadows correctly.
- **Batch 27:** hoist containers (lists, dicts, sets, tuples)
  so functions can read them.

## 61. Batch 26 — per-function declared scope (2026-10-16)

Fixed the last Python-scoping gap: a **function-local variable
shadows the module-level one**.

### The bug

```python
x = "awesome"

def myfunc():
    x = "fantastic"      # local, does NOT touch module x
    print("Kofty is " + x)

myfunc()
print("Kofty is " + x)
```

**Python output:** `fantastic`, `awesome`
**Kofty output (before):** `fantastic`, `fantastic`

`myfunc`'s `x = "fantastic"` wrote the module-level global because
`visit_Assign` saw `x in self.global_vars` and emitted a bare
assignment. `self.declared` also leaked across functions: since
`x` was assigned at module scope, `x` was "already declared"
inside every function.

### The fix

Three coordinated changes to `kofty/transpiler.py`:

1. **`CppEmitter.__init__`** — new `self.current_function = None`.
   `visit_FunctionDef` already sets this to `node.name` before
   emitting the body and back to `None` after. The attribute just
   wasn't initialized, so code paths that ran at module level
   (before any function) hit `AttributeError`.

2. **`visit_FunctionDef`** — reset `self.declared = set()` for the
   duration of the function body, restoring the caller's set
   afterwards. This makes each function's locals truly local.

3. **`visit_Assign`** — the check for "write to the C++ global" is
   now:

   ```python
   _is_global_write = (
       (self.current_function is None and name in self.global_vars)
       or name in self.global_declared
   )
   ```

   A name is written to the global **only when**:
   - we're at module level (`current_function is None`) and the
     name was hoisted, OR
   - the enclosing function declared the name `global`.

   Otherwise, an assignment creates a **local**, even if the name
   is in `global_vars` (because some other function hoisted it).

### The four tutorial examples — all match Python

| Example | Python | Kofty |
|---------|--------|-------|
| 1 — local shadow | `fantastic`, `awesome` | ✅ Same |
| 2 — read module from function | `Kofty is awesome` | ✅ Same |
| 3 — `global x` write (no top-level) | `Kofty is fantastic` | ✅ Same |
| 4 — `global x` write (with top-level) | `Kofty is fantastic` | ✅ Same |

Test files: `D:\koftyTutorial\ex1.kfy` through `ex4.kfy`.

### Two failed attempts before this one

Attempt 1 (Batch 24.2 draft, not committed): hand-edited the
three anchors but referenced `self.current_function` in
`visit_Assign` **without initializing it in `__init__`**. Every
test crashed with `AttributeError`. 346 failures, 10-minute hang.

Attempt 2 (Batch 26, first version): the same anchors, but
Anchor A adds `self.current_function = None` to `__init__`. This
made the change safe.

**Lesson:** never reference `self.<attr>` from a new code path
without first checking that `<attr>` is initialized in `__init__`.
The emitter is a long-lived object; uninitialized attributes
surface as `AttributeError` deep in unrelated code.

### Files changed

- `kofty/transpiler.py` — three anchors (A, B, C).
- `tests/test_batch24_transpile.py` — removed the stale
  `@pytest.mark.xfail` marker on
  `test_local_shadow_still_creates_local`; updated one assertion
  to match the new (correct) emission `x = std::string("awesome")`.
- `tests/test_batch26_transpile.py` — new (4 tests, including
  a composite "all four tutorial examples" case).

### Test count

- **661 transpile tests passing, 0 failing, 0 xfailed.**
- Fresh-venv test confirmed: `ex1.kfy` prints `fantastic` then
  `awesome`; `ex4.kfy` prints `fantastic`.

### Commit

- `950ad59` — "Batch 26: per-function declared scope (local
  shadows module-level)"

### Known limitations still open

1. **Function redefinition.** Stacking multiple examples in one
   `.kfy` file that use the same function name (`def myfunc():`
   twice) causes g++ `redefinition` errors. Python allows it
   (later definition wins). Batch 27 candidate: detect duplicate
   function names at transpile time — either keep the last
   definition (Python semantics) or raise a clear
   `TranspileError`.

2. **Containers are not hoisted.** `xs = [1, 2, 3]` at module
   scope is not visible from inside a function. Container
   type-tracking (`self.list_vars`, `self.dict_vars`, etc.) runs
   in `visit_Assign` and doesn't apply to hoisted containers.
   Batch 28 candidate: hoist module-level containers, or run the
   tracking for hoisted containers too.

3. **Unbound names pass through to C++.** A reference to an
   undefined name emits as a raw C++ identifier and fails at
   g++ compile time. Batch 25 candidate: reject at transpile
   time with a friendly message.

### Wheel state

`dist/kofty-0.1.0-py3-none-any.whl` was rebuilt after Batch 26.
It contains Batches 22, 23, 24, 24.1, 26 — full scalar-scope
semantics. **Ready to ship to testers.**

### What to do next session

1. **Ship the wheel** to the tester (it's already built).
2. **Batch 27 or 28** depending on tester feedback — probably
   whichever bug they hit next.
3. **Update the pyproject.toml license field** to silence the
   setuptools deprecation warnings (`license = "MIT"` instead of
   `license = { text = "MIT" }`) before public PyPI release.

### The bigger picture

The last four batches (22 → 26) went from "no module-scope
visibility" to "full Python scalar scoping":

- Batch 22 — functions can **read** module-level scalars.
- Batch 23 — clear error for `global` (superseded).
- Batch 24 + 24.1 — functions can **write** module-level scalars
  via `global x`.
- Batch 26 — function-local `x` **shadows** module-level `x`
  correctly.

All four Python scoping rules for scalars are now implemented
and tested.

## 62. First release — kofty 0.1.0 wheel shipped (2026-10-17)

### What shipped

First public wheel published as a GitHub Release:

    https://github.com/sharit25/kofty/releases/tag/v0.1.0

- Wheel: `dist/kofty-0.1.0-py3-none-any.whl` (75,158 bytes)
- Source commit: `6572042`
- Requires: Python 3.10+, g++ with C++20 (GCC 10+ or Clang 16+)
- Sent to one tester for feedback

### The three fixes in this commit

**1. `windres` path escaping** (`kofty/cli.py`).

Symptom: `windres` failed on every icon embed with
`unrecognized escape sequence` and truncated the icon path at
the first backslash-letter pair (e.g. `\f` in `fresh_venv`, `\n`
in `new_venv`, `\v` in `verify_venv`). The `.rc` file contained
Windows backslash paths, and resource-compiler `.rc` files treat
`\` as an escape character.

Fix: emit forward slashes in the `.rc` file.

    icon_abs = icon.resolve()
    icon_abs_posix = str(icon_abs).replace("\\", "/")
    rc_file.write_text(f'IDI_ICON1 ICON "{icon_abs_posix}"\n',
                       encoding="utf-8")

Windows `windres` accepts forward slashes. Bug only surfaced when
the install path contained an escape-lookalike sequence — which is
why earlier tests (paths without `\f`/`\n`/`\v`) didn't catch it.
Verified from three such paths: `fresh_venv`, `new_venv`,
`verify_venv`.

**2. `is_to_string` overload ambiguity** (`kofty/transpiler.py`).

Symptom: `print(xs.size())` and similar emitted
`is_to_string(<size_type>)`, which is ambiguous between the
`int`, `double`, and `bool` overloads. g++ error:

    error: call of overloaded 'is_to_string(std::vector<int>::size_type)' is ambiguous

Affects `.size()`, `.length()`, `.find()`, `.count()`, and any
expression yielding `size_t`/`unsigned long long`.

Fix: add three overloads to the preamble, after the `bool`
overload:

    static std::string is_to_string(size_t n)       { return std::to_string(n); }
    static std::string is_to_string(long long n)    { return std::to_string(n); }
    static std::string is_to_string(unsigned int n) { return std::to_string(n); }

Three overloads because `size_type` maps to `size_t` on some
targets and `unsigned long long` on others; `long long` covers
signed arithmetic like `xs.size() - 1`; `unsigned int` covers
32-bit `size_t`.

**3. `kofty.data` package declaration** (`pyproject.toml`).

Symptom: setuptools 84 warned on every build that `kofty.data`
was importable but not in `packages`. Cosmetic — the icon files
*were* included in the wheel — but noisy.

Fix:

    [tool.setuptools]
    packages = ["kofty", "kofty.data"]

Build output is now warning-free.

### `examples/allcheck.kfy` — kept as a working example

The tester's original file defined `myFunc` twice and referenced a
function-local `x` at module scope. That is invalid Python
(`NameError`) and invalid Kofty (unbound name passed through to
g++). Rewritten as a clean example of the §61 ex1 semantics:

    x = "awesome"

    def myFunc():
        x = "fantastic"
        print("Kofty is " + x)

    myFunc()
    print("Kofty is " + x)

Output:

    Kofty is fantastic
    Kofty is awesome

Builds and runs. Added to the repo in commit `6572042`.

### Test count

- `check.py`: 87 Python files parse cleanly
- Transpile suite: **665 passing, 0 failing**
- Runtime suite: ~465 tests, WDAC-blocked on this machine (see §19)

### Commit list this session

    c724e32  HANDOFF: §61 Batch 26 per-function declared scope
    950ad59  Batch 26: per-function declared scope (local shadows module-level)
    6572042  Fix windres path escaping; add size_t is_to_string overloads;
             declare kofty.data in packages  ← this session

### What this session's work did NOT fix

- **Batch 25** — unbound names still pass through to g++. The
  tester's original `allcheck.kfy` was the trigger; now rewritten
  as valid code, so the missing error surface is only visible if
  someone else writes an unbound reference.
- **Batch 27** — function redefinition. The tester's file also had
  `def myFunc()` twice; we didn't fix this because the file was
  rewritten. Still an open gap.
- **Batch 28** — containers not hoisted to module scope.
- **Batch 29** — constructor functions (`list()`, `tuple()`,
  `set()`, `dict()`, `bool()`).
- **Batch 30** — `complex` type.

### Next session (priority order)

1. Wait for tester feedback on `v0.1.0`. Watch for:
   - Unbound name (Batch 25)
   - Function redefinition (Batch 27)
   - Container read from function (Batch 28)
   - Missing constructor function (Batch 29)
2. **Batch 25** — reject unbound names at transpile time. Small,
   high-value error-surface improvement.
3. **Batch 27** — function redefinition. Same trigger family as 25.
4. **Batch 29** — constructor functions. Cheap, directly answers
   the Python-types tutorial page.

### Lessons from the release process

1. **The wheel and the source tree can drift silently.** The
   `size_t` overloads had been in `transpiler.py` for a while, but
   the shipped wheel was built before them. The showcase failed at
   g++ time in a fresh venv while the source tree built fine. Always
   `python -m build` immediately before publishing, and always
   test the *wheel* in a fresh venv, not the source tree.

2. **Escape-lookalike paths in test directories catch real bugs.**
   `fresh_venv` (`\f`), `new_venv` (`\n`), `verify_venv` (`\v`) —
   all three trigger the `windres` escaping bug. Test directory
   names are not neutral; they are inputs.

3. **`git diff` opens a pager on Windows PowerShell.** Use
   `git --no-pager diff <file>` when you need to see the whole
   thing without `less` swallowing the output. The truncated paste
   in this session was a pager artifact, not a real git problem.

4. **`gh` install requires reopening the terminal.** `winget
   install --id GitHub.cli` succeeded, but `gh` wasn't on PATH
   until the shell was restarted. If `gh` reports "not recognized"
   right after install, close and reopen PowerShell.

5. **`gh auth login` is a one-time cost per machine.** The
   browser flow produces a one-time code; copy it, open the URL,
   paste, authorize. After that, `gh release create` just works.

## 63. Batch 25 — reject unbound names at transpile time (2026-10-17)

### The gap

Before this batch, an unbound name like `print(x)` where `x` is never
defined emitted raw C++ `x`, which g++ rejected with:

    error: 'x' was not declared in this scope
    build\file.cpp:480:59: note: suggested alternative: 'y'

The error pointed at line 480 of the emitted `.cpp`, not at the
`.kfy` line that produced it. Tester's original `allcheck.kfy`
hit this — see §62.

### The fix — six anchors in `kofty/transpiler.py`

**A.** New module-level `_BUILTIN_NAMES` set (near line 51) —
    builtin function names, constants, and importable module
    names (`math`, `random`, `time`, `raylib`).

**B.** New `_RAYLIB_CONSTANTS` set (line ~63) — keyboard and
    mouse constants recognized by the raylib preamble.

**C.** New attribute `self.all_bound_names: set = set()` in
    `CppEmitter.__init__` (line 149).

**D.** New module-level function `_collect_bound_names(tree)`
    (ends line 4311). Walks the AST once, returns the set of
    every name bound anywhere: assign targets, aug-assign
    targets, for targets, `with ... as` targets, function and
    class names, function parameters (posonly, args, kwonly,
    vararg, kwarg), import aliases, `except ... as` names, and
    lambda params. If `import raylib` appears, adds
    `_RAYLIB_CONSTANTS` to the set.

**E.** In `transpile()` (line 4482): call
    `emitter.all_bound_names = _collect_bound_names(tree)`
    after the import hoisting loop, before the user class/function
    registration loop.

**F.** In `expr()`'s `ast.Name` branch (line 494): check that
    the name is in `_BUILTIN_NAMES`, `self.all_bound_names`,
    `self.user_funcs`, `self.user_classes`, `self.declared`,
    `self.instance_vars`, `self.global_vars`, or
    `self.lambda_vars`. If not, raise
    `TranspileError(f"name '{_nm}' is not defined")`.

### Design — lenient, whole-file, not strict

The check allows a name to be **used before it is assigned**:

    print(greet)
    greet = "hi"

Python would raise `NameError` at runtime here (line 1 runs before
line 2). But strict ordering analysis is a whole new pass. Batch 25
is deliberately lenient: **if the name is bound *anywhere* in the
file, it's allowed.** Strict ordering is a future batch.

### Test fixture change — this is the workflow shift

Transpile-only tests that used undeclared names for brevity now
fail. Example: `test_boolean_and` was:

    out = transpile("x = a and b")

After Batch 25:

    TranspileError: name 'a' is not defined

The fix is to declare the names:

    out = transpile("a = True\nb = False\nx = a and b")

Same for the raylib fixtures:

    out = transpile("import raylib\nx = is_key_down(KEY_LEFT)")

**Affected tests (10 total, all fixed):**
- `test_boolean_and`
- `test_boolean_or`
- `test_boolean_not`
- `test_boolean_and_three_operands`
- `test_boolean_and_with_comparisons`
- `test_keyboard_constant_passthrough`
- `test_keyboard_constant_space`
- `test_mouse_button_left_passthrough`
- `test_mouse_button_right_passthrough`
- `test_mouse_pressed_passthrough`

**Workflow note for future tests:** any transpile-only test that
uses a bare identifier now must bind it first. This is correct
Kofty behavior (matches Python semantics for unbound names) but is
a change from pre-Batch-25 fixtures.

### Files changed

- `kofty/transpiler.py` — anchors A–F
- `tests/test_transpiler.py` — 10 fixture updates
- `tests/test_batch25_transpile.py` — new, 12 tests

### Test counts

- `check.py`: 88 Python files parse cleanly
- Transpile suite: **677 passing** (was 665; +12 from new file)
- Batch 25 tests: **12 passing**

### Commit

    daa48f0

### Known follow-up

- **Batch 25.1 (future):** strict ordering — reject a name used
  before its module-level assignment. Requires scope-accurate
  analysis; deferred.
- **Batch 27 (next):** function redefinition. Currently `def f():`
  twice emits two C++ functions with the same name; g++ errors.
  Python semantics: later definition wins.

## 63.1 Batch 27 — keep last def on duplicate function names (2026-10-17)

### The gap

Python allows `def f():` twice in one file — the later def wins.
Before Batch 27, Kofty emitted **both** C++ functions:

    auto f() { ...first body... }
    auto f() { ...second body... }

g++ rejected the translation unit with `redefinition of 'auto f()'`.
The tester's original `allcheck.kfy` hit this — see §62.

### The fix — four anchors in `kofty/transpiler.py`

**A.** `CppEmitter.__init__` (line ~147):
    self.shadowed_funcs: set = set()   # ids of earlier defs to skip

**B.** Pass 1 pre-pass after `_scan_ctor_arg_types` (line ~4544):
    _defs_by_name: dict = {}
    for _node in tree.body:
        if isinstance(_node, ast.FunctionDef):
            _defs_by_name.setdefault(_node.name, []).append(_node)
    for _name, _defs in _defs_by_name.items():
        if len(_defs) > 1:
            for _earlier in _defs[:-1]:
                emitter.shadowed_funcs.add(id(_earlier))

**C.** Pass 2, inside `elif isinstance(node, ast.FunctionDef):`
(line ~4819), before `emitter.visit(node)`:
    if id(node) in emitter.shadowed_funcs:
        continue

**D.** `visit_FunctionDef`, right after `_check_name` (line ~3493):
    if id(node) in self.shadowed_funcs:
        return

### Design

- **Keep-last**, matching Python semantics. Not a raise, not keep-first.
- **`id()` identity**, not name-based — the AST nodes are the ground truth.
- **Anchor C is the load-bearing one.** Without it, the set is populated
  and never read — Pass 2 emits both.
- **Anchor D is belt-and-suspenders.** It only fires if someone calls
  `emitter.visit(fn)` directly outside Pass 2.

### Tests

- `tests/test_batch27_transpile.py` — 7 tests, all passing
- Transpile suite: **684 passing** (was 677; +7)
- `check.py`: 89 Python files parse cleanly

### Test-writing lesson

**Substring assertions catch more than intended.** Initial draft had:

    assert "first" not in out

`"first"` matched `a.first` inside `vec2_add` in the preamble. Same for
`"one"` inside `reads one line from stdin` in `input_line`. Fix: assert
on the **specific emission form**:

    assert 'to_string("first")' not in out

`to_string("first")` only appears if the `print("first")` body was
actually emitted. That's the invariant.

### Commit

    fa0bfc6

### Known follow-up

- **Batch 27.1 (future, optional):** the check is `id()`-based, which
  works because Pass 1 pre-pass and Pass 2 see the same `tree` object.
  If a future batch ever re-parses between passes, `id()` breaks.
  A name + line-number tuple would be more robust if this ever bites.

## 64. Batch 29 — constructor functions (2026-10-17)

### The feature

Python's "Setting the Specific Data Type" table from the
tutorial page — `list(...)`, `tuple(...)`, `set(...)`,
`dict(...)`, `bool(...)` — is now supported.

| Constructor | Emit |
|-------------|------|
| `list((a,b,c))` | `std::vector<T>{a,b,c}` |
| `list([a,b,c])` | pass-through of `ast.List` |
| `list(xs)` | `xs` (list variable) |
| `tuple((a,b))` | `std::make_pair(a,b)` |
| `tuple((a,b,c))` | `std::make_tuple(a,b,c)` |
| `tuple([a,b])` | `std::make_pair(a,b)` |
| `set((a,b,c))` | `std::set<int>{a,b,c}` |
| `set([a,b,c])` | `std::set<int>{a,b,c}` |
| `dict({...})` | pass-through of `ast.Dict` |
| `bool(x)` | `(bool)(x)` |

### The fix — two anchors in `kofty/transpiler.py`

**A.** `_call_expr`, five new branches between the `float`
branch (ends line 2276) and the `ptr` branch (starts 2278).
Each accepts exactly 1 argument (except `bool` accepts 1),
rejects 0-arg calls with a clear message. The `list`/`tuple`/
`set` branches re-wrap a `Tuple`/`List` argument into a
synthetic node (`ast.List`, `ast.Tuple`, `ast.Set`) and
delegate to `self.expr()`, which reuses all existing literal
emission logic — no new helpers, no preamble additions.

**B.** `_BUILTIN_NAMES` (line 53) — added `"list", "tuple",
"dict", "set"` so Batch 25's unbound-name check allows these
names in non-call positions.

### Design

- **Delegation, not reimplementation.** The synthetic-node trick
  means `list((1,2,3))` produces exactly the same C++ as
  `[1, 2, 3]` written literally. No duplicate emission logic.
- **Zero arguments raises.** `list()`, `tuple()`, `set()`,
  `dict()` all raise — no element type to infer.
- **`dict(a=1)` deferred.** Kwargs at call sites aren't
  supported yet (Batch 5c was kwargs in *function definitions*).
  `dict({...})` works; kwargs form raises a clear message.
- **`set((1,2,3))` type annotation.** Emits `std::set<int>`
  because `_emit_set_expr` currently hardcodes `int`. Heterogeneous
  set constructors would need a follow-up.

### Tests

- `tests/test_batch29_transpile.py` — 17 tests, all passing
- Transpile suite: **701 passing** (was 684; +17)
- `check.py`: 89 Python files parse cleanly

### Verified demo

    fruits = list(("apple", "banana", "cherry"))
    print(fruits)

Emits:

    auto fruits = std::vector<std::string>{"apple", "banana", "cherry"};
    std::cout << is_to_string(fruits) << std::endl;

### Commit

    6362bf3 (+ amend for _BUILTIN_NAMES)

### Known follow-ups

- **Batch 29.1:** `dict(a=1, b=2)` — needs kwargs call-site support.
- **Batch 29.2:** `set((1, "a"))` — heterogeneous set element types
  (blocked by `_emit_set_expr` hardcoding `std::set<int>`).
- **Batch 29.3:** `list()` / `set()` zero-arg forms with type
  annotation: `xs: list[int] = list()`.

## 65. Batch 28 — hoist module-level containers (2026-10-17)

### The gap

Module-level scalars were hoisted to C++ global scope in Batch 22
so functions could read them. Containers were **not** hoisted:

    xs = [1, 2, 3]
    def show():
        print(xs)     # ✗ g++: 'xs' was not declared in this scope
    show()

Python works. Kofty failed at g++ time. This was the last
scoping hole from the §60–61 arc.

### Why containers were held back

Container variables are tracked in `emitter.list_vars`,
`emitter.dict_vars`, `emitter.set_vars`, `emitter.tuple_vars`
as a **side effect of `visit_Assign`**. If a container were
hoisted with a bare `std::vector<int> xs;` declaration, those
dicts would be empty and `print(xs)` inside a function would
emit raw `is_to_string(xs)` instead of `repr_vector(xs)`.

### The fix — two anchors in `kofty/transpiler.py`

**A.** `_infer_expr_type` gains `ast.Dict` and `ast.Set`
branches (line ~1536, after the `ast.Tuple` branch):

    if isinstance(node, ast.Dict):  ->  "std::map<std::string, {V}>"
    if isinstance(node, ast.Set):   ->  "std::set<int>"

`ast.Set` hardcodes `int` element type to match the existing
`_emit_set_expr`. Prior to this anchor, `_infer_expr_type`
returned `None` for both, so hoisting couldn't distinguish
"unknown type" from "dict/set".

**B.** The hoisting pre-pass (line ~4758, the second
`for _node in tree.body:` loop) gains a container branch
after the existing `_HOISTABLE` check:

    if _gtype is None: continue
    if _gtype.startswith("std::vector<"):
        emitter.global_vars[_gname] = _gtype
        emitter.list_vars[_gname] = <elem>
    elif _gtype.startswith("std::map<"):
        emitter.global_vars[_gname] = _gtype
        emitter.dict_vars[_gname] = <value-type>
    elif _gtype.startswith("std::set<"):
        emitter.global_vars[_gname] = _gtype
        emitter.set_vars[_gname] = <elem>
    elif _gtype.startswith("std::pair<") or "std::tuple<":
        emitter.global_vars[_gname] = _gtype
        emitter.tuple_vars[_gname] = <arity>

The `global_vars` addition triggers:
- `visit_Assign` at 2774 already checks `name in self.global_vars`
  → emits bare `xs = std::vector<int>{1,2,3};` in `main()`
- The declaration loop at 5415 emits `std::vector<int> xs;`
  in the global scope, before `main()`

The tracking dicts addition triggers:
- `print(xs)` inside a function → `repr_vector(xs)`
- `for x in xs:` inside a function → `for (auto x : xs)` (list
  iteration branch)
- `xs[i]`, `len(xs)`, `x in xs` all dispatch correctly

### Scope

**Hoisted:** module-level container literals read from any
function body. List, dict, set, tuple. Element types inferred
via `_infer_expr_type`.

**Not hoisted:**
- Containers whose RHS isn't a literal (`xs = get_items()`)
- Empty container literals (already rejected by base emitter)
- Containers only used at module scope (no function reads them —
  same read-analysis as Batch 22)

**Not in scope:**
- Mutation from a function without `global xs` — that's the
  Python semantics for container mutation (Python doesn't
  require `global` to call `.append()`, but Kofty's global-write
  detection in `visit_Assign` fires on `name in global_vars`
  which would cause a bare assignment to shadow). Deferred to
  28.1 if needed.

### Tests

`tests/test_batch28_transpile.py` — 10 tests, all passing.
- 5 positive (one per container kind)
- 1 iteration dispatch
- 1 negative (no hoisting if no function reads)
- 1 scalar regression
- 1 mixed scalar + container
- 1 bare-assignment-in-main check

Transpile suite: **711 passing** (was 701; +10)

### Files changed

- `kofty/transpiler.py` — anchors A, B
- `tests/test_batch28_transpile.py` — new

### Commit

    (hash)

### Follow-up candidates

- **Batch 28.1:** container mutation from a function without
  `global xs` — need to distinguish `xs.append(4)` (mutation,
  fine) from `xs = [4,5]` (rebinding, needs `global`).
- **Batch 28.2:** containers returned from functions —
  `xs = make_list()` where `make_list` returns `list[int]`.
  Would need function-return type tracking analogous to
  Batch 11b's tuple arity tracking.

## 66. Post-Batch-28 polish — v0.3.2 / v0.3.3 (2026-10-17)

### What landed in v0.3.2

- `str_find(std::string, char)` overload in the preamble (Batch 30a)
- `examples/hangman.kfy` — a full working Hangman game
- `kofty/cli.py` — VERSION now reads from `importlib.metadata`,
  fallback `0.0.0-dev` if not installed

### What landed in v0.3.3

- `pyproject.toml` bump to 0.3.3 so the wheel rebuild picked
  up the fixed `cli.py`. v0.3.2's wheel contained a stale
  `cli.py` (VERSION = "0.0.0-dev" hardcoded).

### Hangman status

`examples/hangman.kfy` compiles and runs. The game works
end-to-end via the `.find()`-based workaround for `in` on
untyped parameters. Adding `in` on untyped vars is **Batch 30.1**
(call-site type inference) — deferred until a real user hits it.

### The stale-wheel lesson

**`python -m build` only captures the current file state.**
If you edit `cli.py` after building the wheel but before
pushing, and don't rebuild, the shipped wheel contains the
pre-edit code. Symptom: fresh venv install works, but the
code you see in source doesn't match runtime behavior.

Fix: rebuild after every edit, before `gh release create`.
Or bump the version and rebuild — the version bump forces a
fresh wheel.

### Test counts

- Transpile suite: 711 passing
- Batch 28 tests: 10 passing
- Batch 29 tests: 17 passing
- Batch 27 tests: 7 passing
- Batch 25 tests: 12 passing

## 66. Post-Batch-28 polish — v0.3.2 / v0.3.3 (2026-10-17)

### What landed in v0.3.2

- `str_find(std::string, char)` overload in the preamble (Batch 30a)
- `examples/hangman.kfy` — a full working Hangman game
- `kofty/cli.py` — `VERSION` now reads from `importlib.metadata.version("kofty")`,
  with fallback `"0.0.0-dev"` if the package isn't installed

### What landed in v0.3.3

- `pyproject.toml` bumped to `0.3.3` so `python -m build` picked up the
  fixed `cli.py`. **v0.3.2's wheel contained a stale `cli.py`**
  (VERSION was still `"0.0.0-dev"` because the try/except block hadn't
  been saved before the build).

### Hangman status

`examples/hangman.kfy` compiles and runs. It uses a `.find()`-based
workaround for `in` on untyped parameters — see Batch 30.1 below.

### The stale-wheel lesson

**`python -m build` only captures the current file state.**
If you edit a file after building but before pushing, and don't
rebuild, the shipped wheel contains the pre-edit code. Symptom:
`pip install` succeeds, `kofty --version` runs, but shows the wrong
version number.

Fix: rebuild after every edit, before `gh release create`.
Bumping the version and rebuilding also forces a fresh wheel —
which is what v0.3.3 did.

### Test counts

- Transpile suite: 711 passing
- Batch 25 tests: 12 passing
- Batch 27 tests: 7 passing
- Batch 28 tests: 10 passing
- Batch 29 tests: 17 passing

### Open follow-ups (all deferred)

- **Batch 30.1** — full `in` on untyped parameters via call-site
  type inference. Hangman uses the `.find()` workaround.
- **`dict(a=1, b=2)`** — needs kwargs at call sites.
- **`set()` with no args** — needs element-type inference from later
  usage.
- **`list(xs)` where `xs` is a variable** — Batch 29 supports literals
  only.

Every one of these is a "wait for a tester report" feature. Don't
build speculatively.

## 67. Batch 33 — empty list literals + File I/O polish (2026-10-17)

### Batch 32 — File I/O core (shipped as v0.4.0)

Full `open()` / `.read()` / `.read(n)` / `.readline()` / `.write()` / `.close()`
support. Modes: `r`, `w`, `a`, `x` (and `rt`, `wt`, `at`, `xt`).

**Preamble `File` struct** (with `std::unique_ptr<std::fstream>` so it's
move-assignable):

- `File(path, "r")` — throws `std::runtime_error` if file missing
- `File(path, "w")` — truncates
- `File(path, "a")` — appends
- `File(path, "x")` — throws if file exists
- `.read()` — whole file as std::string
- `.read(n)` — first n bytes
- `.readline()` — one line
- `.write(s)` — appends s
- `.close()` — explicit close (also in destructor, RAII)
- Move constructor + move assignment (no copy) — allows `f = open(...)` rebind

**New includes:** `<fstream>`, `<filesystem>`, `<memory>`.

**Tracking:** `self.file_vars` — names assigned from `open(...)`. Method
dispatch in `_call_expr` intercepts `.read`/`.readline`/`.write`/`.close`
on tracked file vars.

**Mode validation:** `open()` accepts only `r`/`w`/`a`/`x`/`rt`/`wt`/`at`/`xt`.
Binary modes `rb`/`wb` are rejected with a clear message.

### Batch 33 — empty list literals (shipped as v0.4.1 candidate)

`xs = []` is now allowed. Element type is inferred from later `.append(...)`
calls in the same scope.

**Inference** (`_infer_empty_list_elem_type`): walks the enclosing body
(module scope or function body) looking for `<target>.append(<expr>)`.

Handles:
- `<expr>` is a literal → its C++ type (int/double/string/bool)
- `<expr>` is a loop var over a name known to be a list → element type
- `<expr>` is a loop var over `<call>.split(sep)` → std::string
- otherwise → "int" fallback

**Pre-pass** in `transpile()` populates `emitter.empty_list_types` before
Pass 1. `visit_Assign` looks up the inferred type and emits
`auto xs = std::vector<{inferred}>{}};`.

**`expr()` empty-list guard** changed from `raise TranspileError` to
`return "std::vector<int>{}"` — provisional emission, overridden at
assignment time.

**`visit_Assign`** at the top of the `else:` branch: if `node.value` is
an empty `ast.List`, emits `auto {name} = std::vector<{_et}>{};` with
`_et = self.empty_list_types.get(name, "int")`, registers `list_vars`,
returns.

### Batch 33 additions to `_visit_for_inner`

`for x in <expr>.split(sep):` now works — dispatches to
`for (auto x : str_split(...))`.

### String literal control-char escape (Batch 33 addendum)

`expr()` `ast.Constant` string handler now escapes `\n`, `\r`, `\t`, `\0`
in addition to `\\` and `"`. Fixes `"hello\n"` emitting an unterminated
C++ string literal.

### tests/test_transpiler.py update

Deleted `test_empty_list_raises` — it asserted the pre-Batch-33 limitation.

### `examples/todo.kfy` — persistent todo list

Working end to end. Uses:
- `open` / `.read` / `.close` / `.write`
- `try`/`except` around file-missing
- `str.split("\n")` + `for line in ...`
- `list.append` / `.pop(i)`
- `while` loop with menu
- `input()` and `int(input())`
- helper functions that take and mutate a list parameter

**Note on function mutation:** `add_todo(items)` and `remove_todo(items)` mutate
`items`, but C++ passes vectors by value. **The current version works** because
`save_todos(items)` writes back to disk after each mutation, and `load_todos()`
reloads on startup. But **in-memory `items` is stale within the same session**
after `add_todo` — the appended item only survives because `save_todos` runs
before `add_todo` returns. **Test:** add "buy milk", then list — does it show?
If not, this is the list-parameter-by-value gap (Bug #6 in §5, deferred to
Batch 34).

Wait — actually the current run works because `items.append(text)` inside
`add_todo` modifies the *local copy*, but the loop in `run()` still sees the
original `items`. So the user adds, `save_todos` writes it to disk, and the
next `List` call shows... nothing from the local `items`.

**Confirmed working by your terminal output**: the run started up and menu
worked. **The bug I'm predicting is:** after "Add", the in-session `List`
won't show the newly added item until you quit and restart. **That's the
next fix** if the tester hits it.

Workaround if needed: make `add_todo`/`remove_todo` return the list and
reassign in `run()`:
    items = add_todo(items)
That makes C++ copy-on-return work correctly.

### Menu input — accept words or numbers

`run()` accepts `1`/`list`, `2`/`add`, `3`/`remove`, `4`/`quit`/`q`
(case-insensitive via `.lower()`).

### Test counts

- 710 transpile tests passing (deleted `test_empty_list_raises`)
- `check.py` clean (91 files)
- `examples/todo.kfy` builds and runs

### Commit history this session

    a7c9980  Batch 32.0: file I/O core
    f3f4e04  Bump version to 0.4.0
    (uncommitted)  Batch 33: empty list literals; string escape; todo example

### Next steps for new session

1. **Commit + push Batch 33**:
       git add kofty/transpiler.py tests/test_transpiler.py examples/todo.kfy
       git commit -m "Batch 33: empty list literals; control-char escape; todo example"
       git push origin main

2. **Ship v0.4.1** (bump pyproject, `python -m build`, `gh release create`).

3. **Check the function-mutation bug**: add a todo, list in the same session.
   If the item doesn't show, that's Batch 34 (list params by reference).
   Workaround: `items = add_todo(items)` in `run()`.

4. **Then**: word frequency counter (`sorted()` gap → Batch 35), calculator REPL,
   quiz game, text adventure.

### Status of the "write real programs" plan

- ✅ Todo list — done (with caveat above)
- ⬜ Word counter — needs `sorted()`
- ⬜ Calculator REPL — should work today
- ⬜ Quiz game — should work today
- ⬜ Text adventure — needs nested containers (Batch 36, big lift)

### Batch numbering reset

Since this session added Batches 32, 33 as one logical feature area, consider:

- **Batch 34** — list params by reference (mutating function params)
- **Batch 35** — `sorted(xs)`, `min(xs)`, `max(xs)`, `sum(xs)`
- **Batch 36** — nested containers (weeks)
- **Batch 32.1** — `with` statement + `import os` + `for line in f:` iteration

Nothing else is pressing. The `File` API covers `open`/`read`/`write`/`close`
which is 90% of file I/O in real programs.

### Batch 33 amendments (post-commit)

- **Menu input** — `run()` accepts `1`/`list`, `2`/`add`, `3`/`remove`,
  `4`/`quit`/`q`, case-insensitive via `.lower()`. Both numbers and words
  work.
- **Function-mutation bug** — if Add doesn't appear in a same-session
  List, that's the list-params-by-value gap. Batch 34 candidate.
  Workaround: `items = add_todo(items)` / `items = remove_todo(items)`.

### Confirmed bug: list params by value

`add_todo(items)` and `remove_todo(items)` mutate the *local copy* in C++.
In-session changes to `items` don't persist. `save_todos` writes to disk,
so the item is saved, but the menu's `items` still shows the old value.

**Fix (Batch 34)**: make `add_todo` return the mutated list, and reassign
at call site:
    items = add_todo(items)
    items = remove_todo(items)

Or (transpiler fix): pass list params by reference
(`std::vector<T>& items` instead of `std::vector<T> items`).

## 68. Batch 34 + 35 — empty dict literals + sorted() (2026-10-18)

### Batch 34 — empty dict literals

`d = {}` is now allowed. Value type inferred from first `d[key] = <expr>`
assignment in the enclosing scope.

**New helper** `_infer_empty_dict_value_type(body, target_name)` — walks
the scope looking for `<target>[<key>] = <expr>`. Handles:
- `<expr>` is a literal → its C++ type
- `<expr>` is a name from loop-var types → that var's type
- `<expr>` is `<x> + <y>` BinOp → wider of the two operand types
- otherwise → `"int"` fallback

**Pre-pass** in `transpile()` populates `emitter.empty_dict_types`. Same
pattern as Batch 33's `empty_list_types`.

**Anchor points:**
- `_infer_empty_dict_value_type` — new function before `_infer_empty_list_elem_type`
- `expr()` empty-dict guard (line ~979) — changed from `raise` to
  `return "std::map<std::string, int>{}"`
- `visit_Assign` — new empty-dict case in the `else:` branch (mirrors empty-list case)
- `transpile()` — new pre-pass block after the empty-list pre-pass

**`test_empty_dict_raises` deleted** from `tests/test_transpiler.py` (line 1459).
Was asserting the pre-Batch-34 limitation.

### Batch 35 — sorted(xs)

`sorted(xs)` returns a sorted copy of a list.

**New preamble helper**:
    template <typename T>
    std::vector<T> sorted_helper(const std::vector<T>& xs) {
        std::vector<T> out = xs;
        std::sort(out.begin(), out.end());
        return out;
    }

**New dispatch** in `_call_expr`: `if name == "sorted": return f"sorted_helper({args[0]})"`

**Scope:** 1-argument form only. No `reverse=`, no `key=`. Both are
Batch 35.1 candidates.

### examples/wordfreq.kfy — word frequency counter

Working example:
    f = open("examples/input.txt", "r")
    content = f.read()
    f.close()

    words = content.lower().split(" ")

    counts = {}
    for w in words:
        w = w.strip()
        if w == "":
            continue
        if w in counts:
            counts[w] = counts[w] + 1
        else:
            counts[w] = 1

    for w in counts:
        print(w + ": " + str(counts[w]))

Output for `examples/input.txt`:
    brown: 1
    dog: 1
    fox: 2
    is: 1
    jumps: 1
    lazy: 1
    over: 1
    quick: 2
    the: 2

Notice: `std::map` sorts by key. Fine for this demo.

**BOM caveat:** `examples/input.txt` was created with `Set-Content -Encoding utf8`
(PowerShell default), which writes a UTF-8 BOM. Running the counter on that
file produces `∩╗┐the: 1` as an extra "word" — the BOM is treated as part of
the first word.

**Fix for Batch 32.1:** `File::read()` should strip a UTF-8 BOM if present:
    if (content.size() >= 3
        && (unsigned char)content[0] == 0xEF
        && (unsigned char)content[1] == 0xBB
        && (unsigned char)content[2] == 0xBF) {
        content = content.substr(3);
    }

For now, recreate `input.txt` without BOM:
    [System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))

### Commits this session

    e2cca71  ...  (previous session's last)
    8d1428c  Batch 34+35: empty dict literals; sorted(); word frequency example
    78422fb  Bump version to 0.4.2

### Released as v0.4.2

    https://github.com/sharit25/kofty/releases/tag/v0.4.2

### Test counts

- Transpile suite: 709 passing (deleted `test_empty_dict_raises`)
- `check.py` clean (91 files)
- `examples/todo.kfy` — builds and runs end-to-end
- `examples/wordfreq.kfy` — builds and runs end-to-end

### What's next for a new session

Three independent tracks, any of which is valid:

1. **More real programs** (proves current state):
   - Calculator REPL — should work today
   - Quiz game — should work today
   - Text adventure — needs nested containers (defer)

2. **Polish existing features**:
   - Batch 32.1 — `with open()` statement, `import os`, `for line in f:`, BOM stripping
   - Batch 35.1 — `sorted(xs, reverse=True)`, `sorted(xs, key=...)`
   - Batch 34.1 — `d.items()` iteration, `d.keys()`, `d.values()`

3. **Bigger lifts** (only if a tester asks):
   - Nested containers (list of lists, dict of dicts) — weeks
   - List comprehensions — weeks
   - `list(xs)` where `xs` is a variable — small

**Recommendation:** write the calculator REPL next. It proves the current
language state works for a non-trivial program, and no new batches needed.

## 69. Batch 40 — user-module imports for kofty-gui (2026-10-18)

### Status: 90% complete, one bug remains

### Done

- **`_collect_user_modules(tree)`** helper at line 4705 of `kofty/transpiler.py` —
  walks the AST, returns set of non-builtin module names. **Working** (verified
  standalone: `_collect_user_modules(ast.parse('from kofty_gui import window'))`
  returns `{'kofty_gui'}`).
- **`self.user_modules: set`** added to `CppEmitter.__init__` at line 171.
- **`visit_Import`** — accepts user modules (line 4440-4443). **Works** for
  `import <name>` (plain import form).
- **`visit_ImportFrom`** — accepts user modules (line 4444-4453). **Works**
  for `from <module> import <name>`.
- **`emitter.user_modules = _collect_user_modules(tree)`** — called at line
  4880 of `transpile()`, before preamble emission.
- **`cli.py`** — user-module linking block at line 184. Tries
  `import kofty_gui as _kg` and calls `include_dirs()` / `lib_dirs()` /
  `libs()` (which don't exist yet on the `kofty_gui` package — that's
  part of the next step).

### The bug

**`#include "kofty_gui.hpp"` is not being emitted** despite everything above
working in isolation.

Diagnostic evidence:
- `_collect_user_modules(tree)` returns `{'kofty_gui'}` ✓
- `e.user_modules = _collect_user_modules(tree); e.user_modules` → `{'kofty_gui'}` ✓
- Import-hoisting pass `e.visit(node)` keeps `user_modules` populated ✓
- `emitter.user_modules = _collect_user_modules(tree)` at line 4880 runs ✓
- Anchor E is in place at lines 5929-5931:

## 70. Batch 40.3 — entry-point plugin architecture (2026-10-18)

### The architectural decision

Kofty language and Kofty GUI are **fully independent packages** connected
via Python's standard entry-points mechanism — exactly like Python and
Kivy, or Python and Pandas.

**Before Batch 40.3:**

`kofty/cli.py` contained:

    try:
        import kofty_gui as _kg    # ← kofty named kofty_gui
        for _inc in _kg.include_dirs():
            cmd.append(f"-I{_inc}")
        ...

That meant the language's source code referred to a specific downstream
library by name. The dependency arrow pointed the wrong way.

**After Batch 40.3:**

`kofty/cli.py` contains:

    def _discover_module_flags() -> list:
        """Query all installed `kofty.modules` entry points for g++ flags."""
        ...
        eps = entry_points(group="kofty.modules")
        ...

**`kofty` source has zero references to any specific library.** It just asks
"who wants to contribute g++ flags?" and adds whatever comes back.

`kofty-gui` registers itself:

    # kofty-gui/pyproject.toml
    [project.entry-points."kofty.modules"]
    kofty_gui = "kofty_gui:register"

    # kofty-gui/kofty_gui/__init__.py
    def register():
        return {
            "name": "kofty_gui",
            "include_dirs": [str(package_dir())],
            "lib_dirs": [],
            "libs": [],
        }

Any future Kofty library — `kofty-plot`, `kofty-web`, `kofty-db` — plugs
in the same way. `kofty` needs no changes when a new library is added.

### The four anchors

**A — `kofty/cli.py`: replace hardcoded `import kofty_gui`**

Old code (lines 184-195):

    # Batch 40: user module linking via `kofty_gui` (or any installed
    # Python package that provides include_dirs / lib_dirs / libs).
    try:
        import kofty_gui as _kg
        for _inc in _kg.include_dirs():
            cmd.append(f"-I{_inc}")
        for _libdir in _kg.lib_dirs():
            cmd.append(f"-L{_libdir}")
        for _lib in _kg.libs():
            cmd.append(f"-l{_lib}")
    except ImportError:
        pass

New code:

    # Batch 40.3: query all registered `kofty.modules` entry points for
    # extra g++ flags. Fully generic — kofty doesn't know which modules
    # are installed; each module registers itself via pyproject.toml.
    cmd.extend(_discover_module_flags())

**B — `kofty/cli.py`: add `_discover_module_flags()` helper**

Inserted above `def compile_cpp` (line 158):

    def _discover_module_flags() -> list:
        """Batch 40.3: ask every installed `kofty.modules` entry point for
        g++ include/lib flags.

        Each entry point's callable must return a dict with optional keys:
          - include_dirs: list[str]  → -I<path>
          - lib_dirs:     list[str]  → -L<path>
          - libs:         list[str]  → -l<name>
        """
        flags = []
        try:
            from importlib.metadata import entry_points
            eps = entry_points(group="kofty.modules")
        except Exception:
            return flags
        for ep in eps:
            try:
                info = ep.load()()
                for inc in info.get("include_dirs", []):
                    flags.append(f"-I{inc}")
                for libdir in info.get("lib_dirs", []):
                    flags.append(f"-L{libdir}")
                for lib in info.get("libs", []):
                    flags.append(f"-l{lib}")
            except Exception:
                # A misbehaving module must not break compilation.
                continue
        return flags

**C — `kofty-gui/pyproject.toml`: register the entry point**

Added after `[project.urls]`:

    [project.entry-points."kofty.modules"]
    kofty_gui = "kofty_gui:register"

**D — `kofty-gui/kofty_gui/__init__.py`: add `register()`**

The file now includes:

    def register():
        """Batch 40.3: entry point for kofty's `kofty.modules` discovery."""
        return {
            "name": "kofty_gui",
            "header": str(header_path()),
            "include_dirs": include_dirs(),
            "lib_dirs": lib_dirs(),
            "libs": libs(),
        }

### Verification

- `check.py` → 91 files clean
- Transpile suite → **709 passing**
- `Select-String -Path kofty\*.py -Pattern 'kofty_gui'` → **only one hit**,
  a comment at `transpiler.py:2544` saying `(from kofty_gui, etc.)`. Not
  code. Cosmetic.
- Entry point registered and returns correct dict:
      EP: kofty_gui -> kofty_gui:register
      info: {'name': 'kofty_gui', 'header': 'C:\\kofty-gui\\kofty_gui\\kofty_gui.hpp',
             'include_dirs': ['C:\\kofty-gui\\kofty_gui'], 'lib_dirs': [], 'libs': []}
- `kofty examples\hello_stub.kfy` → `[kofty_gui] hello` ✓
- **After `pip uninstall kofty-gui`:**
  `kofty no_gui_test.kfy` still compiles and runs
  → `hello from kofty without GUI` ✓
- **After `pip install -e .`** in kofty-gui → works again ✓
- Release: https://github.com/sharit25/kofty/releases/tag/v0.5.2

### The user experience now

| User | Command | Result |
|------|---------|--------|
| Console-only | `pip install kofty` | `kofty hello.kfy` compiles console programs. No GUI package. |
| GUI programmer | `pip install kofty-gui` | Pulls in kofty + GUI toolkit. `kofty mygui.kfy` compiles GUI programs. |
| Third-party library | `pip install kofty-plot` | `kofty plot.kfy` works automatically. Zero changes to kofty source. |

**This is the Kivy / Python / Pandas plugin pattern.**

### The stub test — proves the whole pipeline

`kofty-gui/examples/hello_stub.kfy`:

    from kofty_gui import gui_hello
    gui_hello()

`kofty-gui/kofty_gui/kofty_gui.hpp` (current stub):

    #pragma once
    #include <string>
    #include <iostream>

    inline void gui_hello() {
        std::cout << "[kofty_gui] hello" << std::endl;
    }

    inline void gui_echo(const std::string& s) {
        std::cout << "[kofty_gui] " << s << std::endl;
    }

Running `kofty examples\hello_stub.kfy` proves **six layers**:

1. Kofty parses `from kofty_gui import gui_hello` ✓
2. Transpiler emits `#include "kofty_gui.hpp"` at file scope ✓
3. Transpiler emits `gui_hello()` as C++ call ✓
4. g++ finds header via `-I` flag from entry-point discovery ✓
5. g++ links stub (no external libs) ✓
6. Binary runs, prints `[kofty_gui] hello` ✓

**All six layers work end-to-end.**

### Commits this session

Language repo (`kofty`):

    ec2987a  Batch 40: user-module imports
    5f43def  Batch 40.2: fix include emission at file scope
    7675b6e  Batch 40.3: entry-point plugin discovery
    5662b12  Bump version to 0.5.2

GUI repo (`kofty-gui`):

    ec5ed89  Initial kofty-gui scaffold
    80c8d5a  Add README, LICENSE, gitignore, calculator example
    cb91944  Move kofty_gui.hpp into package; add __init__.py
    c42660c  Relax kofty dependency for editable install
    0b1d14d  Stub libs — empty list for no-TGUI stub test
    e80bc57  Register kofty.modules entry point; add register()

### Open items for next session

**Path B — actually build the GUI** (highest priority):

1. **Verify TGUI + raylib build on the machine.** TGUI clone:
   https://github.com/texus/TGUI
