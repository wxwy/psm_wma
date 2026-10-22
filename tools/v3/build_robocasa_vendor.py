#!/usr/bin/env python3
"""Build locked vendor checkouts from local Git objects into a NEW directory.

No pip, network, simulation or edits to either source cache. A failed build is
preserved for inspection. Commit metadata, tree and patch bytes are verified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCK = ROOT / "third_party/robosuite_patches/vendor.lock.json"


def git(repo: Path, *args, env=None, input=None) -> str:
    clean_env = os.environ.copy() if env is None else env.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        clean_env.pop(name, None)
    clean_env.update(
        GIT_NO_LAZY_FETCH="1",
        GIT_ALLOW_PROTOCOL="file",
        GIT_TERMINAL_PROMPT="0",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_CONFIG_NOSYSTEM="1",
        GIT_NO_REPLACE_OBJECTS="1",
    )
    try:
        return subprocess.check_output(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "core.autocrlf=false",
                "-C",
                str(repo),
                *args,
            ],
            env=clean_env,
            input=input,
            text=True,
            stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as error:
        print(error.stderr or "Git command failed without stderr", file=sys.stderr)
        raise


def build_checkout(cache: Path, destination: Path, commit: str) -> None:
    cache = cache.resolve(strict=True)
    if git(cache, "rev-parse", "--is-shallow-repository") not in {"true", "false"}:
        raise ValueError("not a Git source cache")
    if git(cache, "rev-parse", commit + "^{commit}") != commit:
        raise ValueError("cache does not contain the exact commit")
    destination.mkdir()  # Exclusive: never reuse, reset, clean or patch an existing tree.
    git(destination, "init", "-q")
    git(destination, "fetch", "--depth=1", "--no-tags", str(cache), commit)
    git(destination, "-c", "core.autocrlf=false", "checkout", "--detach", commit)


def build(*, robosuite_cache: Path, robocasa_cache: Path, output: Path, lock_path=DEFAULT_LOCK) -> dict:
    lock_path = Path(lock_path).resolve(strict=True)
    lock = json.loads(lock_path.read_text())
    if lock["schema"] != "psm_robocasa_vendor_lock_v1":
        raise ValueError("unknown vendor lock schema")
    spec = lock["robosuite"]
    patch = lock_path.parent / spec["patch"]
    if hashlib.sha256(patch.read_bytes()).hexdigest() != spec["patch_sha256"]:
        raise ValueError("vendor patch SHA256 mismatch")
    output = output.absolute()
    output.mkdir()  # Includes output manifest; do not accept an already-existing namespace.
    rs, rc = output / "robosuite", output / "robocasa"
    build_checkout(robosuite_cache, rs, spec["base_commit"])
    git(rs, "apply", "--check", "--index", str(patch))
    git(rs, "apply", "--index", str(patch))
    tree = git(rs, "write-tree")
    if tree != spec["patched_tree"]:
        raise ValueError("patched vendor tree mismatch")
    env = os.environ.copy()
    for who in ("AUTHOR", "COMMITTER"):
        for key in ("NAME", "EMAIL", "DATE"):
            env[f"GIT_{who}_{key}"] = spec["commit_metadata"][key.lower()]
    commit = git(rs, "commit-tree", tree, "-p", spec["base_commit"], env=env, input=spec["commit_metadata"]["message"])
    if commit != spec["patched_commit"]:
        raise ValueError("deterministic vendor commit mismatch")
    git(rs, "update-ref", "HEAD", commit)
    if git(rs, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("constructed vendor tree is not clean")
    build_checkout(robocasa_cache, rc, lock["robocasa"]["commit"])
    result = {
        "schema": "psm_vendor_build_v1",
        "lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "robosuite": {"path": str(rs), "commit": commit, "tree": tree},
        "robocasa": {"path": str(rc), "commit": lock["robocasa"]["commit"]},
        "package_install_performed": False,
        "simulation_performed": False,
    }
    (output / "build.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robosuite-cache", type=Path, required=True)
    parser.add_argument("--robocasa-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                robosuite_cache=args.robosuite_cache,
                robocasa_cache=args.robocasa_cache,
                output=args.output,
                lock_path=args.lock,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
