#!/usr/bin/env python3
"""Sample CUDA device memory usage as CSV for G0 runtime gates."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import torch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--interval-ms", type=int, default=500)
    args = parser.parse_args()
    if args.interval_ms <= 0:
        raise ValueError("--interval-ms must be positive")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")
    total_mb = torch.cuda.get_device_properties(0).total_memory / 1024**2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8", buffering=1) as stream:
        writer = csv.writer(stream)
        writer.writerow(["used_memory_mb"])
        while True:
            free_bytes, _ = torch.cuda.mem_get_info(0)
            writer.writerow([f"{total_mb - free_bytes / 1024**2:.3f}"])
            time.sleep(args.interval_ms / 1000.0)


if __name__ == "__main__":
    main()
