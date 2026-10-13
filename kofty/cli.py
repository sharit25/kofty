"""Kofty command-line interface.

Usage:
    kofty <file.kfy> [--emit-only] [--out <path>]
    kofty --version
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .transpiler import transpile, TranspileError


VERSION = "0.1.0"

# Adjust these if your Raylib / MinGW lives elsewhere.
RAYLIB_INCLUDE = os.environ.get("RAYLIB_INCLUDE", "C:/raylib/include")
RAYLIB_LIB     = os.environ.get("RAYLIB_LIB",     "C:/raylib/lib")
LINK_FLAGS = "-lraylib -lopengl32 -lgdi32 -lwinmm"


def build_cpp(source: str, out_cpp: Path) -> bool:
    """Transpile and write the C++ file. Returns True on success."""
    try:
        cpp = transpile(source)
    except TranspileError as e:
        print(f"[Kofty] Transpile error: {e}", file=sys.stderr)
        return False
    except SyntaxError as e:
        print(f"[Kofty] Python syntax error: {e}", file=sys.stderr)
        return False

    out_cpp.parent.mkdir(parents=True, exist_ok=True)
    out_cpp.write_text(cpp, encoding="utf-8")
    return True


def compile_cpp(cpp_file: Path, exe_file: Path) -> bool:
    """Invoke g++ to produce an executable.

    Links raylib only if the emitted C++ actually includes raylib.h.
    Pure-console programs link just libstdc++.
    """
    cpp_text = cpp_file.read_text(encoding="utf-8")
    uses_raylib = "raylib.h" in cpp_text

    cmd = [
        "g++", str(cpp_file),
        "-o", str(exe_file),
        "-std=c++17",
    ]
    if uses_raylib:
        cmd += [
            f"-I{RAYLIB_INCLUDE}",
            f"-L{RAYLIB_LIB}",
            *LINK_FLAGS.split(),
        ]

    mode = "raylib" if uses_raylib else "console"
    print(f"[Kofty] ({mode}) {' '.join(cmd)}")

    result = subprocess.run(cmd)
    return result.returncode == 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="kofty")
    parser.add_argument("file", nargs="?", help="Kofty source (.kfy)")
    parser.add_argument("--emit-only", action="store_true",
                        help="Write C++ but do not compile or run.")
    parser.add_argument("--out", default="build",
                        help="Output directory (default: build)")
    parser.add_argument("--version", action="version",
                        version=f"Kofty {VERSION}")
    args = parser.parse_args(argv)

    if not args.file:
        parser.print_help()
        return 1

    src_path = Path(args.file)
    if not src_path.exists():
        print(f"[Kofty] File not found: {src_path}", file=sys.stderr)
        return 1

    # Kofty source files use the .is extension. We also accept .py
    # for backwards compatibility while the language is young.
    allowed_ext = {".kfy", ".is", ".py"}
    if src_path.suffix.lower() not in allowed_ext:
        print(
            f"[Kofty] Unsupported file extension: {src_path.suffix!r}. "
            f"Expected .kfy (or .is / .py for compatibility).",
            file=sys.stderr,
        )
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cpp_file = out_dir / (src_path.stem + ".cpp")
    exe_file = out_dir / (src_path.stem + ".exe")

    if not build_cpp(src_path.read_text(encoding="utf-8"), cpp_file):
        return 1

    print(f"[Kofty] Wrote {cpp_file}")

    if args.emit_only:
        return 0

    if not compile_cpp(cpp_file, exe_file):
        print("[Kofty] Build failed.", file=sys.stderr)
        return 1

    print(f"[Kofty] Launching {exe_file}")
    subprocess.run([str(exe_file)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
