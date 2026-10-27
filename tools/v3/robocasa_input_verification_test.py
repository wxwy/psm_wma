"""Issue6 tiny trusted-store cache and invocation guards; no model/server/GPU."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from robocasa_episode_resume import model_identity as identity
from robocasa_input_verification import InvocationInputGuard, snapshot_inputs
from robocasa_resume_store import ResumeStoreError, RunStore

from tools.v3 import robocasa_resume_store_test as helpers


@pytest.fixture
def checkpoint(tmp_path):
    path = tmp_path / "checkpoint"
    helpers.make_model(path)
    return path


def store(root, checkpoint, *, resume=False, **changes):
    request = dict(checkpoint=checkpoint, num_steps=30, action_horizon=16, guidance=1.0) | changes
    return RunStore(
        root,
        resume=resume,
        current_identity_reader=lambda: identity.build_model_identity(**request),
        model_identity_request=request,
    )


def create(root, checkpoint):
    instance = store(root, checkpoint)
    with instance.locked():
        instance.begin_invocation(helpers.plan([], invocation="initial"), {})
    return instance


def cache_path(root):
    return root / "_resume_v2/input_verification.json"


def model_reader_calls(monkeypatch):
    original = identity._read_hash
    calls = []

    def count(path, *args, **kwargs):
        calls.append(path.name)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(identity, "_read_hash", count)
    return calls


def test_cold_one_full_hash_then_locked_stat_warm_zero_bytes_and_same_anchor(tmp_path, checkpoint, monkeypatch):
    calls = model_reader_calls(monkeypatch)
    root = tmp_path / "run"
    cold = store(root, checkpoint)
    cold.preview()
    assert not root.exists()
    with cold.locked():
        cold.begin_invocation(helpers.plan([]), {})
    assert calls == [".metadata", "__0_0.distcp"]
    cold_bytes = sum(p.stat().st_size for p in (checkpoint / "model").iterdir())
    assert cold.verification_events[0]["model_payload_bytes_read"] == cold_bytes
    anchor = (root / "_resume_v2/model_identity.json").read_bytes()
    before = helpers.snapshot(root)
    monkeypatch.setattr(identity, "_read_hash", Mock(side_effect=AssertionError("warm payload read forbidden")))
    warm = store(root, checkpoint, resume=True)
    warm.preview()
    assert helpers.snapshot(root) == before
    with warm.locked():
        assert warm.current_identity["digest"] == cold.current_identity["digest"]
        assert warm.verification_events[0]["cache_hit"] is True
        assert warm.verification_events[0]["model_payload_bytes_read"] == 0
        assert warm.verification_events[0]["files_read"] == 0
    assert (root / "_resume_v2/model_identity.json").read_bytes() == anchor
    assert helpers.snapshot(root) == before
    print(
        "CACHE_IO_WITNESS "
        + json.dumps(
            {
                "cold_bytes": cold_bytes,
                "cold_hash_calls": calls,
                "warm_bytes": 0,
                "strong_digest": warm.current_identity["digest"],
            }
        ),
        flush=True,
    )


@pytest.mark.parametrize(
    "damage",
    ["missing", "truncated", "checksum", "schema", "expired", "future", "identity", "namespace", "duplicate_keys"],
)
def test_invalid_cache_falls_back_full_strict_same_anchor_and_repairs_under_lease(
    tmp_path, checkpoint, monkeypatch, damage
):
    root = tmp_path / "run"
    first = create(root, checkpoint)
    path = cache_path(root)
    if damage == "missing":
        path.unlink()
    elif damage == "truncated":
        path.write_bytes(b'{"broken":')
    elif damage == "duplicate_keys":
        path.write_bytes(b'{"schema":1,"schema":2}')
    else:
        document = helpers.read(path)
        if damage == "checksum":
            document["integrity_sha256"] = "0" * 64
        elif damage == "schema":
            document["schema"] = "old-cache-schema"
        elif damage in {"expired", "future"}:
            document["verified_at_ns"] = 1 if damage == "expired" else time.time_ns() + 10**15
        elif damage == "namespace":
            document["run_root"] = str(tmp_path / "other-run")
        else:
            document["identity"]["digest"] = "0" * 64
        if damage != "checksum":
            document["integrity_sha256"] = identity._digest(
                {k: v for k, v in document.items() if k != "integrity_sha256"}
            )
        helpers.write(path, document)
    original_anchor = (root / "_resume_v2/model_identity.json").read_bytes()
    before = helpers.snapshot(root)
    calls = model_reader_calls(monkeypatch)
    preview = store(root, checkpoint, resume=True)
    preview.preview()
    assert helpers.snapshot(root) == before  # Dry-run never repairs even bad caches.
    with preview.locked():
        preview.begin_invocation(helpers.plan([], invocation="repair"), {})
        assert preview.current_identity["digest"] == first.current_identity["digest"]
    assert calls == [".metadata", "__0_0.distcp"]
    assert (root / "_resume_v2/model_identity.json").read_bytes() == original_anchor
    with store(root, checkpoint, resume=True).locked() as repaired:
        assert repaired.verification_events[0]["cache_hit"] is True
    assert len(calls) == 2


@pytest.mark.parametrize("change", ["rewrite_same", "mtime", "inode", "extra_ordinary_file"])
def test_changed_stat_rehashes_equal_bytes_and_refreshes_witness_not_strong_anchor(
    tmp_path, checkpoint, monkeypatch, change
):
    root = tmp_path / "run"
    first = create(root, checkpoint)
    anchor = (root / "_resume_v2/model_identity.json").read_bytes()
    shard = checkpoint / "model/__0_0.distcp"
    before = shard.stat()
    if change == "rewrite_same":
        shard.write_bytes(shard.read_bytes())
        os.utime(shard, ns=(before.st_atime_ns, before.st_mtime_ns))
    elif change == "mtime":
        os.utime(shard, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
    elif change == "inode":
        replacement = tmp_path / "replacement"
        shutil.copyfile(shard, replacement)
        os.replace(replacement, shard)
    else:
        (checkpoint / "model/extra_ordinary_note").write_bytes(b"not a claimed model payload")
    calls = model_reader_calls(monkeypatch)
    with store(root, checkpoint, resume=True).locked() as same:
        same.begin_invocation(helpers.plan([], invocation="refresh"), {})
        assert same.current_identity["digest"] == first.current_identity["digest"]
        assert same.verification_events[0]["cache_hit"] is False
    assert len(calls) == 2
    assert (root / "_resume_v2/model_identity.json").read_bytes() == anchor
    with store(root, checkpoint, resume=True).locked() as warm:
        assert warm.verification_events[0]["cache_hit"] is True
    assert len(calls) == 2


@pytest.mark.parametrize(
    "change",
    ["byte_preserve_size_mtime", "new_shard", "removed_shard", "symlink", "metadata", "directory", "symlink_extra"],
)
def test_changed_model_never_refreshes_cache_or_original_anchor(tmp_path, checkpoint, monkeypatch, change):
    root = tmp_path / "run"
    create(root, checkpoint)
    before = helpers.snapshot(root)
    shard = checkpoint / "model/__0_0.distcp"
    if change == "byte_preserve_size_mtime":
        info = shard.stat()
        raw = bytearray(shard.read_bytes())
        raw[-1] ^= 1
        shard.write_bytes(raw)
        os.utime(shard, ns=(info.st_atime_ns, info.st_mtime_ns))
        assert shard.stat().st_size == info.st_size and shard.stat().st_mtime_ns == info.st_mtime_ns
        assert shard.stat().st_ctime_ns != info.st_ctime_ns
    elif change == "new_shard":
        shutil.copyfile(shard, checkpoint / "model/__1_0.distcp")
    elif change == "removed_shard":
        shard.unlink()
    elif change == "directory":
        (checkpoint / "model/foreign-directory").mkdir()
    elif change == "symlink_extra":
        (checkpoint / "model/unclaimed-link").symlink_to(shard)
    elif change == "symlink":
        other = tmp_path / "other-shard"
        shard.rename(other)
        shard.symlink_to(other)
    else:
        (checkpoint / "model/.metadata").write_bytes(b"invalid pickle")
    calls = model_reader_calls(monkeypatch)
    with pytest.raises((ResumeStoreError, identity.IdentityInputError)):
        with store(root, checkpoint, resume=True).locked():
            pytest.fail("changed model admitted")
    assert calls or change in {"symlink", "removed_shard", "directory", "symlink_extra"}
    assert helpers.snapshot(root) == before


@pytest.mark.parametrize(
    "changes", [{"num_steps": 31}, {"action_horizon": 8}, {"guidance": 2.0}, {"checkpoint": "relocated"}]
)
def test_changed_four_parameters_full_read_then_strict_mismatch(tmp_path, checkpoint, monkeypatch, changes):
    root = tmp_path / "run"
    create(root, checkpoint)
    before = helpers.snapshot(root)
    changes = dict(changes)
    target = checkpoint
    if changes.pop("checkpoint", None):
        target = tmp_path / "relocated"
        shutil.copytree(checkpoint, target)
    calls = model_reader_calls(monkeypatch)
    with pytest.raises(ResumeStoreError, match="MODEL_MISMATCH"):
        with store(root, target, resume=True, **changes).locked():
            pytest.fail("model mismatch admitted")
    assert len(calls) == 2 and helpers.snapshot(root) == before


def test_preview_to_lease_race_rehashes_and_rejects_before_any_cache_or_invocation_write(
    tmp_path, checkpoint, monkeypatch
):
    root = tmp_path / "run"
    create(root, checkpoint)
    instance = store(root, checkpoint, resume=True)
    instance.preview()
    before = helpers.snapshot(root)
    shard = checkpoint / "model/__0_0.distcp"
    raw = bytearray(shard.read_bytes())
    raw[-1] ^= 1
    shard.write_bytes(raw)
    calls = model_reader_calls(monkeypatch)
    with pytest.raises(ResumeStoreError, match="MODEL_MISMATCH"):
        with instance.locked():
            pytest.fail("racing mutation admitted")
    assert len(calls) == 2 and helpers.snapshot(root) == before


def test_old_run_22_completed_sources_keep_original_evidence_and_warm_resume(tmp_path, monkeypatch):
    root, checkpoint = helpers.legacy_run(tmp_path, completed=22, trials=50, status="FAILED")
    old = helpers.snapshot(root)
    first = store(root, checkpoint, resume=True)
    with first.locked():
        history = helpers.scan(first)
        assert len(history["records"]) == 22
        first.begin_invocation(helpers.plan(history["records"], requested=50), {})
    assert all(p.read_bytes() == data[0] and p.stat().st_mtime_ns == data[1] for p, data in old.items())
    monkeypatch.setattr(identity, "_read_hash", Mock(side_effect=AssertionError("warm model payload read")))
    with store(root, checkpoint, resume=True).locked() as warm:
        plan = helpers.plan(helpers.scan(warm)["records"], requested=50)
        assert plan["tasks"]["CloseFridge"]["reused"] == 22 and plan["tasks"]["CloseFridge"]["new"] == 28
    assert all(p.read_bytes() == data[0] for p, data in old.items())


@pytest.mark.parametrize("fault", ["raise", "kill"])
def test_interrupted_cache_publish_leaves_no_success_record_and_retry_is_safe(tmp_path, checkpoint, monkeypatch, fault):
    root = tmp_path / "run"
    # Reproduce an old admitted run: strong anchor, no new verification record.
    with RunStore(root, current_identity_reader=helpers.reader(checkpoint)).locked() as old:
        old.begin_invocation(helpers.plan([]), {})
    anchor = (root / "_resume_v2/model_identity.json").read_bytes()
    if fault == "raise":
        original = os.replace

        def fail(src, dst):
            if Path(dst).name == "input_verification.json":
                raise OSError("injected atomic cache publish failure")
            return original(src, dst)

        with monkeypatch.context() as scoped:
            scoped.setattr(os, "replace", fail)
            with pytest.raises(OSError, match="publish failure"):
                with store(root, checkpoint, resume=True).locked() as admitted:
                    admitted.begin_invocation(helpers.plan([], invocation="fail-cache"), {})
                    pytest.fail("published")
    else:
        code = """import os,sys
from pathlib import Path
from robocasa_resume_store import RunStore
from robocasa_episode_resume.model_identity import build_model_identity
root,checkpoint=map(Path,sys.argv[1:]);request=dict(checkpoint=checkpoint,num_steps=30,action_horizon=16,guidance=1.)
os.replace=lambda src,dst: os._exit(23)
with RunStore(root,resume=True,current_identity_reader=lambda:build_model_identity(**request),model_identity_request=request).locked() as store:
 store.begin_invocation({'invocation_id':'killed'}, {})
 raise AssertionError('published')
"""
        result = subprocess.run(
            [sys.executable, "-c", code, str(root), str(checkpoint)],
            env=dict(os.environ, PYTHONPATH=str(ROOT / "scripts")),
            timeout=20,
        )
        assert result.returncode == 23
        assert list((root / "_resume_v2").glob(".pending-*"))
    assert not cache_path(root).exists()
    with store(root, checkpoint, resume=True).locked() as retry:
        retry.begin_invocation(helpers.plan([], invocation="retry"), {})
    assert cache_path(root).is_file() and (root / "_resume_v2/model_identity.json").read_bytes() == anchor


def test_busy_other_process_cannot_publish_or_enter_even_on_cache_hit(tmp_path, checkpoint):
    root = tmp_path / "run"
    create(root, checkpoint)
    before = helpers.snapshot(root)
    code = """import sys
from pathlib import Path
from robocasa_resume_store import RunStore,ResumeStoreError
root=Path(sys.argv[1]);request=dict(checkpoint=Path(sys.argv[2]),num_steps=30,action_horizon=16,guidance=1.)
def forbidden(): raise AssertionError('warm bytes read')
try:
 with RunStore(root,resume=True,current_identity_reader=forbidden,model_identity_request=request).locked(): raise AssertionError('double owner')
except ResumeStoreError as error:
 assert error.code=='RUN_LOCKED'
 print(error.code)
"""
    with store(root, checkpoint, resume=True).locked():
        result = subprocess.run(
            [sys.executable, "-c", code, str(root), str(checkpoint)],
            env=dict(os.environ, PYTHONPATH=str(ROOT / "scripts")),
            text=True,
            capture_output=True,
            timeout=20,
        )
        assert result.returncode == 0 and "RUN_LOCKED" in result.stdout
    assert helpers.snapshot(root) == before


@pytest.fixture
def metadata(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("action_chunk_size: 16\n")
    directory = tmp_path / "dataset"
    (directory / "extras").mkdir(parents=True)
    path = directory / "extras/dataset_meta.json"
    path.write_text('{"task":"CloseFridge"}')
    manifest = {
        "identity": {
            "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
            "tasks": [
                {
                    "task": "CloseFridge",
                    "dataset_dir": str(directory),
                    "env_metadata_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            ],
        }
    }
    return config, path, manifest


def test_many_batches_guard_config_and_task_without_any_file_bytes(metadata, monkeypatch):
    config, path, manifest = metadata
    before = snapshot_inputs(config, [("CloseFridge", path.parent.parent)])
    guard = InvocationInputGuard(config, manifest, before)
    monkeypatch.setattr(Path, "open", Mock(side_effect=AssertionError("batch full read forbidden")))
    for _ in range(20):
        for phase in ("pre_model_load", "post_model_load", "pre_commit"):
            assert guard.verify(manifest, phase)["bytes_read"] == 0
    assert guard.checks == 61


@pytest.mark.parametrize("target", ["config", "task"])
@pytest.mark.parametrize("phase", ["pre_model_load", "post_model_load", "pre_commit", "final_input_verification"])
def test_config_or_task_same_size_restored_mtime_mutation_still_rejects(metadata, target, phase):
    config, path, manifest = metadata
    guard = InvocationInputGuard(config, manifest, snapshot_inputs(config, [("CloseFridge", path.parent.parent)]))
    victim = config if target == "config" else path
    info = victim.stat()
    raw = bytearray(victim.read_bytes())
    raw[-1] ^= 1
    victim.write_bytes(raw)
    os.utime(victim, ns=(info.st_atime_ns, info.st_mtime_ns))
    with pytest.raises(ValueError, match="changed during"):
        guard.verify(manifest, phase)


def test_mutation_during_initial_full_bundle_never_becomes_trusted(metadata):
    config, path, manifest = metadata
    before = snapshot_inputs(config, [("CloseFridge", path.parent.parent)])
    path.write_text("changed during initial full verification")
    with pytest.raises(ValueError, match="changed during"):
        InvocationInputGuard(config, manifest, before)


def test_wrong_job_manifest_hash_cannot_bypass_guard(metadata):
    config, path, manifest = metadata
    guard = InvocationInputGuard(config, manifest, snapshot_inputs(config, [("CloseFridge", path.parent.parent)]))
    changed = copy.deepcopy(manifest)
    changed["identity"]["config_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="manifest changed"):
        guard.verify(changed, "pre_commit")


@pytest.mark.parametrize("fault", ["missing_anchor", "corrupt_anchor", "symlink_cache", "symlink_control"])
def test_cache_cannot_bootstrap_or_override_bad_anchor_or_unsafe_paths(tmp_path, checkpoint, fault):
    root = tmp_path / "run"
    create(root, checkpoint)
    anchor = root / "_resume_v2/model_identity.json"
    if fault == "missing_anchor":
        anchor.unlink()
    elif fault == "corrupt_anchor":
        anchor.write_bytes(b"{bad")
    elif fault == "symlink_cache":
        target = tmp_path / "foreign-cache"
        cache_path(root).rename(target)
        cache_path(root).symlink_to(target)
    else:
        control = root / "_resume_v2"
        target = tmp_path / "external-control"
        control.rename(target)
        control.symlink_to(target, target_is_directory=True)
    before = helpers.snapshot(root)
    with pytest.raises((ResumeStoreError, identity.IdentityInputError)):
        with store(root, checkpoint, resume=True).locked() as current:
            current.begin_invocation(helpers.plan([], invocation="must-not-publish"), {})
    assert helpers.snapshot(root) == before


def test_legacy_relocation_cache_does_not_replace_explicit_owner_permission(tmp_path):
    root, checkpoint = helpers.legacy_run(tmp_path, completed=2)
    moved = tmp_path / "moved" / checkpoint.name
    shutil.copytree(checkpoint, moved, copy_function=shutil.copy2)
    original = helpers.snapshot(root)
    with pytest.raises(ResumeStoreError, match="MODEL_MISMATCH"):
        with store(root, moved, resume=True).locked():
            pytest.fail("silent legacy relocation")
    assert helpers.snapshot(root) == original
    request = dict(checkpoint=moved, num_steps=30, action_horizon=16, guidance=1.0)
    admitted = RunStore(
        root,
        resume=True,
        current_identity_reader=lambda: identity.build_model_identity(**request),
        model_identity_request=request,
        allow_relocated_legacy_checkpoint=True,
    )
    with admitted.locked():
        history = helpers.scan(admitted)
        assert len(history["records"]) == 2
        admitted.begin_invocation(helpers.plan(history["records"]), {})
    with store(root, moved, resume=True).locked() as warm:
        assert warm.verification_events[0]["cache_hit"] is True
    assert all(p.read_bytes() == data[0] for p, data in original.items())
