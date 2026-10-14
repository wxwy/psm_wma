"""V3 Gate B1 isolated torchrun launcher: one frozen leg, P0/P1, two GA2 steps.

Prepare mode never imports Cosmos/PyTorch, touches datasets, or uses GPU.
Execute mode REQUIRES a separate Owner GPU authorization receipt. It preserves
both frozen production children, the original iter1300 DCP, and formal output
namespace. It directly invokes the original native FSDP8 model and trainer
training_step WITHOUT Trainer.train() or any Checkpointer.save().

Usage after explicit Owner GPU authorization (NOT authorized presently):
 torchrun --standalone --nproc_per_node=8 tools/gates/v3_gateb1_run.py --mode execute \
  --leg index8 ... --owner-authorization-json /tmp/b1-approval.json

The two frozen legs are executed in SEPARATE torchrun jobs; their reports are
paired by the CPU-only comparator, never by a fake shared Python process.
"""

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


SOURCE_ROOT = "b159f45906f7261d028aecc226ab7f2bb9807eb9"
SOURCE_CHILD = "937066ffd90f2bf783ad4fbb4909e9c0b8922982"
TARGET_ROOT = "c4731bca1a590663db88bd6cd74dbcf9fd513a85"
TARGET_CHILD = "c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686"
SOURCE_DIGEST = "70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37"
TARGET_DIGEST = "1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a"
PAIRS = {"index8": (SOURCE_ROOT, SOURCE_CHILD, SOURCE_DIGEST),
         "packed128": (TARGET_ROOT, TARGET_CHILD, TARGET_DIGEST)}
RUN_SCHEMA = "psm_v3_b1_native_capture_v1"
APPROVAL_GATE = "V3_PACKED128_B1_GPU_OWNER_APPROVED"


class RunBlocked(RuntimeError):
    """A frozen identity, Owner authorization or native observation is missing."""


def _git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def strict_metadata(args: argparse.Namespace) -> dict[str, Any]:
    """Cheap CPU-only inspection; DOES NOT read/hash a single data payload."""
    root = args.root_worktree.resolve(strict=True)
    child = (root / "cosmos-framework").resolve(strict=True)
    pinned_root, pinned_child, expected_digest = PAIRS[args.leg]
    if _git(root, "rev-parse", "HEAD") != pinned_root:
        raise RunBlocked("frozen Index8/Packed128 Root HEAD mismatch")
    if _git(child, "rev-parse", "HEAD") != pinned_child:
        raise RunBlocked("frozen Child HEAD mismatch")
    gitlink = _git(root, "ls-tree", "HEAD", "cosmos-framework").split()
    if len(gitlink) != 4 or gitlink[:2] != ["160000", "commit"] or gitlink[2] != pinned_child:
        raise RunBlocked("frozen root gitlink does not match pinned child")
    if _git(root, "status", "--porcelain", "--untracked-files=no") or _git(child, "status", "--porcelain"):
        raise RunBlocked("frozen implementation worktree is dirty")
    checkpoint = args.checkpoint.resolve(strict=True)
    if checkpoint.name != "iter_000001300" or not checkpoint.is_dir():
        raise RunBlocked("checkpoint must be original iter_000001300")
    accepted = args.dataset_index_root.resolve(strict=True)
    if not (accepted / "receipt.json").is_file():
        raise RunBlocked("previously accepted index receipt is missing")
    for path in (args.cache_root, args.source_root, args.edge, args.vae, args.base_checkpoint):
        if not path.exists():
            raise RunBlocked(f"required existing asset path unavailable: {path}")
    out_root = args.output_root.resolve()
    tmp = Path("/tmp").resolve()
    if out_root == tmp or not out_root.is_relative_to(tmp):
        raise RunBlocked("B1 result namespace must be a dedicated /tmp subdirectory")
    for protected in (root, child, checkpoint, accepted):
        if out_root.is_relative_to(protected) or protected.is_relative_to(out_root):
            raise RunBlocked("B1 output path overlaps a frozen worktree/checkpoint")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", args.job_name):
        raise RunBlocked("job_name must be a simple isolated identifier")
    if not re.fullmatch(r"[0-9a-f]{64}", args.checkpoint_fingerprint):
        raise RunBlocked("original B0 full-shard checkpoint fingerprint is required")
    return {
        "leg": args.leg, "profile": args.profile, "repeat": args.repeat,
        "root": pinned_root, "child": pinned_child, "resolved_digest_expected": expected_digest,
        "checkpoint": str(checkpoint), "checkpoint_fingerprint": args.checkpoint_fingerprint,
        "dataset_source": "previously_offline_accepted_receipt_NO_RESCAN",
        "checkpoint_write_authorized": False, "gpu_authorized_by_prepare": False,
    }


def _owner_receipt(args: argparse.Namespace, metadata: dict[str, Any]) -> dict[str, Any]:
    receipt = args.owner_authorization_json
    if receipt is None:
        raise RunBlocked("B1 GPU requires a separately signed-off Owner authorization JSON")
    auth = json.loads(receipt.read_text(encoding="utf-8"))
    if not isinstance(auth, dict):
        raise RunBlocked("invalid Owner authorization JSON")
    actual = _git(Path(__file__).resolve().parents[2], "rev-parse", "HEAD")
    if (
        auth.get("gate") != APPROVAL_GATE
        or auth.get("authorized") is not True
        or auth.get("numeric_thresholds_frozen") is not True
        or auth.get("implementation_sha") != actual
        or auth.get("checkpoint_fingerprint") != metadata["checkpoint_fingerprint"]
        or auth.get("source_root") != SOURCE_ROOT or auth.get("target_root") != TARGET_ROOT
        or auth.get("source_child") != SOURCE_CHILD or auth.get("target_child") != TARGET_CHILD
        or not isinstance(auth.get("approval_reference"), str)
        or not auth["approval_reference"].strip()
    ):
        raise RunBlocked("Owner GPU authorization does not bind exact B1 implementation and frozen pair")
    return {"approval_reference": auth["approval_reference"], "implementation_sha": actual}


def _safe_json(value: Any) -> Any:
    """Serialize metadata only: never stringify unknown Tensor/custom data silently."""
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _safe_json(getattr(value, f.name)) for f in fields(value)}
    if value is None or type(value) in (str, bool, int, float):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_json(v) for v in value]
    if isinstance(value, dict):
        if any(type(k) not in (str, int) for k in value):
            raise RunBlocked("noncanonical metadata key")
        return {str(k): _safe_json(v) for k, v in value.items()}
    raise RunBlocked(f"unsupported metadata item: {type(value)}")


def _save_completed(args: argparse.Namespace, capture: Any, metadata: dict[str, Any], *, rank: int) -> dict[str, str]:
    """Atomic per-rank evidence, only CPU primitive tensor dict + JSON."""
    import torch

    legdir = args.output_root / f"{args.leg}_{args.profile}_repeat{args.repeat}"
    legdir.mkdir(parents=True, exist_ok=True)
    basename = f"rank{rank}_iter{capture.completed_iteration}"
    tensor_path, report_path = legdir / f"{basename}.pt", legdir / f"{basename}.json"
    if tensor_path.exists() or report_path.exists():
        raise RunBlocked("evidence namespace already contains this rank/iteration; never overwrite")
    if capture.weighted_losses is None or "weighted_outer" not in capture.weighted_losses:
        raise RunBlocked("missing actual weighted native outer loss")
    by_fqn = {}
    for name, item in sorted(capture.optimizer_snapshot.items()):
        by_fqn[name] = {
            "family": item.family, "shard_key": item.shard_key,
            **{field: getattr(item, field) for field in (
                "gradient", "master_before", "master_after", "m1_before", "m1_after", "m2_before", "m2_after")},
        }
    local = capture.local_snapshot
    if not isinstance(local, dict) or "sidecar" not in local:
        raise RunBlocked("native committed Local snapshot missing sidecar")
    fast = {str(slot): {f"fast_{i}": t for i, t in enumerate(record[2])}
            for slot, record in local["sidecar"].items()}
    tensor_data = {"fqn": by_fqn, "fast": fast, "losses": capture.weighted_losses}
    consumers = [
        {"ga": ga, "slot_id": c.slot_id, "local_t": c.local_t,
         "absolute_step": c.absolute_step, "binding_epoch": c.binding_epoch,
         "identity": _safe_json(c.identity)}
        for ga, coords in capture.native_calls for c in coords
    ]
    unique = {(x["ga"], x["slot_id"], x["local_t"]) for x in consumers}
    if len(unique) != len(consumers):
        raise RunBlocked("duplicated runtime Consumers")
    counts = [sum(x["ga"] == ga for x in consumers) for ga in (0, 1)]
    if not all(0 < count <= 128 for count in counts):
        raise RunBlocked("runtime GA member count outside exact full/terminal window")
    # The B1 GPU gate demands *actual* model-site sigma/noise and text CFG
    # transform payload hashes from the two frozen children. A successful
    # tensor comparison without these is NOT a matched-stochastic test.
    if (len(capture.stochastic_witnesses) != len(consumers)
            or len(capture.cfg_witnesses) != len(consumers)):
        raise RunBlocked("native stochastic/CFG site coverage incomplete")
    form = "full" if counts == [128, 128] else "terminal_partial"
    body = {
        "schema": RUN_SCHEMA,
        **metadata,
        "rank": rank, "completed_iteration": capture.completed_iteration,
        "case": form, "ga_counts": counts,
        "native_calls": len(capture.native_calls),
        "consumers": consumers,
        "model_site_witnesses": list(capture.stochastic_witnesses),
        "cfg_transform_witnesses": list(capture.cfg_witnesses),
        "loss_names": sorted(capture.weighted_losses),
        "selected_fqns": sorted(by_fqn), "fast_slots": sorted(fast),
        "tensor_file": str(tensor_path), "status": "RAW_NATIVE_B1_EVIDENCE_ONLY_NOT_PARITY_PASS",
    }
    # Validate JSON shape before creating any evidence artifact; no malformed
    # candidate may leave a misleading partial .pt file behind.
    encoded = json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
    temporary = tensor_path.with_suffix(".pt.tmp")
    torch.save(tensor_data, temporary)
    os.replace(temporary, tensor_path)
    report_path.write_text(encoded)
    return {"report": str(report_path), "tensor": str(tensor_path), "case": form}


def _sampling(config: Any, args: argparse.Namespace):
    from v3_gateb1_stochastic import SamplingContract

    model = config.model.config
    flow = model.rectified_flow_training_config
    shift_config = flow.shift
    if isinstance(shift_config, dict):
        shift = shift_config[args.vision_resolution]
    else:
        try:
            shift = shift_config[args.vision_resolution]
        except (KeyError, TypeError):
            shift = shift_config
    raw_causal = getattr(model, "causal_training_strategy", None)
    causal = raw_causal if isinstance(raw_causal, str) else getattr(raw_causal, "value", raw_causal)
    if causal is None:
        causal = "none"
    independent = flow.independent_action_schedule
    if type(independent) is not bool:
        raise RunBlocked("resolved independent action schedule not boolean")
    action_shift = getattr(flow, "shift_action", None) if independent else None
    return SamplingContract(
        profile=args.profile, vision_distribution=flow.train_time_video_distribution,
        vision_shift=float(shift), causal_training_strategy=causal,
        independent_action_schedule=independent,
        action_distribution=flow.train_time_action_distribution if independent else None,
        action_shift=float(action_shift) if action_shift is not None else None,
        cfg_dropout_rate=0.1,
    )


def execute(args: argparse.Namespace, meta: dict[str, Any]) -> None:
    # Owner/CLI checks BEFORE touching CUDA or constructing real 4B model.
    auth = _owner_receipt(args, meta)
    import torch
    import torch.distributed as dist

    if not torch.cuda.is_available() or os.environ.get("WORLD_SIZE") != "8":
        raise RunBlocked("requires exact Owner-approved 8-rank CUDA torchrun")
    rank = int(os.environ.get("RANK", "-1"))
    local_rank = int(os.environ.get("LOCAL_RANK", "-1"))
    if not 0 <= rank < 8 or not 0 <= local_rank < 8 or torch.cuda.device_count() < 8:
        raise RunBlocked("missing real 8 CUDA ranks/devices")
    torch.cuda.set_device(local_rank)
    child = args.root_worktree.resolve() / "cosmos-framework"
    sys.path.insert(0, str(child))
    spec = importlib.util.find_spec("cosmos_framework")
    if spec is None or Path(spec.origin).resolve() != child / "cosmos_framework/__init__.py":
        raise RunBlocked("COSMOS import is not from the pinned frozen Child")
    from cosmos_framework.utils import distributed
    from cosmos_framework.utils.context_managers import model_init
    from cosmos_framework.utils.lazy_config import instantiate
    from cosmos_framework.model.generator.mot.robocasa_exact_window_local import (
        ExactWindowRankPlanner, ExactWindowSegmentProducer,
    )
    from cosmos_framework.data.generator.action.datasets import (
        robocasa_verified_index as verified_index,
        robocasa_exact_window_cache as cache_mod,
        robocasa_exact_window_source as source_mod,
    )
    from examples import psm_wma_robocasa_corrected_phase5 as phase5
    from v3_gateb1_no_rescan import trusted_frozen_preflight
    from v3_gateb1_same_job import exact_readonly_same_job_source
    from v3_gateb1_native_driver import build_loaded_native_bridge

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["IMAGINAIRE_OUTPUT_ROOT"] = str(args.output_root)
    opts = [
        "--phase", "fresh", "--root-worktree", str(args.root_worktree),
        "--expected-root", meta["root"], "--expected-child", meta["child"],
        "--source-root", str(args.source_root), "--cache-root", str(args.cache_root),
        "--dataset-index-root", str(args.dataset_index_root),
        "--edge", str(args.edge), "--vae", str(args.vae), "--base-checkpoint", str(args.base_checkpoint),
        "--output-root", str(args.output_root), "--job-name", args.job_name,
        "--t", "16", "--b", "8", "--ga", "2", "--k", "4", "--world-size", "8",
        "--max-iter", "30000", "--save-iter", "100", "--warmup", "500", "--num-workers", "0",
    ]
    formal_args = phase5.parser().parse_args(opts)
    with trusted_frozen_preflight(verified_module=verified_index, cache_module=cache_mod,
                                  source_module=source_mod):
        report, config, catalog, _ = phase5.preflight(formal_args)
    if report["config_digest"] != meta["resolved_digest_expected"]:
        raise RunBlocked("actual frozen corrected Phase5 resolved config digest mismatch")
    # The 'fresh' preflight only constructs data/config with no full state load;
    # overlay the real same-job DCP on the *same* config for read-only restore.
    phase5.overlay_config(config, formal_args, catalog.raw.contract, resume_checkpoint=args.checkpoint)
    if phase5.config_digest(catalog, config, b_stream=8, active_ga=2,
                             witnesses=report["model_witnesses"]) != report["config_digest"]:
        raise RunBlocked("resume overlay unexpectedly changed optimizer/model layout identity")
    config.checkpoint.dcp_async_mode_enabled = False
    if config.checkpoint.load_training_state is not True or config.checkpoint.strict_resume is not True:
        raise RunBlocked("strict full DCP training state must be loaded")
    job = Path(config.job.path_local).resolve()
    if not job.is_relative_to(args.output_root.resolve()) or job == args.output_root.resolve():
        raise RunBlocked("Cosmos trainer config/log output outside isolated /tmp B1 namespace")
    distributed.init()
    if not dist.is_initialized() or dist.get_world_size() != 8 or dist.get_rank() != rank:
        raise RunBlocked("frozen dp_shard8 distributed topology mismatch")
    config.validate()
    config.freeze()
    trainer = phase5.GroupedLocalMemoryTrainer(config)
    with model_init():
        model = instantiate(config.model)
    planner = ExactWindowRankPlanner(catalog, rank=rank, world_size=8, b_stream=8, active_ga=2)
    producer = ExactWindowSegmentProducer(catalog, config_digest=report["config_digest"])
    trainer.bind_grouped_stream(planner, producer, config_digest=report["config_digest"], num_workers=0)
    sampler = _sampling(config, args)
    with exact_readonly_same_job_source(trainer.checkpointer, args.checkpoint):
        runner, restore = build_loaded_native_bridge(
            config=config, model=model, planner=planner, producer=producer, trainer=trainer,
            checkpoint_path=args.checkpoint, leg=args.leg, rank=rank,
            checkpoint_fp=args.checkpoint_fingerprint,
            sampling_contract=sampler,
            target_digest=TARGET_DIGEST if args.leg == "packed128" else None,
        )
        if restore["source_checkpoint_fingerprint"] != args.checkpoint_fingerprint:
            raise RunBlocked("B0 checkpoint fingerprint differs from actual strict DCP snapshot")
        # Keep the checkpoint save-denial method guard active throughout the
        # entire native two-step run, not merely for the DCP loading call.
        results = runner.run()
    reports = [_save_completed(args, r, {**meta, **auth, "restore": restore}, rank=rank) for r in results]
    if rank == 0:
        print(json.dumps({"status": "EVIDENCE_WRITTEN_NOT_B1_PASS", "files": reports}, sort_keys=True))
    dist.barrier()


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("prepare", "execute"), required=True)
    p.add_argument("--leg", choices=tuple(PAIRS), required=True)
    p.add_argument("--profile", choices=("P0_FIXED", "P1_MATCHED_STOCHASTIC"), required=True)
    for name in ("root-worktree", "checkpoint", "dataset-index-root", "cache-root",
                 "source-root", "edge", "vae", "base-checkpoint", "output-root"):
        p.add_argument(f"--{name}", required=True, type=Path)
    p.add_argument("--checkpoint-fingerprint", required=True)
    p.add_argument("--job-name", default="b1_native_evidence")
    p.add_argument("--vision-resolution", required=True,
                   help="Exact frozen training resolution bucket; every real Native Consumer is checked")
    p.add_argument("--repeat", type=int, choices=(0, 1), default=0)
    p.add_argument("--owner-authorization-json", type=Path, default=None)
    return p


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    meta = strict_metadata(args)
    if args.mode == "prepare":
        print(json.dumps({"status": "PREPARE_ONLY_NO_GPU_OR_DATASET_SCAN", **meta}, sort_keys=True, indent=2))
        return
    execute(args, meta)


if __name__ == "__main__":
    main()
