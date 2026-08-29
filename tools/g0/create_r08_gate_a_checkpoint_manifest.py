#!/usr/bin/env python3
"""Create the canonical content-identity manifest for an R08 Gate-A checkpoint."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    checkpoint = a.checkpoint.resolve()
    files = {str(path.relative_to(checkpoint)): {"size_bytes": path.stat().st_size, "sha256": sha(path)} for path in sorted(checkpoint.rglob("*")) if path.is_file()}
    if not {"model/.metadata", "model/__0_0.distcp"} <= set(files):
        raise SystemExit("missing required model checkpoint files")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps({"schema_version": "r08_gate_a_checkpoint_manifest_v1", "checkpoint_path": str(checkpoint), "files": files}, indent=2) + "\n")
    print(f"R08 Gate A checkpoint manifest: {len(files)} files")


if __name__ == "__main__":
    main()
