"""Author CPU/source identity audit. Does not certify server or real VAE Gates."""

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

BASE = "b6311222c364543787f913215bf584065aa1c275"
OUT = Path(os.environ["VF_GATE_OUT"])


def git(*args):
    return subprocess.check_output(["git", *args])


def save(name, value):
    (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def sources():
    return {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for root in ("g2", "tools/g2", "scripts/g2")
        for p in sorted(Path(root).rglob("*"))
        if p.is_file()
        and p.suffix in (".py", ".json", ".sh", ".js", ".html", ".css")
        and "__pycache__" not in p.parts
    }


def ids(path):
    return {
        (c.attrib["classname"], c.attrib["name"])
        for c in ET.parse(path).iter("testcase")
    }


def encode_ast(data):
    return ast.dump(
        next(
            n
            for n in ast.parse(data).body
            if isinstance(n, ast.FunctionDef) and n.name == "encode_record"
        ),
        include_attributes=False,
    )


def main():
    action = sys.argv[1]
    if action == "before":
        save("source_before.json", sources())
        packages = {}
        for name in (
            "torch",
            "numpy",
            "Pillow",
            "pytest",
            "ruff",
            "pyarrow",
            "mujoco",
            "pandas",
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
                base=BASE,
                worktree_head=git("rev-parse", "HEAD").decode().strip(),
                gpu=False,
                new_environment=False,
                install=False,
            ),
        )
        return
    if action == "bind":
        formal = git("rev-parse", sys.argv[2] + "^{commit}").decode().strip()
        hashes = json.loads((OUT / "source_after.json").read_text())
        for path, sha in hashes.items():
            assert (
                hashlib.sha256(git("show", formal + ":" + path)).hexdigest() == sha
            ), path
        scope = (
            git("diff-tree", "--no-commit-id", "--name-only", "-r", BASE, formal)
            .decode()
            .splitlines()
        )
        value = dict(
            formal_root=formal,
            base=BASE,
            child_gitlink=git("ls-tree", formal, "cosmos-framework")
            .decode()
            .split()[2],
            source_count=len(hashes),
            all_tested_git_blobs_match=True,
            scope=scope,
            source_sha256=hashes,
            gpt_approval=False,
        )
        with (OUT / "implementation_scope.json").open("x") as out:
            out.write(json.dumps(value, sort_keys=True, indent=2) + "\n")
        print(
            json.dumps(
                {
                    k: value[k]
                    for k in (
                        "formal_root",
                        "child_gitlink",
                        "source_count",
                        "all_tested_git_blobs_match",
                    )
                }
            )
        )
        return
    before = json.loads((OUT / "source_before.json").read_text())
    after = sources()
    save("source_after.json", after)
    assert before == after
    root = ET.parse(OUT / "pytest.xml")
    cases = list(root.iter("testcase"))
    actual = ids(OUT / "pytest.xml")
    previous = Path("docs/collab/codex/evidence/2026-11-17_issue63/revision2")
    expected = set().union(
        *(
            ids(previous / (n + ".xml"))
            for n in ("pr53", "stage_a", "related", "one_shot", "capsule")
        )
    )
    expected.add(
        (
            "g2.tests.test_one_shot_owned_legacy_output",
            "test_legacy_view_path_accepts_only_signed_owned_v2_namespace",
        )
    )
    for name in (
        "test_view_only_uses_lossless_compressed_source_and_all_required_products",
        "test_compressed_source_bad_bytes_or_receipt_never_validate",
        "test_canonical_legacy_path_requires_new_explicit_view_only_claim",
        "test_unclaimed_preexisting_legacy_content_never_upgraded",
    ):
        expected.add(("g2.tests.test_view_only_source", name))
    assert len(expected) == 560 and not expected - actual, sorted(expected - actual)
    errors = sum(len(c.findall("error")) for c in cases)
    failures = sum(len(c.findall("failure")) for c in cases)
    skipped = [
        dict(
            id=c.attrib["classname"] + "::" + c.attrib["name"],
            reason=c.find("skipped").attrib.get("message"),
        )
        for c in cases
        if c.find("skipped") is not None
    ]
    assert errors == failures == 0
    assert not any(
        (c.attrib["classname"], c.attrib["name"]) not in expected
        and c.find("skipped") is not None
        for c in cases
    )
    old_tests = (
        git("ls-tree", "-r", "--name-only", BASE, "--", "g2/tests")
        .decode()
        .splitlines()
    )
    for path in old_tests:
        if path.endswith(".py"):
            assert Path(path).read_bytes() == git("show", BASE + ":" + path), path
    protected = [
        "g2/latent_cache/encoding.py",
        "g2/latent_cache/contract.py",
        "g2/offline/atomic_6views_run.py",
        "g2/offline/full_production.py",
        "g2/offline/episode.py",
        "g2/offline/output_profile.py",
        "g2/offline/task_entities.py",
        "g2/offline/language_context.py",
        "g2/offline/spatial_metadata.py",
    ]
    for path in protected:
        assert Path(path).read_bytes() == git("show", BASE + ":" + path), path
    assert git("ls-tree", "HEAD", "cosmos-framework") == git(
        "ls-tree", BASE, "cosmos-framework"
    )
    numeric_same = encode_ast(
        Path("g2/latent_cache/builder.py").read_text()
    ) == encode_ast(git("show", BASE + ":g2/latent_cache/builder.py").decode())
    assert numeric_same
    gate = dict(
        schema="g2_view_first_retirement_author_cpu_v1",
        base=BASE,
        tests=len(cases),
        passed=len(cases) - len(skipped) - failures - errors,
        failed=failures,
        errors=errors,
        skipped=len(skipped),
        skipped_cases=skipped,
        original_560_identities_retained=True,
        original_test_source_files_unchanged=True,
        new_cases=len(actual - expected),
        source_count=len(after),
        source_hashes_stable=True,
        encode_record_ast_unchanged=numeric_same,
        protected_files_unchanged=protected,
        child_gitlink=git("ls-tree", "HEAD", "cosmos-framework").decode().split()[2],
        scope="AUTHOR_CPU_SYNTHETIC_NOT_REAL_F27_WAN_GATE",
        training_ready=False,
    )
    save("gate.json", gate)
    print(
        json.dumps(
            {
                k: gate[k]
                for k in (
                    "tests",
                    "passed",
                    "failed",
                    "errors",
                    "skipped",
                    "new_cases",
                    "source_count",
                    "original_560_identities_retained",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
