"""Strict, *read-only* DCP resume seam for future B1 native 8-rank comparator.

Calls the OFFICIAL DistributedCheckpointer.load into prebuilt live objects,
patching only the rank's dataloader callback for transient Packed128 sidecar
digest translation. Never saves a DCP, writes a latest pointer, or invokes
Trainer.train(). The caller must separately initialize native FSDP8, verify
its exact model/optimizer/scheduler config and obtain Owner GPU authorization.
"""

from __future__ import annotations

from pathlib import Path
from types import MethodType
from typing import Any

from v3_gateb1_authority import B0_FULL_SHARD_FINGERPRINT
from v3_packed128_gateb_compare import (
    SOURCE_DIGEST,
    in_memory_target_sidecar,
    snapshot_checkpoint,
    unchanged_checkpoint,
    validate_sidecar,
)


class TransientLoadBlocked(RuntimeError):
    """Exact DCP/source/sidecar/load contract was not met; fail closed."""


REQUIRED_KEYS = frozenset({"model", "optim", "scheduler", "trainer", "dataloader"})


def _lightweight_immutability_snapshot(checkpoint_path: Path) -> dict[str, Any]:
    """Compare B0-approved DCP paths/size/mtime and small metadata/sidecar hashes.

    The returned fingerprint is deliberately NOT the full-content B0 SHA.
    DCP shard bodies are never SHA256-read by this transient B1 path.
    """
    result = snapshot_checkpoint(checkpoint_path, hash_shards=False)
    files = result.get("files")
    if (result.get("component_count") != 4 or result.get("dcp_shards") != 32
            or not isinstance(files, list) or len(files) != 44
            or not isinstance(result.get("checkpoint_fingerprint"), str)):
        raise TransientLoadBlocked("incomplete original DCP lightweight immutability witness")
    if any("sha256" in item for item in files if item.get("path", "").endswith(".distcp")):
        raise TransientLoadBlocked("DCP shard content hashing forbidden in B1 runtime")
    return result


def _validate_dcp_reader(checkpointer: Any, checkpoint_path: Path) -> None:
    config = getattr(checkpointer, "config_checkpoint", None)
    if config is None or getattr(config, "strict_resume", None) is not True:
        raise TransientLoadBlocked("full strict DCP resume required; no partial/warm-start")
    if getattr(checkpointer, "load_training_state", None) is not True:
        raise TransientLoadBlocked("DCP must load full model/optim/scheduler/trainer state")
    try:
        selected_keys, source = checkpointer.keys_to_resume_during_load()
    except Exception as exc:
        raise TransientLoadBlocked("failed reading the official DCP load selection") from exc
    if source is None or getattr(source, "warm_start", None) is not False:
        raise TransientLoadBlocked("source must be full same-job resume, never warm-start")
    try:
        if Path(source.path).resolve(strict=True) != checkpoint_path.resolve(strict=True):
            raise TransientLoadBlocked("DCP reader source differs from immutable iter1300")
    except (OSError, ValueError) as exc:
        raise TransientLoadBlocked("DCP source path missing or inaccessible") from exc
    if not REQUIRED_KEYS.issubset(set(selected_keys)):
        raise TransientLoadBlocked("four DCP components and dataloader are mandatory")


def _callback(trainer: Any) -> Any:
    callbacks = getattr(getattr(trainer, "callbacks", None), "_callbacks", None)
    if not isinstance(callbacks, list):
        raise TransientLoadBlocked("trainer lacks real native callback group")
    matches = [cb for cb in callbacks if getattr(cb, "checkpoint_component", None) == "dataloader"]
    if len(matches) != 1 or not callable(getattr(matches[0], "load_state_dict", None)):
        raise TransientLoadBlocked("exactly one real dataloader state callback required")
    return matches[0]


def strict_transient_load(*, checkpointer: Any, trainer: Any, model: Any, optimizer: Any,
                          scheduler: Any, grad_scaler: Any, checkpoint_path: Path,
                          leg: str, rank: int, source_digest: str = SOURCE_DIGEST,
                          target_digest: str | None = None,
                          authoritative_b0_checkpoint_fingerprint: str) -> dict[str, Any]:
    """Call the official strict full-state loader, never persisting target state.

    The callback conversion is private to this synchronous call. Restores the
    exact Python method in finally, even if DCP or sidecar validation fails.
    Merely calling this function is GPU-native work unless the caller supplies
    CPU fake Checkpointer/Model; it is NOT an authorized GPU launch instruction.
    """
    if leg not in {"index8", "packed128"} or type(rank) is not int or not 0 <= rank < 8:
        raise TransientLoadBlocked("unknown frozen comparison leg/rank")
    if checkpoint_path.name != "iter_000001300" or not source_digest:
        raise TransientLoadBlocked("requires original verified iter1300 source authority")
    if authoritative_b0_checkpoint_fingerprint != B0_FULL_SHARD_FINGERPRINT:
        raise TransientLoadBlocked("B0 original full-shard checkpoint fingerprint mismatch")
    if leg == "packed128" and (not target_digest or target_digest == source_digest):
        raise TransientLoadBlocked("target config digest must be independently resolved")
    if leg == "index8" and target_digest is not None:
        raise TransientLoadBlocked("source must keep its original config digest")
    _validate_dcp_reader(checkpointer, checkpoint_path)
    native_callback = _callback(trainer)
    original = native_callback.load_state_dict
    before = _lightweight_immutability_snapshot(checkpoint_path)
    evidence = {"called": 0}

    def scoped_load(self: Any, state: dict[str, Any]) -> None:
        if evidence["called"]:
            raise TransientLoadBlocked("dataloader state callback loaded more than once")
        validate_sidecar(state, rank=rank, source_digest=source_digest)
        converted = (
            in_memory_target_sidecar(state, source_digest=source_digest,
                                     target_digest=target_digest, rank=rank)
            if leg == "packed128" else state
        )
        original(converted)
        evidence["called"] += 1

    # Assign to this one callback object; never replace a production class.
    native_callback.load_state_dict = MethodType(scoped_load, native_callback)
    try:
        loaded_iteration = checkpointer.load(model, optimizer, scheduler, grad_scaler)
        if type(loaded_iteration) is not int or loaded_iteration != 1300:
            raise TransientLoadBlocked(f"strict DCP restored wrong iteration: {loaded_iteration}")
        if evidence["called"] != 1:
            raise TransientLoadBlocked("native dataloader callback was not invoked exactly once")
        if getattr(trainer, "_pending_grouped_resume", None) is None:
            raise TransientLoadBlocked("native trainer lacks pending committed Local state")
        after = _lightweight_immutability_snapshot(checkpoint_path)
        unchanged_checkpoint(before, after)
        return {
            "status": "STRICT_DCP_LOADED_TRANSIENT_NO_SAVE",
            "leg": leg,
            "rank": rank,
            "iteration": loaded_iteration,
            "source_checkpoint_fingerprint": authoritative_b0_checkpoint_fingerprint,
            "authoritative_b0_checkpoint_fingerprint": authoritative_b0_checkpoint_fingerprint,
            "runtime_lightweight_immutability_witness": before["checkpoint_fingerprint"],
            "runtime_shard_contents_rehashed": False,
            "source_digest": source_digest,
            "effective_config_digest": source_digest if leg == "index8" else target_digest,
            "dataloader_state_load_calls": evidence["called"],
            "checkpoint_write_authorized": False,
            "gpu_parity_approved": False,
        }
    finally:
        # Directly restore the original bound method, even after any exception.
        native_callback.load_state_dict = original
