"""CPU-only runner safety tests. All repositories are isolated synthetic fixtures."""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("migration_gate_under_test", Path(__file__).with_name("run_migration_cpu_gate.py"))
assert spec is not None and spec.loader is not None
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def test_cpu_environment_cannot_inherit_torchrun_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("RANK", "LOCAL_RANK", "WORLD_SIZE", "MASTER_ADDR", "MASTER_PORT"):
        monkeypatch.setenv(key, "synthetic")
    before = os.environ.copy()
    env = gate.cpu_environment(tmp_path)
    assert env["CUDA_VISIBLE_DEVICES"] == ""
    assert env["HF_HUB_OFFLINE"] == "1" and env["TRANSFORMERS_OFFLINE"] == "1"
    assert env["COSMOS_DEVICE"] == "cpu"
    assert env["PYTHONPATH"] == str(tmp_path)
    assert "RANK" not in env and "WORLD_SIZE" not in env and "MASTER_PORT" not in env
    assert os.environ == before


@pytest.mark.parametrize("record", [" M tools/v3/unsafe.py\0", "?? artifacts/unsafe.py\0", " D SESSION.md\0", "R  TODO.md\0old\0"])
def test_source_or_deleted_notes_fail_closed(record: str) -> None:
    with pytest.raises(ValueError):
        gate.allowed_root_records(record)


def test_owner_notes_and_ds_evidence_are_preserved() -> None:
    records = " M SESSION.md\0 M TODO.md\0?? artifacts/g0/evidence.json\0?? docs/collab/chatgpt/DS_PRO_report.md\0"
    assert len(gate.allowed_root_records(records)) == 4


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()


def _init(root: Path) -> str:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Synthetic CPU Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    (root / "fixture.txt").write_text("synthetic\n")
    _git(root, "add", "fixture.txt")
    _git(root, "commit", "-qm", "synthetic fixture")
    return _git(root, "rev-parse", "HEAD")


def test_exact_pair_requires_gitlink_and_clean_child(tmp_path: Path) -> None:
    root = tmp_path / "root"
    _init(root)
    child = root / "cosmos-framework"
    child_sha = _init(child)
    _git(root, "update-index", "--add", "--cacheinfo", f"160000,{child_sha},cosmos-framework")
    _git(root, "commit", "-qm", "pin synthetic child")
    root_sha = _git(root, "rev-parse", "HEAD")
    result = gate.verify_pair(root, root_sha, child_sha)
    assert result["gitlink"] == child_sha
    with pytest.raises(ValueError, match="lock mismatch"):
        gate.verify_pair(root, "a" * 40, child_sha)
    (child / "fixture.txt").write_text("modified\n")
    with pytest.raises(ValueError, match="clean"):
        gate.verify_pair(root, root_sha, child_sha)


def test_evidence_directory_reuse_is_rejected_without_overwrite(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    saved = evidence / "gate.json"
    saved.write_text("preserve me")
    with pytest.raises(FileExistsError):
        gate.main([
            "--root-worktree", str(tmp_path / "root"), "--expected-root", "a" * 40,
            "--expected-child", "b" * 40, "--evidence-dir", str(evidence),
        ])
    assert saved.read_text() == "preserve me"
