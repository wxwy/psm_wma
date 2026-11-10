"""Publish derived scalars/hashes only. All raw server evidence stays private."""

import hashlib
import json
from pathlib import Path
import subprocess

BASE = Path(
    "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue35_kv_hit_parity_20261110"
)
OLD = BASE.parent / "_codex_issue31_prefix_pack_20261109/root2"


def load(path):
    return json.loads(path.read_text())


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            digest.update(block)
    return digest.hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def compare_summary(row):
    return dict(
        all_equal=row["all_equal"],
        tensors={
            name: {k: value[k] for k in ("equal", "max_abs")}
            for name, value in row["tensors"].items()
        },
    )


def main():
    result = dict(
        privacy="Derived scalars/schema/hashes only; no raw tensors, logs, frames, generated code or checkpoint exported",
        independent_approval="NOT_CLAIMED",
        performance_claim="NONE",
        original_identity=dict(
            root=git(OLD, "rev-parse", "HEAD"),
            child=git(OLD / "cosmos-framework", "rev-parse", "HEAD"),
            root_status=git(OLD, "status", "--porcelain"),
            child_status=git(OLD / "cosmos-framework", "status", "--porcelain"),
        ),
        original_probe=[],
    )
    for k in (1, 16):
        path = BASE / f"probe03/k{k}/first_hit_probe/probe_result.json"
        probe = load(path)
        rows = probe["native_und_cache_comparisons"]
        result["original_probe"].append(
            dict(
                k=k,
                status=probe["status"],
                report_sha256=sha(path),
                modes_match_independent={
                    name: row["all_equal"]
                    for name, row in probe["final_outputs_match_independent"].items()
                },
                native_und_static_layers=sum(
                    row["full_step0_vs_full_step1"]["all_equal"] for row in rows
                ),
                cached_und_exact_layers=sum(
                    row["full_step1_vs_cached_read"]["all_equal"] for row in rows
                ),
                layers=len(rows),
                first_gen_difference=next(
                    row
                    for row in probe["layer_differences"]
                    if not row["gen_output_equal"]
                ),
            )
        )
    result["operands"] = {}
    for label in ("operands04", "operands05"):
        path = BASE / label / "k1/operand_probe/result.json"
        value = load(path)
        result["operands"][label] = dict(
            status=value["status"],
            report_sha256=sha(path),
            nonperturbing=value["nonperturbing"],
            layer_checks=[
                {
                    key: row[key]
                    for key in (
                        "k",
                        "layer",
                        "mode",
                        "output_matches_whole_generation",
                        "attention_recorded",
                    )
                }
                for row in value["layer_checks"]
            ],
            comparisons={
                key: compare_summary(row)
                for key, row in value["attention_comparisons"].items()
            },
            normalization_parameters=value.get("normalization_parameters", {}),
            final_modes_match_independent={
                name: row["all_equal"]
                for name, row in value["final_outputs_match_independent"].items()
            },
        )
    path = BASE / "key_partition01.json"
    result["key_partition"] = dict(report_sha256=sha(path), **load(path))
    result["author_h100"] = {}
    for label in ("author_h10001", "author_h10002"):
        directory = BASE / label
        gate = load(directory / "gate.json")
        before, after = (
            load(directory / "source_before.json"),
            load(directory / "source_after.json"),
        )
        row = dict(
            status=gate["status"],
            error=gate.get("error"),
            shell_exit=load(BASE / (label + ".exit.json"))["shell_exit"],
            gate_sha256=sha(directory / "gate.json"),
            source_before_sha256=sha(directory / "source_before.json"),
            source_after_sha256=sha(directory / "source_after.json"),
            identity=before["identity"],
            source_files=len(before["files"]),
            source_unchanged=gate["source_unchanged"] and before == after,
            protected_inputs_unchanged=gate.get("protected_inputs_unchanged", False),
            model=gate.get("model"),
            cases=[],
        )
        for case in gate["cases"]:
            summary = dict(
                k=case["k"],
                source_step=case["source_step"],
                ordinary={
                    name: compare_summary(value)
                    for name, value in case["ordinary"].items()
                },
                observer_nonperturbing={
                    name: value["all_equal"] for name, value in case["observed"].items()
                },
                velocity={},
            )
            for name, values in case["velocity"].items():
                summary["velocity"][name] = dict(
                    steps=len(values),
                    all_equal=all(value["all_equal"] for value in values),
                    per_step_max_abs=[
                        max(tensor["max_abs"] for tensor in value["tensors"].values())
                        for value in values
                    ],
                )
            if "stage1_vs_stage2" in case:
                summary["stage1_vs_stage2"] = compare_summary(case["stage1_vs_stage2"])
            row["cases"].append(summary)
        result["author_h100"][label] = row
    directories = [
        BASE / name
        for name in (
            "probe01",
            "probe02",
            "probe03",
            "operands01",
            "operands02",
            "operands03",
            "operands04",
            "operands05",
            "author_h10001",
            "author_h10002",
        )
    ]
    paths = {
        path
        for directory in directories
        if directory.is_dir()
        for path in directory.rglob("*")
        if path.is_file()
    }
    paths.update(
        path
        for path in BASE.iterdir()
        if path.is_file() and path.suffix in (".py", ".log", ".json")
    )
    inventory = {
        str(path.relative_to(BASE)): dict(bytes=path.stat().st_size, sha256=sha(path))
        for path in sorted(paths)
    }
    manifest = BASE / "private_evidence_index01.json"
    with manifest.open("x") as stream:
        json.dump(inventory, stream, indent=2)
        stream.write("\n")
    result["private_evidence_index"] = dict(
        path=str(manifest),
        files=len(inventory),
        sha256=sha(manifest),
        raw_files_exported=False,
    )
    result["gpu_after"] = subprocess.check_output(
        [
            "nvidia-smi",
            "--id=4,5,6,7",
            "--query-gpu=index,memory.used,utilization.gpu",
            "--format=csv,noheader",
        ],
        text=True,
    ).splitlines()
    result["gpu6_compute_pids_after"] = subprocess.check_output(
        [
            "nvidia-smi",
            "--id=6",
            "--query-compute-apps=pid",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    ).splitlines()
    output = BASE / "public_derived_summary01.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("PUBLIC_DERIVED_JSON " + json.dumps(result, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
