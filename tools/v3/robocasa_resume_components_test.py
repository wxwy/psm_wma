"""Production component parity and bounded-I/O guards; synthetic CPU assets only."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import pickle
import sys
import threading
import time
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from robocasa_episode_resume import (  # noqa: E402
    MAX_EPISODES,  # noqa: E402
    episode_evidence,
    model_identity,
    plan,
    reservation_recovery,
    scene_sampling,
)

from tools.v3.episode_resume_prototype import model_identity as approved_identity  # noqa: E402
from tools.v3.episode_resume_prototype import plan as approved_plan  # noqa: E402
from tools.v3.episode_resume_prototype import scene_sampling as approved_scene  # noqa: E402
from tools.v3.episode_resume_prototype.episode_evidence_test import build_legacy_run  # noqa: E402
from tools.v3.episode_resume_prototype.model_identity_test import legacy  # noqa: E402
from tools.v3.episode_resume_prototype.plan_test import CURRENT, MEDIA, completed_new, history  # noqa: E402


@pytest.fixture
def checkpoint(tmp_path):
    directory = tmp_path / "synthetic-job/checkpoints/iter_000004000"
    model = directory / "model"
    model.mkdir(parents=True)
    (model / ".metadata").write_bytes(pickle.dumps({"synthetic": True}, protocol=4))
    for index in range(2):
        with zipfile.ZipFile(model / f"__{index}_0.distcp", "w") as archive:
            archive.writestr("archive/data.pkl", pickle.dumps({"tiny": index}, protocol=4))
            archive.writestr("archive/data/0", b"synthetic tensor bytes" * (index + 1))
    return directory


def identity(checkpoint, **changes):
    return model_identity.build_model_identity(
        **dict(checkpoint=checkpoint, num_steps=30, action_horizon=16, guidance=1.0) | changes
    )


def stripped(value):
    if isinstance(value, dict):
        return {
            key: stripped(child)
            for key, child in value.items()
            if key not in {"schema", "production_wired", "prototype_only"}
        }
    if isinstance(value, list):
        return [stripped(child) for child in value]
    return value


def make_plan(module, records, *, tasks=("CloseFridge",), episodes=5, seed=0, **kwargs):
    return module.build_plan(
        records,
        tasks=list(tasks),
        requested_episodes=episodes,
        requested_seed=seed,
        requested_media=MEDIA,
        execution={"gpus": [2, 3], "base_port": 8900},
        current_provenance=CURRENT,
        invocation_id="synthetic-invocation",
        **kwargs,
    )


def test_production_modules_do_not_import_isolated_prototypes():
    for path in (ROOT / "scripts/robocasa_episode_resume").glob("*.py"):
        assert "tools.v3.episode_resume_prototype" not in path.read_text()
        ast.parse(path.read_text())


def test_current_full_hash_parity_and_actual_io_telemetry(checkpoint):
    events = []
    current = identity(checkpoint, on_read_progress=events.append)
    original = approved_identity.build_model_identity(
        checkpoint=checkpoint, num_steps=30, action_horizon=16, guidance=1
    )
    assert {key: current[key] for key in original} == original
    stats = current["checkpoint_read_telemetry"]
    metadata_bytes = (checkpoint / "model/.metadata").stat().st_size
    shard_bytes = sum(path.stat().st_size for path in (checkpoint / "model").glob("*.distcp"))
    assert stats["bytes_read"] == stats["expected_bytes"] == metadata_bytes + shard_bytes
    assert stats["metadata_bytes_read"] == metadata_bytes
    assert stats["shard_bytes_read"] == shard_bytes
    assert stats["files_read"] == 3 and stats["elapsed_seconds"] >= 0
    assert events[-1]["files_read"] == 3 and events[-1]["bytes_read"] == stats["bytes_read"]
    assert model_identity.compare_model_identity(original, current)["status"] == "MATCH"


def test_io_progress_callback_failures_never_weaken_or_change_hash(checkpoint):
    first = identity(checkpoint)
    second = identity(checkpoint, on_read_progress=Mock(side_effect=OSError("progress unavailable")))
    assert first["digest"] == second["digest"]
    assert first["parameters"] == second["parameters"]


def test_stat_observation_uses_no_payload_reads_after_full_hash(checkpoint, monkeypatch):
    current = identity(checkpoint)
    monkeypatch.setattr(model_identity, "_read_hash", Mock(side_effect=AssertionError("full rehash forbidden")))
    monkeypatch.setattr(Path, "open", Mock(side_effect=AssertionError("payload read forbidden")))
    result = model_identity.verify_model_observation(current)
    assert result["status"] == "UNCHANGED_STAT_OBSERVATION"
    assert result["bytes_read"] == 0 and result["files_checked"] == 3


@pytest.mark.parametrize("mutation", ["metadata", "shard", "added_shard", "removed_shard", "new_inventory", "symlink"])
def test_stat_observation_rejects_model_changes_between_hash_and_load(checkpoint, mutation):
    current = identity(checkpoint)
    model = checkpoint / "model"
    target = model / ".metadata" if mutation == "metadata" else model / "__0_0.distcp"
    if mutation in {"metadata", "shard"}:
        raw = target.read_bytes()
        target.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    elif mutation == "added_shard":
        (model / "__2_0.distcp").write_bytes(b"new unexpected shard")
    elif mutation == "removed_shard":
        target.unlink()
    elif mutation == "new_inventory":
        (model / "unknown-new-file").write_bytes(b"unclaimed")
    else:
        real = model / "renamed-original"
        target.rename(real)
        target.symlink_to(real)
    with pytest.raises(model_identity.IdentityInputError):
        model_identity.verify_model_observation(current)


def test_fast_observation_never_invents_a_snapshot_from_an_old_persisted_identity(checkpoint):
    current = identity(checkpoint)
    del current["observed_model_files"]
    with pytest.raises(model_identity.IdentityInputError, match="fresh full-model stat observation"):
        model_identity.verify_model_observation(current)


def test_legacy_bridge_keeps_original_sha_scope_and_never_rehashes_per_episode(checkpoint, monkeypatch):
    current = identity(checkpoint)
    manifest = legacy(current)
    before = copy.deepcopy(manifest)
    monkeypatch.setattr(model_identity, "_read_hash", Mock(side_effect=AssertionError("extra full read forbidden")))
    decision = model_identity.legacy_ingest(manifest, current)
    assert decision == {
        **approved_identity.legacy_ingest(manifest, current),
        "owner_accepted_relocated_legacy_checkpoint": False,
    }
    assert decision["historical_payload_sha256"] is None and manifest == before
    assert decision["status"] == "LEGACY_STAT_BRIDGE_MATCH"


@pytest.mark.parametrize(
    "old,new,tasks,seed",
    [
        (0, 5, ["CloseFridge"], 0),
        (3, 5, ["CloseFridge"], 1),
        (8, 5, ["CloseFridge"], 1),
        (5, 5, ["CloseFridge", "NavigateKitchen"], 0),
    ],
)
def test_promoted_planner_scene_and_report_match_approved_r2(old, new, tasks, seed):
    records = history(old)
    before = copy.deepcopy(records)
    actual = make_plan(plan, records, episodes=new, tasks=tasks, seed=seed)
    expected = make_plan(approved_plan, records, episodes=new, tasks=tasks, seed=seed)
    assert stripped(actual) == stripped(expected)
    assert actual["schema"] == "psm_episode_resume_plan_v1" and actual["production_wired"] is True
    assert stripped(plan.build_report(actual, completed_new(actual))) == stripped(
        approved_plan.build_report(expected, completed_new(expected))
    )
    assert records == before


@pytest.mark.parametrize(
    "mode,indices,sources",
    [("fresh_task_stream", range(5), []), ("resume_gap_independent", [3, 4], [{"effective_seed": 0}])],
)
def test_promoted_scene_sampler_is_identical_under_approved_bounds(mode, indices, sources):
    args = dict(
        task="CloseFridge",
        requested_seed=0,
        new_logical_indices=indices,
        attempt_nonce="invocation",
        sampling_mode=mode,
        legacy_sources=sources,
    )
    assert stripped(scene_sampling.plan_scene_sampling(**args)) == stripped(approved_scene.plan_scene_sampling(**args))


@pytest.mark.parametrize(
    "status,completed,expected,corrupt",
    [("FAILED", 2, 2, False), ("RUNNING", 2, 2, False), ("COMPLETE", 5, 5, False), ("COMPLETE", 2, 0, True)],
)
def test_production_scanner_preserves_complete_contradiction_and_partial_prefix_contract(
    tmp_path, status, completed, expected, corrupt
):
    run = build_legacy_run(tmp_path, completed=completed, trials=5, status=status)
    files = {path: path.read_bytes() for path in run.rglob("*") if path.is_file()}
    scanned = episode_evidence.scan_legacy_run(run, sim_python=Path(sys.executable))
    assert len(scanned["records"]) == expected
    assert any(row["code"] == "CORRUPT_LEGACY_COMPLETE_MARKER" for row in scanned["diagnostics"]) is corrupt
    assert {path: path.read_bytes() for path in files} == files
    if expected:
        rows = plan.verified_scan_records(scanned)
        assert len(rows) == expected and all(row["verified"] for row in rows)


@pytest.mark.parametrize("status", ["FAILED", "RUNNING"])
def test_partial_source_cannot_import_an_episode_beyond_original_trial_budget(tmp_path, status):
    run = build_legacy_run(tmp_path, completed=3, trials=2, status=status)
    before = {path: path.read_bytes() for path in run.rglob("*") if path.is_file()}
    manifest = json.loads((run / "evaluation_manifest.json").read_text())
    with pytest.raises(episode_evidence.EpisodeEvidenceError) as error:
        episode_evidence.verify_legacy_episode(
            run / "CloseFridge/attempt_0001", 2, manifest=manifest, sim_python=Path(sys.executable)
        )
    assert error.value.code == "SOURCE_EPISODE_OUTSIDE_ORIGINAL_BUDGET"
    scanned = episode_evidence.scan_legacy_run(run, sim_python=Path(sys.executable))
    assert [row["source_episode"] for row in scanned["records"]] == [0, 1]
    assert any(
        row["code"] == "SOURCE_EPISODE_OUTSIDE_ORIGINAL_BUDGET" and row["episode"] == 2
        for row in scanned["diagnostics"]
    )
    assert {path: path.read_bytes() for path in before} == before


def test_expired_scan_deadline_and_cancel_propagate_without_changing_original_evidence(tmp_path):
    run = build_legacy_run(tmp_path, completed=2, trials=2, status="COMPLETE")
    before = {path: path.read_bytes() for path in run.rglob("*") if path.is_file()}
    manifest = json.loads((run / "evaluation_manifest.json").read_text())
    stop = threading.Event()
    stop.set()
    for options, error in (({"deadline": time.monotonic() - 1}, TimeoutError), ({"stop": stop}, InterruptedError)):
        with pytest.raises(error):
            episode_evidence.scan_legacy_run(run, sim_python=Path(sys.executable), **options)
        with pytest.raises(error):
            episode_evidence.verify_legacy_episode(
                run / "CloseFridge/attempt_0001", 0, manifest=manifest, sim_python=Path(sys.executable), **options
            )
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize("status", ["FAILED", "COMPLETE"])
def test_media_deadline_is_forwarded_and_never_reclassified_as_corrupt_source(tmp_path, monkeypatch, status):
    run = build_legacy_run(tmp_path, completed=1, trials=1, status=status, rollout=True)
    before = {path: path.read_bytes() for path in run.rglob("*") if path.is_file()}
    deadline, stop = time.monotonic() + 30, threading.Event()
    calls = []

    def expired_media(path, *, sim_python, kind, deadline, stop):
        calls.append((deadline, stop))
        raise TimeoutError("synthetic media validation expired")

    monkeypatch.setattr(episode_evidence, "validate_media", expired_media)
    monkeypatch.setattr(episode_evidence, "validate_attempt", lambda *args, **kwargs: None)
    with pytest.raises(TimeoutError, match="synthetic media validation expired"):
        episode_evidence.scan_legacy_run(run, sim_python=Path(sys.executable), deadline=deadline, stop=stop)
    assert calls == [(deadline, stop)]
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize("index", [MAX_EPISODES, 10**30, -1, True])
def test_huge_logical_recovery_slot_rejected_before_range_materialization(index, monkeypatch):
    monkeypatch.setattr(reservation_recovery, "range", Mock(side_effect=AssertionError("range reached")), raising=False)
    reservation = {"logical_episode_index": index, "source_ref": {"path": "/fake/reservation.json", "sha256": "a" * 64}}
    with pytest.raises(ValueError, match="integer in"):
        reservation_recovery.recover_pending_slots(task="CloseFridge", completed_slots=[], reservations=[reservation])


def test_oversized_scene_iterator_is_bounded_before_allocating_an_unlimited_list():
    with pytest.raises(ValueError, match="resource limit"):
        scene_sampling.plan_scene_sampling(
            task="CloseFridge",
            requested_seed=0,
            new_logical_indices=range(10**12),
            attempt_nonce="invocation",
            sampling_mode="fresh_task_stream",
        )


def test_huge_scene_index_rejected_before_fresh_range_check(monkeypatch):
    monkeypatch.setattr(scene_sampling, "range", Mock(side_effect=AssertionError("range reached")), raising=False)
    with pytest.raises(ValueError, match="integer in"):
        scene_sampling.plan_scene_sampling(
            task="CloseFridge",
            requested_seed=0,
            new_logical_indices=[10**30],
            attempt_nonce="invocation",
            sampling_mode="fresh_task_stream",
        )


@pytest.mark.parametrize(
    "episodes,tasks", [(MAX_EPISODES + 1, ["CloseFridge"]), (MAX_EPISODES, ["CloseFridge", "NavigateKitchen"])]
)
def test_requested_and_total_episode_budgets_checked_before_copy_or_plan(episodes, tasks):
    with pytest.raises(ValueError, match="integer in"):
        make_plan(plan, [], episodes=episodes, tasks=tasks)


def test_extension_past_logical_capacity_fails_before_new_range(monkeypatch):
    monkeypatch.setattr(
        plan, "recover_pending_slots", lambda **kwargs: {"pending_slots": [], "next_slot_floor": MAX_EPISODES}
    )
    monkeypatch.setattr(plan, "range", Mock(side_effect=AssertionError("range reached")), raising=False)
    with pytest.raises(ValueError, match="resource bound"):
        make_plan(plan, history(1), episodes=2)


def test_recovery_document_parent_symlink_rejected_without_modifying_source(tmp_path):
    directory = tmp_path / "source"
    directory.mkdir()
    raw = b'{"task":"CloseFridge","reservations":[]}\n'
    (directory / "catalog.json").write_bytes(raw)
    (tmp_path / "alias").symlink_to(directory, target_is_directory=True)
    with pytest.raises(reservation_recovery.ReservationRecoveryError, match="symlink"):
        reservation_recovery.read_recovery_document(tmp_path / "alias/catalog.json")
    assert (directory / "catalog.json").read_bytes() == raw


def test_persistent_huge_trial_claim_rejected_before_whole_complete_validation(tmp_path, monkeypatch):
    run = build_legacy_run(tmp_path, completed=2, trials=5, status="FAILED")
    manifest = json.loads((run / "evaluation_manifest.json").read_text())
    manifest["identity"]["protocol"]["trials"] = 10**30
    manifest["digest"] = hashlib.sha256(episode_evidence._canonical(manifest["identity"])).hexdigest()
    monkeypatch.setattr(
        episode_evidence, "validate_attempt", Mock(side_effect=AssertionError("full validation reached"))
    )
    with pytest.raises(episode_evidence.EpisodeEvidenceError, match="integer in"):
        episode_evidence.verify_legacy_episode(
            run / "CloseFridge/attempt_0001", 0, manifest=manifest, sim_python=Path(sys.executable)
        )


def test_original_manifest_and_c01_observations_preserve_pending_tail_below_current_demand(tmp_path):
    manifest = tmp_path / "evaluation_manifest.json"
    progress = tmp_path / "episode_progress.jsonl"
    manifest.write_text(json.dumps({"identity": {"protocol": {"trials": 5}}}))
    progress.write_text('{"event":"start","episode":2}\n')
    before = {path: path.read_bytes() for path in (manifest, progress)}
    reference = {"path": str(manifest), "sha256": hashlib.sha256(before[manifest]).hexdigest()}
    progress_reference = {"path": str(progress), "sha256": hashlib.sha256(before[progress]).hexdigest()}
    observations = [
        {
            "task": "CloseFridge",
            "logical_episode_index": index,
            "kind": "legacy_original_task_allocation",
            "original_manifest_trials": 5,
            "source_ref": reference,
            "progress_source_refs": [progress_reference],
        }
        for index in range(5)
    ]
    original = copy.deepcopy(observations)
    current = make_plan(plan, history(2), episodes=2, recovery_observations=observations)
    recovery = current["tasks"]["CloseFridge"]["pending_recovery"]
    assert current["tasks"]["CloseFridge"]["new"] == 0
    assert recovery["pending_slots"] == [2, 3, 4]
    assert reference in recovery["authority"]["source_refs"]
    assert progress_reference in recovery["authority"]["source_refs"]
    expanded = make_plan(plan, history(2), episodes=3, recovery_observations=observations)
    assert [row["logical_episode_index"] for row in expanded["tasks"]["CloseFridge"]["new_episodes"]] == [2]
    assert observations == original
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize("observation", [2, {"task": "CloseFridge", "logical_episode_index": 2}])
def test_transient_slot_hints_are_not_source_bearing_recovery_observations(observation):
    with pytest.raises(ValueError, match="actual persistent path/SHA256 witness"):
        make_plan(plan, history(2), episodes=2, recovery_observations=[observation])
