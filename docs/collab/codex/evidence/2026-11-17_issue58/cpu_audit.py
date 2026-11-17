"""Own CPU evidence only. No private data, model load or source acceptance bypass."""

from __future__ import annotations

import hashlib
import importlib.metadata as md
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(os.environ["ISSUE58_AUDIT_OUT"])


def save(name, value):
    (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def sources():
    paths = sorted(
        p
        for root in ("g2", "tools/g2", "scripts/g2")
        for p in Path(root).rglob("*")
        if p.is_file()
        and p.suffix in (".py", ".js", ".html", ".css", ".json", ".sh")
        and "__pycache__" not in p.parts
    )
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def cases(path):
    return {
        (c.attrib["classname"], c.attrib["name"])
        for c in ET.parse(path).iter("testcase")
    }


def main():
    if sys.argv[1] == "before":
        save("source_before.json", sources())
        packages = {}
        for name in (
            "numpy",
            "Pillow",
            "torch",
            "pytest",
            "ruff",
            "pandas",
            "pyarrow",
            "mujoco",
        ):
            try:
                packages[name] = md.version(name)
            except md.PackageNotFoundError:
                packages[name] = None
        save(
            "environment.json",
            dict(
                python=sys.version,
                executable=sys.executable,
                platform=platform.platform(),
                packages=packages,
                worktree_parent_head=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                GPU_used=False,
                new_environment=False,
                packages_installed=False,
                network_during_tests=False,
                test_temp=os.environ["ISSUE58_TEST_TEMP"],
                source_kind="WORKTREE_HASHES_NOT_FORMAL_COMMIT_CLAIM",
            ),
        )
        return
    before = json.loads((OUT / "source_before.json").read_text())
    after = sources()
    save("source_after.json", after)
    assert before == after
    results = {}
    base = Path("docs/collab/codex/evidence/2026-11-17_issue54_a2/revision1")
    for name in ("pr53", "stage_a", "related", "one_shot"):
        root = ET.parse(OUT / (name + ".xml"))
        results[name] = {
            k: sum(int(s.attrib[k]) for s in root.iter("testsuite"))
            for k in ("tests", "failures", "errors", "skipped")
        }
        results[name]["skipped_cases"] = [
            dict(
                id=c.attrib["classname"] + "::" + c.attrib["name"],
                reason=c.find("skipped").attrib.get("message"),
            )
            for c in root.iter("testcase")
            if c.find("skipped") is not None
        ]
        assert results[name]["failures"] == results[name]["errors"] == 0
        if name != "one_shot":
            missing = cases(base / (name + ".xml")) - cases(OUT / (name + ".xml"))
            assert not missing, (name, missing)
            results[name].update(
                baseline_identities=len(cases(base / (name + ".xml"))),
                missing_identities=[],
            )
    assert (
        sum(results[n]["baseline_identities"] for n in ("pr53", "stage_a", "related"))
        == 478
    )
    assert results["one_shot"]["skipped"] == 0 and results["pr53"]["tests"] == 283
    protected = [
        "g2/latent_cache/encoding.py",
        "g2/latent_cache/contract.py",
        "g2/latent_cache/source.py",
        "g2/latent_cache/builder.py",
        "g2/latent_cache/storage.py",
        "g2/latent_cache/production.py",
        "tools/g2/build_spatial_view_vae_cache.py",
        "tools/g2/verify_spatial_view_vae_cache.py",
        "g2/offline/language_context.py",
        "g2/offline/task_entities.py",
        "cosmos-framework",
    ]
    subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            "4ad0fe7394cb62c4b5692fecaf6ce52963b8852c",
            "--",
            *protected,
        ],
        check=True,
        capture_output=True,
    )
    child = subprocess.check_output(
        ["git", "-C", "cosmos-framework", "rev-parse", "HEAD"], text=True
    ).strip()
    assert child == "d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2"
    assert not subprocess.check_output(
        ["git", "-C", "cosmos-framework", "status", "--porcelain"], text=True
    )
    probe = Path(
        "docs/collab/chatgpt/evidence/2026-11-17_issue54_27ccadb0/test_review_source_contracts.py"
    )
    assert (
        hashlib.sha256(probe.read_bytes()).hexdigest()
        == "860424fa81b6447cb361d7272ff0a365dfef6ef6087b0a3f51ab97f63fd306e0"
    )
    temp = Path(os.environ["ISSUE58_TEST_TEMP"]) / "cases"
    stress = list(temp.rglob("stress_receipt.json"))
    assert len(stress) == 1
    stress = json.loads(stress[0].read_text())
    save("sqlite_stress.json", stress)
    case_roots = [
        p for p in temp.glob("test_one_run_stop_resume_real_*") if not p.is_symlink()
    ]
    run = [p / "run_root/result.json" for p in case_roots]
    assert len(run) == 1
    run = json.loads(run[0].read_text())
    assert run["complete"] and run["phase"] == "DONE" and not run["training_ready"]
    save(
        "synthetic_supervisor_result.json",
        dict(scope="CPU_TEST_ONLY_FAKE_RENDER_AND_ENCODER", result=run),
    )
    receipts = [
        p
        for case in case_roots
        for p in (case / "spool_root/completed").glob("*/*.json")
    ]
    assert len(receipts) == 1
    save(
        "synthetic_completed_tombstone.json",
        dict(
            scope="CPU_TEST_ONLY_NOT_REAL_VAE_ACCEPTANCE",
            receipt=json.loads(receipts[0].read_text()),
        ),
    )
    save(
        "gate.json",
        dict(
            schema="g2_issue58_author_cpu_v1",
            results=results,
            source_count=len(before),
            source_hashes_stable=True,
            child_gitlink=child,
            original_478_identities_retained=True,
            original_a1_probes_sha256=hashlib.sha256(probe.read_bytes()).hexdigest(),
            original_a1_probes_execution="NOT_RUN_LOCAL_MISSING_PYARROW_PRIOR_GPT_RESULT_PRESERVED",
            changed_legacy_assertion="same test ID: private retained SQL rows -> durable completed receipt plus zero active rows",
            sqlite_stress=stress,
            training_ready=False,
            not_run=[
                "real F27/Wan/GPU sample",
                "real render-only/render+VAE A/B/resource peaks",
                "full9126 production",
                "old-view deletion",
                "P1 microbatch",
                "state15",
                "joint alignment",
                "training",
                "merge",
            ],
        ),
    )


if __name__ == "__main__":
    main()
