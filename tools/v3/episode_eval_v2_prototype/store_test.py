"""New900 storage/state-machine CPU tests; no legacy evaluation files are inputs."""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from tools.v3.episode_eval_v2_prototype import store as module
from tools.v3.episode_eval_v2_prototype.contract import canonical, try_media
from tools.v3.episode_eval_v2_prototype.contract_test import manifest, record
from tools.v3.episode_eval_v2_prototype.store import Store, read


def fresh(tmp_path, *, tasks=("CloseFridge",), episodes=3):
    m = manifest(tasks, episodes)
    value = Store(tmp_path / "new-run", m)
    value.create()
    return value


def read_index(root):
    return [json.loads(line) for line in (root / "episodes.jsonl").read_text().splitlines()]


def test_900_logical_results_and_per_task_statistics_are_unique_and_reconstructible(tmp_path):
    tasks = tuple(f"Task{i:02d}" for i in range(18))
    m = manifest(tasks, 50, formal=True)
    value = Store(tmp_path / "new900", m)
    value.create()
    with value.locked():
        for task in tasks:
            state = value.begin_task(task)
            for ep in range(50):
                value.commit(record(m, state, ep, success=ep % 2 == 0))
        report = value.publish_views()
    assert report["expected"] == report["valid"] == 900
    assert report["success"] == report["failure"] == 450 and report["sr"] == 0.5
    assert report["results_qualified"] and report["prototype_only"] and not report["runtime_gate_approved"]
    rows = read_index(value.root)
    assert len(rows) == len({(r["task"], r["episode"]) for r in rows}) == 900
    assert all(info["expected"] == 50 and info["sr"] == 0.5 for info in report["tasks"].values())
    # Derived views are not authority and can always be rebuilt from small commits.
    (value.root / "summary.json").write_text("broken")
    (value.root / "episodes.jsonl").write_text('{"duplicate":true}\n' * 3)
    with value.locked():
        assert value.publish_views() == report
    assert len(read_index(value.root)) == 900
    print(
        "V2_DESIGN_WITNESS "
        + json.dumps(
            {"tasks": 18, "episodes": 900, "success": 450, "failure": 450, "sr": report["sr"], "prototype_only": True}
        ),
        flush=True,
    )


def test_invalid_pending_partial_SR_never_silently_drop_from_official_plan(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        state = value.begin_task("CloseFridge")
        value.commit(record(value.manifest, state, 0))
        value.commit(record(value.manifest, state, 1, invalid=True))
        report = value.publish_views()
    assert (report["success"], report["invalid"], report["pending"]) == (1, 1, 1)
    assert report["sr"] is None and report["partial_sr_valid_only"] == 1.0
    assert not report["results_qualified"]
    assert [r["outcome"] for r in read_index(value.root)] == ["success", "invalid", "pending"]


def test_late_process_error_preserves_environment_results_but_blocks_qualification(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        state = value.begin_task("CloseFridge")
        for ep in range(3):
            value.commit(record(value.manifest, state, ep))
        original = (value.root / "tasks/CloseFridge/episodes/ep_000/result.json").read_bytes()
        value.record_process_error(
            task="CloseFridge", stage="worker_exit", message="post-result process exited nonzero"
        )
        report = value.publish_views()
    assert report["sr"] == 1.0 and report["status"] == "complete_with_process_errors"
    assert not report["results_qualified"]
    assert (value.root / "tasks/CloseFridge/episodes/ep_000/result.json").read_bytes() == original


def test_task_restart_moves_partial_bytes_once_never_mixes_scene_streams_or_copies_videos(tmp_path):
    value = fresh(tmp_path, tasks=("CloseFridge", "OpenCabinet"))
    with value.locked():
        first = value.begin_task("CloseFridge")
        value.commit(record(value.manifest, first, 0))
        media = value.root / "tasks/CloseFridge/episodes/ep_000/media/rollout.mp4"
        media.parent.mkdir()
        media.write_bytes(b"diagnostic MP4, never decoded")
        inode = media.stat().st_ino
        done = value.begin_task("OpenCabinet")
        for ep in range(3):
            value.commit(record(value.manifest, done, ep))
    resumed = Store(value.root, value.manifest)
    with resumed.locked():
        assert resumed.begin_task("OpenCabinet")["action"] == "reuse_complete_task"
        second = resumed.begin_task("CloseFridge")
        assert second["action"] == "restart_full_task" and second["generation"] == 1
        assert second["stream_id"] != first["stream_id"]
        assert resumed.rows("CloseFridge") == []
        with pytest.raises(ValueError, match="stale producer"):
            resumed.commit(record(value.manifest, first, 0))
        for ep in range(3):
            resumed.commit(record(value.manifest, second, ep))
        assert resumed.publish_views()["valid"] == 6
    archived = list((value.root / "_internal/abandoned/CloseFridge").glob("*/ep_000/media/rollout.mp4"))
    assert len(archived) == 1 and archived[0].stat().st_ino == inode
    assert archived[0].read_bytes() == b"diagnostic MP4, never decoded"
    assert not (value.root / "videos_view").exists()


@pytest.mark.parametrize("boundary", ["before_move", "after_move", "before_state", "after_state"])
def test_restart_journal_recovery_is_bounded_and_preserves_partial_evidence(tmp_path, monkeypatch, boundary):
    value = fresh(tmp_path)
    with value.locked():
        state = value.begin_task("CloseFridge")
        value.commit(record(value.manifest, state, 0))
    original = (value.root / "tasks/CloseFridge/episodes/ep_000/result.json").read_bytes()
    renamed, written = os.rename, module.write

    def rename(src, dst):
        if boundary == "before_move":
            raise OSError("injected before move")
        renamed(src, dst)
        if boundary == "after_move":
            raise OSError("injected after move")

    def write_state(path, payload, **kwargs):
        is_state = Path(path) == value._state_path("CloseFridge")
        if is_state and boundary == "before_state":
            raise OSError("injected before state")
        written(path, payload, **kwargs)
        if is_state and boundary == "after_state":
            raise OSError("injected after state")

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "rename", rename)
        scoped.setattr(module, "write", write_state)
        with pytest.raises(OSError, match="injected"):
            with Store(value.root, value.manifest).locked() as failed:
                failed.begin_task("CloseFridge")
    with Store(value.root, value.manifest).locked() as recovered:
        state = recovered.begin_task("CloseFridge")
        assert state["generation"] == 1 and state["action"] == "restart_full_task"
        assert not recovered._journal("CloseFridge").exists()
        assert recovered.rows("CloseFridge") == []
        recovered.commit(record(value.manifest, state, 0))
    archives = list((value.root / "_internal/abandoned").glob("**/result.json"))
    assert len(archives) == 1 and archives[0].read_bytes() == original


@pytest.mark.parametrize("mode", ["duplicate", "out_of_order", "post_invalid", "unclaimed"])
def test_episode_dedup_order_and_stream_owner_are_strict(tmp_path, mode):
    value = fresh(tmp_path)
    with value.locked():
        state = value.begin_task("CloseFridge")
        if mode == "unclaimed":
            value.active_tasks.clear()
            with pytest.raises(RuntimeError):
                value.commit(record(value.manifest, state, 0))
        elif mode == "out_of_order":
            with pytest.raises(ValueError):
                value.commit(record(value.manifest, state, 1))
        else:
            value.commit(record(value.manifest, state, 0, invalid=mode == "post_invalid"))
            with pytest.raises(ValueError):
                value.commit(record(value.manifest, state, 0 if mode == "duplicate" else 1))


def test_commit_failure_never_creates_a_complete_episode_and_partial_files_are_not_authority(tmp_path, monkeypatch):
    value = fresh(tmp_path)
    with value.locked():
        state = value.begin_task("CloseFridge")
        with monkeypatch.context() as scoped:
            scoped.setattr(os, "link", Mock(side_effect=OSError("commit failed")))
            with pytest.raises(OSError):
                value.commit(record(value.manifest, state, 0))
        directory = value.root / "tasks/CloseFridge/episodes/ep_000"
        (directory / "actions.jsonl").write_text('{"step":0}\n')
        assert value.rows("CloseFridge") == []
        assert value.publish_views()["pending"] == 3
        assert not list(directory.glob(".pending-*"))


@pytest.mark.parametrize("change", ["checksum", "wrong_stream", "wrong_reset", "bad_utf8", "symlink", "oversized"])
def test_corrupt_result_never_becomes_complete_or_silently_reruns(tmp_path, change):
    value = fresh(tmp_path)
    with value.locked():
        state = value.begin_task("CloseFridge")
        value.commit(record(value.manifest, state, 0))
        path = value.root / "tasks/CloseFridge/episodes/ep_000/result.json"
        if change == "bad_utf8":
            path.write_bytes(b"\xff")
        elif change == "oversized":
            path.write_bytes(b"x" * (module.MAX_JSON + 1))
        elif change == "symlink":
            target = value.root / "outside.json"
            path.rename(target)
            path.symlink_to(target)
        else:
            row = read(path)
            if change == "checksum":
                row["outcome"] = "failure"
            else:
                row["stream_id" if change == "wrong_stream" else "reset_index"] = (
                    "b" * 32 if change == "wrong_stream" else 1
                )
                row["commit_sha256"] = module.digest({k: v for k, v in row.items() if k != "commit_sha256"})
            path.write_bytes(canonical(row))
        with pytest.raises((ValueError, UnicodeError)):
            value.publish_views()


@pytest.mark.parametrize("kind", ["old431", "empty", "foreign_manifest", "unsafe_symlink"])
def test_new_namespace_never_adopts_or_edits_historical_outputs(tmp_path, kind):
    root = tmp_path / "existing"
    root.mkdir()
    original = root / "431_diagnostic.txt"
    original.write_text("never migrate or rewrite")
    if kind == "foreign_manifest":
        (root / "manifest.json").write_text('{"schema":"old"}')
    if kind == "unsafe_symlink":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        with pytest.raises(ValueError):
            Store(alias, manifest())
    else:
        with pytest.raises(FileExistsError):
            Store(root, manifest()).create()
    assert original.read_text() == "never migrate or rewrite"


def test_readonly_summary_never_changes_results_or_recreates_views(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        state = value.begin_task("CloseFridge")
        value.commit(record(value.manifest, state, 0))
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in value.root.rglob("*") if p.is_file()}
    report, rows = value.summary()
    assert report["sr"] is None and len(rows) == 3
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in value.root.rglob("*") if p.is_file()}


def test_distinct_cpu_process_cannot_take_the_original_run_lease(tmp_path):
    value = fresh(tmp_path)
    code = """import json,sys
from tools.v3.episode_eval_v2_prototype.store import Store
store=Store(sys.argv[1],json.loads(sys.argv[2]))
try:
 with store.locked(): raise AssertionError('double owner')
except BlockingIOError: print('RUN_LOCKED')
"""
    with value.locked():
        p = subprocess.run(
            [sys.executable, "-c", code, str(value.root), json.dumps(value.manifest)],
            text=True,
            capture_output=True,
            timeout=20,
        )
        assert p.returncode == 0 and "RUN_LOCKED" in p.stdout


def test_media_corruption_missing_files_and_encoder_errors_never_enter_SR_validation(tmp_path, monkeypatch):
    value = fresh(tmp_path)
    with value.locked():
        state = value.begin_task("CloseFridge")
        for ep in range(3):
            value.commit(record(value.manifest, state, ep, success=ep != 1))
        media = value.root / "tasks/CloseFridge/episodes/ep_000/media"
        media.mkdir()
        (media / "rollout.mp4").write_bytes(b"intentionally unplayable")
        diagnostic = try_media(lambda: (_ for _ in ()).throw(OSError("video failed")))
        assert diagnostic["status"] == "error"
        monkeypatch.setattr(subprocess, "run", Mock(side_effect=AssertionError("decoder/export forbidden")))
        assert value.publish_views()["sr"] == pytest.approx(2 / 3)
        assert not (value.root / "videos_view").exists()


def test_pending_task_summary_is_not_stream_authority_and_can_be_claimed_later(tmp_path):
    value = fresh(tmp_path, tasks=("CloseFridge", "OpenCabinet"))
    with value.locked():
        assert value.publish_views()["pending"] == 6
        assert value.publish_views()["pending"] == 6
        state = value.begin_task("CloseFridge")
        value.commit(record(value.manifest, state, 0))
        assert value.publish_views()["pending"] == 5


def test_corrupt_restart_journal_cannot_move_or_create_paths_outside_archive(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        state = value.begin_task("CloseFridge")
        value.commit(record(value.manifest, state, 0))
    old = {k: state[k] for k in ("task", "generation", "stream_id", "manifest_digest")}
    old["stream_id"] = "../../escape"
    new = dict(old, generation=1, stream_id="b" * 32)
    module.write(value._journal("CloseFridge"), {"old": old, "new": new})
    before = (value.root / "tasks/CloseFridge/episodes/ep_000/result.json").read_bytes()
    with Store(value.root, value.manifest).locked() as resumed:
        with pytest.raises(ValueError, match="stream state"):
            resumed.begin_task("CloseFridge")
    assert not (value.root / "_internal/abandoned").exists()
    assert (value.root / "tasks/CloseFridge/episodes/ep_000/result.json").read_bytes() == before


def test_old431_or_new_canary_manifest_is_never_accepted_as_another_experiment(tmp_path):
    value = fresh(tmp_path)
    before = (value.root / "manifest.json").read_bytes()
    different = manifest(episodes=4)
    with pytest.raises(ValueError, match="identity mismatch"):
        with Store(value.root, different).locked():
            pytest.fail("changed experimental plan adopted")
    assert (value.root / "manifest.json").read_bytes() == before


def test_initial_claim_interruption_is_explicitly_blocked_not_silent_missing_data(tmp_path):
    value = fresh(tmp_path)
    # This is an unsupported half-initialized task, never proof that no old data existed.
    module.write(
        value._state_path("CloseFridge"),
        {"task": "CloseFridge", "generation": 0, "stream_id": "a" * 32, "manifest_digest": value.manifest["digest"]},
    )
    with value.locked():
        with pytest.raises(ValueError, match="missing active"):
            value.begin_task("CloseFridge")
    assert not (value.root / "tasks/CloseFridge/episodes").exists()
