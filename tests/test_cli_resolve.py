"""Batch 10m: `kofty <file>` should find files in subdirectories."""
from pathlib import Path
from kofty.cli import _resolve_source_file


def test_resolve_direct_path(tmp_path, monkeypatch):
    (tmp_path / "foo.kfy").write_text("x = 1\n")
    monkeypatch.chdir(tmp_path)
    assert _resolve_source_file("foo.kfy") == Path("foo.kfy")


def test_resolve_from_subdirectory(tmp_path, monkeypatch):
    sub = tmp_path / "examples"
    sub.mkdir()
    (sub / "foo.kfy").write_text("x = 1\n")
    monkeypatch.chdir(tmp_path)
    result = _resolve_source_file("foo.kfy")
    assert result is not None
    assert result.name == "foo.kfy"
    assert "examples" in str(result)


def test_resolve_ambiguous(tmp_path, monkeypatch, capsys):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "foo.kfy").write_text("x = 1\n")
    (tmp_path / "b" / "foo.kfy").write_text("x = 1\n")
    monkeypatch.chdir(tmp_path)
    result = _resolve_source_file("foo.kfy")
    assert result is None
    captured = capsys.readouterr()
    assert "Ambiguous" in captured.err
    assert "a" in captured.err and "b" in captured.err


def test_resolve_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _resolve_source_file("missing.kfy") is None


def test_resolve_explicit_path_does_not_search(tmp_path, monkeypatch):
    """If the user gave `sub/foo.kfy`, don't fall back to a tree search."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "foo.kfy").write_text("x = 1\n")
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "foo.kfy").write_text("x = 1\n")
    monkeypatch.chdir(tmp_path)
    # `sub/wrong.kfy` doesn't exist — should return None, not find
    # `sub/foo.kfy` or `other/foo.kfy`.
    assert _resolve_source_file("sub/wrong.kfy") is None
