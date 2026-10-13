"""rename_to_kofty.py — rename InterScript -> Kofty, .is -> .kfy.

Idempotent-ish. Backs up critical files to .bak-rename/ first.

What it does:
  1. Renames folder interscript/ -> kofty/
  2. Renames interscript/interscript_stubs.pyi -> kofty/kofty_stubs.pyi
  3. Renames interscript.bat -> kofty.bat
  4. Renames stubs/interscript_stubs.pyi -> stubs/kofty_stubs.pyi (if exists)
  5. Renames every examples/*.is -> examples/*.kfy
  6. Walk-replaces in every .py, .md, .bat, .toml, .pyi, .cfg, .txt:
       from interscript.         -> from kofty.
       import interscript        -> import kofty
       interscript.cli           -> kofty.cli
       interscript.transpiler    -> kofty.transpiler
       interscript.bat           -> kofty.bat
       interscript_stubs         -> kofty_stubs
       interscript/              -> kofty/    (only when preceded by a
                                                word boundary so we don't
                                                clobber URLs)
       .is"                      -> .kfy"     (only in string literals
                                                that look like filenames)

What it does NOT touch:
  - HANDOFF.md (that's history)
  - .git/ (already tracked)
  - build/ (regenerated)
"""
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
BACKUP = ROOT / ".bak-rename"

SKIP_DIRS = {".git", "build", ".venv", "venv", ".bak-rename",
             "__pycache__", ".pytest_cache", ".mypy_cache"}

SKIP_FILES = {"HANDOFF.md", "rename_to_kofty.py",
              "rename_to_pyforge.py", "rename_to_inters.py"}

TEXT_EXTS = {".py", ".md", ".bat", ".toml", ".pyi", ".cfg", ".txt", ".ini"}

SUBS = [
    (re.compile(r"\bfrom interscript\."), "from kofty."),
    (re.compile(r"\bimport interscript\b"), "import kofty"),
    (re.compile(r"\binterscript\.cli\b"), "kofty.cli"),
    (re.compile(r"\binterscript\.transpiler\b"), "kofty.transpiler"),
    (re.compile(r"\binterscript\.bat\b"), "kofty.bat"),
    (re.compile(r"\binterscript_stubs\b"), "kofty_stubs"),
    (re.compile(r"(?<!/)\binterscript/"), "kofty/"),
]


def ensure_backup():
    if BACKUP.exists():
        print(f"  backup dir already exists: {BACKUP}")
        return
    BACKUP.mkdir()
    for name in ["interscript", "interscript.bat", "stubs"]:
        src = ROOT / name
        if src.exists():
            if src.is_dir():
                shutil.copytree(src, BACKUP / name, dirs_exist_ok=True)
            else:
                shutil.copy2(src, BACKUP / name)
    print(f"  backed up to {BACKUP}")


def rename_folder():
    old = ROOT / "interscript"
    new = ROOT / "kofty"
    if old.exists() and not new.exists():
        old.rename(new)
        print(f"  renamed {old.name} -> {new.name}")
    elif new.exists():
        print(f"  {new.name}/ already exists, skipping folder rename")
    else:
        print(f"  WARNING: {old} not found")


def rename_stub():
    for candidate in [
        ROOT / "kofty" / "interscript_stubs.pyi",
        ROOT / "stubs" / "interscript_stubs.pyi",
    ]:
        if candidate.exists():
            target = candidate.with_name("kofty_stubs.pyi")
            if not target.exists():
                candidate.rename(target)
                print(f"  renamed {candidate.relative_to(ROOT)} -> {target.name}")


def rename_bat():
    old = ROOT / "interscript.bat"
    new = ROOT / "kofty.bat"
    if old.exists():
        text = old.read_text()
        text = text.replace("interscript", "kofty")
        new.write_text(text)
        old.unlink()
        print(f"  renamed interscript.bat -> kofty.bat")
    else:
        print(f"  no interscript.bat to rename")


def rename_examples():
    ex = ROOT / "examples"
    if not ex.exists():
        return
    count = 0
    for p in ex.glob("*.is"):
        target = p.with_suffix(".kfy")
        if not target.exists():
            p.rename(target)
            count += 1
    if count:
        print(f"  renamed {count} examples/*.is -> *.kfy")


def should_skip(path: pathlib.Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    if path.name in SKIP_FILES:
        return True
    return False


def replace_in_file(path: pathlib.Path) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    text = original
    for pat, sub in SUBS:
        text = pat.sub(sub, text)
    text = re.sub(r'(\b[\w\-./\\]+)\.is\b', r'\1.kfy', text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def walk_and_replace():
    changed = []
    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        if should_skip(path):
            continue
        if replace_in_file(path):
            changed.append(path.relative_to(ROOT))
    for c in changed:
        print(f"  updated {c}")
    print(f"  total files modified: {len(changed)}")


def main():
    print("rename_to_kofty.py")
    print("=" * 60)
    print("Step 1/5: backup")
    ensure_backup()
    print("Step 2/5: rename folder interscript/ -> kofty/")
    rename_folder()
    print("Step 3/5: rename stubs")
    rename_stub()
    print("Step 4/5: rename batch + examples")
    rename_bat()
    rename_examples()
    print("Step 5/5: text replacement")
    walk_and_replace()
    print()
    print("Done. Next steps:")
    print("  python check.py")
    print('  python -m pytest tests/ -q -k "transpile"')


if __name__ == "__main__":
    main()
