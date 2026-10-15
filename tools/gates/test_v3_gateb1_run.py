"""CPU-only executable parser, pinning, authorization and proof artifact tests."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

import v3_gateb1_run as run
from v3_gateb1_native_driver import ConsumerCoordinate, CompletedNativeWindow


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    root = tmp_path / "root"
    child = root / "cosmos-framework"
    child.mkdir(parents=True)
    checkpoint = tmp_path / "original" / "iter_000001300"
    checkpoint.mkdir(parents=True)
    accepted = tmp_path / "accepted"
    accepted.mkdir()
    (accepted / "receipt.json").write_text("{}")
    for k in ("cache", "source", "edge", "vae", "base"):
        (tmp_path / k).mkdir()
    args = argparse.Namespace(
        leg="index8", profile="P0_FIXED", repeat=0, mode="prepare",
        root_worktree=root, checkpoint=checkpoint, dataset_index_root=accepted,
        cache_root=tmp_path / "cache", source_root=tmp_path / "source",
        edge=tmp_path / "edge", vae=tmp_path / "vae", base_checkpoint=tmp_path / "base",
        output_root=Path("/tmp/b1_cpu_only_fixtures_24362"),
        checkpoint_fingerprint=run.B0_FULL_SHARD_FINGERPRINT, job_name="b1_cpu_test",
        vision_resolution="480", owner_authorization_json=None,
    )

    def fake_git(path, *cmd):
        if cmd == ("rev-parse", "HEAD"):
            return run.SOURCE_CHILD if path == child.resolve() else run.SOURCE_ROOT
        if cmd == ("ls-tree", "HEAD", "cosmos-framework"):
            return f"160000 commit {run.SOURCE_CHILD} cosmos-framework"
        if cmd[0] == "status":
            return ""
        raise AssertionError((path, cmd))

    monkeypatch.setattr(run, "_git", fake_git)
    return args


def test_preparation_is_no_GPU_and_never_reads_dataset_payload(cfg, monkeypatch, capsys):
    # Metadata method checks only accepted receipt exists, no full file read.
    called = []
    def guarded_read(*args, **kwargs):
        called.append(args)
        raise AssertionError("payload read forbidden")
    monkeypatch.setattr(Path, "read_bytes", guarded_read)
    metadata = run.strict_metadata(cfg)
    assert metadata["gpu_authorized_by_prepare"] is False
    assert metadata["resolved_digest_expected"] == run.SOURCE_DIGEST
    assert not called
    assert metadata["dataset_source"].endswith("NO_RESCAN")


def test_code_ref_and_submodule_mismatch_reject_before_cuda(cfg, monkeypatch):
    monkeypatch.setattr(run, "_git", lambda path, *argv: "WRONG")
    with pytest.raises(run.RunBlocked, match="Root HEAD"):
        run.strict_metadata(cfg)


def test_missing_accepted_index_receipt_reject(cfg):
    (cfg.dataset_index_root / "receipt.json").unlink()
    with pytest.raises(run.RunBlocked, match="receipt"):
        run.strict_metadata(cfg)


def test_wrong_checkpoint_iteration_rejected(cfg):
    cfg.checkpoint = cfg.checkpoint.parent
    with pytest.raises(run.RunBlocked, match="iter_000001300"):
        run.strict_metadata(cfg)


def test_output_namespace_must_be_under_tmp(cfg):
    cfg.output_root = Path("/var/tmp/b1_dangerous")
    with pytest.raises(run.RunBlocked, match="/tmp"):
        run.strict_metadata(cfg)


def test_owner_receipt_absence_blocks_before_cuda(cfg):
    metadata = run.strict_metadata(cfg)
    with pytest.raises(run.RunBlocked, match="separately signed-off"):
        run._owner_receipt(cfg, metadata)


def test_owner_receipt_requires_thresholds_frozen_and_sha(cfg, tmp_path):
    metadata = run.strict_metadata(cfg)
    cfg.owner_authorization_json = tmp_path / "owner.json"
    data = dict(gate=run.APPROVAL_GATE, authorized=True, numeric_thresholds_frozen=False,
                implementation_sha="b" * 40,
                checkpoint_fingerprint=run.B0_FULL_SHARD_FINGERPRINT,
                source_root=run.SOURCE_ROOT, source_child=run.SOURCE_CHILD,
                target_root=run.TARGET_ROOT, target_child=run.TARGET_CHILD,
                approval_reference="owner-reviewed-2026-10-14")
    cfg.owner_authorization_json.write_text(json.dumps(data))
    with pytest.raises(run.RunBlocked, match="authorization"):
        run._owner_receipt(cfg, metadata)


def test_cli_requires_all_mandatory_inputs():
    with pytest.raises(SystemExit):
        run.parser().parse_args(["--mode", "prepare"])


@dataclass(frozen=True)
class Identity:
    slot_id: int
    episode_id: str
    source_digest: str = "src"
    segment_id: int = 0
    cursor: int = 0


def fake_window(iteration: int, *, partial: bool):
    calls = []
    for ga in (0, 1):
        coords = tuple(ConsumerCoordinate(ga, slot, t, t, Identity(slot, f"episode_{slot}"), 1)
                       for slot in range(8) for t in range(8 if partial and slot >= 4 else 16))
        calls.append((ga, coords))
    tensor = torch.tensor([1.0, 2.0], dtype=torch.float32)
    item = SimpleNamespace(
        family="generation", shard_key="rank0",
        gradient=tensor, master_before=tensor, master_after=tensor,
        m1_before=tensor, m1_after=tensor, m2_before=tensor, m2_after=tensor,
    )
    local = {"sidecar": {0: (None, None, (tensor, tensor, tensor, tensor))}}
    stochastic = tuple({"consumer": {"ga_member": ga, "slot_id": c.slot_id},
                        "vision_sigma_sha256": "a" * 64} for ga, coords in calls for c in coords)
    cfg = tuple({"consumer": {"ga_member": ga, "slot_id": c.slot_id},
                 "transformed_payload_sha256": "b" * 64} for ga, coords in calls for c in coords)
    return CompletedNativeWindow(iteration, 0, tuple(calls), {"model.generation": item}, local,
                                 {"weighted_outer": torch.tensor(0.5)}, stochastic, cfg)


@pytest.mark.parametrize("partial", [True, False])
def test_rank_capture_serializes_tensors_and_counts_without_pickle_objects(cfg, tmp_path, partial):
    cfg.output_root = tmp_path / "result_root"
    capture = fake_window(1301, partial=partial)
    files = run._save_completed(cfg, capture, {"schema": run.RUN_SCHEMA}, rank=0)
    tensor = torch.load(files["tensor"], weights_only=True)
    assert torch.equal(tensor["fqn"]["model.generation"]["gradient"], torch.tensor([1.0, 2.0]))
    assert len(tensor["fast"]["0"]) == 4
    report = json.loads(Path(files["report"]).read_text())
    assert report["case"] == ("terminal_partial" if partial else "full")
    assert report["ga_counts"] == ([96, 96] if partial else [128, 128])
    assert len(report["consumers"]) == sum(report["ga_counts"])
    with pytest.raises(run.RunBlocked, match="already contains"):
        run._save_completed(cfg, capture, {"schema": run.RUN_SCHEMA}, rank=0)


def test_unknown_metadata_object_fails_closed():
    with pytest.raises(run.RunBlocked, match="unsupported"):
        run._safe_json(object())


def test_capture_rejects_missing_actual_sigma_and_cfg_witness(cfg, tmp_path):
    from dataclasses import replace

    cfg.output_root = tmp_path / "failed_capture"
    complete = fake_window(1301, partial=False)
    broken = replace(complete, stochastic_witnesses=())
    with pytest.raises(run.RunBlocked, match="stochastic/CFG"):
        run._save_completed(cfg, broken, {"schema": run.RUN_SCHEMA}, rank=0)
    assert not list(cfg.output_root.rglob("*.pt"))


def test_real_cli_requires_explicit_resolved_vision_bucket_and_save_denial_scope():
    import inspect

    parser = run.parser()
    assert parser.get_default("vision_resolution") is None
    source = inspect.getsource(run.execute)
    assert "with exact_readonly_same_job_source(trainer.checkpointer, args.checkpoint):" in source
    assert "        results = runner.run()" in source
    assert "trainer.train(" not in source and "checkpointer.save(" not in source


def test_wrong_b0_authority_fails_even_for_existing_checkpoint(cfg):
    cfg.checkpoint_fingerprint = "0" * 64
    with pytest.raises(run.RunBlocked, match="B0 full-shard"):
        run.strict_metadata(cfg)


def test_owner_receipt_must_bind_exact_frozen_numeric_policy(cfg, tmp_path, monkeypatch):
    metadata = run.strict_metadata(cfg)
    authorization = tmp_path / "gpu_approval.json"
    cfg.owner_authorization_json = authorization
    frozen = {
        "gate": run.APPROVAL_GATE, "authorized": True,
        "numeric_thresholds_frozen": True, "numeric_policy_sha256": "0" * 64,
        "implementation_sha": "b" * 40,
        "checkpoint_fingerprint": run.B0_FULL_SHARD_FINGERPRINT,
        "source_root": run.SOURCE_ROOT, "source_child": run.SOURCE_CHILD,
        "target_root": run.TARGET_ROOT, "target_child": run.TARGET_CHILD,
        "approval_reference": "CPU-SYNTHETIC-ONLY-NOT-GPU-PERMISSION",
    }
    real_git = run._git

    def fixture_git(path, *command):
        if command == ("rev-parse", "HEAD") and path == Path(run.__file__).resolve().parents[2]:
            return "b" * 40
        return real_git(path, *command)

    monkeypatch.setattr(run, "_git", fixture_git)
    authorization.write_text(json.dumps(frozen))
    with pytest.raises(run.RunBlocked, match="Owner GPU authorization"):
        run._owner_receipt(cfg, metadata)
    frozen["numeric_policy_sha256"] = run.FROZEN_NUMERIC_POLICY_SHA256
    authorization.write_text(json.dumps(frozen))
    assert run._owner_receipt(cfg, metadata)["implementation_sha"] == "b" * 40
