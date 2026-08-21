#!/usr/bin/env python3
"""Compare VAE weights in DCP checkpoint vs standalone Wan2.2_VAE.pth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch.distributed.checkpoint import FileSystemReader


def load_standalone(path: Path):
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    if isinstance(ckpt, dict) and "state_dict" in ckpt:
        return ckpt["state_dict"]
    return ckpt


def load_dcp_metadata(dcp_dir: Path):
    reader = FileSystemReader(dcp_dir)
    metadata = reader.read_metadata()
    keys = list(metadata.state_dict_metadata.keys())
    return keys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dcp-dir", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    standalone = load_standalone(args.vae_path)
    dcp_keys = load_dcp_metadata(args.dcp_dir)

    vae_keys = [k for k in dcp_keys if "vae" in k.lower() or "tokenizer_vision" in k.lower()]
    result = {
        "standalone_keys": len(standalone),
        "dcp_total_keys": len(dcp_keys),
        "dcp_vae_related_keys": len(vae_keys),
        "dcp_vae_key_sample": vae_keys[:30],
        "standalone_key_sample": list(standalone.keys())[:30],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
