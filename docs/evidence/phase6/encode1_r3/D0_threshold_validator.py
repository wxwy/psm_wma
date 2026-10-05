#!/usr/bin/env python
"""Phase6 Encode1 thresholded validation — 独立验证器（ds Evidence 侧）。

职责边界（严格）：
- **只读** `C0_observational.json` 一个文件，不导入 probe、不读 repo/cache/source/VAE、
  不重新执行任何编码。
- 阈值是**本文件内的冻结常量** `THRESHOLD = 0.0`（`EXACT_REQUIRED = True`），
  不接受任何可放松阈值的 CLI 参数；`--threshold` 之类参数**刻意不存在**。
- 判据全部由本文件独立施加；probe 的 `gate` 自报字段只作为**必须为“未自判”**的证据被检查，
  绝不被当作判定来源。
- 结果写入 `D1_threshold_validation.json`，并由**进程退出码**表达：0=PASS，1=FAIL。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 冻结常量（来自 GPT review 的 numerical acceptance contract）
# ---------------------------------------------------------------------------
THRESHOLD = 0.0
EXACT_REQUIRED = True

SCHEMA_EXPECTED = "robocasa_phase6_encode1_observational_parity_v1"

# 冻结 witness 选择
EXPECTED_TASK_CLASS = "CloseFridge"
EXPECTED_EPISODE_INDEX = 26
EXPECTED_STARTS = [0, 128, 257]
EXPECTED_IMAGE_SIZE = 256
EXPECTED_DEVICE = "cuda:0"
EXPECTED_VIDEO_BACKEND = "pyav"

# 冻结 scratch / cache-source 权威绑定（与 Phase3.5 r3 / Phase6 r1 r2 一致）
EXPECTED_SCRATCH_ROOT = "/tmp/psm_wma_v3_phase6_cx"
EXPECTED_CACHE_MANIFEST_SHA256 = (
    "fa7e52256f177f1160aa431374d9e1da028579c78ca3cfb9c5e11084600d4006"
)
EXPECTED_CORPUS_DIGEST = (
    "aae2573c3b4b8123a060f737de49940259362e9b970111d0b60c2d89f8896df6"
)
EXPECTED_SOURCE_BINDING_DIGEST = (
    "dc56c44fa9feae8e7e534663ab1acfaa585f28410de7b983ea6cd87deddd35a4"
)
EXPECTED_SOURCE_ROOT = "/disk/rl/data/robocasa_v30/CloseFridge/20250816/lerobot"
EXPECTED_VAE_PATH = "/disk/rl/models/wan22_vae/Wan2.2_VAE.pth"

# 冻结几何
EXPECTED_GEOMETRY = {
    "composite_shape": [3, 256, 512],
    "frame_uint8_shape": [3, 256, 512],
    "prepared_source_uint8_shape": [3, 256, 512],
    "padded_single_frame_shape": [3, 1, 192, 320],
    "padded_image_size": [192, 320, 160, 320],
    "video_padded_17_shape": [3, 17, 192, 320],
    "cached_padded_latent_shape": [5, 48, 12, 20],
    "encoded_17_latent_shape": [5, 48, 12, 20],
    "encoded_1_latent_shape": [48, 12, 20],
    "native_crop_shape": [48, 10, 20],
}
EXPECTED_EPISODE_FRAME_COUNT = 274
EXPECTED_CAMERA_KEYS = [
    "observation.images.robot0_agentview_left",
    "observation.images.robot0_eye_in_hand",
]

# 冻结比对面：三层 × 三对
EXPECTED_LAYERS = ["padded_z0", "native_post_crop_z0", "visual96"]
EXPECTED_PAIRS = ["A_vs_B", "B_vs_C", "A_vs_C"]
EXPECTED_TENSOR_KEYS = [
    "A_padded_z0", "B_padded_z0", "C_padded_z0",
    "A_native_z0", "B_native_z0", "C_native_z0",
    "A_visual96", "B_visual96", "C_visual96",
]
EXPECTED_TENSOR_SHAPES = {
    "A_padded_z0": [48, 12, 20], "B_padded_z0": [48, 12, 20], "C_padded_z0": [48, 12, 20],
    "A_native_z0": [48, 10, 20], "B_native_z0": [48, 10, 20], "C_native_z0": [48, 10, 20],
    "A_visual96": [96], "B_visual96": [96], "C_visual96": [96],
}
EXPECTED_PHASE4_KEYS = [
    "A_helper_vs_formula",
    "B_helper_vs_formula",
    "C_helper_vs_formula",
    "B_returned_vs_helper_of_B_z0",
    "C_returned_vs_helper_of_C_z0",
]


class Validator:
    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.failures: list[str] = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            self.failures.append(f"{name}: {detail}")

    # -- 指标级判据：exact_equal 且 max_abs <= THRESHOLD -------------------
    def check_metric_block(self, name: str, block: dict, *,
                           exact_key: str = "exact_equal",
                           require_finite: bool = True) -> None:
        if not isinstance(block, dict):
            self.check(name, False, f"block 缺失或非 dict: {type(block).__name__}")
            return
        if require_finite:
            self.check(f"{name}.finite", block.get("finite") is True,
                       f"finite={block.get('finite')!r}")
        eq = block.get(exact_key)
        self.check(f"{name}.{exact_key}", eq is True, f"{exact_key}={eq!r}")
        mx = block.get("max_abs")
        ok_mx = isinstance(mx, (int, float)) and float(mx) <= THRESHOLD
        self.check(f"{name}.max_abs<=threshold", ok_mx,
                   f"max_abs={mx!r} threshold={THRESHOLD}")
        if EXACT_REQUIRED:
            for k in ("mean_abs", "rmse"):
                v = block.get(k)
                ok_v = isinstance(v, (int, float)) and float(v) <= THRESHOLD
                self.check(f"{name}.{k}<=threshold", ok_v, f"{k}={v!r}")

    # -- 主体 ------------------------------------------------------------
    def run(self, doc: dict) -> None:
        # 1. schema
        self.check("schema", doc.get("schema") == SCHEMA_EXPECTED,
                   f"schema={doc.get('schema')!r}")

        # 2. authority：probe 必须“未自判、无阈值、只读、无 fallback”
        auth = doc.get("authority")
        self.check("authority.present", isinstance(auth, dict), f"{type(auth).__name__}")
        auth = auth if isinstance(auth, dict) else {}
        self.check("authority.threshold_is_none", auth.get("threshold") is None,
                   f"threshold={auth.get('threshold')!r}")
        self.check("authority.self_declared_pass_is_none",
                   auth.get("self_declared_pass") is None,
                   f"self_declared_pass={auth.get('self_declared_pass')!r}")
        self.check("authority.read_only", auth.get("read_only") is True,
                   f"read_only={auth.get('read_only')!r}")
        self.check("authority.no_fallback", auth.get("no_fallback") is True,
                   f"no_fallback={auth.get('no_fallback')!r}")

        # 3. probe 的 gate 自报必须处于“未判定”状态（防止自判 PASS）
        gate = doc.get("gate")
        gate = gate if isinstance(gate, dict) else {}
        self.check("gate.present", isinstance(doc.get("gate"), dict), "gate 缺失")
        self.check("gate.status_observational_no_threshold",
                   gate.get("status") == "OBSERVATIONAL_NO_THRESHOLD",
                   f"status={gate.get('status')!r}")
        self.check("gate.threshold_is_none", gate.get("threshold") is None,
                   f"threshold={gate.get('threshold')!r}")
        self.check("gate.parity_gate_pass_is_none",
                   gate.get("parity_gate_pass") is None,
                   f"parity_gate_pass={gate.get('parity_gate_pass')!r}")

        # 4. scratch / cache-source 权威绑定
        self.check("authority.scratch_root", auth.get("scratch_root") == EXPECTED_SCRATCH_ROOT,
                   f"scratch_root={auth.get('scratch_root')!r}")
        self.check("authority.cache_manifest_sha256",
                   auth.get("cache_manifest_sha256") == EXPECTED_CACHE_MANIFEST_SHA256,
                   f"{auth.get('cache_manifest_sha256')!r}")
        self.check("authority.corpus_digest",
                   auth.get("corpus_digest") == EXPECTED_CORPUS_DIGEST,
                   f"{auth.get('corpus_digest')!r}")
        self.check("authority.source_binding_digest",
                   auth.get("source_binding_digest") == EXPECTED_SOURCE_BINDING_DIGEST,
                   f"{auth.get('source_binding_digest')!r}")
        self.check("authority.runtime_source_root",
                   auth.get("runtime_source_root") == EXPECTED_SOURCE_ROOT,
                   f"{auth.get('runtime_source_root')!r}")
        self.check("authority.runtime_vae_path",
                   auth.get("runtime_vae_path") == EXPECTED_VAE_PATH,
                   f"{auth.get('runtime_vae_path')!r}")

        # 5. 运行配置
        self.check("authority.device", auth.get("device") == EXPECTED_DEVICE,
                   f"device={auth.get('device')!r}")
        self.check("authority.video_backend", auth.get("video_backend") == EXPECTED_VIDEO_BACKEND,
                   f"video_backend={auth.get('video_backend')!r}")
        self.check("authority.image_size", auth.get("image_size") == EXPECTED_IMAGE_SIZE,
                   f"image_size={auth.get('image_size')!r}")
        self.check("authority.cudnn_benchmark_false",
                   auth.get("cudnn_benchmark") is False,
                   f"cudnn_benchmark={auth.get('cudnn_benchmark')!r}")

        # 6. VAE contract 不得走 streaming / retained cache
        ctr = auth.get("resolved_vae_contract")
        ctr = ctr if isinstance(ctr, dict) else {}
        self.check("authority.vae_contract.present", isinstance(auth.get("resolved_vae_contract"), dict),
                   f"{type(auth.get('resolved_vae_contract')).__name__}")
        self.check("authority.vae_contract.use_streaming_encode_false",
                   ctr.get("use_streaming_encode") is False,
                   f"use_streaming_encode={ctr.get('use_streaming_encode')!r}")
        self.check("authority.vae_contract.keep_decoder_cache_false",
                   ctr.get("keep_decoder_cache") is False,
                   f"keep_decoder_cache={ctr.get('keep_decoder_cache')!r}")
        self.check("authority.vae_contract.vae_path",
                   ctr.get("vae_path") == EXPECTED_VAE_PATH, f"{ctr.get('vae_path')!r}")

        # 7. selection（冻结 witness）
        sel = doc.get("selection")
        self.check("selection.present", isinstance(sel, list) and len(sel) >= 1,
                   f"selection={type(sel).__name__}")
        sel0 = sel[0] if isinstance(sel, list) and sel else {}
        self.check("selection.task_class", sel0.get("task_class") == EXPECTED_TASK_CLASS,
                   f"{sel0.get('task_class')!r}")
        self.check("selection.episode_index", sel0.get("episode_index") == EXPECTED_EPISODE_INDEX,
                   f"{sel0.get('episode_index')!r}")
        self.check("selection.starts", sel0.get("starts") == EXPECTED_STARTS,
                   f"starts={sel0.get('starts')!r}")

        # 8. episode
        ep = doc.get("episode")
        ep = ep if isinstance(ep, dict) else {}
        self.check("episode.frame_count", ep.get("episode_frame_count") == EXPECTED_EPISODE_FRAME_COUNT,
                   f"{ep.get('episode_frame_count')!r}")
        self.check("episode.image_size", ep.get("image_size") == [192, 320, 160, 320],
                   f"{ep.get('image_size')!r}")
        self.check("episode.cached_padded_latent_shape",
                   ep.get("cached_padded_latent_shape") == [5, 48, 12, 20],
                   f"{ep.get('cached_padded_latent_shape')!r}")
        self.check("episode.camera_keys",
                   sorted(ep.get("camera_keys") or []) == sorted(EXPECTED_CAMERA_KEYS),
                   f"{ep.get('camera_keys')!r}")
        self.check("episode.shared_uint8_finite",
                   ep.get("shared_episode_uint8_finite") is True,
                   f"{ep.get('shared_episode_uint8_finite')!r}")

        # 9. windows：几何 / 共享预处理 / 张量 / 逐窗比对
        windows = doc.get("windows")
        self.check("windows.count", isinstance(windows, list) and len(windows) == len(EXPECTED_STARTS),
                   f"num_windows={len(windows) if isinstance(windows, list) else None}")
        windows = windows if isinstance(windows, list) else []
        seen_starts = []
        for w in windows:
            if not isinstance(w, dict):
                self.check("window.type", False, f"{type(w).__name__}")
                continue
            sf = w.get("start_frame")
            seen_starts.append(sf)
            p = f"window[{sf}]"

            geo = w.get("geometry") or {}
            for key, expected in EXPECTED_GEOMETRY.items():
                self.check(f"{p}.geometry.{key}", geo.get(key) == expected,
                           f"got={geo.get(key)!r} want={expected!r}")
            self.check(f"{p}.geometry.image_size_match", geo.get("image_size_match") is True,
                       f"{geo.get('image_size_match')!r}")
            self.check(f"{p}.geometry.encoded_1_latent_device",
                       geo.get("encoded_1_latent_device_before_cpu") == EXPECTED_DEVICE,
                       f"{geo.get('encoded_1_latent_device_before_cpu')!r}")

            sp = w.get("shared_preprocessing") or {}
            self.check(f"{p}.shared_preprocessing.source_uint8_dtype",
                       sp.get("source_uint8_dtype") == "torch.uint8",
                       f"{sp.get('source_uint8_dtype')!r}")
            self.check_metric_block(
                f"{p}.shared_preprocessing.padded_single_frame_vs_episode_slice",
                sp.get("padded_single_frame_vs_episode_slice"))

            tens = w.get("tensors") or {}
            for tk in EXPECTED_TENSOR_KEYS:
                tb = tens.get(tk)
                self.check(f"{p}.tensors.{tk}.present", isinstance(tb, dict),
                           f"{type(tb).__name__}")
                tb = tb if isinstance(tb, dict) else {}
                self.check(f"{p}.tensors.{tk}.shape",
                           tb.get("shape") == EXPECTED_TENSOR_SHAPES[tk],
                           f"got={tb.get('shape')!r} want={EXPECTED_TENSOR_SHAPES[tk]!r}")
                self.check(f"{p}.tensors.{tk}.dtype", tb.get("dtype") == "torch.float32",
                           f"{tb.get('dtype')!r}")
                self.check(f"{p}.tensors.{tk}.finite", tb.get("finite") is True,
                           f"{tb.get('finite')!r}")

            cmps = w.get("comparisons") or {}
            for layer in EXPECTED_LAYERS:
                lb = cmps.get(layer)
                self.check(f"{p}.comparisons.{layer}.present", isinstance(lb, dict),
                           f"{type(lb).__name__}")
                lb = lb if isinstance(lb, dict) else {}
                for pair in EXPECTED_PAIRS:
                    self.check_metric_block(f"{p}.comparisons.{layer}.{pair}", lb.get(pair))

            pf = w.get("phase4_formula") or {}
            for pk in EXPECTED_PHASE4_KEYS:
                self.check_metric_block(f"{p}.phase4_formula.{pk}", pf.get(pk))

        self.check("windows.start_frames", sorted(x for x in seen_starts if x is not None) == sorted(EXPECTED_STARTS),
                   f"start_frames={seen_starts!r}")

        # 10. aggregate：跨窗口全量 exact
        agg = doc.get("aggregate")
        agg = agg if isinstance(agg, dict) else {}
        self.check("aggregate.present", isinstance(doc.get("aggregate"), dict), "aggregate 缺失")
        for layer in EXPECTED_LAYERS:
            lb = agg.get(layer)
            lb = lb if isinstance(lb, dict) else {}
            for pair in EXPECTED_PAIRS:
                blk = lb.get(pair)
                blk = blk if isinstance(blk, dict) else {}
                self.check(f"aggregate.{layer}.{pair}.all_exact_equal",
                           blk.get("all_exact_equal") is True,
                           f"{blk.get('all_exact_equal')!r}")
                wm = blk.get("worst_max_abs")
                self.check(f"aggregate.{layer}.{pair}.worst_max_abs<=threshold",
                           isinstance(wm, (int, float)) and float(wm) <= THRESHOLD,
                           f"worst_max_abs={wm!r} threshold={THRESHOLD}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phase6 Encode1 thresholded validator (read-only, threshold frozen at 0.0)")
    ap.add_argument("--observational-json", required=True, type=Path,
                    help="probe 产出的 C0_observational.json（本验证器唯一读取的输入）")
    ap.add_argument("--output-json", required=True, type=Path,
                    help="D1_threshold_validation.json 输出路径")
    # 刻意不提供任何 threshold 覆盖参数：阈值是本文件内的冻结常量。
    args = ap.parse_args()

    src: Path = args.observational_json
    raw = src.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    doc = json.loads(raw.decode("utf-8"))

    v = Validator()
    v.run(doc)

    total = len(v.checks)
    failed = len(v.failures)
    status = "PASS" if failed == 0 else "FAIL"

    out = {
        "schema": "robocasa_phase6_encode1_threshold_validation_v1",
        "status": status,
        "threshold": THRESHOLD,
        "exact_required": EXACT_REQUIRED,
        "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "source_observational_json": str(src),
        "source_observational_sha256": sha,
        "source_schema": doc.get("schema"),
        "checks_total": total,
        "checks_failed": failed,
        "failures": v.failures,
        "criterion": {
            "exact_equal_required": True,
            "max_abs_max": THRESHOLD,
            "mean_abs_max": THRESHOLD,
            "rmse_max": THRESHOLD,
            "layers": EXPECTED_LAYERS,
            "pairs": EXPECTED_PAIRS,
            "note": "阈值在观测后冻结，且由独立验证器施加；probe 自身未传阈值、未自判 PASS",
        },
        "checks": v.checks,
        "exit_code_semantics": {"0": "PASS", "1": "FAIL"},
    }
    args.output_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OBSERVATIONAL_JSON={src}")
    print(f"OBSERVATIONAL_SHA256={sha}")
    print(f"CHECKS_TOTAL={total} CHECKS_FAILED={failed}")
    print(f"THRESHOLD={THRESHOLD} EXACT_REQUIRED={EXACT_REQUIRED}")
    print(f"VALIDATION_STATUS={status}")
    print(f"VALIDATION_JSON={args.output_json}")
    if v.failures:
        print("FAILURES:")
        for f in v.failures:
            print(f"  - {f}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())