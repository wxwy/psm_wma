#!/usr/bin/env python3
"""Summarize archived v2 evidence; no PyTorch, GPU, model, or server access.

This reads recorded summaries, not original gradient tensors. It cannot produce a
new numerical-parity verdict or recover censored per-parameter statistics.
"""

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_SHA256 = {
    0: "10ff7564e70d2d726ea3510202ba0d0a11d4602ce8618534cf345d239d0c6748",
    1: "1bf095cbb5803a4fd3b96ba335bba850994f50935fd6dfc5eba600d47a375260",
    2: "f72b61abd6ccd8df402d3cde8412f5e0bb0daa5247bf0f51362da6df4e21cd08",
    3: "132c81ec536a981d04c62fee867d2b63943169b7e51fcd07397970f2807ac4a0",
}
SIDES = ("dense0a", "dense0b", "compact1")
COMPARISONS = ("intrinsic_noise", "compact_effect")


def file_identity(path):
    data = path.read_bytes()
    return data, {
        "filename": path.name,
        "bytes": len(data),
        "lines": len(data.splitlines()),
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_blob_sha1": hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest(),
    }


def comparison_summary(item):
    worst = item["worst10"]
    groups = {
        name: {**v, "fail": v["covered"] - v["pass"]}
        for name, v in item["group_stats"].items()
    }
    if sum(v["covered"] for v in groups.values()) != item["common_params"]:
        raise ValueError("Group coverage does not match common-parameter count")
    if sum(v["fail"] for v in groups.values()) != item["failure_count"]:
        raise ValueError("Group failure total does not match recorded failure_count")
    return {
        "common_params": item["common_params"],
        "recorded_failure_count": item["failure_count"],
        "returned_failure_prefix_count": len(item["failures"]),
        "failure_list_censored": len(item["failures"]) < item["failure_count"],
        "reported_only_a": item["only_a"],
        "reported_only_b": item["only_b"],
        "max_abs_among_returned_worst10": max(x["max_abs"] for x in worst),
        "rel_l2_range_among_returned_worst10": [
            min(x["rel_l2"] for x in worst),
            max(x["rel_l2"] for x in worst),
        ],
        "recorded_group_counts": groups,
        "returned_worst10": worst,
    }


def analyze_rank(directory, rank):
    path = directory / f"v3_gpu_parity_rank{rank}_v2.json"
    raw, identity = file_identity(path)
    if identity["sha256"] != EXPECTED_SHA256[rank]:
        raise ValueError(f"SHA256 mismatch for rank {rank}")
    doc = json.loads(raw)
    if doc["rank"] != rank or doc["world_size"] != 4:
        raise ValueError(f"Rank/world identity mismatch in {path}")
    summaries = {key: comparison_summary(doc[key]) for key in COMPARISONS}
    prefixes = {key: set(doc[key]["failures"]) for key in COMPARISONS}
    dd, dc = (prefixes[key] for key in COMPARISONS)
    top = {
        key: {x["name"]: x for x in doc[key]["worst10"]}
        for key in COMPARISONS
    }
    matched = [
        {"name": name, "dense_dense": top["intrinsic_noise"][name],
         "dense_compact": top["compact_effect"][name]}
        for name in sorted(set(top["intrinsic_noise"]) & set(top["compact_effect"]))
    ]
    diagnostic = doc["diagnostic"]
    explicit_crossings = [
        row for row in diagnostic["worst_excess10"]
        if row["noise_ok"] and not row["compact_ok"]
    ]
    metadata = {}
    for side in SIDES:
        all_meta = doc[side]["grad_meta"]
        present = {name: m for name, m in all_meta.items() if m["dtype"] is not None}
        metadata[side] = {
            "recorded_grad_params": doc[side]["grad_params"],
            "metadata_count": len(all_meta),
            "metadata_with_gradient": len(present),
            "reported_gradient_dtypes": sorted({m["dtype"] for m in present.values()}),
            "all_present_gradients_report_dtensor": all(m["is_dtensor"] for m in present.values()),
            "loss": doc[side]["loss"],
            "weighted": doc[side]["weighted"],
        }
    return {
        "rank": rank,
        "source_identity": identity,
        "source_hash_matches_readme": True,
        "selected_params": doc["selected_params"],
        "requires_grad_counts": doc["requires_grad_counts"],
        "per_side_recorded_metadata": metadata,
        "loss_three_sides_equal": len({doc[s]["loss"] for s in SIDES}) == 1,
        "weighted_three_sides_equal": len({doc[s]["weighted"] for s in SIDES}) == 1,
        "comparisons": summaries,
        "returned_failure_prefix_overlap": {
            "warning": "Only each comparison's first 50 failures, not its full failure set.",
            "intersection_count": len(dd & dc),
            "dense_dense_prefix_only_count": len(dd - dc),
            "dense_compact_prefix_only_count": len(dc - dd),
            "dense_dense_prefix_only_names": sorted(dd - dc),
            "dense_compact_prefix_only_names": sorted(dc - dd),
        },
        "parameters_present_in_both_returned_worst10": matched,
        "recorded_all_param_diagnostic_summary": {
            key: value for key, value in diagnostic.items() if key != "worst_excess10"
        },
        "diagnostic_summary_independently_recomputable": False,
        "returned_worst_excess10": diagnostic["worst_excess10"],
        "explicit_noise_pass_compact_fail_in_returned_worst_excess10": explicit_crossings,
        "explicit_crossings_are_exhaustive": False,
        "original_formal_pass": doc["formal_pass"],
        "original_all_ranks_pass": doc["all_ranks_pass"],
        "original_verdict": doc["verdict"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ranks = [analyze_rank(args.input_dir, rank) for rank in range(4)]
    result = {
        "analysis_version": 1,
        "method": "Offline Python standard-library analysis of recorded v2 JSON summaries.",
        "raw_gradient_tensors_available": False,
        "gpu_or_project_code_executed": False,
        "ranks": ranks,
        "interpretation": {
            "original_strict_gate": "FAIL_PARITY",
            "baseline_repeatability": "DOES_NOT_MEET_FROZEN_ALLCLOSE",
            "compact_specific_causal_regression": "INCONCLUSIVE",
            "new_parity_pass_claim": False,
            "s2_permission_changed_by_this_analysis": False,
        },
        "limitations": [
            "No original gradients: allclose and gradient metrics cannot be independently recomputed.",
            "Only first 50 failure names and top 10 max-absolute-error metrics per comparison are serialized.",
            "Full failure-set overlap, per-element failure fraction, all-parameter relative-L2 distribution and cosine metrics are unavailable.",
            "worst10 is ordered by max_abs, not rel_l2; its relative-L2 range is a selected-subset statistic.",
            "max_abs values here are maxima among returned worst10. The harness sorts all per-parameter max_abs values, but finite gradients were not fully witnessed.",
            "Diagnostic excess_positive and ratio summaries originate from transient full per_param dictionaries that were not serialized; they are recorded, not independently recomputed.",
            "The harness excludes zero-noise denominators from ratio statistics and uses an upper-middle item, not an averaged middle pair, for even-count ratio_median.",
            "The harness defines rel_l2=0 when the reference gradient norm is zero, so that statistic alone is not a safe zero-gradient discrepancy check.",
            "Gradient metadata report float32 DTensor; this is not evidence that stored gradients are BF16, nor a proof of the source of execution variation.",
            "Four ranks and 294 tensors are correlated parts of one distributed triplet, not independent repeated experiments.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "all_source_hashes_match": all(x["source_hash_matches_readme"] for x in ranks),
        "ranks": [{
            "rank": x["rank"],
            "dd_fail": x["comparisons"]["intrinsic_noise"]["recorded_failure_count"],
            "dc_fail": x["comparisons"]["compact_effect"]["recorded_failure_count"],
            "dd_max_abs": x["comparisons"]["intrinsic_noise"]["max_abs_among_returned_worst10"],
            "dc_max_abs": x["comparisons"]["compact_effect"]["max_abs_among_returned_worst10"],
            "prefix_intersection": x["returned_failure_prefix_overlap"]["intersection_count"],
            "visible_threshold_crossings": len(x["explicit_noise_pass_compact_fail_in_returned_worst_excess10"]),
        } for x in ranks],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
