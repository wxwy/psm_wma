"""Design gate using real legacy schemas, native tiny MP4 decode and fake Episodes."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from episode_evidence import EpisodeEvidenceError, scan_legacy_run, verify_legacy_episode  # noqa: E402


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def write_lines(path, values):
    path.write_text("".join(json.dumps(value) + "\n" for value in values))


def build_legacy_run(
    tmp_path, *, completed=2, trials=5, status="FAILED", mode="none", rollout=False, png=False, seed=0
):
    """Public fake-data helper for the parent's scanner -> planner integration test."""
    run = tmp_path / "legacy"
    run.mkdir()
    checkpoint = tmp_path / "job/checkpoints/iter_000004000"
    (checkpoint / "model").mkdir(parents=True)
    metadata = checkpoint / "model/.metadata"
    shard = checkpoint / "model/__0_0.distcp"
    metadata.write_bytes(b"synthetic metadata; not a real DCP")
    shard.write_bytes(b"synthetic model shard; never deserialized")
    config = checkpoint.parent.parent / "config.yaml"
    config.write_text("synthetic_cpu_only: true\n")
    dataset = tmp_path / "dataset/CloseFridge/lerobot"
    (dataset / "extras").mkdir(parents=True)
    (dataset / "extras/dataset_meta.json").write_text('{"env_args":{"env_name":"CloseFridge"}}\n')
    runtime = {
        "schema": "psm_robocasa_runtime_v1",
        "fixture_scope": "synthetic metadata only; no simulator/physics/import acceptance",
        "protocol": {"official_horizons": {"CloseFridge": 17}},
    }
    runtime["digest"] = hashlib.sha256(canonical(runtime)).hexdigest()
    stat = shard.stat()
    identity = {
        "schema": "psm_v3_eval_identity_vendor_v1",
        "root_sha": "1" * 40,
        "child_sha": "2" * 40,
        "checkpoint": str(checkpoint),
        "model_metadata_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
        "model_shard_stat_witnesses": [[shard.name, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]],
        "checkpoint_identity_scope": "metadata_hash_and_shard_stats_not_full_payload_hash",
        "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "tasks": [
            {
                "task": "CloseFridge",
                "dataset_dir": str(dataset),
                "env_metadata_sha256": hashlib.sha256((dataset / "extras/dataset_meta.json").read_bytes()).hexdigest(),
            }
        ],
        "evaluation_runtime": runtime,
        "protocol": {
            "seed": seed,
            "R": 16,
            "H_pred": 16,
            "server_action_chunk_size": 16,
            "raw_action_dim": 15,
            "max_action_dim": 64,
            "policy_seed": 0,
            "num_steps": 30,
            "guidance": 1.0,
            "trials": trials,
            "fps": 20,
            "camera_set": "left_wrist",
            "use_state": True,
            "base_encoding": "raw",
            "local_memory_mode": "required",
            "save_rollout_mp4": rollout,
            "save_generated_video": mode,
            "save_init_png": png,
            "save_action_jsonl": True,
            "save_prediction_jsonl": True,
        },
    }
    write_json(
        run / "evaluation_manifest.json",
        {"identity": identity, "digest": hashlib.sha256(canonical(identity)).hexdigest()},
    )
    if rollout or png or mode != "none":
        frames = [np.full((16, 16, 3), value, dtype=np.uint8) for value in (30, 190)]
        imageio.mimwrite(tmp_path / "tiny.mp4", frames, fps=20, macro_block_size=None)
        Image.fromarray(frames[0]).save(tmp_path / "tiny.png")
    append_attempt(run, attempt=1, completed=completed, status=status)
    return run


def append_attempt(run_dir, *, attempt=2, completed=2, status="FAILED", outcomes=None):
    manifest = json.loads((run_dir / "evaluation_manifest.json").read_text())
    identity, digest = manifest["identity"], manifest["digest"]
    policy = identity["protocol"]
    directory = run_dir / "CloseFridge" / f"attempt_{attempt:04d}"
    directory.mkdir(parents=True)
    attempt_id = f"CloseFridge/{directory.name}"
    write_json(
        directory / "attempt.json",
        dict(
            schema="psm_robocasa_task_attempt_v1",
            attempt_id=directory.name,
            evaluation_run_digest=digest,
            status=status,
        ),
    )
    write_json(directory / "runtime_attestation.json", identity["evaluation_runtime"])
    rows, progress = [], []
    for episode in range(completed):
        prefix = f"rollout{episode:02d}"
        outcome = outcomes[episode] if outcomes is not None else "success" if episode % 2 == 0 else "behavioral_failure"
        common = dict(evaluation_run_digest=digest, evaluation_attempt_id=attempt_id, episode=episode)
        actions = [
            dict(
                common,
                source_step=step,
                predicted_raw15=[0.0] * 15,
                canonical_executed_raw15=[0.0] * 15,
                submitted_env12=[0.0] * 12,
                evidence_completed=True,
            )
            for step in range(17)
        ]
        predictions = [
            dict(
                common,
                step_before_query=step,
                latency_ms=1.25,
                action_chunk=[[0.0] * 15] * 16,
                local_memory={
                    "session_id": f"{'a' * 32}:0:{episode + 1:032x}",
                    "episode_id": f"{episode + 1:032x}",
                    "consumer_step": step,
                    "prefix_present": step > 0,
                },
            )
            for step in (0, 16)
        ]
        names = (
            []
            if policy["save_generated_video"] == "none"
            else [f"{prefix}_generated.mp4"]
            if policy["save_generated_video"] == "first"
            else [f"{prefix}_generated_replan{index:04d}.mp4" for index in range(2)]
        )
        row = {
            "ep": episode,
            "policy": outcome == "success",
            "outcome": outcome,
            "error": "RuntimeError: injected partial episode" if outcome == "runtime_error" else None,
            "evaluation_run_digest": digest,
            "evaluation_attempt_id": attempt_id,
            "steps": 17,
            "completed_action_records": 17,
            "replans": 2,
            "actions_file": f"{prefix}_actions.jsonl",
            "predictions_file": f"{prefix}_predictions.jsonl",
            "generated_videos": names,
        }
        write_json(directory / f"{prefix}_episode.json", row)
        write_lines(directory / row["actions_file"], actions)
        write_lines(directory / row["predictions_file"], predictions)
        write_json(
            directory / f"{prefix}_cleanup.json",
            dict(
                session_id=f"{'a' * 32}:0:{episode + 1:032x}",
                reset_ok=True,
                cleanup_error=None,
                rollout_error=None,
                media_error=None,
            ),
        )
        if policy["save_rollout_mp4"]:
            shutil.copyfile(run_dir.parent / "tiny.mp4", directory / f"{prefix}.mp4")
        if policy["save_init_png"]:
            shutil.copyfile(run_dir.parent / "tiny.png", directory / f"{prefix}_init.png")
        if names:
            videos = []
            for index, name in enumerate(names):
                shutil.copyfile(run_dir.parent / "tiny.mp4", directory / name)
                videos.append(dict(replan=index, source_step=(0, 16)[index], file=name, frames=2))
            write_json(
                directory / f"{prefix}_generated_manifest.json",
                dict(
                    schema="psm_generated_video_v1",
                    status="COMPLETE",
                    evaluation_run_digest=digest,
                    evaluation_attempt_id=attempt_id,
                    mode=policy["save_generated_video"],
                    videos=videos,
                ),
            )
        progress.extend(dict(common, schema="psm_episode_progress_v1", event=event) for event in ("start", "end"))
        rows.append(row)
    if completed < policy["trials"]:
        progress.append(
            dict(
                schema="psm_episode_progress_v1",
                evaluation_run_digest=digest,
                evaluation_attempt_id=attempt_id,
                episode=completed,
                event="start",
            )
        )
    write_lines(directory / "episode_progress.jsonl", progress)
    write_json(directory / "results.json", rows)
    return directory


def scan(run, **kwargs):
    return scan_legacy_run(run, sim_python=Path(sys.executable), **kwargs)


def snapshot(run):
    return {
        str(path.relative_to(run)): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in run.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize("status", ["RUNNING", "FAILED", "COMPLETE"])
def test_complete_episodes_reusable_without_task_complete_or_total_trial_count(tmp_path, status):
    run = build_legacy_run(tmp_path, completed=2, trials=5, status=status)
    before = snapshot(run)
    result = scan(run)
    assert [row["source_episode"] for row in result["records"]] == [0, 1]
    assert [row["outcome"] for row in result["records"]] == ["success", "behavioral_failure"]
    assert all(row["original_task_status"] == status for row in result["records"])
    assert result["records"][0]["source_ref"]["original_digest"] == result["original_manifest"]["digest"]
    assert before == snapshot(run)


def test_actual_partial_third_episode_excluded_with_first_two_unchanged(tmp_path):
    run = build_legacy_run(tmp_path)
    attempt = run / "CloseFridge/attempt_0001"
    (attempt / "rollout02_actions.jsonl").write_text('{"incomplete":')
    before = snapshot(run)
    result = scan(run)
    assert len(result["records"]) == 2
    assert any(row["code"] == "INCOMPLETE_EPISODE" and row.get("episode") == 2 for row in result["diagnostics"])
    assert before == snapshot(run)


def test_truncated_progress_tail_does_not_destroy_completed_prefix(tmp_path):
    run = build_legacy_run(tmp_path)
    path = run / "CloseFridge/attempt_0001/episode_progress.jsonl"
    with path.open("ab") as handle:
        handle.write(b'{"event":')
    result = scan(run)
    assert len(result["records"]) == 2
    assert any(row["code"] == "PARTIAL_PROGRESS_TAIL" for row in result["diagnostics"])


def test_numeric_oldest_valid_attempt_wins_never_highest_success(tmp_path):
    run = build_legacy_run(tmp_path, completed=0)
    append_attempt(run, attempt=10, completed=2, outcomes=["success", "success"])
    append_attempt(run, attempt=3, completed=2, outcomes=["behavioral_failure", "behavioral_failure"])
    result = scan(run)
    assert len(result["records"]) == 2 and not any(row["policy"] for row in result["records"])
    assert all(row["source_ref"]["attempt"] == "attempt_0003" for row in result["records"])
    conflicts = [row for row in result["diagnostics"] if row["code"] == "DUPLICATE_CONFLICT_EXCLUDED"]
    assert len(conflicts) == 2
    assert all("attempt_0010" in row["excluded"]["path"] for row in conflicts)


def test_identical_duplicate_not_double_counted_and_provenance_is_explicit(tmp_path):
    run = build_legacy_run(tmp_path)
    append_attempt(run, attempt=3, completed=2)
    result = scan(run)
    assert len(result["records"]) == 2
    assert sum(row["code"] == "DUPLICATE_EXCLUDED" for row in result["diagnostics"]) == 2


@pytest.mark.parametrize(
    "original,requested,expected_missing", [("none", "all", 2), ("first", "all", 1), ("all", "none", 0)]
)
def test_media_upgrade_does_not_rerun_or_fabricate_historical_media(tmp_path, original, requested, expected_missing):
    run = build_legacy_run(tmp_path, completed=1, mode=original)
    before = snapshot(run)
    result = scan(
        run, requested_media=dict(save_generated_video=requested, save_rollout_mp4=False, save_init_png=False)
    )
    coverage = result["records"][0]["media_coverage"]
    assert len(coverage["missing_requested_media"]) == expected_missing
    assert coverage["available_generated"] == {"none": 0, "first": 1, "all": 2}[original]
    assert before == snapshot(run)


def test_original_environment_video_and_png_are_really_decoded(tmp_path):
    run = build_legacy_run(tmp_path, completed=1, mode="all", rollout=True, png=True)
    result = scan(run)
    coverage = result["records"][0]["media_coverage"]
    assert coverage["available_rollout"] and coverage["available_init_png"]
    assert coverage["available_generated"] == 2 and coverage["missing_requested_media"] == []
    assert len(coverage["videos_view"]["rollout"]) == 1


def test_none_video_policy_still_preserves_verified_prediction_count(tmp_path):
    run = build_legacy_run(tmp_path, completed=1, mode="none")
    result = scan(run)
    record = result["records"][0]
    row = json.loads(Path(record["source_ref"]["path"]).read_text())
    predictions = Path(record["source_ref"]["path"]).parent / row["predictions_file"]
    assert record["media_coverage"]["prediction_count"] == row["replans"] == len(predictions.read_text().splitlines())
    assert record["media_coverage"]["available_generated"] == 0


@pytest.mark.parametrize(
    "failure",
    [
        "missing_actions",
        "truncated_actions",
        "foreign_action_attempt",
        "bad_action_abi",
        "bad_prediction_frontier",
        "missing_cleanup",
        "cleanup_failed",
        "foreign_digest",
        "duplicate_aggregate",
        "aggregate_conflict",
        "runtime_error",
        "early_behavioral_failure",
        "bad_runtime",
        "symlink_action",
        "audit_traversal",
        "missing_local_status",
        "wrong_local_session",
        "wrong_local_frontier",
        "mixed_local_episode",
    ],
)
def test_invalid_individual_episode_excluded_with_explicit_diagnostics(tmp_path, failure):
    run = build_legacy_run(tmp_path, completed=1)
    directory = run / "CloseFridge/attempt_0001"
    row_path = directory / "rollout00_episode.json"
    row = json.loads(row_path.read_text())
    actions = directory / row["actions_file"]
    predictions = directory / row["predictions_file"]
    if failure == "missing_actions":
        actions.unlink()
    elif failure == "truncated_actions":
        actions.write_text(actions.read_text().rstrip("\n"))
    elif failure in {"foreign_action_attempt", "bad_action_abi"}:
        values = [json.loads(line) for line in actions.read_text().splitlines()]
        if failure == "foreign_action_attempt":
            values[0]["evaluation_attempt_id"] = "CloseFridge/attempt_9999"
        else:
            values[0]["submitted_env12"] = [0] * 15
        write_lines(actions, values)
    elif failure == "bad_prediction_frontier":
        values = [json.loads(line) for line in predictions.read_text().splitlines()]
        values[1]["step_before_query"] = 0
        write_lines(predictions, values)
    elif failure in {"missing_local_status", "wrong_local_session", "wrong_local_frontier", "mixed_local_episode"}:
        values = [json.loads(line) for line in predictions.read_text().splitlines()]
        if failure == "missing_local_status":
            values[0].pop("local_memory")
        elif failure == "wrong_local_session":
            values[0]["local_memory"]["session_id"] = f"{'b' * 32}:0:{'c' * 32}"
        elif failure == "wrong_local_frontier":
            values[1]["local_memory"]["consumer_step"] = 0
        else:
            values[1]["local_memory"]["episode_id"] = "b" * 32
        write_lines(predictions, values)
    elif failure == "missing_cleanup":
        (directory / "rollout00_cleanup.json").unlink()
    elif failure == "cleanup_failed":
        path = directory / "rollout00_cleanup.json"
        value = json.loads(path.read_text())
        value["reset_ok"] = False
        write_json(path, value)
    elif failure == "foreign_digest":
        row["evaluation_run_digest"] = "b" * 64
    elif failure == "duplicate_aggregate":
        write_json(directory / "results.json", [row, row])
    elif failure == "aggregate_conflict":
        write_json(directory / "results.json", [dict(row, policy=False, outcome="behavioral_failure")])
    elif failure == "runtime_error":
        row.update(policy=False, outcome="runtime_error", error="TimeoutError: partial episode")
    elif failure == "early_behavioral_failure":
        row.update(policy=False, outcome="behavioral_failure", steps=1)
    elif failure == "bad_runtime":
        path = directory / "runtime_attestation.json"
        value = json.loads(path.read_text())
        value["protocol"]["official_horizons"]["CloseFridge"] = 18
        write_json(path, value)
    elif failure == "symlink_action":
        actions.rename(tmp_path / "outside.jsonl")
        actions.symlink_to(tmp_path / "outside.jsonl")
    elif failure == "audit_traversal":
        row["actions_file"] = "../../not-readable.jsonl"
    if failure in {"foreign_digest", "runtime_error", "early_behavioral_failure", "audit_traversal"}:
        write_json(row_path, row)
        write_json(directory / "results.json", [row])
    result = scan(run)
    assert result["records"] == []
    assert result["diagnostics"]


@pytest.mark.parametrize("failure", ["duplicate", "foreign_attempt", "wrong_order", "duplicate_json_key"])
def test_corrupt_progress_is_not_a_valid_completed_episode(tmp_path, failure):
    run = build_legacy_run(tmp_path, completed=1)
    path = run / "CloseFridge/attempt_0001/episode_progress.jsonl"
    values = [json.loads(line) for line in path.read_text().splitlines()]
    if failure == "duplicate":
        values.insert(2, values[1])
    elif failure == "foreign_attempt":
        values[0]["evaluation_attempt_id"] = "CloseFridge/attempt_9999"
    elif failure == "wrong_order":
        values[0], values[1] = values[1], values[0]
    if failure == "duplicate_json_key":
        path.write_text('{"event":"start","event":"end"}\n')
    else:
        write_lines(path, values)
    result = scan(run)
    assert result["records"] == []
    assert any(row["code"] == "CORRUPT_PROGRESS" for row in result["diagnostics"])


@pytest.mark.parametrize("media", ["rollout", "generated", "png"])
def test_corrupt_media_required_by_original_policy_is_not_an_upgrade_gap(tmp_path, media):
    run = build_legacy_run(tmp_path, completed=1, mode="first", rollout=True, png=True)
    directory = run / "CloseFridge/attempt_0001"
    name = {"rollout": "rollout00.mp4", "generated": "rollout00_generated.mp4", "png": "rollout00_init.png"}[media]
    (directory / name).write_bytes(b"nonempty garbage must never pass")
    result = scan(run, requested_media=dict(save_rollout_mp4=False, save_generated_video="none", save_init_png=False))
    assert result["records"] == []
    assert any(row.get("episode") == 0 for row in result["diagnostics"])


def test_changed_requested_seed_never_rewrites_original_episode_provenance(tmp_path):
    run = build_legacy_run(tmp_path, seed=0)
    result = scan(run)
    assert {row["effective_seed"] for row in result["records"]} == {0}
    assert all(row["sampling_protocol"] == "legacy_task_stream" for row in result["records"])
    assert all(row["seed_source"] == "original_manifest.protocol.seed" for row in result["records"])


def test_manifest_tamper_stops_before_ingesting_any_episode(tmp_path):
    run = build_legacy_run(tmp_path)
    path = run / "evaluation_manifest.json"
    value = json.loads(path.read_text())
    value["identity"]["protocol"]["seed"] = 1
    write_json(path, value)
    with pytest.raises(EpisodeEvidenceError, match="canonical digest"):
        scan(run)


def test_current_task_expansion_or_reduction_does_not_reject_original_manifest(tmp_path):
    run = build_legacy_run(tmp_path)
    expanded = scan(run, tasks=["CloseFridge", "NavigateKitchen"])
    assert len(expanded["records"]) == 2
    assert any(
        value["code"] == "NO_LEGACY_TASK_SOURCE" and value["task"] == "NavigateKitchen"
        for value in expanded["diagnostics"]
    )
    reduced = scan(run, tasks=["NavigateKitchen"])
    assert reduced["records"] == []
    assert len(scan(run)["records"]) == 2  # No source was erased by the selected view.


def test_numeric_attempt_alias_is_ambiguous_and_never_chosen_lexicographically(tmp_path):
    run = build_legacy_run(tmp_path)
    source = run / "CloseFridge/attempt_0001"
    alias = run / "CloseFridge/attempt_00001"
    shutil.copytree(source, alias)
    marker = json.loads((alias / "attempt.json").read_text())
    marker["attempt_id"] = alias.name
    write_json(alias / "attempt.json", marker)
    result = scan(run)
    assert result["records"] == []
    assert sum(value["code"] == "AMBIGUOUS_ATTEMPT_INDEX" for value in result["diagnostics"]) == 2


def test_bad_oldest_candidate_does_not_hide_a_later_complete_candidate(tmp_path):
    run = build_legacy_run(tmp_path)
    (run / "CloseFridge/attempt_0001/rollout00_cleanup.json").unlink()
    append_attempt(run, attempt=2, completed=2)
    result = scan(run)
    first = next(value for value in result["records"] if value["source_episode"] == 0)
    second = next(value for value in result["records"] if value["source_episode"] == 1)
    assert first["source_ref"]["attempt"] == "attempt_0002"
    assert second["source_ref"]["attempt"] == "attempt_0001"
    assert len(result["records"]) == 2


def test_unavailable_original_media_policy_is_diagnosed_not_invented(tmp_path):
    run = build_legacy_run(tmp_path)
    path = run / "evaluation_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["identity"]["protocol"].pop("save_generated_video")
    manifest["digest"] = hashlib.sha256(canonical(manifest["identity"])).hexdigest()
    write_json(path, manifest)
    with pytest.raises(EpisodeEvidenceError, match="media policy"):
        scan(run)


def test_core_uses_actual_production_helpers_without_importing_whole_task_gate(tmp_path, monkeypatch):
    import episode_evidence

    assert episode_evidence._jsonl.__module__ == "robocasa_eval_results"
    assert episode_evidence._validate_local_cleanup.__module__ == "robocasa_eval_results"
    run = build_legacy_run(tmp_path)
    attempt = run / "CloseFridge/attempt_0001"
    manifest = json.loads((run / "evaluation_manifest.json").read_text())
    row = verify_legacy_episode(attempt, 1, manifest=manifest, sim_python=Path(sys.executable))
    assert row["outcome"] == "behavioral_failure" and row["source_episode"] == 1
