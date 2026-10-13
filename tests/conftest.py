"""tests/conftest.py — shared test helper.

Provides `run_is` with a retry loop for the Windows Application Control
flake (WinError 4551). Every test file's local `run_is` should import
this, or duplicate the retry logic.
"""

import shutil
import subprocess
import sys
import textwrap
import time

import pytest


def run_is(src: str, tmp_path, _max_attempts: int = 3):
    """Transpile, compile, and run a .is snippet. Retries WinError 4551."""
    if shutil.which("g++") is None:
        pytest.skip("g++ not on PATH")
    src = textwrap.dedent(src).strip() + "\n"
    is_file = tmp_path / "prog.kfy"
    is_file.write_text(src)

    last_err = None
    for attempt in range(_max_attempts):
        result = subprocess.run(
            [sys.executable, "-m", "kofty.cli", str(is_file)],
            capture_output=True, text=True,
        )
        # WinError 4551 fires when launching the freshly-built exe.
        # Detect it in stderr and retry.
        if "WinError 4551" not in result.stderr:
            return result.returncode, result.stdout, result.stderr
        last_err = result.stderr
        time.sleep(0.3)

    return 1, "", last_err or "run_is: exhausted retries on WinError 4551"


def assert_runs(src: str, expected_stdout: str, tmp_path):
    rc, out, err = run_is(src, tmp_path)
    assert rc == 0, f"transpile/compile failed:\nSTDERR:\n{err}\nSTDOUT:\n{out}"
    user_lines = [
        line for line in out.splitlines()
        if not line.startswith("[InterScript]")
    ]
    actual = "\n".join(user_lines).strip()
    expected = expected_stdout.strip()
    assert actual == expected, (
        f"\n--- expected ---\n{expected}\n"
        f"--- actual ---\n{actual}\n"
        f"--- raw stdout ---\n{out}\n"
        f"--- stderr ---\n{err}"
    )


def assert_transpile_fails(src: str, needle: str, tmp_path):
    rc, out, err = run_is(src, tmp_path)
    assert rc != 0, f"expected failure, got rc=0\nOUT:\n{out}\nERR:\n{err}"
    combined = out + err
    assert needle in combined, (
        f"expected error to mention {needle!r}.\n"
        f"STDOUT:\n{out}\nSTDERR:\n{err}"
    )
