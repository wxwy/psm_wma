#!/usr/bin/env python3
"""Validate the external cache/online latent parity evidence before enabling cache."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--atol", type=float, default=1e-5)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text())
    passed = (
        str(evidence.get("status", "")).upper() == "PASS"
        and float(evidence.get("latent_max_abs_diff", float("inf"))) <= args.atol
        and float(evidence.get("loss_max_abs_diff", float("inf"))) <= args.atol
    )
    if not passed:
        raise SystemExit("R06 latent parity FAIL: keep online VAE path enabled")
    print(json.dumps({"status": "PASS", "atol": args.atol}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
