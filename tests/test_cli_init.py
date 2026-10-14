"""Batch 10n / 10n.1: kofty init writes .vscode/tasks.json and settings.json."""
import json
from kofty.cli import _run_init


def test_init_writes_tasks_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = _run_init()
    assert rc == 0
    tasks = tmp_path / ".vscode" / "tasks.json"
    assert tasks.exists()
    data = json.loads(tasks.read_text(encoding="utf-8"))
    assert "tasks" in data
    assert any(t.get("label") == "Kofty: build and run"
               for t in data["tasks"])


def test_init_does_not_overwrite_tasks(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".vscode").mkdir()
    original = '{"custom_tasks": true}\n'
    (tmp_path / ".vscode" / "tasks.json").write_text(original, encoding="utf-8")
    rc = _run_init()
    assert rc == 0
    assert (tmp_path / ".vscode" / "tasks.json").read_text(encoding="utf-8") == original
    captured = capsys.readouterr()
    assert "already exists" in captured.out


def test_init_creates_vscode_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / ".vscode").exists()
    _run_init()
    assert (tmp_path / ".vscode").is_dir()


def test_init_helpful_output(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _run_init()
    captured = capsys.readouterr()
    assert "Ctrl+Shift+B" in captured.out


def test_init_writes_settings_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _run_init()
    settings = tmp_path / ".vscode" / "settings.json"
    assert settings.exists()
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data.get("files.associations", {}).get("*.kfy") == "python"


def test_init_settings_skips_if_present(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "settings.json").write_text('{"custom": true}\n', encoding="utf-8")
    _run_init()
    assert (tmp_path / ".vscode" / "settings.json").read_text(encoding="utf-8") == '{"custom": true}\n'
    captured = capsys.readouterr()
    assert "already exists" in captured.out


def test_init_both_files_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _run_init()
    assert (tmp_path / ".vscode" / "tasks.json").exists()
    assert (tmp_path / ".vscode" / "settings.json").exists()


def test_init_partial_setup_completes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "tasks.json").write_text('{"custom_tasks": true}\n', encoding="utf-8")
    _run_init()
    assert (tmp_path / ".vscode" / "tasks.json").read_text(encoding="utf-8") == '{"custom_tasks": true}\n'
    assert (tmp_path / ".vscode" / "settings.json").exists()