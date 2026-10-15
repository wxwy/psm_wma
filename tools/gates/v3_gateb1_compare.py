"""CPU-only audit of B1 FSDP8 two-window evidence across frozen legs.

Pairs all 8 ranks and both post-1300 steps for P0/P1 and repeat0/repeat1;
compares canonical Consumers/CFG+stochastic witness fields exactly and all
selected optimizer-FQN tensors using Owner-frozen r2 numerical limits.

Even when all frozen metrics pass, the GPU Gate still requires independent
parity evidence review and separate Owner GPU authorization.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import re
from pathlib import Path
from typing import Any

from v3_gateb1_authority import FROZEN_NUMERIC_POLICY_SHA256, assert_numeric_policy_frozen

SOURCE_ROOT = "b159f45906f7261d028aecc226ab7f2bb9807eb9"
TARGET_ROOT = "c4731bca1a590663db88bd6cd74dbcf9fd513a85"
SOURCE_CHILD = "937066ffd90f2bf783ad4fbb4909e9c0b8922982"
TARGET_CHILD = "c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686"
SCHEMA = "psm_v3_b1_native_capture_v1"
SOURCE_DIGEST = "70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37"
TARGET_DIGEST = "1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a"


class CompareBlocked(RuntimeError):
    pass


def canonical_consumers(payload: dict[str, Any]) -> tuple[str, ...]:
    """Ignore real source-index vs packed slot call order, never Consumer values."""
    values = payload.get("consumers")
    if not isinstance(values, list) or not values:
        raise CompareBlocked("missing nonempty Consumer roster")
    seen = set()
    normalized = []
    for consumer in values:
        key = (consumer["ga"], consumer["slot_id"], consumer["local_t"])
        if key in seen or consumer["ga"] not in (0, 1):
            raise CompareBlocked("duplicate/unexpected Consumer identity")
        seen.add(key)
        normalized.append((key, json.dumps(consumer, sort_keys=True, separators=(",", ":"), allow_nan=False)))
    if [sum(k[0] == ga for k, _ in normalized) for ga in (0, 1)] != payload["ga_counts"]:
        raise CompareBlocked("actual Consumer count does not match member counts")
    return tuple(x[1] for x in sorted(normalized, key=lambda kv: kv[0]))


def canonical_site_witnesses(report: dict[str, Any], field: str) -> tuple[str, ...]:
    """Compare actual model sigma/epsilon/masks and text CFG hashes by ConsumerKey."""
    entries = report.get(field)
    expected = {(c["ga"], c["slot_id"], c["absolute_step"]) for c in report["consumers"]}
    if not isinstance(entries, list) or len(entries) != len(expected):
        raise CompareBlocked(f"{field}: missing actual per-consumer witnesses")
    mapped = {}
    for item in entries:
        key = item.get("consumer")
        if not isinstance(key, dict):
            raise CompareBlocked(f"{field}: missing canonical ConsumerKey")
        index = (key.get("ga_member"), key.get("slot_id"), key.get("absolute_step"))
        if index in mapped:
            raise CompareBlocked(f"{field}: duplicate site ConsumerKey")
        required = (("vision_sigma_sha256", "action_sigma_sha256", "vision_epsilon_sha256",
                     "action_epsilon_sha256", "action_condition_mask_sha256", "vision_condition_mask_sha256")
                    if field == "model_site_witnesses" else ("transformed_payload_sha256",))
        if any(not isinstance(item.get(k), str) or
               (item[k] != "ALL_ACTION_CONDITIONING" and not re.fullmatch(r"[0-9a-f]{64}", item[k]))
               for k in required):
            raise CompareBlocked(f"{field}: missing/malformed stochastic or CFG hash")
        mapped[index] = json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if set(mapped) != expected:
        raise CompareBlocked(f"{field}: ConsumerKey coverage differs from original roster")
    return tuple(mapped[k] for k in sorted(mapped))


def validate_pair(source: dict[str, Any], target: dict[str, Any], *, rank: int,
                  iteration: int, profile: str, repeat: int) -> str:
    """Rank-local exact key/value contract BEFORE comparing numeric tensors."""
    for leg, report, expected_root, expected_child, expected_digest in (
        ("index8", source, SOURCE_ROOT, SOURCE_CHILD, SOURCE_DIGEST),
        ("packed128", target, TARGET_ROOT, TARGET_CHILD, TARGET_DIGEST),
    ):
        restore = report.get("restore")
        if not isinstance(restore, dict) or (
            restore.get("iteration") != 1300 or
            restore.get("effective_config_digest") != expected_digest or
            restore.get("source_checkpoint_fingerprint") != report.get("checkpoint_fingerprint")
        ):
            raise CompareBlocked(f"{leg}: strict original iter1300 checkpoint DCP restore identity missing")
        if (
            report.get("schema") != SCHEMA or report.get("leg") != leg
            or report.get("root") != expected_root or report.get("child") != expected_child
            or report.get("profile") != profile or report.get("repeat") != repeat
            or report.get("rank") != rank or report.get("completed_iteration") != iteration
            or report.get("checkpoint_write_authorized") is not False
            or report.get("status") != "RAW_NATIVE_B1_EVIDENCE_ONLY_NOT_PARITY_PASS"
        ):
            raise CompareBlocked(f"{leg}: frozen native schema/pair/profile/rank/step mismatch")
    for key in ("checkpoint_fingerprint", "approval_reference", "case", "ga_counts"):
        if source.get(key) != target.get(key):
            raise CompareBlocked(f"Source/Target {key} differs")
    if source["case"] not in ("full", "terminal_partial"):
        raise CompareBlocked("missing real Full/Terminal Partial case label")
    if source["case"] == "full" and source["ga_counts"] != [128, 128]:
        raise CompareBlocked("Full label has nonfull GA counts")
    if source["case"] == "terminal_partial" and all(x == 128 for x in source["ga_counts"]):
        raise CompareBlocked("Terminal label contains no actual partial member")
    if canonical_consumers(source) != canonical_consumers(target):
        raise CompareBlocked("source/target original Consumer identity is not equal")
    for field in ("model_site_witnesses", "cfg_transform_witnesses"):
        if canonical_site_witnesses(source, field) != canonical_site_witnesses(target, field):
            raise CompareBlocked(f"source/target actual {field} differs despite matching Consumer identity")
    return source["case"]


def _tensor_data(info: dict[str, Any], *, source_dir: Path):
    import torch

    name = Path(info.get("tensor_file", "")).resolve(strict=True)
    if not name.is_relative_to(source_dir.resolve()) or name.suffix != ".pt":
        raise CompareBlocked("tensor capture file outside evidence namespace")
    # Primitive dict[str,Tensor] only, NEVER pickle a foreign production object.
    raw = torch.load(name, map_location="cpu", weights_only=True)
    if set(raw) != {"fqn", "fast", "losses"}:
        raise CompareBlocked("missing canonical captured tensor fields")
    return raw


def _compare_numeric(source: dict[str, Any], target: dict[str, Any], *, evidence_dir: Path):
    from v3_gateb1_metrics import FQNSnapshot, compare_fqn_inventory, compare_losses, compare_local_fast_state

    a = _tensor_data(source, source_dir=evidence_dir)
    b = _tensor_data(target, source_dir=evidence_dir)
    snap_fields = ("gradient", "master_before", "master_after", "m1_before", "m1_after", "m2_before", "m2_after")
    def full_inventory(d):
        return {name: FQNSnapshot(family=x["family"], shard_key=x["shard_key"],
                                  **{k: x[k] for k in snap_fields}) for name, x in d["fqn"].items()}
    def fast_states(d):
        return {str(slot): tuple(v[f"fast_{i}"] for i in range(4)) for slot, v in d["fast"].items()}

    comps = compare_fqn_inventory(full_inventory(a), full_inventory(b))
    scalar = compare_losses(a["losses"], b["losses"])
    fast = compare_local_fast_state(fast_states(a), fast_states(b))
    passed = all(c.passed for c in comps.values()) and all(scalar.values()) and all(
        m.passed for tensors in fast.values() for m in tensors)
    return {
        "candidate_only_pass": passed, "selected_fqn_count": len(comps),
        "fqn": {k: asdict(v) for k, v in comps.items()},
        "loss_components": scalar,
        "fast_state": {k: [asdict(m) for m in vec] for k, vec in fast.items()},
    }


def _load_report(folder: Path, *, leg: str, profile: str, repeat: int, rank: int, iteration: int):
    path = folder / f"{leg}_{profile}_repeat{repeat}" / f"rank{rank}_iter{iteration}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if Path(data.get("tensor_file", "")).name != f"rank{rank}_iter{iteration}.pt":
        raise CompareBlocked("paired tensor filename does not correspond to JSON")
    return data


def compare_complete_evidence(folder: Path, *, profiles=("P0_FIXED", "P1_MATCHED_STOCHASTIC"),
                              repeats=(0, 1)) -> dict[str, Any]:
    """All 4 Full/Terminal × P0/P1 cases and both reproducibility runs."""
    assert_numeric_policy_frozen()
    detailed = {}
    repeats_audit = {}
    for profile in profiles:
        seen = set()
        reports = {}
        for repeat in repeats:
            for rank in range(8):
                for iteration in (1301, 1302):
                    a = _load_report(folder, leg="index8", profile=profile,
                                     repeat=repeat, rank=rank, iteration=iteration)
                    b = _load_report(folder, leg="packed128", profile=profile,
                                     repeat=repeat, rank=rank, iteration=iteration)
                    case = validate_pair(a, b, rank=rank, iteration=iteration,
                                         profile=profile, repeat=repeat)
                    seen.add(case)
                    reports[("index8", repeat, rank, iteration)] = a
                    reports[("packed128", repeat, rank, iteration)] = b
                    label = f"{profile}/repeat{repeat}/rank{rank}/iter{iteration}"
                    detailed[label] = {"case": case, "numeric": _compare_numeric(a, b, evidence_dir=folder)}
        # Independent same-leg reproducibility: require the exact per-Consumer
        # stochastic/CFG input hashes to match across separate restart runs.
        if len(repeats) != 2:
            raise CompareBlocked("B1 requires two independently restarted witness repeats")
        for leg in ("index8", "packed128"):
            for rank in range(8):
                for iteration in (1301, 1302):
                    a = reports[(leg, repeats[0], rank, iteration)]
                    b = reports[(leg, repeats[1], rank, iteration)]
                    if (canonical_consumers(a) != canonical_consumers(b) or
                        any(canonical_site_witnesses(a, field) != canonical_site_witnesses(b, field)
                            for field in ("model_site_witnesses", "cfg_transform_witnesses"))):
                        raise CompareBlocked(f"{leg}/rank{rank}/iter{iteration}: run-to-run source/stochastic drift")
                    repeats_audit[f"{profile}/{leg}/rank{rank}/iter{iteration}"] = _compare_numeric(a, b, evidence_dir=folder)
        if seen != {"full", "terminal_partial"}:
            raise CompareBlocked(f"{profile}: actual full AND terminal-partial window coverage missing: {sorted(seen)}")
    return {
        "schema": "psm_v3_b1_complete_candidate_comparison_v1",
        "status": "OWNER_FROZEN_R2_NUMERIC_EVIDENCE_ONLY_GPU_GATE_NOT_APPROVED",
        "numeric_policy_sha256": FROZEN_NUMERIC_POLICY_SHA256,
        "numeric_thresholds_owner_frozen": True,
        "gpu_gate_approved": False,
        "profiles": list(profiles), "repeats": list(repeats),
        "pair_count": len(detailed),
        "all_candidate_thresholds_pass": (
            all(x["numeric"]["candidate_only_pass"] for x in detailed.values())
            and all(x["candidate_only_pass"] for x in repeats_audit.values())
        ),
        "per_rank_step": detailed, "same_leg_repeat_audit": repeats_audit,
    }


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence-dir", type=Path, required=True)
    p.add_argument("--output-report", type=Path, required=True)
    args = p.parse_args(argv)
    if args.output_report.exists():
        raise CompareBlocked("comparison JSON output already exists; no overwrites")
    if args.output_report.resolve().is_relative_to(args.evidence_dir.resolve()) is False:
        raise CompareBlocked("comparison report must remain inside evidence directory")
    result = compare_complete_evidence(args.evidence_dir)
    args.output_report.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    print(json.dumps({k: v for k, v in result.items() if k != "per_rank_step"}, sort_keys=True))


if __name__ == "__main__":
    main()
