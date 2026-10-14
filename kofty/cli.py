"""Kofty command-line interface.

Usage:
    kofty <file.kfy> [--emit-only] [--out <path>]
    kofty --version
"""

import argparse
import importlib.resources
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .transpiler import transpile, TranspileError


VERSION = "0.1.0"

# Banner for --version and --help.
# Uses Unicode block characters that render in any modern terminal.
_BANNER = r"""
  K   K  OOO  FFFF TTTT Y   Y
  K  K  O   O F      T   Y Y
  KKK   O   O FFF    T    Y
  K  K  O   O F      T    Y
  K   K  OOO  F      T    Y
"""



def print_banner():
    """Print the Kofty ASCII banner + version."""
    print(_BANNER)
    print(f"  Kofty v{VERSION} - Python subset -> C++ -> native binary")
    print(f"  https://github.com/sharit25/kofty")
    print()

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


def resolve_icon(icon_arg, source_file: Path):
    """Batch 10d: which .ico to embed, if any.

    Returns a Path to the icon, or None to skip icon embedding.
    """
    if icon_arg == "none":
        return None
    if icon_arg:
        p = Path(icon_arg)
        if not p.is_file():
            print(f"[Kofty] Warning: --icon file not found: {p}",
                  file=sys.stderr)
            return None
        return p

    for c in (source_file.parent / "kofty.ico", Path.cwd() / "kofty.ico"):
        if c.is_file():
            return c

    # Packaged icon.
    try:
        ref = importlib.resources.files("kofty").joinpath("data/kofty.ico")
        with importlib.resources.as_file(ref) as p:
            if p.is_file():
                # Copy to build dir so the path stays valid.
                return Path(str(p))
    except Exception:
        pass
    return None


def build_icon_object(icon: Path, build_dir: Path, stem: str):
    """Batch 10d: compile `icon` into a Windows .o with windres."""
    if shutil.which("windres") is None:
        print("[Kofty] Warning: windres not on PATH; skipping icon embed.",
              file=sys.stderr)
        return None

    rc_file = build_dir / f"{stem}_res.rc"
    obj_file = build_dir / f"{stem}_res.o"

    icon_abs = icon.resolve()
    rc_file.write_text(f'IDI_ICON1 ICON "{icon_abs}"\n', encoding="utf-8")

    cmd = ["windres", str(rc_file), "-O", "coff", "-o", str(obj_file)]
    print(f"[Kofty] (icon) {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[Kofty] windres failed:\n{result.stderr}", file=sys.stderr)
        return None
    return obj_file


def compile_cpp(cpp_file: Path, exe_file: Path, icon=None) -> bool:
    """Invoke g++ to produce an executable.

    Batch 10d: if `icon` is a Path to a .ico, embeds it via windres.
    """
    cpp_text = cpp_file.read_text(encoding="utf-8")
    uses_raylib = "raylib.h" in cpp_text

    cmd = [
        "g++", str(cpp_file),
        "-o", str(exe_file),
        "-std=c++17",
    ]

    if icon is not None:
        obj = build_icon_object(icon, exe_file.parent, exe_file.stem)
        if obj is not None:
            cmd.append(str(obj))

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

def _resolve_source_file(name: str) -> Path | None:
    """Resolve a Kofty source file by name.

    Resolution order (Batch 10m):
      1. The path as given, relative to CWD (current behavior).
      2. A recursive search of CWD for a file with that name
         (up to 3 levels deep). If exactly one match is found,
         return it. If multiple, print all candidates and return
         None (caller should exit). If zero, return None with no
         message — the caller prints "not found".
    """
    direct = Path(name)
    if direct.exists():
        return direct

    # Only search if the argument was a bare filename. If the user
    # gave a path with separators (e.g. `sub/foo.kfy`), don't search
    # — they told us where to look, respect that.
    if "/" in name or "\\" in name:
        return None

    # Recursive search. `rglob` on `.` walks the whole tree; we
    # filter to keep the search shallow and fast.
    candidates = []
    try:
        for p in Path(".").rglob(name):
            if not p.is_file():
                continue
            # Depth check: count path parts relative to "."
            try:
                rel = p.relative_to(Path("."))
            except ValueError:
                continue
            # Allow `.`, `./sub/`, `./a/b/` = depth 1, 2, 3
            if len(rel.parts) > 3:
                continue
            candidates.append(p)
    except OSError:
        # Permissions, symlink loops, etc. — treat as no match.
        return None

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        print(
            f"[Kofty] Ambiguous filename: {name!r} matches "
            f"{len(candidates)} files:",
            file=sys.stderr,
        )
        for c in candidates:
            print(f"  {c}", file=sys.stderr)
        print(
            "[Kofty] Please pass the full path.",
            file=sys.stderr,
        )
    return None

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="kofty")
    parser.add_argument("file", nargs="?", help="Kofty source (.kfy)")
    parser.add_argument("--emit-only", action="store_true",
                        help="Write C++ but do not compile or run.")
    parser.add_argument("--out", default="build",
                        help="Output directory (default: build)")
    parser.add_argument("--icon", default=None,
                        help="Embed an .ico in the compiled .exe. "
                             "Use --icon=none to disable.")
    parser.add_argument("--version", action="store_true",
                        help="Show version and banner, then exit.")
    args = parser.parse_args(argv)

    if args.version:
        print_banner()
        return 0

    if not args.file:
        parser.print_help()
        return 1

    src_path = _resolve_source_file(args.file)
    if src_path is None:
        print(f"[Kofty] File not found: {args.file}", file=sys.stderr)
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

    # utf-8-sig strips a leading UTF-8 BOM if present, and behaves
    # like plain utf-8 otherwise. This makes .kfy files created by
    # PowerShell's Set-Content, Notepad, or Visual Studio (all of
    # which write BOM-prefixed UTF-8 by default on Windows) parse
    # correctly.
    if not build_cpp(src_path.read_text(encoding="utf-8-sig"), cpp_file):
        return 1

    print(f"[Kofty] Wrote {cpp_file}")

    if args.emit_only:
        return 0

    # Batch 10d: resolve the icon (may be None).
    _icon = resolve_icon(args.icon, src_path)

    if not compile_cpp(cpp_file, exe_file, icon=_icon):
        print("[Kofty] Build failed.", file=sys.stderr)
        return 1

    print(f"[Kofty] Launching {exe_file}")
    subprocess.run([str(exe_file)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
