# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: OpenMDW-1.1
"""G0-R06 zero-shot vision-generation probe.

Diagnose whether the zero-shot Cosmos3-Edge-Policy-DROID checkpoint's *future
frame generation* collapses to a static "repeat the condition" shortcut — the
same failure observed on the SFT iter700 predictions.

Three inputs, all served through the existing /predict endpoint (which returns
``action`` + ``video`` with 17 frames: frame 0 = cond reconstruction, frames
1..16 = generated future):

  - text_lib_gray   : grey(127.5) condition + LIBERO task text   (text-only)
  - text_droid_gray : grey(127.5) condition + DROID-style text   (text-only)
  - real_lib        : real LIBERO agentview frame + LIBERO text  (image + text)

For each we save the decoded 17-frame video as MP4 and print the frame-to-frame
MAE (median / p90) so "static future" can be quantified against the SFT pred.mp4
median (~0.65) and the real rollout median (~1.6).
"""
from __future__ import annotations

import base64
import io
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

SERVER = "http://localhost:8001"
OUT_DIR = Path("/gemini/code/psm_wma/artifacts/g0/r06/vision_gen_probe_zeroshot")
IMAGE_SIZE = 256

LIBERO_TEXT = (
    "put the white mug on the left plate and put the yellow and white mug on the right plate"
)
# DROID-style instructions: short robot-manipulation directives close to the
# Edge-Policy-DROID training distribution (vs the long multi-object LIBERO sentence).
DROID_TEXTS = [
    "pick up the mug",
    "place the mug on the plate",
]


def _ndarray_to_b64(img: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _b64_to_ndarray(b64: str) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB"))


def _gray_frame(size: int) -> np.ndarray:
    return np.full((size, size, 3), 127.5, dtype=np.uint8)


def _load_real_frame() -> np.ndarray:
    # Real LIBERO agentview observation (256x256) extracted from a rollout video.
    p = Path("/tmp/psm_vframe/real_obs_f0.png")
    if not p.exists():
        # Fall back to grey if the extracted frame is missing.
        print("[probe] WARNING: real frame missing, falling back to grey", file=sys.stderr)
        return _gray_frame(IMAGE_SIZE)
    return np.asarray(Image.open(p).convert("RGB"))


def _post_predict(image: np.ndarray, prompt: str) -> dict:
    payload = {
        "image": _ndarray_to_b64(image),
        "prompt": prompt,
        "domain_name": "libero",
        "image_size": IMAGE_SIZE,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SERVER + "/predict",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _frame_stats(frames: list[np.ndarray]) -> dict:
    fr = [f.astype(np.float32) for f in frames]
    adj = [np.abs(fr[i] - fr[i - 1]).mean() for i in range(1, len(fr))]
    adj = np.array(adj)
    # frame0 -> frame1 is cond-reconstruction vs first predicted frame; report
    # both the full window and the generated-only (frames 1..16) stats.
    gen = adj[1:] if len(adj) > 1 else adj
    return {
        "n_frames": len(fr),
        "adj_mae_mean": float(adj.mean()),
        "adj_mae_median": float(np.median(adj)),
        "adj_mae_p90": float(np.percentile(adj, 90)),
        "gen_mae_median": float(np.median(gen)),  # frames 1..16 only
        "f0_f1_mae": float(adj[0]),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    real_frame = _load_real_frame()
    gray = _gray_frame(IMAGE_SIZE)

    jobs = [
        ("text_lib_gray", gray, LIBERO_TEXT),
        *[(f"text_droid{i}_gray", gray, t) for i, t in enumerate(DROID_TEXTS)],
        ("real_lib", real_frame, LIBERO_TEXT),
    ]

    results = {}
    for name, image, prompt in jobs:
        print(f"[probe] -> {name}  prompt={prompt!r}  image_shape={image.shape}")
        try:
            data = _post_predict(image, prompt)
        except Exception as exc:  # noqa: BLE001
            print(f"[probe] {name} FAILED: {exc}", file=sys.stderr)
            results[name] = {"error": str(exc)}
            continue

        frames = [_b64_to_ndarray(b) for b in data["video"]]
        stats = _frame_stats(frames)
        mp4_path = OUT_DIR / f"{name}.mp4"
        try:
            import imageio.v2 as imageio

            imageio.mimsave(mp4_path, frames, fps=20)
            stats["mp4"] = str(mp4_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[probe] {name} mp4 save failed: {exc}", file=sys.stderr)
            stats["mp4_error"] = str(exc)

        stats["action_rows"] = len(data.get("action", []))
        results[name] = stats
        print(
            f"[probe] {name}: n={stats['n_frames']} "
            f"adj_median={stats['adj_mae_median']:.3f} "
            f"gen_median={stats['gen_mae_median']:.3f} "
            f"f0_f1={stats['f0_f1_mae']:.3f}"
        )

    out_json = OUT_DIR / "summary.json"
    out_json.write_text(json.dumps(results, indent=2))
    print(f"[probe] wrote {out_json}")

    # Quick reference table
    print("\n[probe] summary (compare: SFT pred.mp4 gen_median ~0.65, real rollout ~1.6):")
    for name, r in results.items():
        if "error" in r:
            print(f"  {name:<24} ERROR: {r['error']}")
        else:
            print(
                f"  {name:<24} adj_median={r['adj_mae_median']:6.3f} "
                f"gen_median={r['gen_mae_median']:6.3f} f0_f1={r['f0_f1_mae']:6.3f}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
