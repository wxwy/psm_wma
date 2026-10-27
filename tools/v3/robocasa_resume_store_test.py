"""Durable-store gate using synthetic model containers and real Episode schemas."""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import pickle
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from robocasa_episode_resume.model_identity import build_model_identity  # noqa: E402
from robocasa_episode_resume.plan import build_plan  # noqa: E402
from robocasa_resume_store import ResumeStoreError, RunStore  # noqa: E402

from tools.v3.episode_resume_prototype.episode_evidence_test import build_legacy_run  # noqa: E402

MEDIA = {"save_rollout_mp4": False, "save_generated_video": "none", "save_init_png": False}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write(path, value):
    Path(path).write_bytes(canonical(value) + b"\n")


def read(path):
    return json.loads(Path(path).read_text())


def snapshot(path):
    return {item: (item.read_bytes(), item.stat().st_mtime_ns) for item in path.rglob("*") if item.is_file()}


def make_model(directory):
    model = directory / "model"
    model.mkdir(parents=True, exist_ok=True)
    (model / ".metadata").write_bytes(pickle.dumps({"synthetic": True}, protocol=4))
    with zipfile.ZipFile(model / "__0_0.distcp", "w") as archive:
        archive.writestr("archive/data.pkl", b"synthetic; never tensor-loaded")


def reader(checkpoint, **changes):
    def read_identity():
        return build_model_identity(
            **dict(checkpoint=checkpoint, num_steps=30, action_horizon=16, guidance=1.0) | changes
        )

    return read_identity


@pytest.fixture
def checkpoint(tmp_path):
    directory = tmp_path / "job/checkpoints/iter_000004000"
    make_model(directory)
    return directory


def legacy_run(tmp_path, **kwargs):
    """Upgrade only the synthetic container fixture; preserve actual legacy schema."""
    run = build_legacy_run(tmp_path, **kwargs)
    manifest = read(run / "evaluation_manifest.json")
    checkpoint = Path(manifest["identity"]["checkpoint"])
    make_model(checkpoint)
    metadata = checkpoint / "model/.metadata"
    shard = checkpoint / "model/__0_0.distcp"
    observed = shard.stat()
    manifest["identity"]["model_metadata_sha256"] = hashlib.sha256(metadata.read_bytes()).hexdigest()
    manifest["identity"]["model_shard_stat_witnesses"] = [
        [shard.name, observed.st_size, observed.st_mtime_ns, observed.st_ctime_ns]
    ]
    old_digest = manifest["digest"]
    manifest["digest"] = hashlib.sha256(canonical(manifest["identity"])).hexdigest()
    for path in run.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".jsonl"}:
            path.write_text(path.read_text().replace(old_digest, manifest["digest"]))
    write(run / "evaluation_manifest.json", manifest)
    (run / ".run.lock").touch()
    return run, checkpoint


def plan(records, invocation="test-invocation", requested=5, documents=(), observations=()):
    return build_plan(
        records,
        tasks=["CloseFridge"],
        requested_episodes=requested,
        requested_seed=0,
        requested_media=MEDIA,
        execution={"gpus": [0]},
        current_provenance={},
        invocation_id=invocation,
        recovery_documents=documents,
        recovery_observations=observations,
    )


def batch(manifest, *, logical=(3,), seed=123, mode="resume_gap_independent"):
    manifest = copy.deepcopy(manifest)
    manifest["identity"]["protocol"].update(seed=seed, trials=len(logical))
    return {
        "task": "CloseFridge",
        "dataset_dir": manifest["identity"]["tasks"][0]["dataset_dir"],
        "effective_seed": seed,
        "requested_seed": 0,
        "sampling_mode": mode,
        "episodes": [{"logical_episode_index": slot, "source_episode": index} for index, slot in enumerate(logical)],
        "sampler": {"sampler_version": "test-v1", "requested_seed": 0, "sampling_mode": mode},
    }, manifest


def copy_source_episode(run, job):
    source = run / "CloseFridge/attempt_0001"
    old_digest = read(run / "evaluation_manifest.json")["digest"]
    new_digest = job["source_manifest"]["digest"]
    for path in source.iterdir():
        if path.is_file():
            target = job["attempt_dir"] / path.name
            if path.suffix in {".json", ".jsonl"}:
                target.write_text(path.read_text().replace(old_digest, new_digest))
            else:
                shutil.copyfile(path, target)


def scan(store):
    return store.discover_history(sim_python=Path(sys.executable), requested_media=MEDIA)


def test_fresh_preview_one_hash_and_inside_lease_stat_guard_and_release(checkpoint, tmp_path):
    calls = []

    def observed():
        calls.append(1)
        return reader(checkpoint)()

    store = RunStore(tmp_path / "run", current_identity_reader=observed)
    assert store.preview()["status"] == "FRESH"
    with store.locked():
        assert len(calls) == 1
        assert scan(store)["records"] == []
        invocation = store.begin_invocation(plan([]), {"fake": True})
        assert invocation.is_dir()
    with RunStore(store.root, current_identity_reader=reader(checkpoint), resume=True).locked():
        pass


def test_existing_namespace_requires_resume_without_any_writes(checkpoint, tmp_path):
    root = tmp_path / "existing"
    root.mkdir()
    before = snapshot(root)
    with pytest.raises(ResumeStoreError, match="RESUME_REQUIRED"):
        with RunStore(root, current_identity_reader=reader(checkpoint)).locked():
            pytest.fail("admitted")
    assert snapshot(root) == before


def test_legacy_missing_lock_is_blocked_without_creating_one(tmp_path):
    root, checkpoint = legacy_run(tmp_path)
    (root / ".run.lock").unlink()
    before = snapshot(root)
    with pytest.raises(ResumeStoreError, match="MISSING_RUN_LOCK"):
        with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked():
            pytest.fail("admitted")
    assert snapshot(root) == before


def test_busy_same_legacy_lock_preserves_original_files(tmp_path):
    root, checkpoint = legacy_run(tmp_path)
    before = snapshot(root)
    with (root / ".run.lock").open("r+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ResumeStoreError, match="RUN_LOCKED"):
            with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked():
                pytest.fail("admitted")
    assert snapshot(root) == before


@pytest.mark.parametrize("parameter,value", [("num_steps", 31), ("action_horizon", 8), ("guidance", 2.0)])
def test_model_scalar_mismatch_precedes_migration_and_invocation(tmp_path, parameter, value):
    root, checkpoint = legacy_run(tmp_path)
    before = snapshot(root)
    with pytest.raises(ResumeStoreError, match="MODEL_MISMATCH"):
        with RunStore(root, current_identity_reader=reader(checkpoint, **{parameter: value}), resume=True).locked():
            pytest.fail("admitted")
    assert snapshot(root) == before


def test_strong_payload_change_rejected_even_same_path(tmp_path, checkpoint):
    root = tmp_path / "new-run"
    with RunStore(root, current_identity_reader=reader(checkpoint)).locked() as store:
        store.begin_invocation(plan([]), {})
    with zipfile.ZipFile(checkpoint / "model/__0_0.distcp", "a") as archive:
        archive.writestr("changed", b"new model bytes")
    before = snapshot(root)
    with pytest.raises(ResumeStoreError, match="MODEL_MISMATCH"):
        with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked():
            pytest.fail("admitted")
    assert snapshot(root) == before


def test_checkpoint_path_is_a_hard_model_parameter_even_with_same_payload(tmp_path):
    root, checkpoint = legacy_run(tmp_path)
    other = tmp_path / "different-checkpoint"
    shutil.copytree(checkpoint, other)
    before = snapshot(root)
    with pytest.raises(ResumeStoreError, match="MODEL_MISMATCH"):
        with RunStore(root, current_identity_reader=reader(other), resume=True).locked():
            pytest.fail("admitted")
    assert snapshot(root) == before


def test_explicit_owner_legacy_relocation_resumes_without_rewriting_original_episodes(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=2)
    original = snapshot(root)
    relocated = tmp_path / "relocated" / checkpoint.name
    shutil.copytree(checkpoint, relocated, copy_function=shutil.copy2)
    store = RunStore(
        root,
        current_identity_reader=reader(relocated),
        resume=True,
        allow_relocated_legacy_checkpoint=True,
    )
    assert store.preview()["status"] == "MATCH"
    assert snapshot(root) == original
    with store.locked() as admitted:
        decision = admitted._legacy_decision
        assert decision["status"] == "LEGACY_STAT_BRIDGE_MATCH"
        assert decision["owner_accepted_relocated_legacy_checkpoint"] is True
        history = scan(admitted)
        assert len(history["records"]) == 2
        admitted.begin_invocation(plan(history["records"]), {})
    migrated = read(root / "_resume_v2/legacy_migration.json")
    assert migrated["decision"]["owner_accepted_relocated_legacy_checkpoint"] is True
    assert migrated["decision"]["historical_payload_sha256"] is None
    assert read(root / "_resume_v2/model_identity.json")["parameters"]["checkpoint"]["path"] == str(relocated.resolve())
    for old_path, old_witness in original.items():
        assert (old_path.read_bytes(), old_path.stat().st_mtime_ns) == old_witness
    # New strong anchor must function without repeatedly needing relocation override.
    with RunStore(root, current_identity_reader=reader(relocated), resume=True).locked():
        pass


def test_legacy_relocation_optin_must_not_bypass_strong_new_run_checkpoint_path(tmp_path, checkpoint):
    root = tmp_path / "strong-run"
    with RunStore(root, current_identity_reader=reader(checkpoint)).locked() as store:
        store.begin_invocation(plan([]), {})
    relocated = tmp_path / "moved" / checkpoint.name
    shutil.copytree(checkpoint, relocated, copy_function=shutil.copy2)
    before = snapshot(root)
    with pytest.raises(ResumeStoreError, match="MODEL_MISMATCH"):
        with RunStore(
            root,
            current_identity_reader=reader(relocated),
            resume=True,
            allow_relocated_legacy_checkpoint=True,
        ).locked():
            pytest.fail("strong new-run identity must not use legacy relocation bypass")
    assert snapshot(root) == before


def test_legacy_relocation_optin_without_resume_rejected_before_model_read(tmp_path):
    with pytest.raises(ValueError, match="requires explicit --resume"):
        RunStore(
            tmp_path / "run",
            current_identity_reader=lambda: pytest.fail("no model read allowed"),
            allow_relocated_legacy_checkpoint=True,
        )


def test_second_hash_catches_change_after_preview_before_writes(tmp_path):
    root, checkpoint = legacy_run(tmp_path)
    store = RunStore(root, current_identity_reader=reader(checkpoint), resume=True)
    store.preview()
    with zipfile.ZipFile(checkpoint / "model/__0_0.distcp", "a") as archive:
        archive.writestr("between-lock", b"changed")
    before = snapshot(root)
    with pytest.raises(ResumeStoreError, match="MODEL_MISMATCH"):
        with store.locked():
            pytest.fail("admitted")
    assert snapshot(root) == before


def test_exception_releases_lease(tmp_path, checkpoint):
    root = tmp_path / "run"
    with pytest.raises(RuntimeError, match="injected"):
        with RunStore(root, current_identity_reader=reader(checkpoint)).locked() as store:
            store.begin_invocation(plan([]), {})
            raise RuntimeError("injected")
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked():
        pass


@pytest.mark.parametrize("kind", ["root", "lock", "fifo_lock"])
def test_symlink_and_nonregular_lease_rejected(tmp_path, checkpoint, kind):
    real = tmp_path / "real"
    real.mkdir()
    root = tmp_path / "run"
    if kind == "root":
        root.symlink_to(real, target_is_directory=True)
    else:
        root.mkdir()
        if kind == "lock":
            (real / "lock").touch()
            (root / ".run.lock").symlink_to(real / "lock")
        else:
            os.mkfifo(root / ".run.lock")
    with pytest.raises(ResumeStoreError, match="UNSAFE_PATH|MISSING_RUN_LOCK"):
        with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked():
            pytest.fail("admitted")


@pytest.mark.parametrize(
    "status,completed,expected", [("FAILED", 2, 2), ("RUNNING", 2, 2), ("COMPLETE", 2, 0), ("COMPLETE", 5, 5)]
)
def test_original_sources_are_rescanned_under_their_own_protocol(tmp_path, status, completed, expected):
    root, checkpoint = legacy_run(tmp_path, status=status, completed=completed)
    before = snapshot(root)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        history = scan(store)
        assert len(history["records"]) == expected
        if status == "COMPLETE" and completed == 2:
            assert any(row["code"] == "CORRUPT_LEGACY_COMPLETE_MARKER" for row in history["diagnostics"])
        store.begin_invocation(plan(history["records"]), {})
        store.publish_catalog(history["records"])
    for path, value in before.items():
        assert (path.read_bytes(), path.stat().st_mtime_ns) == value


def test_partial_source_catalog_never_supplies_completion_without_source_revalidation(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=1)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        original = scan(store)
        store.begin_invocation(plan(original["records"]), {})
        catalog = store.publish_catalog(original["records"])[0]
    forged = read(catalog)
    forged["record"]["verified"] = True
    write(catalog, forged)
    (root / "CloseFridge/attempt_0001/rollout00_predictions.jsonl").write_text('{"forged":true}\n')
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        history = scan(store)
        assert history["records"] == []
        assert any(row["code"] == "CATALOG_SOURCE_NOT_REVALIDATED" for row in history["diagnostics"])


def test_foreign_model_catalog_cannot_allocate_pending_slots(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=1)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        original = scan(store)
        store.begin_invocation(plan(original["records"]), {})
        catalog = store.publish_catalog(original["records"])[0]
    foreign = read(catalog)
    foreign["model_identity_digest"] = "f" * 64
    foreign["completed_slots"][0]["logical_episode_index"] = 99
    write(catalog, foreign)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        with pytest.raises(ResumeStoreError, match="CATALOG_MODEL_MISMATCH"):
            scan(store)


def test_catalog_checks_changed_core_even_if_new_evidence_remains_structurally_valid(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=1)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        original = scan(store)
        store.begin_invocation(plan(original["records"]), {})
        store.publish_catalog(original["records"])
    path = root / "CloseFridge/attempt_0001/rollout00_actions.jsonl"
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    lines[0]["predicted_raw15"][0] = 0.25
    path.write_text("".join(json.dumps(line) + "\n" for line in lines))
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        with pytest.raises(ResumeStoreError, match="SOURCE_EVIDENCE_CHANGED"):
            scan(store)


def test_durable_reservation_maps_physical_zero_to_logical_three_after_restart(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=1)
    manifest = read(root / "evaluation_manifest.json")
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        history = scan(store)
        invocation = store.begin_invocation(plan(history["records"]), {})
        spec, source = batch(manifest)
        job = store.reserve_batch(invocation, spec, source)
        assert read(job["attempt_dir"] / "attempt.json")["status"] == "RUNNING"
        assert read(job["reservation_path"])["reservations"][0]["logical_episode_index"] == 3
        assert job["source_manifest"]["identity"]["model_identity"]["digest"] == store.current_identity["digest"]
        copy_source_episode(root, job)
        rows = store.read_reserved_batch(job, sim_python=Path(sys.executable))["records"]
        assert len(rows) == 1 and rows[0]["source_episode"] == 0 and rows[0]["logical_episode_index"] == 3
        assert rows[0]["effective_seed"] == 123 and rows[0]["requested_seed"] == 0
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        history = scan(store)
        assert sorted(row["logical_episode_index"] for row in history["records"]) == [0, 3]
        recovered = plan(history["records"], invocation="restart", documents=history["recovery_documents"])
        assert recovered["tasks"]["CloseFridge"]["reused"] == 2


def test_unfinished_reserved_tail_is_recovered_from_disk_not_memory(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=1)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        invocation = store.begin_invocation(plan(scan(store)["records"]), {})
        spec, manifest = batch(read(root / "evaluation_manifest.json"), logical=(4,))
        job = store.reserve_batch(invocation, spec, manifest)
        shutil.rmtree(job["source_root"])
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        history = scan(store)
        result = plan(history["records"], "restart", documents=history["recovery_documents"])
        recovery = result["tasks"]["CloseFridge"]["pending_recovery"]
        assert 4 in recovery["pending_slots"]
        assert any(row["code"] == "RESERVED_SOURCE_NOT_CREATED" for row in history["diagnostics"])


def test_actual_legacy_progress_retains_original_unclosed_tail_after_shrink(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=2, trials=5)
    before = snapshot(root)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        history = scan(store)
        observations = history["recovery_observations"]
        assert [row["logical_episode_index"] for row in observations] == list(range(5))
        progress = root / "CloseFridge/attempt_0001/episode_progress.jsonl"
        assert observations[4]["progress_source_refs"] == [
            {"path": str(progress), "sha256": hashlib.sha256(progress.read_bytes()).hexdigest()}
        ]
        smaller = plan(history["records"], requested=1, observations=observations)
        assert smaller["tasks"]["CloseFridge"]["pending_recovery"]["pending_slots"] == [2, 3, 4]
        expanded = plan(history["records"], "expanded", requested=5, observations=observations)
        assert [row["logical_episode_index"] for row in expanded["tasks"]["CloseFridge"]["new_episodes"]] == [2, 3, 4]
    assert snapshot(root) == before


def test_foreign_legacy_progress_does_not_create_allocation_authority(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=2, trials=5)
    path = root / "CloseFridge/attempt_0001/episode_progress.jsonl"
    digest = read(root / "evaluation_manifest.json")["digest"]
    path.write_text(path.read_text().replace(digest, "f" * 64))
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        history = scan(store)
        assert history["records"] == [] and history["recovery_observations"] == []
        assert any(row["code"] == "LEGACY_ALLOCATION_STREAM_EXCLUDED" for row in history["diagnostics"])


def test_new_source_uses_strong_payload_binding_after_timestamp_only_change(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=1)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        invocation = store.begin_invocation(plan(scan(store)["records"]), {})
        spec, manifest = batch(read(root / "evaluation_manifest.json"))
        job = store.reserve_batch(invocation, spec, manifest)
        copy_source_episode(root, job)
    shard = checkpoint / "model/__0_0.distcp"
    observed = shard.stat()
    os.utime(shard, ns=(observed.st_atime_ns, observed.st_mtime_ns + 1_000_000))
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        assert len(scan(store)["records"]) == 2


def test_original_real_media_stays_valid_under_changed_current_media_request(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=1, mode="first", rollout=True, png=True)
    requested = dict(MEDIA, save_rollout_mp4=True, save_generated_video="all", save_init_png=True)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        history = store.discover_history(sim_python=Path(sys.executable), requested_media=requested)
        assert len(history["records"]) == 1
        coverage = history["records"][0]["media_coverage"]
        assert coverage["prediction_count"] == 2
        assert coverage["available_rollout"] and coverage["available_init_png"]
        assert coverage["available_generated"] == 1 and coverage["missing_requested_media"] == [
            "generated_prediction_1"
        ]


@pytest.mark.parametrize("fault", ["manifest", "reservation", "symlink"])
def test_changed_or_escaping_source_is_rejected_before_new_invocation(tmp_path, fault):
    root, checkpoint = legacy_run(tmp_path, completed=1)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        invocation = store.begin_invocation(plan(scan(store)["records"]), {})
        spec, manifest = batch(read(root / "evaluation_manifest.json"))
        job = store.reserve_batch(invocation, spec, manifest)
    if fault == "manifest":
        value = read(job["source_manifest_path"])
        value["identity"]["protocol"]["seed"] = 124
        value["digest"] = hashlib.sha256(canonical(value["identity"])).hexdigest()
        write(job["source_manifest_path"], value)
    elif fault == "reservation":
        value = read(job["reservation_path"])
        value["source_root"] = str(tmp_path / "foreign")
        write(job["reservation_path"], value)
    else:
        job["source_manifest_path"].unlink()
        job["source_manifest_path"].symlink_to(root / "evaluation_manifest.json")
    before = snapshot(root) if fault != "symlink" else None
    with pytest.raises(ResumeStoreError, match="SOURCE_MANIFEST_CHANGED|SOURCE_PATH_MISMATCH|UNSAFE_PATH"):
        with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked():
            pytest.fail("admitted")
    if before is not None:
        assert snapshot(root) == before


def test_reports_are_live_snapshots_and_old_invocations_and_root_summary_stay_immutable(tmp_path):
    root, checkpoint = legacy_run(tmp_path, completed=1)
    old_summary = root / "screening_summary.json"
    old_summary.write_text('{"old":true}\n')
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        invocation = store.begin_invocation(plan(scan(store)["records"]), {})
        first = store.write_report(invocation, {"state": "RUNNING", "completed_episodes": 0})
        second = store.write_report(invocation, {"state": "RUNNING", "completed_episodes": 1})
        assert first != second and read(first)["completed_episodes"] == 0
        pointer = read(root / "latest_invocation.json")
        assert read(pointer["summary_path"])["completed_episodes"] == 1
        assert pointer["report_path"] == str(second)
    before = snapshot(invocation)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        fresh = store.begin_invocation(plan(scan(store)["records"], "second"), {})
        store.write_report(fresh, {"state": "COMPLETE"})
        with pytest.raises(ResumeStoreError, match="INVALID_INVOCATION"):
            store.write_report(invocation, {"state": "forged"})
    assert snapshot(invocation) == before and old_summary.read_text() == '{"old":true}\n'


def test_reserved_batch_passes_shared_deadline_and_cancellation_to_real_scanner_boundary(tmp_path, monkeypatch):
    root, checkpoint = legacy_run(tmp_path, completed=1)
    with RunStore(root, current_identity_reader=reader(checkpoint), resume=True).locked() as store:
        invocation = store.begin_invocation(plan(scan(store)["records"]), {})
        spec, manifest = batch(read(root / "evaluation_manifest.json"))
        job = store.reserve_batch(invocation, spec, manifest)
        observed = {}
        stop = lambda: False  # noqa: E731

        def scanner(path, **kwargs):
            observed.update(path=path, **kwargs)
            return {"original_manifest": job["source_manifest"], "records": [], "diagnostics": []}

        monkeypatch.setattr("robocasa_resume_store.scan_legacy_run", scanner)
        assert (
            store.read_reserved_batch(
                job, sim_python=Path(sys.executable), requested_media=MEDIA, deadline=123.5, stop=stop
            )["records"]
            == []
        )
        assert observed["path"] == job["source_root"]
        assert observed["deadline"] == 123.5 and observed["stop"] is stop
