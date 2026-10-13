"""
Pre-flight check: make sure every Python file in the project parses
before we run pytest. Catches indentation / syntax mistakes immediately.

Usage:
    python check.py
"""

import py_compile
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).parent
    targets = [
        root / "interscript",
        root / "tests",
        root / "examples",
    ]

    all_files = []
    for target in targets:
        if target.exists():
            all_files.extend(sorted(target.glob("**/*.py")))

    if not all_files:
        print("No Python files found.", file=sys.stderr)
        return 1

    failures = []
    for path in all_files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as e:
            failures.append((path, e))

    if failures:
        print(f"\n❌ {len(failures)} file(s) failed to compile:\n")
        for path, err in failures:
            print(f"  {path.relative_to(root)}")
            print(f"    {err}\n")
        return 1

    print(f"✅ All {len(all_files)} Python files parse cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
