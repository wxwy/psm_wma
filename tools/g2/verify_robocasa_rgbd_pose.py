"""Validate a committed RGB-D/Pose episode; optionally replay it on the server.

Offline cache integrity is not physical geometry acceptance. --replay additionally
checks original RGB, state restoration, per-frame camera matrices, fresh depth and
independent, renderer-filtered mj_ray geometry. No RGB/depth images are exported.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .rgbd_pose import SCHEMA
from .rgbd_pose.cache import cached_sample, durable_json, verify_episode
from .rgbd_pose.geometry import depth_statistics, rgb_metrics
from .rgbd_pose.replay import Replay, original_rgb, reprojection_error
from .rgbd_pose.source import Episode, load_episode, verify_witnesses


def verify(
    directory,
    *,
    replay=False,
    raw_root=None,
    flat_root=None,
    state_index_policy=None,
    source_dataset=None,
    frames=None,
    geometry_atol_m=0.01,
    min_ray_samples=16,
    rgb_mae_max=5.0,
    replay_factory=Replay,
    rgb_reader=original_rgb,
):
    if (
        not np.isfinite([geometry_atol_m, rgb_mae_max]).all()
        or min(geometry_atol_m, rgb_mae_max) <= 0
    ):
        raise ValueError("numeric verification tolerances must be finite and positive")
    if type(min_ray_samples) is not int or not 1 <= min_ray_samples <= 128:
        raise ValueError("min_ray_samples must be in 1..128")
    directory = Path(directory)
    manifest, rows = verify_episode(directory)
    spec = manifest["identity"]
    report = {
        "schema": SCHEMA,
        "cache_integrity": "PASS",
        "export_digest": manifest["export_digest"],
        "frame_count": manifest["frame_count"],
        "full_episode": manifest["full_episode"],
        "compressed_payload_bytes": manifest["compressed_payload_bytes"],
        "compression_ratio_raw_over_stored": manifest[
            "compression_ratio_raw_over_stored"
        ],
        "depth_quantization_max_abs_m": manifest["quantization_max_abs_m"],
        "geometry_gate": "NOT_EXECUTED",
        "runtime_at_export": manifest["runtime"],
        "thresholds": {
            "geometry_atol_m": geometry_atol_m,
            "min_ray_samples": min_ray_samples,
            "rgb_mae_max": rgb_mae_max,
        },
        "frames": [],
    }
    if not replay:
        report["status"] = "OFFLINE_CACHE_VALID_NOT_PHYSICAL_ACCEPTANCE"
        return report
    if raw_root is None or flat_root is None or state_index_policy != "frame_index":
        raise ValueError(
            "physical replay requires raw/Flat roots and explicit state-index-policy"
        )
    selected = spec["frames"] if frames is None else frames
    if (
        not selected
        or selected != sorted(set(selected))
        or set(selected) - set(spec["frames"])
    ):
        raise ValueError(
            "verification frames must be a nonempty ordered subset of committed frames"
        )
    verify_witnesses(spec["source_files"])
    source = load_episode(
        raw_root,
        flat_root,
        Episode(**spec["episode"]),
        spec["cameras"],
        state_index_policy=state_index_policy,
        source_dataset=source_dataset,
    )
    if (
        source.witnesses != spec["source_files"]
        or source.alignment != spec["alignment"]
    ):
        raise ValueError("physical replay source binding differs from committed cache")
    backend = replay_factory(source)
    passed = backend.identity == manifest["runtime"]
    report["runtime_at_replay"] = backend.identity
    report["runtime_matches_export"] = passed
    transforms, offsets = {c: [] for c in spec["cameras"]}, []
    by_frame = {row["frame_index"]: row for row in rows}
    try:
        for frame in selected:
            row = by_frame[frame]
            restoration = backend.restore(frame)
            offset = restoration["sim_time"] - row["flat_timestamp"]
            offsets.append(offset)
            frame_report = {
                "frame_index": frame,
                "source_state_index": row["source_state_index"],
                "global_row_index": row["global_row_index"],
                **restoration,
                "sim_time_minus_flat_timestamp_s": offset,
                "cameras": {},
            }
            for camera in spec["cameras"]:
                actual = backend.render(camera)
                saved = cached_sample(directory, manifest, row, camera)
                original = rgb_reader(source.rgb[camera], row["source_rgb_frame_index"])
                metrics = rgb_metrics(original, actual["rgb"])
                same_mask = np.array_equal(saved["valid"], actual["valid"])
                valid = saved["valid"] & actual["valid"]
                depth_error = (
                    float(
                        np.max(
                            np.abs(saved["depth_m"][valid] - actual["depth_m"][valid])
                        )
                    )
                    if valid.any()
                    else None
                )
                matrix_errors = {
                    k: float(np.max(np.abs(saved[k] - actual[k])))
                    for k in ("K", "T_world_camera_gl", "T_world_camera_cv")
                }
                geometry = backend.ray_check(
                    camera, saved, atol_m=geometry_atol_m, min_samples=min_ray_samples
                )
                projection = reprojection_error(saved)
                quantization_tolerance = max(
                    1e-5, manifest["quantization_max_abs_m"] + 1e-7
                )
                camera_pass = (
                    same_mask
                    and depth_error is not None
                    and depth_error <= quantization_tolerance
                    and max(matrix_errors.values()) <= 1e-5
                    and metrics["mae"] <= rgb_mae_max
                    and geometry["status"] == "PASS"
                    and projection is not None
                    and projection <= 1e-7
                )
                passed = passed and camera_pass
                frame_report["cameras"][camera] = {
                    "status": "PASS" if camera_pass else "FAIL",
                    "rgb": metrics,
                    "depth": depth_statistics(saved["depth_m"], saved["valid"]),
                    "valid_mask_matches_replay": same_mask,
                    "fresh_depth_max_abs_m": depth_error,
                    "fresh_depth_tolerance_m": quantization_tolerance,
                    "camera_matrix_max_abs": matrix_errors,
                    "corrected_backprojection_max_abs_pixels": projection,
                    "independent_geometry": geometry,
                }
                transforms[camera].append(saved["T_world_camera_cv"])
            report["frames"].append(frame_report)
    finally:
        backend.close()
    report["camera_pose_motion"] = {}
    for camera, values in transforms.items():
        initial = values[0]
        translations = [
            float(np.linalg.norm(v[:3, 3] - initial[:3, 3])) for v in values
        ]
        rotations = [
            float(
                np.arccos(
                    np.clip((np.trace(initial[:3, :3].T @ v[:3, :3]) - 1) / 2, -1, 1)
                )
            )
            for v in values
        ]
        report["camera_pose_motion"][camera] = {
            "max_translation_m": max(translations),
            "max_rotation_rad": max(rotations),
            "changed": max(translations) > 1e-6 or max(rotations) > 1e-5,
        }
    verify_witnesses(source.witnesses)
    report["timestamp_diagnostic"] = {
        "min_offset_s": min(offsets),
        "max_offset_s": max(offsets),
        "index_shift_applied": False,
    }
    native = backend.identity.get("kind") == "official_state_replay"
    report["evidence_kind"] = (
        "SERVER_NATIVE_REPLAY" if native else "CPU_BOUNDARY_DOUBLE"
    )
    report["geometry_gate"] = "PASS" if passed else "FAIL_OR_INCONCLUSIVE"
    report["status"] = (
        ("PHYSICAL_REPLAY_PASS" if native else "SYNTHETIC_REPLAY_VERIFIED")
        if passed
        else "PHYSICAL_REPLAY_NOT_ACCEPTED"
    )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-dir", type=Path, required=True)
    parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="new text-only JSON outside the immutable episode",
    )
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--flat-root", type=Path)
    parser.add_argument("--source-dataset", type=Path)
    parser.add_argument("--state-index-policy", choices=["frame_index"])
    parser.add_argument(
        "--frames",
        help="subset of committed frame indices; default all committed frames",
    )
    parser.add_argument("--geometry-atol-m", type=float, default=0.01)
    parser.add_argument("--min-ray-samples", type=int, default=16)
    parser.add_argument("--rgb-mae-max", type=float, default=5.0)
    args = parser.parse_args(argv)
    report_path = args.report.resolve()
    if report_path.exists() or report_path.is_relative_to(args.episode_dir.resolve()):
        raise ValueError("report must be new and outside the immutable episode")
    try:
        result = verify(
            args.episode_dir,
            replay=args.replay,
            raw_root=args.raw_root,
            flat_root=args.flat_root,
            source_dataset=args.source_dataset,
            state_index_policy=args.state_index_policy,
            frames=None
            if args.frames is None
            else [int(v) for v in args.frames.split(",")],
            geometry_atol_m=args.geometry_atol_m,
            min_ray_samples=args.min_ray_samples,
            rgb_mae_max=args.rgb_mae_max,
        )
    except Exception as exc:
        result = {
            "schema": SCHEMA,
            "status": "VERIFICATION_FAILED",
            "geometry_gate": "NOT_ACCEPTED",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    durable_json(report_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return (
        0
        if result["status"]
        in {"OFFLINE_CACHE_VALID_NOT_PHYSICAL_ACCEPTANCE", "PHYSICAL_REPLAY_PASS"}
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
