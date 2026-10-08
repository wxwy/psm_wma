#!/usr/bin/env python3
"""Audit Round-3 per-window Encode1/Encode17/cache parity counts.

Read-only on original evidence; an optional separate JSON report is written.
Explicitly supports both original unprefixed comparisons and DS_PRO's
feature-prefixed ``z0_A_vs_B``/``visual96_A_vs_B`` schema.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "psm_v3_round3_parity_count_audit_v2"
_COMPARISONS = ("A_vs_B", "A_vs_C", "B_vs_C")
_FEATURES = ("z0", "visual96")
_ALIASES = {
    "A_vs_B": ("A_vs_B", "a_vs_b", "A/B", "a_b", "cache_vs_encode17"),
    "A_vs_C": ("A_vs_C", "a_vs_c", "A/C", "a_c", "cache_vs_encode1"),
    "B_vs_C": ("B_vs_C", "b_vs_c", "B/C", "b_c", "encode17_vs_encode1"),
}


class EvidenceError(ValueError):
    """Missing, malformed, or contradictory per-window evidence."""


def _metric(value: Mapping[str, Any], name: str, identity: tuple[str, int, int]) -> tuple[bool, float]:
    if "metrics" in value and isinstance(value["metrics"], Mapping):
        value = value["metrics"]
    exact = value.get("exact_equal", value.get("exact"))
    max_abs = value.get("max_abs")
    if type(exact) is not bool or isinstance(max_abs, bool) or not isinstance(max_abs, (float, int)):
        raise EvidenceError(f"{identity}: {name} requires exact_equal and max_abs")
    max_abs = float(max_abs)
    if not math.isfinite(max_abs) or max_abs < 0.0:
        raise EvidenceError(f"{identity}: {name} max_abs is invalid")
    if exact != (max_abs == 0.0):
        raise EvidenceError(f"{identity}: {name} exact_equal contradicts max_abs")
    return exact, max_abs


def _field(
    comparisons: Mapping[str, Any], name: str, feature: str, identity: tuple[str, int, int]
) -> tuple[bool, float]:
    """Prefer explicit feature-qualified keys; never use z0 metrics for visual96."""
    if feature not in _FEATURES:
        raise EvidenceError(f"unknown feature {feature}")
    aliases = _ALIASES[name]
    candidates: list[tuple[str, Mapping[str, Any]]] = []
    nested = comparisons.get(feature)
    if isinstance(nested, Mapping):
        for key in aliases:
            value = nested.get(key)
            if isinstance(value, Mapping):
                candidates.append((f"{feature}.{key}", value))
    for key in (f"{feature}_{alias}" for alias in aliases):
        value = comparisons.get(key)
        if isinstance(value, Mapping):
            candidates.append((key, value))
    if feature == "z0":
        for key in aliases:
            value = comparisons.get(key)
            if isinstance(value, Mapping):
                candidates.append((key, value))
    if not candidates:
        raise EvidenceError(f"{identity}: missing {feature}_{name} comparison")
    records = [_metric(value, key, identity) for key, value in candidates]
    if any(metric != records[0] for metric in records[1:]):
        raise EvidenceError(f"{identity}: conflicting comparison aliases {feature}_{name}")
    return records[0]


def _identity(row: Mapping[str, Any]) -> tuple[str, int, int]:
    task = row.get("task_class", row.get("task"))
    episode = row.get("episode_index", row.get("episode"))
    start = row.get("start_frame", row.get("start"))
    if not isinstance(task, str) or not task.strip():
        raise EvidenceError("missing/non-string task_class")
    if type(episode) is not int or episode < 0 or type(start) is not int or start < 0:
        raise EvidenceError("missing/invalid episode_index or start_frame")
    return task, episode, start


def audit(
    payload: Mapping[str, Any], claimed: Mapping[str, int] | None = None, *, feature: str = "z0"
) -> dict[str, Any]:
    if feature not in _FEATURES:
        raise EvidenceError(f"unsupported feature {feature!r}")
    windows = payload.get("windows", payload.get("records"))
    if not isinstance(windows, list) or not windows:
        raise EvidenceError("expected nonempty windows/records list with per-window comparisons")
    counts = {key: {"exact": 0, "non_exact": 0, "max_abs": 0.0} for key in _COMPARISONS}
    non_exact: dict[str, list[dict[str, Any]]] = {key: [] for key in _COMPARISONS}
    seen: set[tuple[str, int, int]] = set()
    for row in windows:
        if not isinstance(row, Mapping):
            raise EvidenceError("each window entry must be an object")
        identity = _identity(row)
        if identity in seen:
            raise EvidenceError(f"duplicate window identity {identity}")
        seen.add(identity)
        comparisons = row.get("comparisons", row)
        if not isinstance(comparisons, Mapping):
            raise EvidenceError(f"{identity}: comparisons must be a mapping")
        metrics = {name: _field(comparisons, name, feature, identity) for name in _COMPARISONS}
        # If B == C, the differences A-B and A-C must be identical.
        if metrics["B_vs_C"][0] and metrics["A_vs_B"] != metrics["A_vs_C"]:
            raise EvidenceError(f"{identity}: B_vs_C exact but A_vs_B / A_vs_C mismatch")
        for name, (exact, mx) in metrics.items():
            counts[name]["exact" if exact else "non_exact"] += 1
            counts[name]["max_abs"] = max(counts[name]["max_abs"], mx)
            if not exact:
                non_exact[name].append({
                    "task_class": identity[0], "episode_index": identity[1],
                    "start_frame": identity[2], "max_abs": mx,
                })
    mismatches = []
    for name, count in (claimed or {}).items():
        if name not in _COMPARISONS or type(count) is not int or count < 0:
            raise EvidenceError(f"invalid claimed count {name!r}={count!r}")
        observed = counts[name]["non_exact"]
        if observed != count:
            mismatches.append({"comparison": name, "claimed_non_exact": count, "actual_non_exact": observed})
    return {
        "schema": SCHEMA, "feature": feature,
        "status": "PASS" if not mismatches else "FAIL",
        "total_windows": len(windows), "comparison_counts": counts,
        "non_exact_windows": non_exact, "claimed_count_mismatches": mismatches,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="Separate report JSON; original evidence never overwritten")
    parser.add_argument("--feature", choices=_FEATURES, default="z0")
    parser.add_argument("--claimed-a-b-non-exact", type=int)
    parser.add_argument("--claimed-a-c-non-exact", type=int)
    parser.add_argument("--claimed-b-c-non-exact", type=int)
    args = parser.parse_args(argv)
    if args.output is not None and args.input.resolve() == args.output.resolve():
        parser.error("output must not overwrite evidence input")
    claimed = {name: count for name, count in {
        "A_vs_B": args.claimed_a_b_non_exact,
        "A_vs_C": args.claimed_a_c_non_exact,
        "B_vs_C": args.claimed_b_c_non_exact,
    }.items() if count is not None}
    try:
        result = audit(json.loads(args.input.read_text(encoding="utf-8")), claimed, feature=args.feature)
        report = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(report)
        print(report, end="")
        return 0 if result["status"] == "PASS" else 1
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ROUND3_AUDIT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
