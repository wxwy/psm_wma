"""CPU B0 preflight for the V3 Packed128-vs-Index8 numerical comparator.

This isolated diagnostic is NOT the GPU B1 runner or a checkpoint migrator.
It never calls Trainer.train(), Checkpointer.save(), or performs DCP writes.
B1 execution is intentionally fail-closed until reviewed separately.

The two frozen implementation pairs remain unchanged. Run this file from an
independent Gate B checkout, with each leg's pinned cosmos-framework on PYTHONPATH.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import dataclasses
import hashlib
import json
import os
import pickle
import random
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

SOURCE_ROOT = "b159f45906f7261d028aecc226ab7f2bb9807eb9"
SOURCE_CHILD = "937066ffd90f2bf783ad4fbb4909e9c0b8922982"
PACKED_ROOT = "c4731bca1a590663db88bd6cd74dbcf9fd513a85"
PACKED_CHILD = "c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686"
SOURCE_DIGEST = "70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37"
COMPONENTS = ("model", "optim", "scheduler", "trainer")
SIDECAR_KEYS = frozenset((
    "format", "iteration", "cache_manifest_sha256", "cache_corpus_digest",
    "source_binding_digest", "config_digest", "profile", "frontier", "scheduler", "sidecar",
))
SIDECAR_FORMAT = "psm_v3_corrected_grouped_local_v2"
GEOMETRY = {"world_size": 8, "b_stream": 8, "ttt_tbptt_steps": 16, "active_ga": 2}
ALLOWED_PAIRS = {"index8": (SOURCE_ROOT, SOURCE_CHILD), "packed128": (PACKED_ROOT, PACKED_CHILD)}
WITNESS_SCHEMA = "psm_v3_gate_b0_consumer_witness_v1"
REPORT_SCHEMA = "psm_v3_gate_b0_cpu_plan_v1"


class Blocked(RuntimeError):
    """Fail-closed B0 contract violation, not a GPU parity verdict."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Blocked(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def stable_seed(fields: Mapping[str, Any], *, domain: str) -> int:
    """Stable, domain-separated seed; never use Python's process-salted hash()."""
    require(bool(domain) and isinstance(fields, Mapping), "invalid witness seed scope")
    blob = json.dumps({"domain": domain, "key": dict(fields), "schema": WITNESS_SCHEMA},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    # Length prefix prevents accidental concatenation ambiguity.
    digest = hashlib.sha256(len(blob).to_bytes(8, "big") + blob).digest()
    return int.from_bytes(digest[:8], "big")


@dataclass(frozen=True)
class ConsumerKey:
    source_checkpoint_fingerprint: str
    rank: int
    completed_iteration: int
    ga_member: int
    slot_id: int
    episode_uid: str
    source_digest: str
    binding_epoch: int
    segment_id: int
    segment_cursor: int
    absolute_step: int

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def scoped(self, site: str, modality: str, item_index: int = 0, subindex: int = 0) -> dict[str, Any]:
        require(site != "" and modality != "" and item_index >= 0 and subindex >= 0, "invalid witness site")
        return {**self.as_dict(), "site": site, "modality": modality, "item_index": item_index, "subindex": subindex}


@contextlib.contextmanager
def scoped_python_cfg_rng(key: ConsumerKey) -> Iterator[None]:
    """Isolated python-random scope for the *serial* producer's real CFG call.

    This changes no production code. Refuse threaded processes rather than risk
    another Python thread observing a temporary global random state.
    """
    require(threading.current_thread() is threading.main_thread() and threading.active_count() == 1,
            "CFG global RNG scope requires one Python main thread and nw=0")
    previous = random.getstate()
    try:
        random.seed(stable_seed(key.scoped("cfg_dropout", "caption"), domain="python_cfg"))
        yield
    finally:
        random.setstate(previous)



@contextlib.contextmanager
def scoped_disable_tqdm_monitor() -> Iterator[None]:
    """Prevent benign progress-bar TMonitor before creating the real CPU catalog.

    This isolates this diagnostic process only. The strict CFG scope continues to
    reject *any* other live background thread rather than guessing RNG safety.
    """
    require(threading.current_thread() is threading.main_thread()
            and threading.active_count() == 1,
            "CFG preflight requires one Python main thread before tqdm initialization")
    from tqdm.std import tqdm

    old_interval = tqdm.monitor_interval
    try:
        # Set BEFORE metadata readers create progress bars / their TMonitor.
        tqdm.monitor_interval = 0
        yield
    finally:
        tqdm.monitor_interval = old_interval


def deterministic_witness_cpu(key: ConsumerKey, *, profile: str, site: str, modality: str,
                              shape: tuple[int, ...], item_index: int = 0) -> Any:
    """P0 CPU fixture. P1 must use a verified production sigma sampler in B1.

    A CPU tensor witness exercises identity/order/shape/seed determinism only.
    It is NOT an injection hook for the real Cosmos GPU forward.
    """
    require(profile in ("P0", "P1"), "unknown witness profile")
    require(site in ("sigma", "epsilon"), "unknown numerical stochastic site")
    require(bool(shape) and all(type(x) is int and x > 0 for x in shape), "invalid witness tensor shape")
    if profile == "P1" and site == "sigma":
        raise Blocked("P1 sigma requires resolved production shift/sampler; B0 must not invent its distribution")
    import torch
    if site == "sigma":
        return torch.full(shape, 0.5, dtype=torch.float32)
    if profile == "P0":
        return torch.zeros(shape, dtype=torch.float32)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(stable_seed(key.scoped(site, modality, item_index), domain="torch_cpu_epsilon"))
    return torch.randn(shape, generator=generator, dtype=torch.float32)


def _git(worktree: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True, check=False)
    require(p.returncode == 0, f"git pin error: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout.strip()


def validate_pair(root: Path, child: Path, leg: str) -> dict[str, str]:
    require(leg in ALLOWED_PAIRS, "unknown frozen comparator leg")
    expected_root, expected_child = ALLOWED_PAIRS[leg]
    root, child = root.resolve(strict=True), child.resolve(strict=True)
    require(_git(root, "rev-parse", "HEAD") == expected_root, "root HEAD mismatch")
    require(_git(child, "rev-parse", "HEAD") == expected_child, "child HEAD mismatch")
    tree = _git(root, "ls-tree", "HEAD", "cosmos-framework").split()
    require(len(tree) == 4 and tree[:2] == ["160000", "commit"] and tree[2] == expected_child,
            "Root child Gitlink mismatch")
    status = _git(child, "status", "--porcelain")
    require(not status, "child worktree dirty; import provenance not frozen")
    # Do not use pre-imported cosmos modules from unrelated worktrees.
    for name, module in sys.modules.items():
        if name.startswith("cosmos_framework") or name.startswith("examples.psm_wma_robocasa_corrected_phase5"):
            origin = getattr(module, "__file__", None)
            require(origin is None or Path(origin).resolve().is_relative_to(child), f"foreign import: {name} -> {origin}")
    return {"root": expected_root, "child": expected_child, "gitlink": tree[2], "root_worktree": str(root), "child_worktree": str(child)}


def snapshot_checkpoint(path: Path, *, hash_shards: bool) -> dict[str, Any]:
    checkpoint = path.resolve(strict=True)
    require(checkpoint.is_dir() and checkpoint.name == "iter_000001300", "checkpoint must be iter_000001300")
    entries: list[dict[str, Any]] = []
    num_shards = 0
    for component in COMPONENTS:
        directory = checkpoint / component
        meta = directory / ".metadata"
        require(meta.is_file() and not meta.is_symlink(), f"missing/linked DCP metadata: {component}")
        shards = sorted(directory.glob("*.distcp"))
        require(shards and all(f.is_file() and not f.is_symlink() for f in shards), f"DCP shards missing/linked: {component}")
        num_shards += len(shards)
        entries.append({"path": f"{component}/.metadata", "size": meta.stat().st_size, "sha256": sha256_file(meta)})
        for shard in shards:
            stat = shard.stat()
            rec = {"path": f"{component}/{shard.name}", "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
            if hash_shards:
                rec["sha256"] = sha256_file(shard)
            entries.append(rec)
    require(num_shards == 32, f"expected 32 DCP shards from frozen iter1300, got {num_shards}")
    for rank in range(8):
        side = checkpoint / "dataloader" / f"rank_{rank}.pkl"
        require(side.is_file() and not side.is_symlink(), f"missing/linked sidecar rank{rank}")
        entries.append({"path": f"dataloader/rank_{rank}.pkl", "size": side.stat().st_size, "sha256": sha256_file(side)})
    return {"path": str(checkpoint), "files": entries, "component_count": 4, "dcp_shards": num_shards,
            "checkpoint_fingerprint": _sha256_json([{"path": x["path"], "size": x["size"],
            "sha256": x.get("sha256", None)} for x in entries])}


def unchanged_checkpoint(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    require(before == after, "source checkpoint changed during B0")


def validate_sidecar(state: Any, *, rank: int, source_digest: str) -> dict[str, Any]:
    """Structural CPU witness. Real production restore() remains a B1 requirement."""
    import torch
    require(type(state) is dict and set(state) == SIDECAR_KEYS, "sidecar top-level 10-key schema mismatch")
    require(state["format"] == SIDECAR_FORMAT and state["iteration"] == 1300, "sidecar format/iteration mismatch")
    require(state["config_digest"] == source_digest, "source config digest mismatch")
    for field in ("cache_manifest_sha256", "cache_corpus_digest", "source_binding_digest"):
        require(type(state[field]) is str and state[field], f"sidecar {field} missing")
    profile = state["profile"]
    require(type(profile) is tuple and len(profile) == 17 and profile[:5] == (rank, 8, 0, 8, 2),
            "sidecar rank profile expected 17 fields and (rank,8,0,8,2)")
    require(profile[-3:] == (64, 16, 17), "sidecar profile tail mismatch")
    frontier = state["frontier"]
    require(type(frontier).__name__ == "ExactWindowCatalogFrontier", "frontier type mismatch")
    require(type(getattr(frontier, "slots", None)) is tuple and len(frontier.slots) == 8,
            "frontier slot geometry invalid")
    require(type(getattr(frontier, "epoch", None)) is int and frontier.epoch >= 0, "frontier epoch invalid")
    committed, saved = state["scheduler"], state["sidecar"]
    expected_slots = set(range(rank * 8, rank * 8 + 8))
    require(type(committed) is dict and set(committed) == expected_slots, "scheduler keys mismatch")
    require(type(saved) is dict and set(saved) <= expected_slots, "sidecar record slots mismatch")
    for slot_id, (identity, provenance, values) in saved.items():
        require(slot_id == identity.slot_id and committed[slot_id] == identity,
                "sidecar identity / committed chronology mismatch")
        require(type(provenance).__name__ == "SegmentProvenance" and provenance.config_digest == source_digest,
                "nested provenance digest mismatch")
        require(provenance.manifest_digest == state["cache_manifest_sha256"] and
                provenance.source_digest == identity.source_digest and provenance.segment_id == identity.segment_id,
                "nested provenance source/segment mismatch")
        require(type(values) is tuple and len(values) == 4, "four fast-state tensors required")
        for value in values:
            require(type(value) is torch.Tensor and value.device.type == "cpu" and value.dtype == torch.float32
                    and not value.requires_grad and value.grad_fn is None and bool(torch.isfinite(value).all()),
                    "fast-state must be finite plain CPU fp32")
    return {"rank": rank, "epoch": frontier.epoch, "committed": len(committed),
            "active_records": len(saved), "profile": list(profile)}


def in_memory_target_sidecar(source_state: Mapping[str, Any], *, source_digest: str,
                             target_digest: str, rank: int) -> dict[str, Any]:
    """No serialization or checkpoint publication: translate only config digests."""
    validate_sidecar(source_state, rank=rank, source_digest=source_digest)
    require(target_digest and target_digest != source_digest, "target layout must have distinct digest")
    state = copy.deepcopy(source_state)
    state["config_digest"] = target_digest
    for slot, (identity, provenance, values) in state["sidecar"].items():
        require(dataclasses.is_dataclass(provenance), "provenance is not dataclass")
        state["sidecar"][slot] = (identity, dataclasses.replace(provenance, config_digest=target_digest), values)
    # The only structural edits are the digest and nested provenance digest.
    require(set(state) == SIDECAR_KEYS and state["profile"] == source_state["profile"] and
            state["frontier"] == source_state["frontier"] and state["scheduler"] == source_state["scheduler"],
            "target clone changed non-digest state")
    for slot, (sid, prov, vals) in state["sidecar"].items():
        old_id, old_prov, old_vals = source_state["sidecar"][slot]
        require(sid == old_id and prov.manifest_digest == old_prov.manifest_digest and
                prov.source_digest == old_prov.source_digest and prov.segment_id == old_prov.segment_id,
                "target translation altered provenance identity")
        import torch
        require(all(torch.equal(x, y) for x, y in zip(vals, old_vals, strict=True)),
                "target translation altered fast state")
        require(old_prov.config_digest == source_digest and prov.config_digest == target_digest,
                "invalid nested migration source/target digest")
    return state


def _load_sidecars(checkpoint: Path, *, source_digest: str) -> tuple[list[Any], list[dict[str, Any]]]:
    sidecars, evidence = [], []
    for rank in range(8):
        # TRUSTED PINNED checkpoint only. Python pickle MUST NOT be loaded from untrusted sources.
        with (checkpoint / "dataloader" / f"rank_{rank}.pkl").open("rb") as f:
            state = pickle.load(f)  # noqa: S301 (trusted source and user-provided path)
        evidence.append(validate_sidecar(state, rank=rank, source_digest=source_digest))
        sidecars.append(state)
    return sidecars, evidence


def _frozen_manifest_from_plans(planners: Sequence[Any], sidecars: Sequence[Any], *,
                                checkpoint_fp: str) -> dict[str, Any]:
    require(len(planners) == len(sidecars) == 8, "expect eight rank-local planners/states")
    rows: list[dict[str, Any]] = []
    for rank, (planner, state) in enumerate(zip(planners, sidecars, strict=True)):
        frontier = state["frontier"]
        planner.validate_frontier(frontier)
        for offset in range(2):
            plan = planner.plan_window(frontier)
            require(len(plan.members) == 2 and len(plan.member_counts) == 2 and
                    all(type(x) is int and 0 < x <= 128 for x in plan.member_counts),
                    "invalid GA2 member count")
            consumers = []
            for ga, member in enumerate(plan.members):
                for request in member:
                    require(request.valid_count >= 1 and request.valid_count <= 16,
                            "invalid terminal member fragment")
                    for t in range(request.valid_count):
                        identity = request.identity
                        ck = ConsumerKey(checkpoint_fp, rank, 1300 + offset, ga,
                                         identity.slot_id, identity.episode_id, identity.source_digest,
                                         request.binding_epoch, identity.segment_id, identity.cursor,
                                         identity.cursor * 16 + t)
                        consumers.append(ck.as_dict())
            require(len(consumers) == plan.n_window == sum(plan.member_counts),
                    "Consumer count disagrees with planned member counts")
            consumer_hashes = [_sha256_json(x) for x in consumers]
            require(len(set(consumer_hashes)) == len(consumer_hashes), "duplicated Consumer identity")
            rows.append({"rank": rank, "completed_iteration_before": 1300 + offset,
                         "member_counts": list(plan.member_counts), "n_window": plan.n_window,
                         "index8_active_indices": [list(range(max(request.valid_count for request in member))) for member in plan.members],
                         "consumer_identity_sha256": _sha256_json(consumers),
                         "consumer_count": len(consumers), "terminal_partial": any(c < 128 for c in plan.member_counts),
                         "consumers": consumers})
            frontier = plan.candidate_frontier
    # Each rank can have different temporal active ranges; detect before any FSDP collective.
    rhythms = {offset: [tuple(len(rows[rank * 2 + offset]["index8_active_indices"][ga]) for ga in range(2))
                        for rank in range(8)] for offset in range(2)}
    require(all(len(set(values)) == 1 for values in rhythms.values()),
            "FSDP collective rhythm unsafe: Index8 active-index counts differ across ranks")
    return {"rows": rows, "collective_rhythm": rhythms,
            "terminal_partial_present": any(x["terminal_partial"] for x in rows),
            "plan_fingerprint": _sha256_json([x["consumer_identity_sha256"] for x in rows])}


def _stable_payload_hash(value: Any) -> str:
    """Hash complete Native inputs, including dataclass field values.

    Class identity, ordered field names and all recursively supported values
    participate in the hash; never use object repr() or skip unknown leaves.
    Cyclic containers fail closed instead of overflowing the recursion limit.
    """
    import torch
    h = hashlib.sha256()
    active_containers: set[int] = set()

    def feed(item: Any) -> None:
        is_record = dataclasses.is_dataclass(item) and not isinstance(item, type)
        is_container = isinstance(item, (tuple, list, dict)) or is_record
        if is_container:
            require(id(item) not in active_containers, "cyclic Native payload is unsupported")
            active_containers.add(id(item))
        try:
            if isinstance(item, torch.Tensor):
                require(item.device.type == "cpu", "CPU B0 payload unexpectedly on CUDA")
                tensor = item.detach().contiguous()
                h.update(b"T")
                h.update(str(tensor.dtype).encode())
                h.update(json.dumps(list(tensor.shape)).encode())
                h.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
            elif isinstance(item, (tuple, list)):
                h.update(b"L" if isinstance(item, list) else b"U")
                h.update(len(item).to_bytes(8, "big"))
                for val in item:
                    feed(val)
            elif isinstance(item, dict):
                require(all(type(k) is str for k in item), "non-string payload key unsupported")
                h.update(b"D")
                h.update(len(item).to_bytes(8, "big"))
                for key in sorted(item):
                    feed(key)
                    feed(item[key])
            elif is_record:
                cls = type(item)
                fields = dataclasses.fields(item)
                h.update(b"C")
                feed(f"{cls.__module__}.{cls.__qualname__}")
                h.update(len(fields).to_bytes(8, "big"))
                for field in fields:
                    feed(field.name)
                    feed(getattr(item, field.name))
            elif item is None or type(item) in (str, bool, int, float, bytes):
                encoded = json.dumps({"type": type(item).__name__, "value": item.hex() if isinstance(item, bytes) else item},
                                     sort_keys=True, allow_nan=False).encode()
                h.update(b"S" + len(encoded).to_bytes(8, "big") + encoded)
            else:
                raise Blocked(f"unhandled Native payload leaf type: {type(item).__module__}.{type(item).__qualname__}")
        finally:
            if is_container:
                active_containers.remove(id(item))

    feed(value)
    return h.hexdigest()

def _native_payload_digest(producer: Any, request: Any, *, fp: str, rank: int,
                           completed_iteration: int, ga: int) -> list[str]:
    """One isolated real producer execution with serial per-consumer CFG witness.

    Future B1 must provide sigma/epsilon probes at model call sites separately.
    """
    sft = producer.catalog.wrapped_sft
    original = sft._transform
    identity = request.identity

    def keyed_transform(item: dict[str, Any], resolution: Any) -> dict[str, Any]:
        absolute_step = int(item["start_frame"])
        ck = ConsumerKey(fp, rank, completed_iteration, ga, identity.slot_id,
                         identity.episode_id, identity.source_digest, request.binding_epoch,
                         identity.segment_id, identity.cursor, absolute_step)
        with scoped_python_cfg_rng(ck):
            return original(item, resolution)

    # Local instance-only temporary adapter: does not edit production files or global functions.
    sft._transform = keyed_transform
    try:
        segment = producer.produce(request)
    finally:
        sft._transform = original
    segment.validate(16)
    actual = int(segment.consumer_valid[0].sum())
    require(actual == request.valid_count, "real producer payload count differs from planner")
    return [_stable_payload_hash(segment.consumer_payload[0][i]) for i in range(actual)]


def materialized_consumer_hashes(catalog: Any, source_sidecars: Sequence[Any], *,
                                  checkpoint_fp: str, config_digest: str) -> dict[str, Any]:
    """Heavy CPU-only source-to-Native-Transform witness for both frozen legs."""
    from cosmos_framework.model.generator.mot.robocasa_exact_window_local import (
        ExactWindowRankPlanner, ExactWindowSegmentProducer,
    )
    outputs: list[dict[str, Any]] = []
    for rank in range(8):
        planner = ExactWindowRankPlanner(catalog, rank=rank, world_size=8, b_stream=8, active_ga=2)
        producer = ExactWindowSegmentProducer(catalog, config_digest=config_digest)
        frontier = source_sidecars[rank]["frontier"]
        for offset in range(2):
            plan = planner.plan_window(frontier)
            member_hashes = []
            for ga, member in enumerate(plan.members):
                payloads = []
                for request in member:
                    payloads.extend(_native_payload_digest(producer, request, fp=checkpoint_fp,
                                                           rank=rank, completed_iteration=1300 + offset, ga=ga))
                require(len(payloads) == plan.member_counts[ga], "materialized member count mismatch")
                member_hashes.append(_sha256_json(payloads))
            outputs.append({"rank": rank, "completed_iteration_before": 1300 + offset,
                            "member_payload_sha256": member_hashes})
            frontier = plan.candidate_frontier
    return {"members": outputs, "fingerprint": _sha256_json(outputs),
            "status": "CPU_TRANSFORM_PAYLOAD_HASHED_NOT_GPU_VALIDATED"}


def _restricted_output_dir(output_dir: Path, source: Path, root: Path, child: Path) -> Path:
    # Only create results in /tmp, never a path inside original DCP/worktree.
    resolved = output_dir.resolve()
    tmp = Path("/tmp").resolve()
    require(resolved != tmp and resolved.is_relative_to(tmp), "B0 outputs must be in dedicated /tmp directory")
    for protected in (source.resolve(), root.resolve(), child.resolve()):
        require(not resolved.is_relative_to(protected) and not protected.is_relative_to(resolved),
                "B0 output path overlaps protected source/worktree")
    require(not resolved.exists(), "B0 output namespace must be brand new")
    return resolved


def _preflight_catalog(args: argparse.Namespace) -> tuple[Any, str]:
    """CPU-only metadata path; no model/trainer/optimizer construction or DCP load."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    from examples.psm_wma_robocasa_corrected_phase5 import parser as production_parser, preflight
    config_argv = ["--phase", "fresh", "--output-root", str(args.output_dir),
                   "--source-root", str(args.source_root), "--cache-root", str(args.cache_root),
                   "--edge", str(args.edge), "--vae", str(args.vae),
                   "--base-checkpoint", str(args.base_checkpoint),
                   "--root-worktree", str(args.root_worktree),
                   "--dataset-index-root", str(args.dataset_index_root),
                   "--expected-root", ALLOWED_PAIRS[args.leg][0],
                   "--expected-child", ALLOWED_PAIRS[args.leg][1],
                   "--job-name", "gateb_cpu_plan_only", "--num-workers", "0", "--t", "16",
                   "--b", "8", "--ga", "2", "--k", "4", "--world-size", "8",
                   "--max-iter", "30000", "--warmup", "500", "--save-iter", "100"]
    production_args = production_parser().parse_args(config_argv)
    report, _resolved_config, catalog, _dataset = preflight(production_args)
    return catalog, report["config_digest"]


def run_cpu_plan(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = _restricted_output_dir(args.output_dir, args.source_checkpoint, args.root_worktree,
                                        args.child_worktree)
    require(args.source_config_digest == SOURCE_DIGEST, "unexpected frozen source digest")
    require(args.steps == 2 and args.num_workers == 0, "CPU B0 contract requires exactly2 windows, nw0")
    provenance = validate_pair(args.root_worktree, args.child_worktree, args.leg)
    child = args.child_worktree.resolve()
    # PYTHONPATH must already be pinned to the exact Child, not an unrelated checkout.
    from importlib.util import find_spec
    spec = find_spec("cosmos_framework")
    require(spec is not None and spec.origin is not None and Path(spec.origin).resolve().is_relative_to(child),
            "cosmos_framework import would resolve outside frozen child")
    with scoped_disable_tqdm_monitor():
        before = snapshot_checkpoint(args.source_checkpoint, hash_shards=args.hash_all_shards)
        sidecars, sidecar_evidence = _load_sidecars(args.source_checkpoint, source_digest=args.source_config_digest)
        catalog, run_digest = _preflight_catalog(args)
        if args.leg == "index8":
            require(run_digest == args.source_config_digest, "source runtime digest != source sidecar digest")
        else:
            require(run_digest and run_digest != args.source_config_digest,
                    "Packed128 runtime digest must differ from old source digest")
            for rank, old in enumerate(sidecars):
                new = in_memory_target_sidecar(old, source_digest=args.source_config_digest,
                                               target_digest=run_digest, rank=rank)
                require(new["config_digest"] == run_digest, "in-memory target digest failed")
        from cosmos_framework.model.generator.mot.robocasa_exact_window_local import ExactWindowRankPlanner
        planners = [ExactWindowRankPlanner(catalog, rank=r, world_size=8, b_stream=8, active_ga=2)
                    for r in range(8)]
        plans = _frozen_manifest_from_plans(planners, sidecars,
                                           checkpoint_fp=before["checkpoint_fingerprint"])
        payload_witness = (
            materialized_consumer_hashes(catalog, sidecars, checkpoint_fp=before["checkpoint_fingerprint"],
                                         config_digest=run_digest)
            if args.verify_payloads else None
        )
        after = snapshot_checkpoint(args.source_checkpoint, hash_shards=args.hash_all_shards)
        unchanged_checkpoint(before, after)
        # Report only after all validations; strictly no checkpoint writes.
        report = {"schema": REPORT_SCHEMA, "status": "CPU_PLAN_PRODUCED_NOT_GPU_VALIDATED",
                  "leg": args.leg, "pair": provenance, "checkpoint": before,
                  "source_digest": args.source_config_digest, "resolved_digest": run_digest,
                  "sidecar_static": sidecar_evidence, "plan": plans, "payload_witness": payload_witness,
                  "unverified": ["real_FSDP8_DCP_load", "production_Local_restore",
                                 *([] if args.verify_payloads else ["payload_tensors"]),
                                 "native_forward_backward", "P1_sigma_sampler", "GPU_gradient_parity"],
                  "gpu_authorized": False, "checkpoint_write_authorized": False}
        output_dir.mkdir(parents=True, exist_ok=False)
        target = output_dir / f"gateb0_{args.leg}.json"
        with target.open("x", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False)
        return {"status": report["status"], "report": str(target),
                "plan_sha256": plans["plan_fingerprint"], "terminal_partial": plans["terminal_partial_present"]}


def compare_cpu_reports(ref_path: Path, packed_path: Path) -> dict[str, Any]:
    with ref_path.open("r", encoding="utf-8") as f:
        a = json.load(f)
    with packed_path.open("r", encoding="utf-8") as f:
        b = json.load(f)
    require(a["schema"] == b["schema"] == REPORT_SCHEMA and a["leg"] == "index8" and
            b["leg"] == "packed128", "paired report schema / leg mismatch")
    require(a["pair"]["root"] == SOURCE_ROOT and b["pair"]["root"] == PACKED_ROOT,
            "incorrect comparator provenance")
    require(a["checkpoint"]["checkpoint_fingerprint"] == b["checkpoint"]["checkpoint_fingerprint"],
            "different source checkpoint fingerprints")
    require(a["source_digest"] == b["source_digest"] == SOURCE_DIGEST and
            a["resolved_digest"] == SOURCE_DIGEST and b["resolved_digest"] != SOURCE_DIGEST,
            "source/target digest contract mismatch")
    require(a["plan"]["plan_fingerprint"] == b["plan"]["plan_fingerprint"] and
            a["plan"]["rows"] == b["plan"]["rows"], "consumer window plan not identical")
    if (a.get("payload_witness") is None) != (b.get("payload_witness") is None):
        raise Blocked("only one leg materialized real CPU payloads")
    if a.get("payload_witness") is not None:
        require(a["payload_witness"] == b["payload_witness"], "Native input payload parity mismatch")
    return {"status": "CPU_PLAN_PARITY_ONLY", "matched_16_rank_windows": True,
            "plan_sha256": a["plan"]["plan_fingerprint"], "gpu_authorized": False}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("cpu-plan-only", "compare-cpu-reports", "paired-run"), required=True)
    p.add_argument("--leg", choices=("index8", "packed128"))
    p.add_argument("--root-worktree", type=Path)
    p.add_argument("--child-worktree", type=Path)
    p.add_argument("--source-checkpoint", type=Path)
    p.add_argument("--source-config-digest", default=SOURCE_DIGEST)
    p.add_argument("--dataset-index-root", type=Path)
    p.add_argument("--source-root", type=Path)
    p.add_argument("--cache-root", type=Path)
    p.add_argument("--edge", type=Path)
    p.add_argument("--vae", type=Path)
    p.add_argument("--base-checkpoint", type=Path)
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--steps", type=int, default=2)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--hash-all-shards", action="store_true")
    p.add_argument("--verify-payloads", action="store_true", help="Read+transform every consumer in two 8-rank windows (CPU intensive)")
    p.add_argument("--reference-report", type=Path)
    p.add_argument("--target-report", type=Path)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.mode == "paired-run":
            raise Blocked("GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED; no model training may start from CPU B0 harness")
        if args.mode == "compare-cpu-reports":
            require(args.reference_report is not None and args.target_report is not None,
                    "comparison requires two report paths")
            output = compare_cpu_reports(args.reference_report, args.target_report)
        else:
            required = ("leg", "root_worktree", "child_worktree", "source_checkpoint", "output_dir",
                        "dataset_index_root", "source_root", "cache_root", "edge", "vae", "base_checkpoint")
            require(all(getattr(args, key) is not None for key in required), "missing required B0 source path or leg")
            output = run_cpu_plan(args)
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
        return 0
    except (Blocked, OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
