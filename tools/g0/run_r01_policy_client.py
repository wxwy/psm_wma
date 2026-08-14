#!/usr/bin/env python3
"""Run the minimal G0-R01 OpenPI policy protocol smoke."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from openpi_client import msgpack_numpy
from websockets.sync.client import connect


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="ws://127.0.0.1:8000")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--num-iterations", type=int, default=2)
    args = parser.parse_args()

    image = np.zeros((540, 640, 3), dtype=np.uint8)
    image[180:360, 240:400] = np.array([64, 128, 255], dtype=np.uint8)
    observation = {
        "prompt": "Move the robot safely toward the target object.",
        "observation/image": image,
        "observation/joint_position": np.zeros((1, 7), dtype=np.float32),
        "observation/gripper_position": np.array([[0.5]], dtype=np.float32),
    }
    packer = msgpack_numpy.Packer()
    rows = []
    log_lines = []
    with connect(args.uri, compression=None, max_size=None, ping_interval=None) as websocket:
        msgpack_numpy.unpackb(websocket.recv())
        for index in range(args.warmup + args.num_iterations):
            start = time.monotonic()
            websocket.send(packer.pack(observation))
            response_raw = websocket.recv()
            latency_ms = (time.monotonic() - start) * 1000.0
            if isinstance(response_raw, str):
                raise RuntimeError(response_raw)
            response = msgpack_numpy.unpackb(response_raw)
            action = np.asarray(response["action"])
            video = np.asarray(response["video"])
            row = {
                "warmup": index < args.warmup,
                "latency_ms": latency_ms,
                "action": {
                    "shape": list(action.shape),
                    "finite": bool(np.isfinite(action).all()),
                    "preview": action[:2].tolist(),
                },
                "video": {
                    "shape": list(video.shape),
                    "finite": bool(np.isfinite(video).all()),
                    "dtype": str(video.dtype),
                    "min": int(video.min()),
                    "max": int(video.max()),
                },
            }
            rows.append(row)
            line = json.dumps(row, ensure_ascii=False)
            log_lines.append(line)
            print(line, flush=True)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = {
        "input": {
            "prompt": observation["prompt"],
            "image_shape": list(image.shape),
            "joint_position": observation["observation/joint_position"].tolist(),
            "gripper_position": observation["observation/gripper_position"].tolist(),
        },
        "requests": rows,
    }
    (args.output_dir / "robolab_client_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "robolab_client.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
