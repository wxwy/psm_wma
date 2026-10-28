"""r2 D1/D2/D3 CPU tests. Superseded r1 Task-replay assertions are replaced."""

import hashlib
import os
import subprocess
import sys

import pytest

from tools.v3.episode_eval_v2_prototype.contract import try_media
from tools.v3.episode_eval_v2_prototype.contract_test import manifest, record
from tools.v3.episode_eval_v2_prototype.store import Store, save


class Crash(BaseException):
    pass


def fresh(tmp_path, *, tasks=("CloseFridge",), episodes=3, formal=False):
    m = manifest(tasks, episodes, formal)
    value = Store(tmp_path / "new900", m)
    value.create()
    return value


def cleaned(_):
    return {"probe_id": "CPU mock ownership/local probe", "owned_processes_gone": True, "local_sessions_closed": True}


def healthy(_):
    return {"probe_id": "CPU mock new worker health", "healthy": True}


def close_streams(value, task):
    for s in value._streams(task):
        value.cleanup_stream(task, s["stream_id"], cleaned)


def admitted(value, a):
    value.begin_initialization(a)
    assert value.initialization_outcome(a, initial_success=False)["status"] == "admitted"
    return a


def valid(value, a, *, success=True, invalid=False):
    event = value.events(a)[-1]
    row = record(
        value.manifest,
        {**a, "reset_index": event["data"]["reset_index"]},
        a["episode"],
        success=success,
        invalid=invalid,
    )
    value.commit(row)
    return row


def complete(value, task, ep, *, success=True):
    a = admitted(value, value.begin_episode(task, ep))
    return valid(value, a, success=success)


def bytes_of_results(value):
    return {
        str(p.relative_to(value.root)): (p.read_bytes(), p.stat().st_ino)
        for p in value.root.glob("tasks/*/episodes/ep_*/result.json")
    }


def inject(stage):
    def fault(at):
        if at == stage:
            raise Crash(stage)

    return fault


@pytest.mark.parametrize("boundary", ["before_core_commit", "after_core_commit"])
def test_episode37_commit_crash_retries_only_uncommitted_slot_and_keeps_prefix_bytes(tmp_path, boundary):
    value = fresh(tmp_path, episodes=50)
    with pytest.raises(Crash), value.locked():
        value.begin_task("CloseFridge")
        for ep in range(37):
            complete(value, "CloseFridge", ep, success=ep % 2 == 0)
        original = bytes_of_results(value)
        media = value._slot("CloseFridge", 0) / "media/rollout.mp4"
        media.parent.mkdir()
        media.write_bytes(b"one original diagnostic video")
        inode = media.stat().st_ino
        a = admitted(value, value.begin_episode("CloseFridge", 37))
        value.fault = inject(boundary)
        valid(value, a)
    resumed = Store(value.root, value.manifest)
    with resumed.locked():
        close_streams(resumed, "CloseFridge")
        state = resumed.begin_task("CloseFridge", seed=90210)
        assert state["kind"] == "resume_new_stream_no_scene_reproduction"
        if boundary == "after_core_commit":
            with pytest.raises(ValueError, match="immutable"):
                resumed.begin_episode("CloseFridge", 37)
            first = 38
        else:
            first = 37
        for ep in range(first, 50):
            row = complete(resumed, "CloseFridge", ep)
            assert row["seed"] == 90210 and row["reset_index"] == ep - first
        after = bytes_of_results(resumed)
        assert all(after[k] == v for k, v in original.items())
        assert media.stat().st_ino == inode
        assert not (resumed.root / "videos_view").exists()
        assert resumed.summary()[0]["valid"] == 50


@pytest.mark.parametrize("boundary", ["before_intent", "after_intent", "after_directory", "after_ready"])
@pytest.mark.parametrize("is_slot", [False, True])
def test_task_and_episode_initialization_transaction_recovers_every_boundary(tmp_path, boundary, is_slot):
    value = fresh(tmp_path, tasks=("CloseFridge", "OpenCabinet"))
    with value.locked():
        value.begin_task("OpenCabinet")
        complete(value, "OpenCabinet", 0)
        close_streams(value, "OpenCabinet")
        untouched = bytes_of_results(value)
        if is_slot:
            value.begin_task("CloseFridge")
        value.fault = inject(boundary)
        with pytest.raises(Crash):
            if is_slot:
                value.begin_episode("CloseFridge", 0)
            else:
                value.begin_task("CloseFridge")
    with Store(value.root, value.manifest).locked() as resumed:
        close_streams(resumed, "CloseFridge")
        resumed.begin_task("CloseFridge")
        complete(resumed, "CloseFridge", 0)
        after = bytes_of_results(resumed)
        assert all(after[k] == v for k, v in untouched.items())
        assert resumed.rows("CloseFridge")[0]["episode"] == 0


@pytest.mark.parametrize("boundary", ["after_stream", "after_attempt_claim"])
def test_crash_after_claim_requires_cleanup_then_new_leased_producer(tmp_path, boundary):
    value = fresh(tmp_path)
    with pytest.raises(Crash), value.locked():
        if boundary == "after_stream":
            value.fault = inject(boundary)
        value.begin_task("CloseFridge")
        value.fault = inject(boundary)
        value.begin_episode("CloseFridge", 0)
    with Store(value.root, value.manifest).locked() as resumed:
        with pytest.raises(ValueError, match="not cleaned"):
            resumed.begin_task("CloseFridge")
        close_streams(resumed, "CloseFridge")
        resumed.begin_task("CloseFridge")
        complete(resumed, "CloseFridge", 0)
        attempts = resumed._attempts("CloseFridge", 0)
        assert len(attempts) == (2 if boundary == "after_attempt_claim" else 1)


@pytest.mark.parametrize("is_slot", [False, True])
def test_ambiguous_unready_producer_data_is_not_erased_or_adopted(tmp_path, is_slot):
    value = fresh(tmp_path)
    with value.locked():
        if is_slot:
            value.begin_task("CloseFridge")
        value.fault = inject("after_directory")
        with pytest.raises(Crash):
            value._initialize("CloseFridge", 0 if is_slot else None)
        public = value._slot("CloseFridge", 0) if is_slot else value._task("CloseFridge") / "episodes"
        bad = public / "unowned.bin"
        bad.write_bytes(b"preserve me")
        value.fault = lambda _: None
        with pytest.raises(ValueError, match="ambiguous"):
            value._initialize("CloseFridge", 0 if is_slot else None)
        assert bad.read_bytes() == b"preserve me"


def test_ready_directory_loss_is_ambiguous_not_silently_recreated(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        (value._task("CloseFridge") / "episodes").rmdir()
        with pytest.raises(ValueError, match="lost ready"):
            value._initialize("CloseFridge")


def test_old_fault_valid_retry_can_resolve_without_losing_history_or_polluting_other_task(tmp_path):
    value = fresh(tmp_path, tasks=("CloseFridge", "OpenCabinet"), episodes=1)
    with value.locked():
        old = value.begin_task("CloseFridge")
        a = admitted(value, value.begin_episode("CloseFridge", 0))
        value.finish_invalid(a, "Local cleanup failed")
        fault = value.errors("CloseFridge")[0]
        fault_path = value._internal("CloseFridge") / "errors" / f"{fault['id']}.json"
        preserved = fault_path.read_bytes()
        value.begin_task("OpenCabinet")
        complete(value, "OpenCabinet", 0)
        close_streams(value, "OpenCabinet")
        assert value.summary()[0]["tasks"]["OpenCabinet"]["results_qualified"]
        with pytest.raises(ValueError, match="current process fault"):
            value.begin_episode("CloseFridge", 0)
        value.cleanup_stream("CloseFridge", old["stream_id"], cleaned)
        value.begin_task("CloseFridge", seed=18)
        cert = value.certify_recovery("CloseFridge", old["stream_id"], healthy)
        with pytest.raises(ValueError, match="valid retry"):
            value.resolve_error("CloseFridge", fault["id"], cert)
        replacement = complete(value, "CloseFridge", 0, success=False)
        assert not value.summary()[0]["results_qualified"]
        value.resolve_error("CloseFridge", fault["id"], cert, replacement=replacement)
        close_streams(value, "CloseFridge")
        report = value.publish_views()
        assert report["results_qualified"] and report["resolved_process_errors"] == 1
        assert report["sr"] == 0.5 and fault_path.read_bytes() == preserved
        assert fault["attempt"]["attempt_id"] != replacement["attempt_id"]
        value.begin_task("CloseFridge", recovery_only=True)
        value.record_process_error("CloseFridge", "late", "new stream failure")
        assert not value.summary()[0]["results_qualified"]


def test_late_fault_keeps_numeric_SR_needs_explicit_execution_recovery_no_retest(tmp_path):
    value = fresh(tmp_path, episodes=1)
    with value.locked():
        old = value.begin_task("CloseFridge")
        a = admitted(value, value.begin_episode("CloseFridge", 0))
        valid(value, a)
        before = bytes_of_results(value)
        fault = value.record_process_error("CloseFridge", "worker_exit", "post-last-result exit nonzero", attempt=a)
        report = value.publish_views()
        assert report["sr"] == 1.0 and not report["results_qualified"]
        assert report["status"] == "complete_with_process_errors"
        with pytest.raises(ValueError, match="unsafe cleanup"):
            value.cleanup_stream(
                "CloseFridge", old["stream_id"], lambda _: dict(cleaned(_), owned_processes_gone=False)
            )
        assert value.errors("CloseFridge")[0]["resolution"] is None
        value.cleanup_stream("CloseFridge", old["stream_id"], cleaned)
        value.begin_task("CloseFridge", recovery_only=True)
        cert = value.certify_recovery("CloseFridge", old["stream_id"], healthy)
        value.resolve_error("CloseFridge", fault["id"], cert)
        close_streams(value, "CloseFridge")
        assert value.summary()[0]["results_qualified"] and bytes_of_results(value) == before
        with pytest.raises(ValueError, match="immutable"):
            value.begin_episode("CloseFridge", 0)


def test_wrong_task_certificate_or_unhealthy_probe_cannot_clear_error(tmp_path):
    value = fresh(tmp_path, tasks=("CloseFridge", "OpenCabinet"), episodes=1)
    with value.locked():
        old = value.begin_task("CloseFridge")
        fault = value.record_process_error("CloseFridge", "worker", "owned worker failed")
        other = value.begin_task("OpenCabinet")
        close_streams(value, "OpenCabinet")
        value.begin_task("OpenCabinet")
        cert = value.certify_recovery("OpenCabinet", other["stream_id"], healthy)
        with pytest.raises((ValueError, FileNotFoundError)):
            value.resolve_error("CloseFridge", fault["id"], cert)
        close_streams(value, "CloseFridge")
        value.begin_task("CloseFridge")
        with pytest.raises(ValueError, match="health proof"):
            value.certify_recovery("CloseFridge", old["stream_id"], lambda _: {"probe_id": "bad", "healthy": False})
        assert value.summary()[0]["unresolved_process_errors"] == 1


@pytest.mark.parametrize(
    "field", ["worker_id", "attempt_id", "episode", "stream_id", "seed", "generation", "reset_index"]
)
def test_misrouted_async_or_wrong_attempt_response_cannot_commit(tmp_path, field):
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        a = admitted(value, value.begin_episode("CloseFridge", 0))
        row = record(value.manifest, {**a, "reset_index": 0}, 0)
        row[field] = "f" * 32 if field.endswith("_id") else 1
        with pytest.raises(ValueError):
            value.commit(row)
        assert not value.rows("CloseFridge")


def test_stale_coordinator_duplicate_commit_and_behavioral_failure_never_retried(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        a = admitted(value, value.begin_episode("CloseFridge", 0))
        row = valid(value, a, success=False)
        with pytest.raises(ValueError):
            value.commit(row)
        with pytest.raises(ValueError, match="immutable"):
            value.begin_episode("CloseFridge", 0)
    with Store(value.root, value.manifest).locked() as resumed:
        close_streams(resumed, "CloseFridge")
        resumed.begin_task("CloseFridge")
        with pytest.raises(ValueError):
            resumed.commit(row)
        with pytest.raises(ValueError, match="immutable"):
            resumed.begin_episode("CloseFridge", 0)
        assert resumed.rows("CloseFridge")[0]["outcome"] == "failure"


@pytest.mark.parametrize(
    "payload", [b"\xff", b'{"a":1,"a":2}', b"NaN", b"x" * (256 * 1024 + 1), b'{"body": {}, "sha256": "wrong"}']
)
def test_corrupt_Core_record_cannot_be_reused(tmp_path, payload):
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        complete(value, "CloseFridge", 0)
        (value._slot("CloseFridge", 0) / "result.json").write_bytes(payload)
        with pytest.raises((ValueError, UnicodeError)):
            value.summary()


def test_media_failures_never_change_Core_or_trigger_retry(tmp_path):
    value = fresh(tmp_path, episodes=1)
    with value.locked():
        value.begin_task("CloseFridge")
        complete(value, "CloseFridge", 0)
        before = bytes_of_results(value)
        assert try_media(lambda: (_ for _ in ()).throw(OSError("bad encoder")))["status"] == "error"
        close_streams(value, "CloseFridge")
        assert value.publish_views()["results_qualified"]
        with pytest.raises(ValueError, match="immutable"):
            value.begin_episode("CloseFridge", 0)
        assert bytes_of_results(value) == before


def test_lease_competing_cpu_process_readonly_summary_and_existing_namespace_refusal(tmp_path):
    value = fresh(tmp_path)
    with pytest.raises(FileExistsError):
        value.create()
    with value.locked():
        code = "from pathlib import Path; from tools.v3.episode_eval_v2_prototype.store_test import *; m=manifest(); s=Store(Path(sys.argv[1]),m);\nwith s.locked(): pass"
        child = subprocess.run(
            [sys.executable, "-c", code, str(value.root)], capture_output=True, text=True, timeout=10
        )
        assert child.returncode != 0 and "BlockingIOError" in child.stderr
        with pytest.raises(RuntimeError):
            with value.locked():
                pass
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in value.root.rglob("*") if p.is_file()}
    assert value.summary()[0]["pending"] == 3
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in value.root.rglob("*") if p.is_file()}
    assert before == after


def test_atomic_write_failure_keeps_prior_record_and_does_not_publish_partial(tmp_path, monkeypatch):
    path = tmp_path / "atomic.json"
    save(path, {"old": True})
    old = path.read_bytes()
    with pytest.raises(FileExistsError):
        save(path, {"new": True})
    assert path.read_bytes() == old

    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(os, "link", fail)
    with pytest.raises(OSError):
        save(tmp_path / "missing.json", {"new": True})
    assert not (tmp_path / "missing.json").exists()


def test_unknown_task_out_of_bounds_and_symlinks_fail_closed(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        with pytest.raises(ValueError):
            value.begin_task("Unknown")
        value.begin_task("CloseFridge")
        with pytest.raises(ValueError):
            value.begin_episode("CloseFridge", 50)
        foreign = tmp_path / "foreign"
        foreign.mkdir()
        (value._task("CloseFridge") / "episodes/ep_000").symlink_to(foreign, target_is_directory=True)
        with pytest.raises(ValueError):
            value.rows("CloseFridge")


@pytest.mark.parametrize("scope", ["task", "slot"])
@pytest.mark.parametrize("lost", ["init_intent.json", "ready.json"])
def test_lost_published_init_authority_never_reconstructed_over_producer_ledger(tmp_path, scope, lost):
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        value.begin_episode("CloseFridge", 0)
        ledger = value._internal("CloseFridge") if scope == "task" else value._ledger("CloseFridge", 0)
        (ledger / lost).unlink()
        with pytest.raises(ValueError, match="intent lost|producer ledger"):
            value._initialize("CloseFridge", None if scope == "task" else 0)


@pytest.mark.parametrize("kind", ["unsafe", "invalid"])
def test_critical_process_fault_persisted_before_terminal_event_and_crash_does_not_hide_it(tmp_path, kind):
    value = fresh(tmp_path, episodes=1)
    with pytest.raises(Crash), value.locked():
        old = value.begin_task("CloseFridge")
        a = value.begin_episode("CloseFridge", 0)
        if kind == "unsafe":
            value.begin_initialization(a)
            value.fault = inject("after_unsafe_fault_before_event")
            value.initialization_outcome(a, error=RuntimeError("EGL"), stage="reset", safe_to_retry=False)
        else:
            admitted(value, a)
            value.fault = inject("after_invalid_fault_before_event")
            value.finish_invalid(a, "Local cleanup failed")
    with Store(value.root, value.manifest).locked() as resumed:
        report = resumed.summary()[0]
        assert report["unresolved_process_errors"] == 1 and not report["results_qualified"]
        assert report["sr"] is None
        fault = resumed.errors("CloseFridge")[0]
        close_streams(resumed, "CloseFridge")
        resumed.begin_task("CloseFridge")
        cert = resumed.certify_recovery("CloseFridge", old["stream_id"], healthy)
        replacement = complete(resumed, "CloseFridge", 0)
        resumed.resolve_error("CloseFridge", fault["id"], cert, replacement=replacement)
        close_streams(resumed, "CloseFridge")
        assert resumed.summary()[0]["results_qualified"]


def test_valid_numeric_SR_is_provisional_until_owned_worker_cleanup(tmp_path):
    value = fresh(tmp_path, episodes=1)
    with value.locked():
        value.begin_task("CloseFridge")
        complete(value, "CloseFridge", 0)
        report = value.publish_views()
        assert report["sr"] == 1.0 and not report["results_qualified"]
        assert report["status"] == "complete_awaiting_worker_cleanup"
        close_streams(value, "CloseFridge")
        assert value.summary()[0]["results_qualified"]


def test_resolution_is_revalidated_not_trusted_as_a_clear_flag(tmp_path):
    from tools.v3.episode_eval_v2_prototype.store import load, sealed, write

    value = fresh(tmp_path, episodes=1)
    with value.locked():
        old = value.begin_task("CloseFridge")
        complete(value, "CloseFridge", 0)
        fault = value.record_process_error("CloseFridge", "exit", "failed worker exit")
        close_streams(value, "CloseFridge")
        value.begin_task("CloseFridge", recovery_only=True)
        cert = value.certify_recovery("CloseFridge", old["stream_id"], healthy)
        value.resolve_error("CloseFridge", fault["id"], cert)
        path = value._internal("CloseFridge") / "resolutions" / f"{fault['id']}.json"
        corrupted = load(path)
        corrupted["mode"] = "forget_error"
        write(path, sealed(corrupted), replace=True)
        with pytest.raises(ValueError, match="requires valid retry"):
            value.summary()


def test_report_bound_does_not_relax_Core_limits_and_contradictory_admission_is_rejected(tmp_path):
    from tools.v3.episode_eval_v2_prototype.store import load, sealed, write, write_report

    with pytest.raises(ValueError, match="oversized"):
        save(tmp_path / "too_large_core.json", {"payload": "x" * (256 * 1024)})
    with pytest.raises(ValueError, match="cannot be used"):
        write_report(tmp_path / "result.json", {})
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        a = admitted(value, value.begin_episode("CloseFridge", 0))
        valid(value, a)
        event = value._ledger("CloseFridge", 0) / "events" / a["attempt_id"] / "000000.json"
        changed = load(event)
        changed["data"]["reset_index"] = 99
        write(event, sealed(changed), replace=True)
        with pytest.raises(ValueError, match="contradicts reset"):
            value.summary()
