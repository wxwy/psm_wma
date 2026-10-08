#!/usr/bin/env python3
"""Audit reported Round-3 Encode1 parity counts against per-window JSON facts.

This tool never changes an evidence file or substitutes a summary for missing rows.
It deliberately rejects unfamiliar schemas rather than guessing field locations.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "psm_v3_round3_parity_count_audit_v1"
_COMPARISONS = ("A_vs_B", "A_vs_C", "B_vs_C")
_ALIASES = {
    "A_vs_B": ("A_vs_B", "a_vs_b", "A/B", "a_b", "cache_vs_encode17"),
    "A_vs_C": ("A_vs_C", "a_vs_c", "A/C", "a_c", "cache_vs_encode1"),
    "B_vs_C": ("B_vs_C", "b_vs_c", "B/C", "b_c", "encode17_vs_encode1"),
}


class EvidenceError(ValueError):
    """An evidence record is missing, contradictory, or malformed."""


def _field(container: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    for key in _ALIASES[name]:
        value = container.get(key)
        if isinstance(value, Mapping):
            return value
    raise EvidenceError(f"missing comparison {name}")


def _identity(row: Mapping[str, Any]) -> tuple[str, int, int]:
    task = row.get("task_class", row.get("task"))
    episode = row.get("episode_index", row.get("episode"))
    start = row.get("start_frame", row.get("start"))
    if not isinstance(task, str) or not task.strip():
        raise EvidenceError("missing/non-string task_class")
    if type(episode) is not int or episode < 0 or type(start) is not int or start < 0:
        raise EvidenceError("missing/invalid episode_index or start_frame")
    return task, episode, start


def _metric(value: Mapping[str, Any], name: str, identity: tuple[str, int, int]) -> tuple[bool, float]:
    # Accept the explicit pairwise metric object and reject contradictory flags.
    if "metrics" in value and isinstance(value["metrics"], Mapping):
        value = value["metrics"]
    exact = value.get("exact_equal", value.get("exact"))
    max_abs = value.get("max_abs")
    if type(exact) is not bool or isinstance(max_abs, bool) or not isinstance(max_abs, (int, float)):
        raise EvidenceError(f"{identity}: {name} must have exact_equal and max_abs")
    if not math.isfinite(max_abs) or max_abs < 0:
        raise EvidenceError(f"{identity}: {name} max_abs invalid")
    if exact != (max_abs == 0):
        raise EvidenceError(f"{identity}: {name} exact_equal contradicts max_abs")
    return exact, float(max_abs)


def audit(payload: Mapping[str, Any], claimed: Mapping[str, int] | None = None) -> dict[str, Any]:
    # Normalize only well-defined tables; do not infer counts from summary text.
    windows = payload.get("windows", payload.get("records"))
    if not isinstance(windows, list) or not windows:
        raise EvidenceError("expected a non-empty windows/records list of per-window comparisons")
    counts = {key: {"exact": 0, "non_exact": 0, "max_abs": 0.0} for key in _COMPARISONS}
    seen: set[tuple[str, int, int]] = set()
    non_exact: dict[str, list[dict[str, Any]]] = {key: [] for key in _COMPARISONS}
    for row in windows:
        if not isinstance(row, Mapping):
            raise EvidenceError("window entry must be an object")
        ident = _identity(row)
        if ident in seen:
            raise EvidenceError(f"duplicate window: {ident}")
        seen.add(ident)
        comparisons = row.get("comparisons", row)
        if not isinstance(comparisons, Mapping):
            raise EvidenceError(f"{ident}: comparisons must be a mapping")
        for name in _COMPARISONS:
            exact, mx = _metric(_field(comparisons, name), name, ident)
            counts[name]["exact" if exact else "non_exact"] += 1
            counts[name]["max_abs"] = max(counts[name]["max_abs"], mx)
            if not exact:
                non_exact[name].append({"task_class": ident[0], "episode_index": ident[1], "start_frame": ident[2], "max_abs": mx})
    for name in _COMPARISONS:
        if counts[name]["exact"] + counts[name]["non_exact"] != len(windows):
            raise AssertionError("count accounting error")
    mismatches = []
    for name, count in (claimed or {}).items():
        if name not in _COMPARISONS:
            raise EvidenceError(f"unknown comparison in claimed counts: {name}")
        if type(count) is not int or count < 0:
            raise EvidenceError(f"invalid claimed count for {name}")
        if counts[name]["non_exact"] != count:
            mismatches.append({"comparison": name, "claimed_non_exact": count, "actual_non_exact": counts[name]["non_exact"]})
    return {
        "schema": SCHEMA,
        "status": "PASS" if not mismatches else "FAIL",
        "total_windows": len(windows),
        "comparison_counts": counts,
        "non_exact_windows": non_exact,
        "claimed_count_mismatches": mismatches,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Raw per-window JSON evidence")
    parser.add_argument("--output", type=Path, help="Optional separate audit JSON; never overwrites input")
    parser.add_argument("--claimed-a-b-non-exact", type=int)
    parser.add_argument("--claimed-a-c-non-exact", type=int)
    parser.add_argument("--claimed-b-c-non-exact", type=int)
    args = parser.parse_args(argv)
    if args.output is not None and args.input.resolve() == args.output.resolve():
        parser.error("output must not overwrite evidence input")
    claimed = {
        key: value for key, value in {
            "A_vs_B": args.claimed_a_b_non_exact,
            "A_vs_C": args.claimed_a_c_non_exact,
            "B_vs_C": args.claimed_b_c_non_exact,
        }.items() if value is not None
    }
    try:
        content = json.loads(args.input.read_text(encoding="utf-8"))
        result = audit(content, claimed)
        output = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        print(output, end="")
        return 0 if result["status"] == "PASS" else 1
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ROUND3_AUDIT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
