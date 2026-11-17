"""Read a fixed commit, not dirty diff, and bind the actual tested sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(["git", *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--gate-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = git("rev-parse", args.root + "^{commit}").decode().strip()
    gate = json.loads((args.gate_dir / "gate.json").read_text())
    before = json.loads((args.gate_dir / "source_before.json").read_text())
    after = json.loads((args.gate_dir / "source_after.json").read_text())
    assert before == after and gate["source_hashes_stable"]
    for path, sha in before.items():
        assert hashlib.sha256(git("show", root + ":" + path)).hexdigest() == sha, path
    base = gate["base"]
    paths = (
        git("diff-tree", "--no-commit-id", "--name-only", "-r", base, root)
        .decode()
        .splitlines()
    )
    child = git("ls-tree", root, "cosmos-framework").decode().split()[2]
    assert child == gate["child_gitlink"]
    assert "cosmos-framework" not in paths
    scope = {
        "product": [
            p
            for p in paths
            if p.startswith(("g2/", "tools/", "scripts/"))
            and not p.startswith("g2/tests/")
        ],
        "tests": [p for p in paths if p.startswith("g2/tests/")],
        "docs_and_evidence": [
            p for p in paths if not p.startswith(("g2/", "tools/", "scripts/"))
        ],
    }
    value = dict(
        schema="g2_issue63_fixed_source_binding_v1",
        formal_root=root,
        base=base,
        child_gitlink=child,
        nav_sha="70eb7b447e65d793b0ebe18b258291ce46f057c1",
        tested_source_count=len(before),
        all_tested_sha256_match_formal_git_blobs=True,
        source_stable_during_tests=True,
        original_501_identities_retained=gate["original_501_identities_retained"],
        encode_record_ast_unchanged=gate["encode_record_ast_unchanged"],
        protected_files_unchanged=gate["protected_files_unchanged"],
        scope=scope,
        results=gate["results"],
        source_sha256=before,
        not_run=gate["not_run"],
        author_cpu_only=True,
        independent_GPT_approval=False,
        training_ready=False,
    )
    with args.output.open("x") as out:
        out.write(json.dumps(value, sort_keys=True, indent=2) + "\n")
    print(
        json.dumps(
            {
                "formal_root": root,
                "source_count": len(before),
                "scope_counts": {k: len(v) for k, v in scope.items()},
                "output": str(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
