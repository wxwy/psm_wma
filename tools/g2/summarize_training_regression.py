"""Summarize Issue #90 from its existing private logs without exporting rows."""

import argparse
import hashlib
import json
import statistics
from pathlib import Path

G2_RAW = (
    "g2_async8_benchmark_20261119/psm_wma_v3/corrected_phase5/r1_g2_bench_solo_20261119"
)
G2_SYNC = "g2_formal_20261119/psm_wma_v3/corrected_phase5/r1_g2_formal_30000_20261119"
NO_TTT = "no_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/no_ttt_packed128_droid_fresh_30k_world4_ga4"
G1 = "local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019"
WINDOWS = {
    "g2_raw8": (G2_RAW, 1, 10),
    "g2_sync_matched": (G2_SYNC, 1, 10),
    "g2_sync_steady": (G2_SYNC, 40, 49),
    "no_ttt": (NO_TTT, 29991, 30000),
    "g1_local": (G1, 27696, 27705),
}
SECONDS = (
    "step_wall_ms",
    "data_prepare_ms",
    "data_wait_ms",
    "batch_collate_ms",
    "batch_transfer_ms",
    "local_scan_ms",
    "forward_ms",
    "backward_ms",
    "optimizer_ms",
    "other_host_overhead_ms",
    "gpu_data_stall_ms",
    "batch_transfer_cuda_event_ms",
    "local_scan_cuda_event_ms",
    "forward_cuda_event_ms",
    "backward_cuda_event_ms",
    "optimizer_cuda_event_ms",
)
LOADER_STAGES = (
    "raw_wait_host_ms",
    "collate_host_ms",
    "transform_host_ms",
    "source_read_ms",
    "worker_source_ms_sum",
    "worker_transform_ms_sum",
    "main_decode_cfg_ms",
)


def statistics_for(rows, name, divisor=1):
    values = [
        row[name] / divisor for row in rows if type(row.get(name)) in (int, float)
    ]
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "p50": statistics.median(values),
        "min": min(values),
        "max": max(values),
    }


def training_rows(output, name, start, end):
    path = output / name / "monitor/train_rank0.jsonl"
    digest = hashlib.sha256()
    result = {}
    with path.open("rb") as stream:
        for line in stream:
            digest.update(line)
            row = json.loads(line)
            iteration = row.get("iteration")
            if (
                row.get("status") != "optimizer_committed"
                or type(iteration) is not int
                or not start <= iteration <= end
            ):
                continue
            if iteration in result:
                raise ValueError(f"{name}: duplicate committed iteration {iteration}")
            result[iteration] = row
    if sorted(result) != list(range(start, end + 1)):
        raise ValueError(f"{name}: incomplete committed iteration coverage")
    return result, digest.hexdigest()


def loader_rows(output):
    paths = list(
        output.glob(
            "no_ttt_robocasa_raw15/_launch_logs/*/"
            "launch_1793430750568591122_u56ot0_1.log"
        )
    )
    if len(paths) != 1:
        raise ValueError("expected the fixed final No-TTT launch log")
    marker = "[NoTTT][cpu_loader] "
    decoder = json.JSONDecoder()
    rows = {}
    uncovered_lines = 0
    with paths[0].open(errors="replace") as stream:
        for line in stream:
            for segment in line.split(marker)[1:]:
                try:
                    row, _ = decoder.raw_decode(segment.lstrip())
                except ValueError:
                    uncovered_lines += 1
                    continue
                if row.get("rank") == 0 and 29991 <= row.get("iteration", -1) <= 30000:
                    rows[row["iteration"]] = row
    if len(rows) != 10:
        raise ValueError("missing Rank0 No-TTT loader samples")
    return {
        "schema": rows[30000]["schema"],
        "execution": rows[30000]["execution"],
        "profile": rows[30000]["loader_profile"],
        "steps": sorted(rows),
        "undecodable_fragments_any_rank": uncovered_lines,
        "milliseconds": {
            key: statistics_for(rows.values(), key) for key in LOADER_STAGES
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outputs", type=Path)
    args = parser.parse_args()
    views = {}
    rows = {}
    for group, (name, start, end) in WINDOWS.items():
        group_rows, digest = training_rows(args.outputs, name, start, end)
        rows[group] = group_rows
        views[group] = {
            "input_sha256": digest,
            "iterations": sorted(group_rows),
            "seconds": {
                m: statistics_for(group_rows.values(), m, 1000) for m in SECONDS
            },
            "pipeline": group_rows[end]["data_pipeline_execution"],
            "cpu_timing_scope": group_rows[end]["cpu_timing_scope"],
            "cuda_samples": [
                i for i, row in group_rows.items() if row.get("cuda_sampled")
            ],
            "rank_scope": group_rows[end]["rank_scope"],
        }
    raw, sync = rows["g2_raw8"], rows["g2_sync_matched"]
    result = {
        "windows": views,
        "matched_consumer_sha_steps": sum(
            bool(raw[i].get("actual_consumer_identity_sha256"))
            and raw[i]["actual_consumer_identity_sha256"]
            == sync[i].get("actual_consumer_identity_sha256")
            for i in raw.keys() & sync.keys()
        ),
        "no_ttt_runtime": loader_rows(args.outputs),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
