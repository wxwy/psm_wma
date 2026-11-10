"""Reduce existing profiler records on-server; export derived statistics only.

This does not run a model. Kernel work sums and timeline unions are separate;
inclusive CPU durations cannot be added to GPU work or called saved latency.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def union_us(events):
    intervals = sorted((e["ts"], e["ts"] + e["dur"]) for e in events)
    end = float("-inf")
    total = 0.0
    for start, stop in intervals:
        total += max(0, stop - max(start, end))
        end = max(end, stop)
    return total


def quantile(values, p):
    values = sorted(values)
    i = (len(values) - 1) * p
    lo = int(i)
    return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (i - lo)


def summary(events):
    durations = [e["dur"] for e in events]
    if not durations:
        return dict(count=0, work_sum_ms=0, timeline_union_ms=0)
    return dict(
        count=len(events),
        work_sum_ms=sum(durations) / 1000,
        timeline_union_ms=union_us(events) / 1000,
        per_event_p50_us=quantile(durations, 0.5),
        per_event_p95_us=quantile(durations, 0.95),
    )


def classify(name):
    if "prepare_varlen_num_blocks_kernel" in name:
        return "flash_varlen_prepare"
    if "CollectiveMainloopFwdSm90" in name:
        match = re.search(r"cutlass::arch::Sm90,\s*(true|false),", name)
        if match:
            return "flash_sm90_causal" if match[1] == "true" else "flash_sm90_noncausal"
        return "unclassified_flash_sm90"
    if name.startswith("triton_") and "_flash_attn_forward" in name:
        return "fused_flash_pre_post_not_exclusively_unused_work"
    if "fmha_" in name:
        return "other_fmha"
    return "other_kernel"


def reduce_trace(path):
    digest = sha(path)
    data = json.loads(path.read_text())
    events = [e for e in data["traceEvents"] if e.get("ph") == "X" and "dur" in e]
    kernels = [e for e in events if e.get("cat") == "kernel"]
    groups = defaultdict(list)
    for e in kernels:
        groups[classify(e["name"])].append(e)
    cpu = defaultdict(list)
    for e in events:
        name = e.get("name", "")
        if e.get("cat") in ("cpu_op", "cuda_runtime") and (
            "flash_attn" in name.lower()
            or name in ("cudaLaunchKernel", "cudaLaunchKernelExC")
        ):
            cpu[name].append(e)
    assert digest == sha(path), "profiler source changed during reduction"
    return dict(
        file=path.name,
        bytes=path.stat().st_size,
        sha256=digest,
        categories=dict(Counter(e.get("cat", "") for e in events)),
        all_kernel=summary(kernels),
        gpu_groups={k: summary(v) for k, v in sorted(groups.items())},
        cpu_inclusive_not_self_time={k: summary(v) for k, v in sorted(cpu.items())},
        source_unchanged=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "immutable output; choose a new destination"
    counts_path = args.input_dir / "kernel_counts.json"
    counts_hash = sha(counts_path)
    counts = json.loads(counts_path.read_text())
    result = dict(
        status="DERIVED_EXISTING_SYNTHETIC_TRACE_NOT_REAL_INPUT_GATE",
        layers=28,
        denoise_steps=30,
        cache_hit_layer_executions=28 * 29,
        kernel_counts_sha256=counts_hash,
        modes={},
    )
    for mode in ("baseline", "optimized"):
        row = reduce_trace(args.input_dir / ("profile_" + mode + ".json"))
        expected = Counter()
        for name, count in counts[mode].items():
            expected[classify(name)] += count
        for group in (
            "flash_varlen_prepare",
            "flash_sm90_causal",
            "flash_sm90_noncausal",
        ):
            assert row["gpu_groups"][group]["count"] == expected[group]
        assert expected["flash_sm90_causal"] == 28
        assert expected["flash_sm90_noncausal"] == 840
        assert expected["flash_varlen_prepare"] == 868
        row["kernel_count_crosscheck"] = True
        result["modes"][mode] = row
    assert sha(counts_path) == counts_hash
    with args.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
