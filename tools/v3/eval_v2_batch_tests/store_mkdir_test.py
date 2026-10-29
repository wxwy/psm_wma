"""Deterministic Store fault-directory collision and fail-closed path checks."""

import errno
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from cosmos_framework.evaluation.robocasa_v2 import store as module

from tools.v3.eval_v2_production_tests.store_test import admitted, fresh


def test_two_real_fault_writers_preserve_both_UUIDs_and_parent_fsync(
    tmp_path, monkeypatch
):
    value = fresh(tmp_path, episodes=1)
    with value.locked():
        task = "CloseFridge"
        value.begin_task(task)
        attempt = admitted(value, value.begin_episode(task, 0))
        directory = value._internal(task) / "errors"
        assert not directory.exists()
        barrier = Barrier(2)
        original_mkdir, original_sync = Path.mkdir, module.sync_dir
        synced = []

        def collision(path, *args, **kwargs):
            if path == directory:
                # Both threads have already observed the absent directory.
                barrier.wait(timeout=5)
            return original_mkdir(path, *args, **kwargs)

        def sync(path):
            original_sync(path)
            synced.append(path)

        monkeypatch.setattr(Path, "mkdir", collision)
        monkeypatch.setattr(module, "sync_dir", sync)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(value.finish_invalid, attempt, "Action Server exited 23"),
                pool.submit(
                    value.record_process_error,
                    task,
                    "coordinator_stop",
                    "Action Server exited 23",
                    attempt=attempt,
                ),
            ]
            for future in futures:
                future.result(timeout=10)

        faults = value.errors(task)
        assert len(faults) == len({fault["id"] for fault in faults}) == 2
        assert {fault["stage"] for fault in faults} == {
            "core_invalid",
            "coordinator_stop",
        }
        assert all(
            fault["attempt"] == attempt
            and fault["resolution"] is None
            and fault["core_committed_at_fault"] is False
            for fault in faults
        )
        assert {path.stem for path in directory.glob("*.json")} == {
            fault["id"] for fault in faults
        }
        # Both mkdir contenders durably sync the parent, including the loser.
        assert synced.count(directory.parent) == 2
        assert not (value._slot(task, 0) / "result.json").exists()
        report, _ = value.summary()
        assert report["valid"] == 0 and not report["results_qualified"]
        assert report["tasks"][task]["invalid"] == 1
        assert report["unresolved_process_errors"] == 2


@pytest.mark.parametrize("kind", ["file", "symlink", "parent_symlink"])
def test_mkdir_rejects_preexisting_non_directory_or_symlink(tmp_path, kind):
    path = tmp_path / "target"
    if kind == "file":
        path.write_text("keep this file")
    else:
        other = tmp_path / "other"
        other.mkdir()
        path.symlink_to(other, target_is_directory=True)
        if kind == "parent_symlink":
            path = path / "child"
    with pytest.raises(ValueError, match="directory required|symlink path forbidden"):
        module.mkdir(path)
    assert not (tmp_path / "other/child").exists()
    if kind == "file":
        assert path.read_text() == "keep this file"


@pytest.mark.parametrize("kind", ["file", "symlink", "dangling_symlink"])
def test_mkdir_revalidates_non_directory_inserted_after_absence_check(
    tmp_path, monkeypatch, kind
):
    path = tmp_path / "target"
    other = tmp_path / "other"
    if kind == "symlink":
        other.mkdir()
    original_mkdir = Path.mkdir

    def collision(candidate, *args, **kwargs):
        if candidate == path:
            if kind == "file":
                path.write_text("keep this file")
            else:
                path.symlink_to(other, target_is_directory=True)
        return original_mkdir(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", collision)
    with pytest.raises(ValueError, match="directory required|symlink path forbidden"):
        module.mkdir(path)
    if kind == "file":
        assert path.read_text() == "keep this file"
    else:
        assert path.is_symlink()


def test_mkdir_does_not_swallow_unrelated_OS_errors(tmp_path, monkeypatch):
    path = tmp_path / "target"
    error = OSError(errno.EIO, "injected filesystem failure")
    original_mkdir = Path.mkdir

    def failed(candidate, *args, **kwargs):
        if candidate == path:
            raise error
        return original_mkdir(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", failed)
    with pytest.raises(OSError) as raised:
        module.mkdir(path)
    assert raised.value is error and not path.exists()
