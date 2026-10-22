"""CPU evidence gates: task-only resume, immutable attempts and real media decode."""

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from robocasa_eval_results import (  # noqa: E402
    fail_attempt,
    find_completed_attempt,
    finish_attempt,
    start_attempt,
    validate_attempt,
    validate_media,
)

DIGEST = "a" * 64


def write_json(path, value):
    path.write_text(json.dumps(value) + "\n")


def write_jsonl(path, values):
    path.write_text("".join(json.dumps(value) + "\n" for value in values))


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    directory = tmp_path_factory.mktemp("actual-media")
    frames = [np.full((16, 16, 3), value, dtype=np.uint8) for value in (30, 190)]
    imageio.mimwrite(directory / "tiny.mp4", frames, fps=20, macro_block_size=None)
    Image.fromarray(frames[0]).save(directory / "tiny.png")
    return directory


def options(mode="none", rollout=False, png=False):
    return dict(
        digest=DIGEST,
        expected_trials=2,
        video_mode=mode,
        rollout_enabled=rollout,
        init_png_enabled=png,
        sim_python=Path(sys.executable),
    )


def populate(directory, media, *, mode="none", rollout=False, png=False):
    write_json(
        directory / "process_cleanup.json",
        {role: dict(pid=1234, pgid=1234, live_group=False, remaining_pids=[]) for role in ("server", "simulator")},
    )
    results = []
    for episode in range(2):
        prefix = f"rollout{episode:02d}"
        common = dict(
            evaluation_run_digest=DIGEST,
            episode=episode,
            evaluation_attempt_id=f"{directory.parent.name}/{directory.name}",
        )
        actions = [
            dict(
                common,
                source_step=step,
                predicted_raw15=[0.0] * 15,
                canonical_executed_raw15=[0.0] * 15,
                submitted_env12=[0.0] * 12,
                evidence_completed=True,
            )
            for step in range(2)
        ]
        predictions = [dict(common, step_before_query=step) for step in range(2)]
        videos = (
            []
            if mode == "none"
            else [f"{prefix}_generated.mp4"]
            if mode == "first"
            else [f"{prefix}_generated_replan{step:04d}.mp4" for step in range(2)]
        )
        row = dict(
            ep=episode,
            policy=episode == 0,
            steps=2,
            replans=2,
            completed_action_records=2,
            error=None,
            outcome="success" if episode == 0 else "behavioral_failure",
            evaluation_run_digest=DIGEST,
            evaluation_attempt_id=f"{directory.parent.name}/{directory.name}",
            actions_file=f"{prefix}_actions.jsonl",
            predictions_file=f"{prefix}_predictions.jsonl",
            generated_videos=videos,
        )
        write_jsonl(directory / row["actions_file"], actions)
        write_jsonl(directory / row["predictions_file"], predictions)
        if rollout:
            shutil.copyfile(media / "tiny.mp4", directory / f"{prefix}.mp4")
        if png:
            shutil.copyfile(media / "tiny.png", directory / f"{prefix}_init.png")
        if mode != "none":
            records = []
            for index, name in enumerate(videos):
                shutil.copyfile(media / "tiny.mp4", directory / name)
                records.append(dict(replan=index, source_step=index, file=name, frames=2))
            write_json(
                directory / f"{prefix}_generated_manifest.json",
                dict(
                    evaluation_run_digest=DIGEST,
                    evaluation_attempt_id=f"{directory.parent.name}/{directory.name}",
                    mode=mode,
                    schema="psm_generated_video_v1",
                    status="COMPLETE",
                    videos=records,
                ),
            )
        results.append(row)
        write_json(directory / f"{prefix}_episode.json", row)
    write_json(directory / "results.json", results)
    return results


@pytest.mark.parametrize("mode", ["none", "first", "all"])
def test_complete_task_only_resume_requires_actual_decodable_artifacts(tmp_path, media, mode):
    task = tmp_path / "CloseFridge"
    attempt = start_attempt(task, digest=DIGEST, resume=False)
    opts = options(mode, rollout=True, png=True)
    expected = populate(attempt, media, mode=mode, rollout=True, png=True)
    assert find_completed_attempt(task, **opts) is None  # Full rows alone are not a committed task.
    assert finish_attempt(attempt, **opts) == expected
    assert find_completed_attempt(task, **opts) == attempt
    assert json.loads((attempt / "attempt.json").read_text())["status"] == "COMPLETE"


def test_interrupted_task_preserved_new_attempt_always_starts_from_zero(tmp_path, media):
    task = tmp_path / "CloseFridge"
    first = start_attempt(task, digest=DIGEST, resume=False)
    populate(first, media)
    partial = json.loads((first / "results.json").read_text())[:1]
    write_json(first / "results.json", partial)
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in first.iterdir()}
    assert find_completed_attempt(task, **options()) is None
    second = start_attempt(task, digest=DIGEST, resume=True)
    assert second.name == "attempt_0002"
    assert sorted(path.name for path in second.iterdir()) == ["attempt.json"]
    assert before == {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in first.iterdir()}
    rows = populate(second, media)
    assert rows[0]["ep"] == 0
    finish_attempt(second, **options())
    assert find_completed_attempt(task, **options()) == second


def test_failed_attempt_records_original_error_and_is_not_reused(tmp_path):
    task = tmp_path / "CloseFridge"
    first = start_attempt(task, digest=DIGEST, resume=False)
    fail_attempt(first, "TimeoutError: simulator blocked; cleanup successful")
    marker = json.loads((first / "attempt.json").read_text())
    assert marker["status"] == "FAILED" and "simulator blocked" in marker["error"]
    fail_attempt(first, "OSError: secondary evidence publication failed")
    marker = json.loads((first / "attempt.json").read_text())
    assert "simulator blocked" in marker["error"]
    assert marker["additional_errors"] == ["OSError: secondary evidence publication failed"]
    assert find_completed_attempt(task, **options()) is None
    assert start_attempt(task, digest=DIGEST, resume=True).name == "attempt_0002"


def test_missing_marker_cannot_be_imported_but_crash_namespace_is_preserved(tmp_path):
    task = tmp_path / "CloseFridge"
    partial = task / "attempt_0001"
    partial.mkdir(parents=True)
    (partial / "actions.jsonl").write_text("partial history")
    assert find_completed_attempt(task, **options()) is None
    assert start_attempt(task, digest=DIGEST, resume=True).name == "attempt_0002"
    assert (partial / "actions.jsonl").read_text() == "partial history"


@pytest.mark.parametrize("digest", ["b" * 64, "bad", None])
def test_foreign_or_invalid_digest_never_creates_new_attempt(tmp_path, digest):
    task = tmp_path / "CloseFridge"
    start_attempt(task, digest=DIGEST, resume=False)
    with pytest.raises(ValueError):
        start_attempt(task, digest=digest, resume=True)
    assert len(list(task.iterdir())) == 1


def test_existing_namespace_without_explicit_resume_refuses(tmp_path):
    task = tmp_path / "CloseFridge"
    start_attempt(task, digest=DIGEST, resume=False)
    with pytest.raises(FileExistsError):
        start_attempt(task, digest=DIGEST, resume=False)


def test_legacy_results_are_never_imported(tmp_path):
    task = tmp_path / "CloseFridge"
    task.mkdir()
    write_json(task / "results.json", [{"ep": 0}])
    with pytest.raises(ValueError, match="legacy"):
        find_completed_attempt(task, **options())


@pytest.mark.parametrize("kind", ["task", "attempt", "marker", "artifact"])
def test_symlink_evidence_rejects_without_following(tmp_path, media, kind):
    task = tmp_path / "CloseFridge"
    attempt = start_attempt(task, digest=DIGEST, resume=False)
    populate(attempt, media)
    if kind == "task":
        task.rename(tmp_path / "foreign")
        task.symlink_to(tmp_path / "foreign", target_is_directory=True)
    elif kind == "attempt":
        attempt.rename(tmp_path / "foreign")
        attempt.symlink_to(tmp_path / "foreign", target_is_directory=True)
    else:
        path = attempt / ("attempt.json" if kind == "marker" else "rollout00_actions.jsonl")
        path.rename(tmp_path / "foreign")
        path.symlink_to(tmp_path / "foreign")
    with pytest.raises(ValueError, match="symlink"):
        if kind in {"task", "attempt", "marker"}:
            find_completed_attempt(task, **options())
        else:
            validate_attempt(attempt, **options())


@pytest.mark.parametrize(
    "failure",
    [
        "partial",
        "duplicate_ep",
        "wrong_digest",
        "wrong_attempt",
        "wrong_episode_record",
        "missing_actions",
        "truncated_actions",
        "mixed_actions",
        "wrong_action_order",
        "bad_action_abi",
        "mixed_predictions",
        "bad_frontier",
        "bad_count",
        "runtime_error",
        "foreign_audit_path",
        "unexpected_generated",
    ],
)
def test_cpu_negative_evidence_cannot_be_committed(tmp_path, media, failure):
    attempt = start_attempt(tmp_path / "CloseFridge", digest=DIGEST, resume=False)
    rows = populate(attempt, media)
    actions_path = attempt / "rollout00_actions.jsonl"
    predictions_path = attempt / "rollout00_predictions.jsonl"
    actions = [json.loads(line) for line in actions_path.read_text().splitlines()]
    predictions = [json.loads(line) for line in predictions_path.read_text().splitlines()]
    if failure == "partial":
        rows.pop()
    elif failure == "duplicate_ep":
        rows[1]["ep"] = 0
    elif failure == "wrong_digest":
        rows[0]["evaluation_run_digest"] = "b" * 64
    elif failure == "wrong_attempt":
        rows[0]["evaluation_attempt_id"] = "attempt_9999"
    elif failure == "wrong_episode_record":
        rows[0]["steps"] = 99
    elif failure == "missing_actions":
        actions_path.unlink()
    elif failure == "truncated_actions":
        actions_path.write_text(actions_path.read_text().rstrip("\n"))
    elif failure == "mixed_actions":
        actions[1]["evaluation_attempt_id"] = "attempt_9999"
        write_jsonl(actions_path, actions)
    elif failure == "wrong_action_order":
        actions[1]["source_step"] = 0
        write_jsonl(actions_path, actions)
    elif failure == "bad_action_abi":
        actions[0]["submitted_env12"] = [0] * 15
        write_jsonl(actions_path, actions)
    elif failure == "mixed_predictions":
        predictions[0]["episode"] = 1
        write_jsonl(predictions_path, predictions)
    elif failure == "bad_frontier":
        predictions[1]["step_before_query"] = 0
        write_jsonl(predictions_path, predictions)
    elif failure == "bad_count":
        rows[0]["replans"] = 3
    elif failure == "runtime_error":
        rows[0].update(policy=False, outcome="runtime_error", error="TimeoutError: server stopped")
    elif failure == "foreign_audit_path":
        rows[0]["actions_file"] = "../foreign.jsonl"
    elif failure == "unexpected_generated":
        shutil.copyfile(media / "tiny.mp4", attempt / "rollout00_generated.mp4")
    write_json(attempt / "results.json", rows)
    if failure != "wrong_episode_record":
        for row in rows:
            write_json(attempt / f"rollout{row['ep']:02d}_episode.json", row)
    with pytest.raises(ValueError):
        finish_attempt(attempt, **options())
    assert json.loads((attempt / "attempt.json").read_text())["status"] == "RUNNING"


@pytest.mark.parametrize("failure", ["missing", "empty", "truncated", "garbage", "png"])
def test_required_media_is_really_decoded_not_just_checked_for_existence(tmp_path, media, failure):
    path = tmp_path / ("sample.png" if failure == "png" else "sample.mp4")
    if failure == "empty":
        path.touch()
    elif failure == "garbage":
        path.write_bytes(b"a nonempty file is not a video")
    elif failure == "truncated":
        path.write_bytes((media / "tiny.mp4").read_bytes()[:150])
    elif failure == "png":
        path.write_bytes(b"not an image")
    with pytest.raises(ValueError):
        validate_media(path, sim_python=Path(sys.executable), kind="png" if failure == "png" else "mp4")


@pytest.mark.parametrize("failure", ["wrong_digest", "wrong_attempt", "bad_source_step", "wrong_frames", "missing"])
def test_generated_video_manifest_binds_replan_and_real_frame_count(tmp_path, media, failure):
    attempt = start_attempt(tmp_path / "CloseFridge", digest=DIGEST, resume=False)
    populate(attempt, media, mode="all")
    path = attempt / "rollout00_generated_manifest.json"
    manifest = json.loads(path.read_text())
    if failure == "wrong_digest":
        manifest["evaluation_run_digest"] = "b" * 64
    elif failure == "wrong_attempt":
        manifest["evaluation_attempt_id"] = "attempt_9999"
    elif failure == "bad_source_step":
        manifest["videos"][1]["source_step"] = 0
    elif failure == "wrong_frames":
        manifest["videos"][0]["frames"] = 999
    elif failure == "missing":
        (attempt / manifest["videos"][0]["file"]).unlink()
    write_json(path, manifest)
    with pytest.raises(ValueError):
        finish_attempt(attempt, **options("all"))


def test_corrupt_completed_task_cannot_be_silently_skipped(tmp_path, media):
    task = tmp_path / "CloseFridge"
    attempt = start_attempt(task, digest=DIGEST, resume=False)
    populate(attempt, media)
    finish_attempt(attempt, **options())
    (attempt / "rollout00_predictions.jsonl").unlink()
    with pytest.raises(ValueError, match="audit JSONL"):
        find_completed_attempt(task, **options())
    with pytest.raises(ValueError, match="completed"):
        fail_attempt(attempt, "must not overwrite committed evidence")


def test_deadline_prevents_task_commit_even_when_all_rows_exist(tmp_path, media):
    attempt = start_attempt(tmp_path / "CloseFridge", digest=DIGEST, resume=False)
    populate(attempt, media)
    with pytest.raises(TimeoutError, match="wall deadline"):
        finish_attempt(attempt, **options(), deadline=time.monotonic() - 1)
    assert json.loads((attempt / "attempt.json").read_text())["status"] == "RUNNING"


def test_media_decoder_deadline_is_bounded(tmp_path, monkeypatch):
    import robocasa_eval_results as module

    path = tmp_path / "video.mp4"
    path.write_bytes(b"not read by the injected CPU sleeper")
    monkeypatch.setattr(module, "_MEDIA_PROBE", "import time; time.sleep(60)")
    started = time.monotonic()
    with pytest.raises(TimeoutError, match="wall deadline"):
        validate_media(path, sim_python=Path(sys.executable), kind="mp4", deadline=started + 0.15)
    assert time.monotonic() - started < 3


@pytest.mark.parametrize("failure", ["missing", "missing_role", "live", "remaining", "error", "bad_pid"])
def test_cleanup_witness_required_before_task_can_be_skipped(tmp_path, media, failure):
    attempt = start_attempt(tmp_path / "CloseFridge", digest=DIGEST, resume=False)
    populate(attempt, media)
    path = attempt / "process_cleanup.json"
    payload = json.loads(path.read_text())
    if failure == "missing":
        path.unlink()
    else:
        if failure == "missing_role":
            payload.pop("server")
        elif failure == "live":
            payload["server"]["live_group"] = True
        elif failure == "remaining":
            payload["simulator"]["remaining_pids"] = [1234]
        elif failure == "error":
            payload["server"]["error"] = "kill failed"
        elif failure == "bad_pid":
            payload["server"]["pid"] = 0
        write_json(path, payload)
    with pytest.raises(ValueError):
        finish_attempt(attempt, **options())


@pytest.mark.parametrize("failure", [None, "missing", "foreign", "modified"])
def test_resume_rechecks_canonical_runtime_attestation(tmp_path, media, failure):
    task = tmp_path / "CloseFridge"
    attempt = start_attempt(task, digest=DIGEST, resume=False)
    populate(attempt, media)
    runtime = {"schema": "runtime_probe_fixture", "path": "/只读/依赖"}
    encoded = json.dumps(runtime, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    expected = hashlib.sha256(encoded).hexdigest()
    runtime["digest"] = "b" * 64 if failure == "foreign" else expected
    if failure == "modified":
        runtime["path"] = "/tampered"
    if failure != "missing":
        write_json(attempt / "runtime_attestation.json", runtime)
    if failure is None:
        finish_attempt(attempt, **options(), runtime_digest=expected)
        assert find_completed_attempt(task, **options(), runtime_digest=expected) == attempt
    else:
        with pytest.raises(ValueError):
            finish_attempt(attempt, **options(), runtime_digest=expected)


def test_cross_task_copy_with_same_attempt_number_cannot_complete(tmp_path, media):
    first = start_attempt(tmp_path / "CloseFridge", digest=DIGEST, resume=False)
    second = start_attempt(tmp_path / "NavigateKitchen", digest=DIGEST, resume=False)
    populate(first, media)
    populate(second, media)
    assert first.name == second.name
    for source in first.glob("rollout*"):
        shutil.copyfile(source, second / source.name)
    shutil.copyfile(first / "results.json", second / "results.json")
    with pytest.raises(ValueError, match="foreign task attempt"):
        finish_attempt(second, **options())


def test_cancellation_prevents_task_commit(tmp_path, media):
    import threading

    attempt = start_attempt(tmp_path / "CloseFridge", digest=DIGEST, resume=False)
    populate(attempt, media)
    stop = threading.Event()
    stop.set()
    with pytest.raises(InterruptedError, match="cancelled"):
        finish_attempt(attempt, **options(), stop=stop)
    assert json.loads((attempt / "attempt.json").read_text())["status"] == "RUNNING"


def test_cancel_stalled_decoder_reaps_its_process(tmp_path, monkeypatch):
    import threading

    import robocasa_eval_results as module

    processes = []
    original = module.subprocess.Popen

    def launch(*args, **kwargs):
        process = original(*args, **kwargs)
        processes.append(process)
        return process

    path = tmp_path / "video.mp4"
    path.write_bytes(b"CPU sleeper boundary")
    marker = tmp_path / "decoder_child.pid"
    monkeypatch.setattr(
        module,
        "_MEDIA_PROBE",
        "import signal,subprocess,sys,time; from pathlib import Path; "
        "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); "
        "Path(sys.argv[1]).with_name('decoder_child.pid').write_text(str(child.pid)); time.sleep(60)",
    )
    monkeypatch.setattr(module.subprocess, "Popen", launch)
    stop = threading.Event()

    def cancel_after_fork():
        until = time.monotonic() + 2
        while not marker.exists() and time.monotonic() < until:
            stop.wait(0.01)
        stop.set()

    timer = threading.Thread(target=cancel_after_fork)
    timer.start()
    started = time.monotonic()
    try:
        with pytest.raises(InterruptedError, match="cancelled"):
            validate_media(path, sim_python=Path(sys.executable), kind="mp4", stop=stop)
    finally:
        timer.join()
    assert time.monotonic() - started < 3
    assert len(processes) == 1 and processes[0].poll() is not None
    assert marker.is_file()
    assert not module.OwnedProcess.__init__.__globals__["group_members"](processes[0].pid)
    assert not Path("/proc", marker.read_text()).exists()
