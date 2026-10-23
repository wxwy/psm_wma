"""CPU current-plan witnesses; fixtures are validated references, never real rollouts."""

from __future__ import annotations

import copy
import fcntl
import json
import pickle
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from tools.v3.episode_resume_prototype.model_identity import build_model_identity
from tools.v3.episode_resume_prototype.plan import (
    build_plan,
    build_report,
    locked_snapshot,
    render_plan,
    verified_scan_records,
)

MEDIA = {"save_rollout_mp4": True, "save_generated_video": "all", "save_init_png": True}
CURRENT = {"source_root": "b" * 40, "source_child": "c" * 40, "runtime_digest": "d" * 64}


def history(count, task="CloseFridge", *, seed=0, mode="none"):
    return [
        {
            "verified": True,
            "task": task,
            "source_episode": episode,
            "sampling_protocol": "legacy_task_stream",
            "effective_seed": seed,
            "seed_source": "inferred_from_original_manifest_not_rng_snapshot",
            "source_root": "a" * 40,
            "source_child": "a" * 40,
            "runtime_digest": "e" * 64,
            "outcome": "success" if episode % 2 == 0 else "behavioral_failure",
            "policy": episode % 2 == 0,
            "error": None,
            "source_ref": {
                "path": f"/synthetic/{task}/attempt_0001/rollout{episode:02d}_episode.json",
                "original_digest": "f" * 64,
                "attempt": "attempt_0001",
                "source_episode": episode,
                "hashes": {"core": f"{episode:064x}"},
            },
            "media_coverage": {
                "available_rollout": mode == "all",
                "available_init_png": mode == "all",
                "available_generated": 0 if mode == "none" else 1 if mode == "first" else 3,
                "prediction_count": 3,
                "original_policy": {"save_rollout_mp4": False, "save_generated_video": mode},
                "missing_requested_media": [] if mode == "all" else ["rollout", "generated"],
            },
        }
        for episode in range(count)
    ]


def plan(records, *, tasks=None, episodes=5, seed=0, **changes):
    options = {
        "tasks": tasks or ["CloseFridge"],
        "requested_episodes": episodes,
        "requested_seed": seed,
        "requested_media": MEDIA,
        "execution": {"gpus": [2, 3], "base_port": 8900, "task_wall_timeout_s": 1000},
        "current_provenance": CURRENT,
        "invocation_id": "fake-invocation-2",
    }
    options.update(changes)
    return build_plan(records, **options)


def completed_new(value):
    return [
        {
            **copy.deepcopy(row),
            "verified": True,
            "policy": True,
            "outcome": "success",
            "error": None,
            "source_ref": {
                "path": (
                    f"/synthetic/{task}/attempt_new_{row['execution_batch']}/"
                    f"rollout{row['source_episode']:02d}_episode.json"
                ),
                "original_digest": "1" * 64,
                "attempt": f"attempt_new_{row['execution_batch']}",
                "source_episode": row["source_episode"],
                "hashes": {"core": str(row["logical_episode_index"])},
            },
            "media_coverage": {
                "available_rollout": True,
                "available_init_png": True,
                "available_generated": 3,
                "prediction_count": 3,
                "missing_requested_media": [],
            },
        }
        for task, info in value["tasks"].items()
        for row in info["new_episodes"]
    ]


@pytest.mark.parametrize("old,requested,reused,new,excluded", [(3, 5, 3, 2, 0), (8, 5, 5, 0, 3), (5, 5, 5, 0, 0)])
def test_resize_only_counts_current_plan(old, requested, reused, new, excluded):
    sources = history(old)
    before = copy.deepcopy(sources)
    value = plan(sources, episodes=requested)
    row = value["tasks"]["CloseFridge"]
    assert (row["reused"], row["new"], row["excluded"]) == (reused, new, excluded)
    report = build_report(value, completed_new(value))
    assert report["status"] == "COMPLETE" and report["completed"] == requested
    assert sources == before and len(row["excluded_sources"]) == excluded
    if old == 8:
        assert report["sr"] == 3 / 5
    if old == 3:
        assert [item["logical_episode_index"] for item in row["new_episodes"]] == [3, 4]
        assert [item["source_episode"] for item in row["new_episodes"]] == [0, 0]


def test_expand_and_shrink_tasks_do_not_rewrite_or_count_other_tasks():
    sources = history(5) + history(5, "NavigateKitchen")
    expanded = plan(sources, tasks=["TurnOnSinkFaucet", "NavigateKitchen", "CloseFridge"])
    assert expanded["tasks"]["TurnOnSinkFaucet"]["new"] == 5
    assert expanded["tasks"]["NavigateKitchen"]["reused"] == 5
    shrunk = plan(sources)
    report = build_report(shrunk, [])
    assert report["requested"] == report["completed"] == 5
    assert set(report["tasks"]) == {"CloseFridge"} and len(sources) == 10


def test_seed_change_preserves_history_and_reports_actual_mixture():
    old = history(5)
    value = plan(old, episodes=8, seed=1)
    new = completed_new(value)
    assert all(row["effective_seed"] == 0 for row in old)
    assert all(row["requested_seed"] == 1 for row in new)
    report = build_report(value, new)
    assert "MIXED_SEED" in report["actual_conditions"]["flags"]
    assert "MIXED_RUNTIME" in report["actual_conditions"]["flags"]
    assert "MIXED_SAMPLING_PROTOCOL" in report["actual_conditions"]["flags"]
    assert report["actual_conditions"]["benchmark_qualification"].startswith("CONVENIENCE_AGGREGATE")
    assert report["actual_conditions"]["effective_seeds"] == sorted({0, *(row["effective_seed"] for row in new)})


def test_full_reuse_does_not_claim_requested_seed_or_current_runtime_was_used():
    value = plan(history(8), seed=1)
    report = build_report(value, [])
    assert report["executed"] == 0 and report["actual_conditions"]["effective_seeds"] == [0]
    assert report["actual_conditions"]["runtime_digests"] == ["e" * 64]
    assert "MIXED_RUNTIME" not in report["actual_conditions"]["flags"]
    assert any(row.get("code") == "NO_NEW_EPISODES_AT_REQUESTED_SEED" for row in report["warnings"])
    assert "previous_completed=8 reused=5 new=0 excluded=3" in render_plan(value)


@pytest.mark.parametrize("mode", ["none", "first", "all"])
def test_media_request_changes_do_not_schedule_already_verified_episodes(mode):
    value = plan(history(5, mode=mode))
    assert value["tasks"]["CloseFridge"]["new"] == 0
    report = build_report(value, [])
    assert report["status"] == "COMPLETE" and report["executed"] == 0
    assert report["missing_requested_media"] == (0 if mode == "all" else 15)
    assert value["requested_media"] == MEDIA


def test_execution_changes_and_task_reordering_do_not_change_reused_sources_or_new_seeds():
    records = history(3) + history(2, "NavigateKitchen")
    first = plan(records, tasks=["NavigateKitchen", "CloseFridge"])
    second = plan(
        records,
        tasks=["CloseFridge", "NavigateKitchen"],
        invocation_id="another-invocation",
        execution={"gpus": [7], "base_port": 9010, "task_wall_timeout_s": 4, "progress": False},
    )
    for task in first["selected_tasks"]:
        assert first["tasks"][task]["reused_sources"] == second["tasks"][task]["reused_sources"]
        assert [row["effective_seed"] for row in first["tasks"][task]["new_episodes"]] == [
            row["effective_seed"] for row in second["tasks"][task]["new_episodes"]
        ]


def test_partial_runtime_error_is_not_behavioral_failure_or_a_completed_episode():
    value = plan(history(3))
    executed = completed_new(value)
    executed[-1].update(verified=False, outcome="runtime_error", policy=False, error="RuntimeError: reset failed")
    report = build_report(value, executed)
    assert report["status"] == "PARTIAL" and report["exit_code"] == 1
    assert (report["completed"], report["failed"], report["remaining"]) == (4, 1, 1)
    assert report["sr"] is None and report["partial_sr"] == 3 / 4


def test_current_worker_error_remains_failure_even_with_all_requested_results():
    report = build_report(plan(history(5)), [], invocation_errors=[{"code": "WORKER_INITIALIZATION_ERROR"}])
    assert report["completed"] == 5 and report["remaining"] == 0
    assert report["status"] == "PARTIAL" and report["exit_code"] == 1 and report["sr"] is None


def test_historical_runtime_error_does_not_permanently_poison_completed_new_invocation():
    records = history(3)
    broken = copy.deepcopy(records[-1])
    broken.update(verified=False, outcome="runtime_error", error="prior interruption")
    value = plan(records + [broken])
    assert value["tasks"]["CloseFridge"]["previous_completed"] == 3
    assert build_report(value, completed_new(value))["status"] == "COMPLETE"


def test_duplicate_refs_and_duplicate_executions_cannot_double_count():
    records = history(3)
    value = plan(records + [records[0]])
    assert value["tasks"]["CloseFridge"]["reused"] == 3
    executed = completed_new(value)
    report = build_report(value, executed + [executed[0]])
    assert report["completed"] == 5 and report["status"] == "PARTIAL" and report["exit_code"] == 1


def test_shared_task_snapshot_change_does_not_create_a_second_episode():
    old = history(1)[0]
    old["source_ref"]["hashes"]["results.json"] = "old-aggregate"
    newer = copy.deepcopy(old)
    newer["source_ref"]["hashes"]["results.json"] = "aggregate-with-later-episode"
    value = plan([old, newer], episodes=2)
    assert value["tasks"]["CloseFridge"]["reused"] == 1
    assert value["diagnostics"][0]["code"] == "REPEATED_SOURCE_REFERENCE_EXCLUDED"


def test_task_level_cleanup_added_on_complete_does_not_change_episode_identity():
    earlier = history(1)[0]
    completed = copy.deepcopy(earlier)
    completed["source_ref"]["hashes"]["process_cleanup.json"] = "now-closed-task-processes"
    value = plan([earlier, completed], episodes=1)
    assert value["tasks"]["CloseFridge"]["reused"] == 1
    assert value["tasks"]["CloseFridge"]["new"] == 0


def test_same_locator_with_changed_core_is_rejected_instead_of_double_counted():
    old = history(1)[0]
    changed = copy.deepcopy(old)
    changed["source_ref"]["hashes"]["core"] = "tampered-action-record"
    with pytest.raises(ValueError, match="SOURCE_EVIDENCE_CHANGED"):
        plan([old, changed], episodes=2)


def test_two_attempts_for_same_logical_slot_never_count_twice_or_prefer_success():
    older = history(1)[0]
    older.update(logical_episode_index=0, outcome="behavioral_failure", policy=False)
    newer = copy.deepcopy(older)
    newer.update(outcome="success", policy=True)
    newer["source_ref"].update(
        attempt="attempt_0002", path="/synthetic/CloseFridge/attempt_0002/rollout00_episode.json"
    )
    value = plan([newer, older], episodes=2)
    assert value["tasks"]["CloseFridge"]["reused"] == 1
    assert value["tasks"]["CloseFridge"]["reused_sources"][0]["policy"] is False
    assert any(row["code"] == "LOGICAL_SLOT_DUPLICATE_EXCLUDED" for row in value["diagnostics"])
    assert build_report(value, completed_new(value))["sr"] == 1 / 2


def test_legacy_physical_index_and_new_explicit_logical_slot_cannot_double_count():
    older = history(1)[0]
    newer = copy.deepcopy(older)
    newer.update(logical_episode_index=0, sampling_protocol="independent_episode_v1")
    newer["source_ref"].update(attempt="attempt_0002")
    value = plan([newer, older], episodes=2)
    assert value["tasks"]["CloseFridge"]["reused"] == 1
    assert value["tasks"]["CloseFridge"]["new"] == 1


@pytest.mark.parametrize("original_mode", ["none", "first", "all"])
def test_turning_off_all_requested_media_never_rewrites_history_or_requires_rerun(original_mode):
    records = history(5, mode=original_mode)
    disabled = {"save_rollout_mp4": False, "save_generated_video": "none", "save_init_png": False}
    value = plan(records, requested_media=disabled)
    report = build_report(value, [])
    assert report["completed"] == 5 and report["executed"] == 0 and report["missing_requested_media"] == 0


def test_current_media_policy_recomputes_stale_catalog_coverage_without_source_changes():
    records = history(5)
    before = copy.deepcopy(records)
    disabled = {"save_rollout_mp4": False, "save_generated_video": "none", "save_init_png": False}
    value = plan(records, requested_media=disabled)
    report = build_report(value, [])
    assert report["missing_requested_media"] == 0 and report["requested_media_coverage"] == 1.0
    assert records == before and report["executed"] == 0


def test_scanner_diagnostics_are_retained_in_start_plan_and_end_report():
    diagnostics = [{"code": "DUPLICATE_CONFLICT_EXCLUDED", "task": "CloseFridge", "reason": "old attempt kept"}]
    value = plan(history(5), scan_diagnostics=diagnostics)
    report = build_report(value, [])
    assert value["diagnostics"] == report["diagnostics"] == diagnostics


def test_one_derived_seed_family_is_distinguished_from_multiple_environment_seeds():
    value = plan(history(1, seed=9), episodes=3, seed=9)
    report = build_report(value, completed_new(value))
    actual = report["actual_conditions"]
    assert actual["requested_seed_families"] == [9] and len(actual["effective_seeds"]) == 3
    assert "MIXED_SEED" not in actual["flags"]
    assert "MULTIPLE_EFFECTIVE_ENV_SEEDS" in actual["flags"]


def test_fresh_task_retains_literal_seed_single_environment_and_physical_episode_order():
    value = plan([], episodes=5, seed=9)
    task = value["tasks"]["CloseFridge"]
    assert task["sampling_mode"] == "fresh_task_stream"
    assert [row["effective_seed"] for row in task["new_episodes"]] == [9] * 5
    assert [row["source_episode"] for row in task["new_episodes"]] == list(range(5))
    assert [row["logical_episode_index"] for row in task["new_episodes"]] == list(range(5))
    assert len(task["execution_batches"]) == 1
    assert task["execution_batches"][0]["environment_constructions"] == 1
    assert task["execution_batches"][0]["public_reset_calls"] == 5
    assert not value["warnings"]
    report = build_report(value, completed_new(value))
    assert report["status"] == "COMPLETE" and report["actual_conditions"]["effective_seeds"] == [9]
    assert "MIXED_SAMPLING_PROTOCOL" not in report["actual_conditions"]["flags"]


def test_expanding_four_to_eighteen_tasks_uses_fresh_protocol_only_for_new_tasks():
    old_tasks = ["CloseFridge", "TaskOne", "TaskTwo", "TaskThree"]
    new_tasks = [f"NewTask{index}" for index in range(14)]
    records = [row for task in old_tasks for row in history(3, task=task)]
    value = plan(records, tasks=old_tasks + new_tasks, episodes=5, seed=0)
    for task in old_tasks:
        item = value["tasks"][task]
        assert item["reused"] == 3 and item["sampling_mode"] == "resume_gap_independent"
        assert [row["logical_episode_index"] for row in item["new_episodes"]] == [3, 4]
        assert [row["source_episode"] for row in item["new_episodes"]] == [0, 0]
        assert len(item["execution_batches"]) == 2
    for task in new_tasks:
        item = value["tasks"][task]
        assert item["reused"] == 0 and item["sampling_mode"] == "fresh_task_stream"
        assert [row["effective_seed"] for row in item["new_episodes"]] == [0] * 5
        assert [row["source_episode"] for row in item["new_episodes"]] == list(range(5))
        assert len(item["execution_batches"]) == 1
    assert "MIXED_SAMPLING_PROTOCOL" in value["planned_conditions"]["flags"]


def test_sparse_completed_catalog_recovers_failed_slot_after_disk_roundtrip_without_pending_hint(tmp_path):
    records = history(5)
    records.pop(2)
    catalog = tmp_path / "verified-synthetic-catalog.json"
    catalog.write_text(json.dumps(records))
    before = catalog.read_bytes()
    restarted = plan(json.loads(catalog.read_text()), episodes=5)
    item = restarted["tasks"]["CloseFridge"]
    assert [row["logical_episode_index"] for row in item["new_episodes"]] == [2]
    assert item["pending_recovery"]["pending_slots"] == [2]
    assert any(
        row["code"] == "INFERRED_FROM_PERSISTENT_COMPLETED_SLOT_GAP" for row in item["pending_recovery"]["diagnostics"]
    )
    report = build_report(restarted, completed_new(restarted))
    assert report["status"] == "COMPLETE" and report["completed"] == 5
    assert catalog.read_bytes() == before


def test_shrink_then_expand_preserves_unfinished_slot_and_excluded_sources():
    records = history(5)
    records.pop(2)
    smaller = plan(records, episodes=2)
    assert smaller["tasks"]["CloseFridge"]["new"] == 0
    assert smaller["tasks"]["CloseFridge"]["pending_recovery"]["pending_slots"] == [2]
    larger = plan(records, episodes=5)
    assert [row["logical_episode_index"] for row in larger["tasks"]["CloseFridge"]["new_episodes"]] == [2]
    assert larger["tasks"]["CloseFridge"]["pending_recovery"]["pending_slots"] == [2]


def test_unpersisted_optional_pending_hint_cannot_invent_a_new_slot():
    with pytest.raises(ValueError, match="UNPERSISTED_PENDING_HINT"):
        plan(history(3), episodes=5, pending_slots={"CloseFridge": [8]})


def test_restarted_plan_reads_persisted_tail_reservation_and_progress_without_memory_state(tmp_path):
    document = {
        "task": "CloseFridge",
        "reservations": [
            {
                "logical_episode_index": 2,
                "reservation_id": "CloseFridge:slot:2",
                "attempt": "attempt_0002",
                "source_episode": 0,
            }
        ],
        "progress_diagnostics": [
            {
                "logical_episode_index": 2,
                "reservation_id": "CloseFridge:slot:2",
                "attempt": "attempt_0002",
                "source_episode": 0,
                "event": "start",
            }
        ],
    }
    path = tmp_path / "logical_slots.json"
    path.write_text(json.dumps(document))
    before = path.read_bytes()
    value = plan(history(2), episodes=3, recovery_documents=[path])
    item = value["tasks"]["CloseFridge"]
    assert [row["logical_episode_index"] for row in item["new_episodes"]] == [2]
    assert item["pending_recovery"]["pending_slots"] == [2]
    # A process restart reparses bytes; no optional in-memory pending list is supplied.
    again = plan(history(2), episodes=3, recovery_documents=[path], invocation_id="restarted-again")
    assert (
        again["tasks"]["CloseFridge"]["new_episodes"][0]["effective_seed"] == item["new_episodes"][0]["effective_seed"]
    )
    assert path.read_bytes() == before


def test_quarantined_history_diagnostic_survives_whole_task_fresh_restart():
    diagnostics = [{"code": "CORRUPT_LEGACY_COMPLETE_MARKER", "task": "CloseFridge", "attempt": "attempt_0001"}]
    value = plan([], scan_diagnostics=diagnostics)
    assert value["tasks"]["CloseFridge"]["sampling_mode"] == "fresh_task_stream"
    report = build_report(value, completed_new(value))
    assert value["diagnostics"] == report["diagnostics"] == diagnostics


def test_config_or_same_task_metadata_changes_are_warnings_not_a_fifth_model_parameter():
    records = history(2)
    for row in records:
        row.update(config_sha256="1" * 64, task_metadata_sha256="2" * 64)
    records[1].update(config_sha256="3" * 64, task_metadata_sha256="4" * 64)
    report = build_report(plan(records, episodes=2), [])
    assert report["status"] == "COMPLETE"
    assert "MIXED_CONFIG" in report["actual_conditions"]["flags"]
    assert "MIXED_TASK_METADATA" in report["actual_conditions"]["flags"]
    assert report["actual_conditions"]["benchmark_qualification"].startswith("CONVENIENCE_AGGREGATE")


def test_wrong_actual_seed_is_rejected_before_it_can_be_counted():
    value = plan(history(4))
    executed = completed_new(value)
    executed[0]["effective_seed"] += 1
    report = build_report(value, executed)
    assert report["completed"] == 4 and report["failed"] == 1 and report["sr"] is None
    assert report["invocation_errors"][0]["code"] == "EXECUTED_SEED_MISMATCH"


def test_unfinished_slot_retries_with_new_attempt_without_reusing_partial_source():
    records = history(3)
    records.pop(1)
    value = plan(records, episodes=3, pending_slots={"CloseFridge": [1]})
    assert [row["logical_episode_index"] for row in value["tasks"]["CloseFridge"]["new_episodes"]] == [1]
    report = build_report(value, completed_new(value))
    assert report["status"] == "COMPLETE"
    assert [
        row.get("logical_episode_index", row["source_episode"])
        for row in report["tasks"]["CloseFridge"]["episode_sources"]
    ] == [0, 1, 2]


def test_unknown_historical_seed_is_not_filled_from_requested_seed():
    value = plan(history(5, seed=None), seed=8)
    report = build_report(value, [])
    assert "UNKNOWN_SEED" in report["actual_conditions"]["flags"]
    assert report["actual_conditions"]["effective_seeds"] == []


def make_model(tmp_path, **overrides):
    path = tmp_path / "checkpoint"
    model = path / "model"
    model.mkdir(parents=True, exist_ok=True)
    (model / ".metadata").write_bytes(pickle.dumps({"fake_metadata": True}, protocol=4))
    with zipfile.ZipFile(model / "__0_0.distcp", "w") as archive:
        archive.writestr("archive/data.pkl", b"fake, not actual tensor data")
    return build_model_identity(checkpoint=path, num_steps=30, action_horizon=16, guidance=1.0, **overrides)


@pytest.mark.parametrize("field,value", [("num_steps", 20), ("action_horizon", 8), ("guidance", 2.0)])
def test_model_parameter_mismatch_precedes_lock_read_callback_and_any_new_attempt(tmp_path, field, value):
    expected = make_model(tmp_path)
    parameters = {"checkpoint": tmp_path / "checkpoint", "num_steps": 30, "action_horizon": 16, "guidance": 1.0}
    parameters[field] = value
    current = build_model_identity(**parameters)
    called = []
    with pytest.raises(ValueError, match=field):
        locked_snapshot(
            tmp_path / "nonexistent-run",
            expected_identity=expected,
            current_identity_reader=lambda: current,
            snapshot_reader=lambda: called.append("launch"),
        )
    assert not called and not (tmp_path / "nonexistent-run").exists()


def test_checkpoint_payload_mismatch_precedes_lock_or_launch(tmp_path):
    expected = make_model(tmp_path)
    with zipfile.ZipFile(tmp_path / "checkpoint/model/__0_0.distcp", "a") as archive:
        archive.writestr("archive/changed", b"replacement")
    current = build_model_identity(checkpoint=tmp_path / "checkpoint", num_steps=30, action_horizon=16, guidance=1.0)
    with pytest.raises(ValueError, match="checkpoint"):
        locked_snapshot(
            tmp_path / "no-run",
            expected_identity=expected,
            current_identity_reader=lambda: current,
            snapshot_reader=lambda: pytest.fail("must not schedule"),
        )
    assert not (tmp_path / "no-run").exists()


def test_busy_lease_never_writes_migration_or_invocation(tmp_path):
    identity = make_model(tmp_path)
    lock = tmp_path / ".run.lock"
    lock.touch()
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    with lock.open("a") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            locked_snapshot(
                tmp_path,
                expected_identity=identity,
                current_identity_reader=lambda: identity,
                snapshot_reader=lambda: pytest.fail("must not read or write invocation"),
            )
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_rechecks_identity_after_lease_and_releases_lease_on_error(tmp_path):
    identity = make_model(tmp_path)
    changed = build_model_identity(checkpoint=tmp_path / "checkpoint", num_steps=10, action_horizon=16, guidance=1)
    (tmp_path / ".run.lock").touch()
    reads = iter([identity, changed])
    with pytest.raises(ValueError, match="num_steps"):
        locked_snapshot(
            tmp_path,
            expected_identity=identity,
            current_identity_reader=lambda: next(reads),
            snapshot_reader=lambda: pytest.fail("must not schedule"),
        )
    assert (
        locked_snapshot(
            tmp_path,
            expected_identity=identity,
            current_identity_reader=lambda: identity,
            snapshot_reader=lambda: "unmodified snapshot",
        )
        == "unmodified snapshot"
    )


def test_unsafe_lock_path_is_not_followed(tmp_path):
    identity = make_model(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.touch()
    (tmp_path / ".run.lock").symlink_to(elsewhere)
    with pytest.raises(ValueError, match="unsafe"):
        locked_snapshot(
            tmp_path,
            expected_identity=identity,
            current_identity_reader=lambda: identity,
            snapshot_reader=lambda: pytest.fail("unsafe namespace"),
        )


def test_actual_owned_process_cleanup_does_not_kill_a_foreign_process():
    from scripts.robocasa_processes import OwnedProcess

    foreign = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    owned = None
    try:
        owned = OwnedProcess([sys.executable, "-c", "import time; time.sleep(30)"], grace_s=0.2)
        result = owned.close()
        assert result["live_group"] is False and foreign.poll() is None
    finally:
        if owned is not None:
            owned.close()
        foreign.terminate()
        foreign.wait(timeout=5)


def test_actual_partial_legacy_evidence_scan_to_current_plan_and_report(tmp_path):
    from tools.v3.episode_resume_prototype.episode_evidence import scan_legacy_run
    from tools.v3.episode_resume_prototype.episode_evidence_test import build_legacy_run

    directory = build_legacy_run(tmp_path, completed=2, trials=5, status="FAILED", seed=0)
    before = {str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    scan = scan_legacy_run(directory, sim_python=Path(sys.executable), requested_media=MEDIA)
    value = plan(verified_scan_records(scan), seed=1, scan_diagnostics=scan["diagnostics"])
    assert (value["tasks"]["CloseFridge"]["reused"], value["tasks"]["CloseFridge"]["new"]) == (2, 3)
    report = build_report(value, completed_new(value))
    assert report["status"] == "COMPLETE" and report["reused"] == 2 and report["executed"] == 3
    assert "MIXED_SEED" in report["actual_conditions"]["flags"]
    assert {str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob("*") if p.is_file()} == before
