"""Independent browsing copies: CPU binary/JSON fixtures, no codec or simulator."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import robocasa_eval_video_view as video_view  # noqa: E402

DIGEST = "a" * 64


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n")


def make_run(
    tmp_path, *, prompt="close the fridge", status="success", episode=0, task="CloseFridge", attempt="attempt_0001"
):
    run = tmp_path / "run"
    run.mkdir(exist_ok=True)
    write_json(run / "evaluation_manifest.json", {"digest": DIGEST})
    directory = run / task / attempt
    directory.mkdir(parents=True)
    write_json(
        directory / "attempt.json", {"attempt_id": attempt, "evaluation_run_digest": DIGEST, "status": "COMPLETE"}
    )
    row = {
        "ep": episode,
        "outcome": status,
        "policy": status == "success",
        "error": "RuntimeError: test" if status == "runtime_error" else None,
        "prompt": prompt,
        "evaluation_attempt_id": f"{task}/{attempt}",
        "evaluation_run_digest": DIGEST,
    }
    write_json(directory / f"rollout{episode:02d}_episode.json", row)
    write_json(directory / "results.json", [row])
    video = directory / f"rollout{episode:02d}.mp4"
    video.write_bytes(b"tiny binary fixture, deliberately not a decoded movie\x00" + bytes([episode]))
    return run, directory, row, video


def snapshot(run):
    return {
        str(path.relative_to(run)): (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_ino)
        for path in run.rglob("*")
        if path.is_file() and "videos_view" not in path.relative_to(run).parts
    }


def test_environment_generated_names_full_instruction_and_independent_inodes(tmp_path):
    run, directory, _, original = make_run(tmp_path)
    first = directory / "rollout00_generated.mp4"
    first.write_bytes(b"generated first")
    # Separate Episode avoids an ambiguous first-vs-replan0 logical identity.
    second, second_dir, _, _ = make_run(tmp_path, episode=1, attempt="attempt_0002", prompt="turn on the faucet")
    assert second == run
    (second_dir / "rollout01_generated_replan0000.mp4").write_bytes(b"predicted replan")
    before = snapshot(run)
    result = video_view.export_videos(run)
    assert result["status"] == "OK" and result["exported_count"] == 4
    assert snapshot(run) == before
    by_name = {Path(row["output_path"]).name: row for row in result["records"]}
    assert "rollout00_success_close_the_fridge.mp4" in by_name
    first_prediction = by_name["rollout00_success_close_the_fridge_generated_replan0000.mp4"]
    assert first_prediction["prediction_replan"] == 0
    assert first_prediction["prediction_role"] == "first_prediction"
    predicted = by_name["rollout01_success_turn_on_the_faucet_generated_replan0000.mp4"]
    assert predicted["video_kind"] == "generated_prediction" and predicted["prediction_replan"] == 0
    assert predicted["prediction_role"] == "replan"
    row = by_name["rollout00_success_close_the_fridge.mp4"]
    destination = Path(row["output_path"])
    assert row["instruction"] == "close the fridge" and row["instruction_missing"] is False
    assert row["original_path"] == str(original)
    assert row["original_sha256"] == hashlib.sha256(original.read_bytes()).hexdigest()
    assert destination.stat().st_ino != original.stat().st_ino
    destination.write_bytes(b"browser edit")
    assert original.read_bytes() == before[str(original.relative_to(run))][0]


@pytest.mark.parametrize(
    "outcome,error,policy,expected",
    [
        ("success", None, True, "success"),
        ("behavioral_failure", None, False, "fail"),
        ("runtime_error", "ValueError: infrastructure", False, "error"),
        ("runtime_error", "KeyboardInterrupt: stopped", False, "incomplete"),
        ("runtime_error", "SystemExit: 7", False, "error"),
        (None, None, False, "incomplete"),
        ("success", "RuntimeError: conflicting", True, "error"),
    ],
)
def test_typed_episode_status_never_turns_runtime_errors_into_behavioral_failures(
    tmp_path, outcome, error, policy, expected
):
    run, directory, row, _ = make_run(tmp_path)
    row.update(outcome=outcome, error=error, policy=policy)
    write_json(directory / "rollout00_episode.json", row)
    write_json(directory / "results.json", [row])
    result = video_view.export_videos(run)
    assert result["records"][0]["status"] == expected
    assert f"_{expected}_" in Path(result["records"][0]["output_path"]).name


@pytest.mark.parametrize(
    "instruction", ["Close the Fridge!", "关闭 冰箱/冷藏室", "../a\\b\n\x00c?*", "", "   ", "very long " * 80]
)
def test_slug_safe_unicode_empty_and_long_names_preserve_full_actual_text(tmp_path, instruction):
    run, _, _, _ = make_run(tmp_path, prompt=instruction)
    result = video_view.export_videos(run)
    record = result["records"][0]
    name = Path(record["output_path"]).name
    assert record["instruction"] == instruction and record["instruction_missing"] is False
    assert len(name.encode()) < 255 and ".." not in name and "\\" not in name and "\n" not in name
    assert Path(record["output_path"]).is_relative_to(run / "videos_view")
    if instruction.startswith("very long"):
        assert hashlib.sha256(instruction.encode()).hexdigest()[:10] in name
    if instruction == "Close the Fridge!":
        assert name == "rollout00_success_close_the_fridge.mp4"


def test_missing_instruction_is_unknown_not_task_name(tmp_path):
    run, _, _, _ = make_run(tmp_path, prompt=None)
    result = video_view.export_videos(run)
    row = result["records"][0]
    assert row["instruction"] is None and row["instruction_missing"]
    assert "unknown_instruction" in row["output_path"]
    index = json.loads(Path(result["index_file"]).read_text())
    assert any("instruction missing" in warning for warning in index["last_export"]["warnings"])


def test_bound_live_instruction_fallback_for_runtime_error(tmp_path):
    run, directory, _, _ = make_run(tmp_path, prompt=None, status="runtime_error")
    record = {
        "schema": "psm_eval_live_progress_v1",
        "task": directory.parent.name,
        "episode": 0,
        "evaluation_run_digest": DIGEST,
        "evaluation_attempt_id": "CloseFridge/attempt_0001",
        "instruction": "the actual prompt before runtime failure",
        "event": "stage",
    }
    (directory / "live_progress.jsonl").write_text(json.dumps(record) + "\n")
    result = video_view.export_videos(run)
    row = result["records"][0]
    assert row["status"] == "error" and row["instruction"] == record["instruction"]
    assert row["instruction_source"] == "live_progress.instruction"


@pytest.mark.parametrize(
    "field,value",
    [
        ("task", "OtherTask"),
        ("episode", True),
        ("evaluation_run_digest", "b" * 64),
        ("evaluation_attempt_id", "CloseFridge/attempt_9999"),
    ],
)
def test_foreign_live_instruction_never_used(tmp_path, field, value):
    run, directory, _, _ = make_run(tmp_path, prompt=None)
    record = {
        "schema": "psm_eval_live_progress_v1",
        "task": "CloseFridge",
        "episode": 0,
        "evaluation_run_digest": DIGEST,
        "evaluation_attempt_id": "CloseFridge/attempt_0001",
        "instruction": "do not trust",
    }
    record[field] = value
    (directory / "live_progress.jsonl").write_text(json.dumps(record) + "\n")
    result = video_view.export_videos(run)
    assert result["records"][0]["instruction_missing"]


def test_episode_prompt_precedes_live_observation_and_results_fallback(tmp_path):
    run, directory, _, _ = make_run(tmp_path)
    (directory / "rollout00_episode.json").unlink()
    live = dict(
        schema="psm_eval_live_progress_v1",
        task="CloseFridge",
        episode=0,
        evaluation_run_digest=DIGEST,
        evaluation_attempt_id="CloseFridge/attempt_0001",
        instruction="stale",
    )
    (directory / "live_progress.jsonl").write_text(json.dumps(live) + "\n")
    result = video_view.export_videos(run)
    assert result["records"][0]["instruction"] == "close the fridge"
    assert result["records"][0]["instruction_source"] == "results.prompt"


def test_conflicting_duplicate_or_foreign_episode_metadata_not_trusted(tmp_path):
    run, directory, row, _ = make_run(tmp_path)
    write_json(directory / "results.json", [row, dict(row)])
    result = video_view.export_videos(run)
    assert result["records"][0]["status"] == "incomplete"
    assert result["records"][0]["instruction_missing"]
    assert any("duplicate episode" in warning for warning in result["warnings"])


def test_reexport_idempotent_and_does_not_scan_its_own_copies(tmp_path):
    run, _, _, _ = make_run(tmp_path)
    first = video_view.export_videos(run)
    target = Path(first["records"][0]["output_path"])
    before = (target.read_bytes(), target.stat().st_ino, target.stat().st_mtime_ns)
    second = video_view.export_videos(run)
    assert second["exported_count"] == 0 and second["reused_count"] == 1
    assert (target.read_bytes(), target.stat().st_ino, target.stat().st_mtime_ns) == before
    assert len(json.loads(Path(second["index_file"]).read_text())["records"]) == 1


def test_external_view_never_scans_canonical_browsing_directory(tmp_path):
    run, _, _, _ = make_run(tmp_path)
    old_view = run / "videos_view" / "attempt_0001"
    old_view.mkdir(parents=True)
    (old_view / "rollout00.mp4").write_bytes(b"prior browser copy")
    before = (old_view / "rollout00.mp4").read_bytes()
    result = video_view.export_videos(run, view_dir=tmp_path / "outside_view")
    assert result["status"] == "OK" and result["exported_count"] == 1
    assert {row["task"] for row in result["records"]} == {"CloseFridge"}
    assert (old_view / "rollout00.mp4").read_bytes() == before


@pytest.mark.parametrize("change", ["video", "status", "instruction"])
def test_changed_source_or_metadata_keeps_old_export_and_adds_revision(tmp_path, change):
    run, directory, row, original = make_run(tmp_path)
    first = video_view.export_videos(run)
    old = Path(first["records"][0]["output_path"])
    original_copy = old.read_bytes()
    if change == "video":
        original.write_bytes(b"new source video")
    elif change == "status":
        row.update(outcome="behavioral_failure", policy=False)
    else:
        row["prompt"] = "a new actual instruction"
    if change != "video":
        write_json(directory / "rollout00_episode.json", row)
        write_json(directory / "results.json", [row])
    result = video_view.export_videos(run)
    assert result["exported_count"] == 1 and result["records"][0]["revision"] == 2
    assert "__rev_02_" in result["records"][0]["output_path"]
    assert old.read_bytes() == original_copy
    assert len(json.loads(Path(result["index_file"]).read_text())["records"]) == 2


def test_new_attempt_never_collides_with_previous_attempt_episode(tmp_path):
    run, _, _, _ = make_run(tmp_path)
    make_run(tmp_path, attempt="attempt_0002")
    result = video_view.export_videos(run)
    assert result["exported_count"] == 2
    assert len({row["output_path"] for row in result["records"]}) == 2
    assert {row["attempt"] for row in result["records"]} == {"attempt_0001", "attempt_0002"}


def test_unindexed_export_conflict_and_corrupted_index_never_overwritten(tmp_path):
    run, _, _, _ = make_run(tmp_path)
    first = video_view.export_videos(run)
    target = Path(first["records"][0]["output_path"])
    index = Path(first["index_file"])
    body = json.loads(index.read_text())
    body["records"] = []
    write_json(index, body)
    before = target.read_bytes()
    second = video_view.export_videos(run)
    assert second["status"] == "PARTIAL" and second["conflict_count"] == 1
    assert target.read_bytes() == before
    index.write_text("corrupt index, do not replace")
    result = video_view.export_videos(run)
    assert result["status"] == "ERROR" and index.read_text() == "corrupt index, do not replace"


def test_browser_edit_is_detected_without_touching_original(tmp_path):
    run, _, _, original = make_run(tmp_path)
    result = video_view.export_videos(run)
    copy = Path(result["records"][0]["output_path"])
    copy.write_bytes(b"browser edit")
    before = original.read_bytes()
    repeated = video_view.export_videos(run)
    assert repeated["status"] == "PARTIAL" and repeated["error_count"] == 1
    assert original.read_bytes() == before and copy.read_bytes() == b"browser edit"


def test_source_hardlink_replacement_of_browser_copy_is_rejected(tmp_path):
    run, _, _, original = make_run(tmp_path)
    first = video_view.export_videos(run)
    copy = Path(first["records"][0]["output_path"])
    copy.unlink()
    os.link(original, copy)
    result = video_view.export_videos(run)
    assert result["status"] == "PARTIAL" and result["reused_count"] == 0


@pytest.mark.parametrize(
    "location", ["CloseFridge", "FutureTask", "FutureTask/attempt_0001", "videos_view/nested", "."]
)
def test_custom_view_inside_run_cannot_pollute_current_or_future_task(tmp_path, location):
    run, _, _, _ = make_run(tmp_path)
    target = run / location
    before = snapshot(run)
    result = video_view.export_videos(run, view_dir=target)
    assert result["status"] == "ERROR"
    assert snapshot(run) == before
    if location == "FutureTask":
        assert not target.exists()


def test_custom_external_view_and_unknown_namespace_protection(tmp_path):
    run, _, _, _ = make_run(tmp_path)
    view = tmp_path / "external-view"
    result = video_view.export_videos(run, view_dir=view)
    assert result["status"] == "OK" and Path(result["records"][0]["output_path"]).is_relative_to(view)
    unknown = tmp_path / "unknown"
    unknown.mkdir()
    (unknown / "existing.txt").write_text("keep")
    rejected = video_view.export_videos(run, view_dir=unknown)
    assert rejected["status"] == "ERROR" and (unknown / "existing.txt").read_text() == "keep"


def test_duplicate_logical_episode_files_and_nested_partial_files_not_exported(tmp_path):
    run, directory, _, _ = make_run(tmp_path)
    (directory / "rollout0.mp4").write_bytes(b"duplicate logical episode")
    (directory / "rollout00_partial.mp4").write_bytes(b"not canonical")
    nested = directory / "nested"
    nested.mkdir()
    (nested / "rollout01.mp4").write_bytes(b"do not recurse")
    result = video_view.export_videos(run)
    assert result["status"] == "PARTIAL" and result["exported_count"] == 0 and result["conflict_count"] == 2


@pytest.mark.parametrize("target", ["source", "view", "task"])
def test_symlinks_never_copy_outside_source_or_write_outside_view(tmp_path, target):
    run, directory, _, original = make_run(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "video.mp4").write_bytes(b"foreign")
    view = None
    if target == "source":
        original.unlink()
        original.symlink_to(outside / "video.mp4")
    elif target == "task":
        (run / "OtherTask").symlink_to(outside, target_is_directory=True)
    else:
        (run / "videos_view").symlink_to(outside, target_is_directory=True)
    result = video_view.export_videos(run, view_dir=view)
    assert (outside / "video.mp4").read_bytes() == b"foreign"
    assert len(list(outside.iterdir())) == 1
    if target != "task":
        assert result["status"] in {"ERROR", "PARTIAL"}


def test_copy_error_persists_warning_but_does_not_mutate_resume_or_results(tmp_path, monkeypatch):
    run, _, _, _ = make_run(tmp_path)
    before = snapshot(run)

    def fail(*args):
        raise OSError("injected disk error")

    monkeypatch.setattr(video_view, "_copy", fail)
    result = video_view.export_videos(run)
    assert result["status"] == "PARTIAL" and result["error_count"] == 1
    assert snapshot(run) == before
    index = json.loads(Path(result["index_file"]).read_text())
    assert index["last_export"]["status"] == "PARTIAL"
    assert any("injected disk error" in warning for warning in index["last_export"]["warnings"])


def test_source_replaced_during_copy_never_published(tmp_path, monkeypatch):
    run, _, _, original = make_run(tmp_path)
    copier = video_view.shutil.copyfileobj

    def mutate(reader, writer, **kwargs):
        copier(reader, writer, **kwargs)
        original.write_bytes(b"source changed concurrently")

    monkeypatch.setattr(video_view.shutil, "copyfileobj", mutate)
    result = video_view.export_videos(run)
    assert result["status"] == "PARTIAL" and result["exported_count"] == 0
    assert not list((run / "videos_view").rglob("*.mp4"))


def test_cli_runs_with_stdlib_only_and_returns_index(tmp_path):
    run, _, _, _ = make_run(tmp_path)
    completed = subprocess.run(
        [sys.executable, str(Path(video_view.__file__)), "--run-dir", str(run)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert result["exported_count"] == 1 and Path(result["index_file"]).is_file()
