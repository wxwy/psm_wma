"""Bind tested source hashes to an explicit immutable implementation commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(["git", *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formal-root", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = git("rev-parse", args.formal_root + "^{commit}").decode().strip()
    base = "29f9993d2543b8bb638f135aac9dd7172b71baf0"
    sources = json.loads((args.evidence / "source_before.json").read_text())
    bound = {}
    for path, sha in sources.items():
        data = git("show", root + ":" + path)
        assert hashlib.sha256(data).hexdigest() == sha, path
        bound[path] = git("rev-parse", root + ":" + path).decode().strip()
    link = git("ls-tree", root, "cosmos-framework").decode().split()[2]
    assert link == "d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2"
    changed = git("diff", "--name-only", base, root).decode().splitlines()
    allowed = (
        "g2/latent_cache/",
        "g2/offline/",
        "g2/tests/",
        "tools/g2/",
        "scripts/g2/",
        "docs/",
    )
    assert all(p in ("SESSION.md", "TODO.md") or p.startswith(allowed) for p in changed)
    protected = [
        "g2/latent_cache/encoding.py",
        "g2/latent_cache/contract.py",
        "g2/latent_cache/source.py",
        "g2/latent_cache/builder.py",
        "g2/latent_cache/storage.py",
        "g2/latent_cache/production.py",
        "tools/g2/build_spatial_view_vae_cache.py",
        "tools/g2/verify_spatial_view_vae_cache.py",
        "cosmos-framework",
    ]
    assert not git("diff", "--name-only", base, root, "--", *protected)
    result = dict(
        formal_root=root,
        child_gitlink=link,
        base=base,
        branch="codex/g2-one-shot-production-issue58",
        tested_source_count=len(bound),
        tested_git_blobs=bound,
        source_hashes_match_commit=True,
        increment_files=changed,
        formal_commit_files=git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", root
        )
        .decode()
        .splitlines(),
        protected_core_unchanged=protected,
        scope="SOURCE_IDENTITY_NOT_SERVER_OR_GPT_APPROVAL",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise RuntimeError("do not overwrite publication evidence")
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(
        json.dumps(
            dict(formal_root=root, tested_sources=len(bound), identity_match=True)
        )
    )


if __name__ == "__main__":
    main()
