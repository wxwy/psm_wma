# SPDX-License-Identifier: OpenMDW-1.1
"""Phase6 Encode1 observational parity probe (ds evidence only; 位于 /tmp，不改仓库)。

A = cache exact-window 实际 padded Z_t[0]（Phase3.5 cache reader，只读）
B = corrected Phase6 独立 T_pixel=1 Encode1(current composite)
C = 同一共享预处理后的 current frame 重复为 17 Policy 帧后的 normal encode，取 latent[0]

观测 only：无阈值、不自判 PASS、不写 cache/source。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import torch
import torch.nn.functional as F

SCRATCH = Path("/tmp/psm_wma_v3_phase6_cx")
TOOL_PATH = SCRATCH / "tools/v3/verify_robocasa_exact_window_real_parity.py"

if not Path(__file__).resolve().is_relative_to(Path("/tmp")):
    raise SystemExit("probe 必须位于 /tmp")


def _load_tool(path: Path):
    spec = importlib.util.spec_from_file_location("phase3p5_parity_tool", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = _load_tool(TOOL_PATH)

from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_cache import (  # noqa: E402
    RoboCasaExactWindowCacheCatalog,
    RoboCasaExactWindowEpisodeReader,
)
from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_policy import (  # noqa: E402
    CorrectedRoboCasaPolicyContract,
)
from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_source import (  # noqa: E402
    RoboCasaExactWindowSourceReader,
)
from cosmos_framework.data.generator.action.datasets.robocasa_lerobot_dataset import (  # noqa: E402
    _IMAGE_FEATURES,
    RoboCasaLeRobotDataset,
)
from cosmos_framework.inference.robocasa_composite_visual import (  # noqa: E402
    encode_current_composite_visual96,
    prepare_robocasa_composite_frame,
)
from cosmos_framework.model.generator.mot.robocasa_exact_window_local import (  # noqa: E402
    robocasa_current_latent_to_visual96,
)

PAIRS = (("A_vs_B", "A", "B"), ("B_vs_C", "B", "C"), ("A_vs_C", "A", "C"))


def _single_frame_composite(deps, paths, timestamp, tolerance_s, video_backend):
    """复用 Phase3.5 reconstruct_episode 的同一 authority，只取单个 timestamp 的 256x512 composite。"""
    proxy = object.__new__(RoboCasaLeRobotDataset)
    proxy._image_features = _IMAGE_FEATURES
    proxy._skip_video_loading = False
    sample = {}
    for feature, (path, from_ts) in paths.items():
        kwargs = {"backend": video_backend} if video_backend is not None else {}
        frames = deps.decode(path, [from_ts + timestamp], tolerance_s, **kwargs)
        tool._validate_frames(frames, 1, feature)
        sample[feature] = frames
    composite = deps.compose(proxy, sample)
    if tuple(composite.shape) != (1, 3, 256, 512) or not bool(torch.isfinite(composite).all()):
        raise ValueError(f"single-frame official composite shape/finite 无效：{tuple(composite.shape)}")
    uint8 = deps.convert(proxy, composite)
    if uint8.dtype != torch.uint8 or tuple(uint8.shape) != (3, 1, 256, 512):
        raise ValueError(f"single-frame official uint8 conversion 无效：{uint8.dtype}/{tuple(uint8.shape)}")
    return composite[0], uint8[:, 0].contiguous()


def _crop_z0(latent, image_size, factor, deps):
    """与 tool.compare_window 逐行相同的 official native post-crop，取 temporal 0。"""
    if latent.ndim != 4 or latent.shape[1] != 48:
        raise ValueError(f"crop 输入必须为 [T,48,H,W]：{tuple(latent.shape)}")
    warp = latent.permute(1, 0, 2, 3).unsqueeze(0).contiguous()  # [1,48,T,H,W]
    proxy = SimpleNamespace(tokenizer_vision_gen=SimpleNamespace(spatial_compression_factor=factor))
    cropped = deps.crop(proxy, [warp], [torch.tensor(image_size, dtype=torch.long)])[0]
    if cropped.ndim != 5 or cropped.shape[0] != 1 or cropped.shape[1] != 48:
        raise ValueError(f"native crop layout 无效：{tuple(cropped.shape)}")
    return cropped[0, :, 0].contiguous()


def _formula_visual96(z0):
    """独立重算 Phase4 公式（不经 helper 模块），用于验证 helper 返回值。"""
    return F.adaptive_avg_pool2d(z0.unsqueeze(0), output_size=(1, 2)).flatten()


def _flags(tensor):
    return {
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype),
        "device": str(tensor.device),
        "finite": bool(torch.isfinite(tensor).all()),
    }


def _pairwise(tensors):
    return {name: tool.metrics(tensors[left], tensors[right]) for name, left, right in PAIRS}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-root", required=True, type=Path)
    ap.add_argument("--source-root", required=True, type=Path)
    ap.add_argument("--vae-path", required=True, type=Path)
    ap.add_argument("--output-json", required=True, type=Path)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--task-class", default="CloseFridge")
    ap.add_argument("--episode-index", type=int, default=26)
    ap.add_argument("--starts", default="0,128,257")
    ap.add_argument("--video-backend", default="pyav")
    ap.add_argument("--tolerance-s", type=float, default=1e-4)
    ap.add_argument("--image-size", type=int, default=256)
    args = ap.parse_args()
    starts = tuple(int(part) for part in args.starts.split(","))

    if not args.vae_path.is_file():
        raise FileNotFoundError(f"本地 Wan VAE 文件缺失：{args.vae_path}")

    deps = tool.ProbeDependencies()
    catalog = RoboCasaExactWindowCacheCatalog(args.cache_root)
    reader = RoboCasaExactWindowEpisodeReader(catalog)
    source = RoboCasaExactWindowSourceReader(catalog, args.source_root)
    contract = CorrectedRoboCasaPolicyContract.from_cache_catalog(catalog)
    config = tool.resolve_vae_config(contract, args.vae_path)
    selection = tool.select_episodes(catalog, (args.task_class,), args.episode_index, starts, 1)
    factor = int(config["spatial_compression_factor"])

    device = torch.device(args.device)
    if device.type != "cuda" or not torch.cuda.is_available():
        raise ValueError("Encode1 observational parity 需要可用 CUDA")
    torch.backends.cudnn.benchmark = False

    record, sel_starts = selection[0]
    key = record.key
    rows, timestamps = tool.episode_rows(source, record)
    witnesses = tool.verify_witnesses(reader, key, sel_starts, rows)
    paths = tool.video_paths(source, key)

    report: dict[str, object] = {
        "schema": "robocasa_phase6_encode1_observational_parity_v1",
        "authority": {
            "scratch_root": str(SCRATCH),
            "parity_tool_path": str(TOOL_PATH),
            "cache_manifest_sha256": catalog.manifest_sha256,
            "corpus_digest": catalog.corpus_digest,
            "source_binding_digest": source.source_binding_digest,
            "runtime_source_root": str(args.source_root),
            "runtime_vae_path": str(args.vae_path),
            "vae_sha256": None,
            "tokenizer_class": "Wan2pt2VAEInterface",
            "resolved_vae_contract": config,
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "device": args.device,
            "video_backend": args.video_backend,
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "image_size": args.image_size,
            "image_size_authority": (
                "closed_loop_eval --image-size default=256 == 原生 composite 高度；"
                "local_memory_client.begin image_size default=256（均不触发 PIL resize）"
            ),
            "tolerance_s": args.tolerance_s,
            "read_only": True,
            "no_fallback": True,
            "threshold": None,
            "self_declared_pass": None,
        },
        "selection": [
            {
                "task_class": key.task_class,
                "episode_index": key.episode_index,
                "starts": list(sel_starts),
                "witnesses": witnesses,
            }
        ],
        "episode": {},
        "windows": [],
        "aggregate": {},
        "gate": {"threshold": None, "parity_gate_pass": None, "status": "OBSERVATIONAL_NO_THRESHOLD"},
    }

    tokenizer = deps.tokenizer_factory(**config)
    tool.prepare_tokenizer_device(tokenizer, device)

    with torch.inference_mode():
        video, geometry = tool.reconstruct_episode(
            source, key, timestamps, paths, args.tolerance_s, args.video_backend, deps
        )
        image_size = tool._geometry(
            tuple(video.shape), geometry["image_size"], catalog.latent_shape, factor, len(timestamps)
        )
        report["episode"] = {
            "task_class": key.task_class,
            "episode_index": key.episode_index,
            "episode_frame_count": len(timestamps),
            "composite_shape": list(geometry["composite_shape"]),
            "resized_shared_uint8_shape": list(video.shape),
            "image_size": list(image_size),
            "cached_padded_latent_shape": list(catalog.latent_shape),
            "camera_keys": [_IMAGE_FEATURES["left"], _IMAGE_FEATURES["wrist"]],
            "shared_episode_uint8_dtype": str(video.dtype),
            "shared_episode_uint8_finite": bool(torch.isfinite(video).all()),
        }

        for start in sel_starts:
            composite_s, frame_uint8 = _single_frame_composite(
                deps, paths, timestamps[start], args.tolerance_s, args.video_backend
            )
            prepared = prepare_robocasa_composite_frame(frame_uint8, args.image_size)
            padded_single = prepared.padded_single_frame
            padded_image_size = [int(x) for x in prepared.padded_image_size.flatten().tolist()]

            shared = tool.metrics(video[:, start].float(), padded_single[:, 0].float())

            cache = reader.read_window(key, start)
            z0_b, visual_b = encode_current_composite_visual96(tokenizer, prepared)
            z0_b_device_before_cpu = str(z0_b.device)
            z0_b = z0_b.cpu().contiguous()
            visual_b = visual_b.cpu().contiguous()
            video_padded = padded_single.repeat(1, 17, 1, 1)
            latent_c = tool.encode_window(video_padded, tokenizer, device, catalog.latent_shape, deps)
            z0_c = latent_c[0].contiguous()
            z0_a = cache[0].contiguous()

            visual_a = robocasa_current_latent_to_visual96(z0_a)
            visual_c = robocasa_current_latent_to_visual96(z0_c)

            padded = {"A": z0_a, "B": z0_b, "C": z0_c}
            cropped = {
                "A": _crop_z0(cache, image_size, factor, deps),
                "B": _crop_z0(z0_b.unsqueeze(0), image_size, factor, deps),
                "C": _crop_z0(latent_c, image_size, factor, deps),
            }
            visual = {"A": visual_a, "B": visual_b, "C": visual_c}

            report["windows"].append(
                {
                    "start_frame": start,
                    "geometry": {
                        "composite_shape": list(composite_s.shape),
                        "frame_uint8_shape": list(frame_uint8.shape),
                        "prepared_source_uint8_shape": list(prepared.source_uint8.shape),
                        "padded_single_frame_shape": list(padded_single.shape),
                        "padded_image_size": padded_image_size,
                        "image_size_match": padded_image_size == list(image_size),
                        "video_padded_17_shape": list(video_padded.shape),
                        "cached_padded_latent_shape": list(cache.shape),
                        "encoded_17_latent_shape": list(latent_c.shape),
                        "encoded_1_latent_shape": list(z0_b.shape),
                        "encoded_1_latent_device_before_cpu": z0_b_device_before_cpu,
                        "native_crop_shape": list(cropped["A"].shape),
                    },
                    "shared_preprocessing": {
                        "padded_single_frame_vs_episode_slice": shared,
                        "source_uint8_dtype": str(prepared.source_uint8.dtype),
                        "note": "phase3p5 reconstruct_episode 的 episode 级 VideoResize 切片 vs Phase6 helper 单帧 prep",
                    },
                    "tensors": {
                        "A_padded_z0": _flags(z0_a),
                        "B_padded_z0": _flags(z0_b),
                        "C_padded_z0": _flags(z0_c),
                        "A_native_z0": _flags(cropped["A"]),
                        "B_native_z0": _flags(cropped["B"]),
                        "C_native_z0": _flags(cropped["C"]),
                        "A_visual96": _flags(visual_a),
                        "B_visual96": _flags(visual_b),
                        "C_visual96": _flags(visual_c),
                    },
                    "comparisons": {
                        "padded_z0": _pairwise(padded),
                        "native_post_crop_z0": _pairwise(cropped),
                        "visual96": _pairwise(visual),
                    },
                    "phase4_formula": {
                        "A_helper_vs_formula": tool.metrics(visual_a, _formula_visual96(z0_a)),
                        "B_helper_vs_formula": tool.metrics(visual_b, _formula_visual96(z0_b)),
                        "C_helper_vs_formula": tool.metrics(visual_c, _formula_visual96(z0_c)),
                        "B_returned_vs_helper_of_B_z0": tool.metrics(
                            visual_b, robocasa_current_latent_to_visual96(z0_b)
                        ),
                        "C_returned_vs_helper_of_C_z0": tool.metrics(
                            visual_c, robocasa_current_latent_to_visual96(z0_c)
                        ),
                    },
                }
            )

    windows = report["windows"]
    aggregate: dict[str, object] = {}
    for group in ("padded_z0", "native_post_crop_z0", "visual96"):
        aggregate[group] = {}
        for name, _, _ in PAIRS:
            worst = max(windows, key=lambda w, n=name, g=group: w["comparisons"][g][n]["max_abs"])
            aggregate[group][name] = {
                "all_exact_equal": all(w["comparisons"][group][name]["exact_equal"] for w in windows),
                "worst_max_abs": worst["comparisons"][group][name]["max_abs"],
                "worst_max_abs_start_frame": worst["start_frame"],
                "worst_mean_abs": worst["comparisons"][group][name]["mean_abs"],
                "worst_rmse": worst["comparisons"][group][name]["rmse"],
                "numel": worst["comparisons"][group][name]["numel"],
            }
    report["aggregate"] = aggregate

    args.output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    print(f"REPORT={args.output_json}")
    print(f"episode_frames={report['episode']['episode_frame_count']} image_size={image_size}")
    for window in windows:
        geom = window["geometry"]
        print(
            f"start={window['start_frame']:>3} padded_single={geom['padded_single_frame_shape']} "
            f"prep_vs_episode_slice_exact={window['shared_preprocessing']['padded_single_frame_vs_episode_slice']['exact_equal']} "
            f"prep_vs_episode_slice_max_abs={window['shared_preprocessing']['padded_single_frame_vs_episode_slice']['max_abs']:.3e}"
        )
        for group in ("padded_z0", "native_post_crop_z0", "visual96"):
            cells = " ".join(
                f"{name}:eq={window['comparisons'][group][name]['exact_equal']}"
                f",max={window['comparisons'][group][name]['max_abs']:.6e}"
                f",rms={window['comparisons'][group][name]['rmse']:.6e}"
                for name, _, _ in PAIRS
            )
            print(f"    {group:<20} {cells}")
    print("phase4_formula:", {
        k: (v["exact_equal"], v["max_abs"]) for k, v in windows[0]["phase4_formula"].items()
    }, "(start=0)")
    print("aggregate:")
    for group, values in aggregate.items():
        print(f"    {group:<20} " + " ".join(f"{n}:all_exact={v['all_exact_equal']},max={v['worst_max_abs']:.6e}" for n, v in values.items()))
    print("OBSERVATIONAL_NO_THRESHOLD: no threshold argument, no self-declared PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())