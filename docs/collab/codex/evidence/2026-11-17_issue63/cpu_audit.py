"""Bind complete old501/new cases, untouched numeric AST, and source hashes."""

from __future__ import annotations

import ast
import hashlib
import importlib.metadata as md
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(os.environ["ISSUE63_AUDIT_OUT"])
BASE = "d0bb45343a047fdf90d8e376acf4502fdf13fff4"


def save(name, value):
    (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def git(*args):
    return subprocess.check_output(["git", *args])


def sources():
    paths = sorted(
        p
        for root in ("g2", "tools/g2", "scripts/g2")
        for p in Path(root).rglob("*")
        if p.is_file()
        and p.suffix in (".py", ".json", ".sh", ".html", ".js", ".css")
        and "__pycache__" not in p.parts
    )
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def cases(path):
    return {
        (c.attrib["classname"], c.attrib["name"])
        for c in ET.parse(path).iter("testcase")
    }


def numeric_ast(text, name):
    return ast.dump(
        next(
            n
            for n in ast.parse(text).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name
        ),
        include_attributes=False,
    )


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
                worktree_parent_head=git("rev-parse", "HEAD").decode().strip(),
                GPU_used=False,
                server_access=False,
                new_environment=False,
                packages_installed=False,
                source_kind="WORKTREE_HASHES_NOT_FORMAL_COMMIT_AUTHORITY",
            ),
        )
        return
    before = json.loads((OUT / "source_before.json").read_text())
    after = sources()
    save("source_after.json", after)
    assert before == after
    previous = Path("docs/collab/codex/evidence/2026-11-17_issue58/revision2")
    results = {}
    for name in ("pr53", "stage_a", "related", "one_shot", "capsule"):
        root = ET.parse(OUT / (name + ".xml"))
        results[name] = {
            k: sum(int(s.attrib[k]) for s in root.iter("testsuite"))
            for k in ("tests", "failures", "errors", "skipped")
        }
        assert results[name]["failures"] == results[name]["errors"] == 0
        results[name]["skipped_cases"] = [
            dict(
                id=c.attrib["classname"] + "::" + c.attrib["name"],
                reason=c.find("skipped").attrib.get("message"),
            )
            for c in root.iter("testcase")
            if c.find("skipped") is not None
        ]
        if name != "capsule":
            expected = cases(previous / (name + ".xml"))
            if name == "one_shot":
                expected.add(
                    (
                        "g2.tests.test_one_shot_renderer_environment",
                        "test_gt_worker_inherits_renderer_dependencies_and_consumer_does_not",
                    )
                )
            assert not expected - cases(OUT / (name + ".xml")), (
                name,
                expected - cases(OUT / (name + ".xml")),
            )
            results[name].update(
                original_identities=len(expected), missing_identities=[]
            )
    assert (
        sum(
            results[n]["original_identities"]
            for n in ("pr53", "stage_a", "related", "one_shot")
        )
        == 501
    )
    assert results["capsule"]["skipped"] == 0 and results["pr53"]["tests"] == 283
    baseline_tests = [
        p
        for p in git("ls-tree", "-r", "--name-only", BASE, "--", "g2/tests")
        .decode()
        .splitlines()
        if "/test_" in p and p.endswith(".py")
    ]
    unchanged_tests = []
    for path in baseline_tests:
        assert Path(path).read_bytes() == git("show", BASE + ":" + path), path
        unchanged_tests.append(path)
    protected = [
        "g2/latent_cache/encoding.py",
        "g2/latent_cache/contract.py",
        "g2/offline/task_entities.py",
        "g2/offline/language_context.py",
        "g2/offline/spatial_metadata.py",
        "g2/offline/episode.py",
        "g2/offline/atomic_6views_run.py",
        "g2/views/render_connections.py",
        "tools/g2/build_spatial_view_vae_cache.py",
        "tools/g2/verify_spatial_view_vae_cache.py",
        "cosmos-framework",
    ]
    assert not git("diff", "--name-only", BASE, "--", *protected)
    old = numeric_ast(
        git("show", BASE + ":g2/latent_cache/builder.py").decode(), "encode_record"
    )
    new = numeric_ast(Path("g2/latent_cache/builder.py").read_text(), "encode_record")
    assert old == new
    child = git("-C", "cosmos-framework", "rev-parse", "HEAD").decode().strip()
    assert child == "d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2" and not git(
        "-C", "cosmos-framework", "status", "--porcelain"
    )
    example = json.loads((OUT / "synthetic_protocol.json").read_text())
    assert (
        example["all_product_and_pt_bytes_equal"]
        and example["numerical_audit"]["max_abs_error"] == 0
    )
    save(
        "gate.json",
        dict(
            schema="g2_issue63_author_cpu_gate_v1",
            base=BASE,
            results=results,
            source_count=len(before),
            source_hashes_stable=True,
            original_501_identities_retained=True,
            all_original_test_files_unchanged=unchanged_tests,
            protected_files_unchanged=protected,
            encode_record_ast_sha256=hashlib.sha256(new.encode()).hexdigest(),
            encode_record_ast_unchanged=True,
            child_gitlink=child,
            training_ready=False,
            scope="AUTHOR_CPU_SYNTHETIC_NOT_GPT_REAL_OR_CAPACITY_APPROVAL",
            not_run=[
                "real169Wan reencode",
                "real419pixel comparison",
                "18task private corpus capacity",
                "32worker resources",
                "full9126",
                "old data deletion",
                "P1microbatch",
                "state15",
                "alignment",
                "training",
                "merge",
                "original A1threeprobes missing native PyArrow locally",
            ],
        ),
    )


if __name__ == "__main__":
    main()
