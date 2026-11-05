"""Validate a committed RGB-D/Pose episode; optionally replay it on the server.

Offline cache integrity is not physical geometry acceptance. --replay additionally
checks original RGB, state restoration, per-frame camera matrices, fresh depth and
independent, renderer-filtered mj_ray geometry. No RGB/depth images are exported.
Under the Owner's spatial-v2 policy, re-rendered RGB photometry is diagnostic.
Automatic spatial checks do not attest to a human RGB/Depth visual inspection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .rgbd_pose import SCHEMA
from .rgbd_pose.cache import cached_sample, durable_json, verify_episode
from .rgbd_pose.geometry import (
    ENCODING_COUNTS,
    depth_statistics,
    encode_depth,
    encoding_statistics,
    pose_motion,
    rgb_metrics,
)
from .rgbd_pose.replay import Replay, original_rgb, reprojection_error
from .rgbd_pose.source import Episode, load_episode, verify_witnesses

ACCEPTANCE_POLICY = "g2_stage1_spatial_v2"
POLICY_AUTHORITY = (
    "https://github.com/wxwy/psm_wma/blob/"
    "f63454610ec2b95617c670444875339034c3c1c7/"
    "docs/collab/chatgpt/reviews/"
    "2026-11-04_G2_GateB_Owner_Visual_Alignment_Acceptance_and_Revision.md"
)
SPATIAL_SCOPE = "AUTOMATED_CHECKS_ONLY_VISUAL_REVIEW_EXTERNAL"


def _owner_visual_review(reference):
    """Record external provenance without claiming its author, scope or verdict."""
    return {
        "status": "EXTERNAL_RECORD_REFERENCED" if reference else "NOT_PROVIDED",
        "provenance_reference": reference or None,
        "verified_by_tool": False,
    }


def _photometric_diagnostic(mae_max):
    return {
        "status": "NOT_EXECUTED",
        "blocking": False,
        # Invalid CLI thresholds must still allow a finite failure report.
        "mae_max": mae_max if np.isfinite(mae_max) else None,
        "checked_camera_frames": 0,
        "failed_camera_frames": 0,
    }


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
    owner_visual_review_ref=None,
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
    if owner_visual_review_ref is not None and (
        not isinstance(owner_visual_review_ref, str)
        or not owner_visual_review_ref.strip()
    ):
        raise ValueError("owner review reference must be nonempty text, not a checkbox")
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
        "depth_storage": spec["depth_storage"],
        "depth_encoding": manifest["depth_encoding"],
        "geometry_gate": "NOT_EXECUTED",
        "acceptance_policy": ACCEPTANCE_POLICY,
        "acceptance_policy_authority": POLICY_AUTHORITY,
        "spatial_alignment_gate": "NOT_EXECUTED",
        "spatial_alignment_scope": SPATIAL_SCOPE,
        "photometric_diagnostic": _photometric_diagnostic(rgb_mae_max),
        "owner_visual_review": _owner_visual_review(owner_visual_review_ref),
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
    spatial_passed = backend.identity == manifest["runtime"]
    report["runtime_at_replay"] = backend.identity
    report["runtime_matches_export"] = spatial_passed
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
                photometric_passed = metrics["mae"] <= rgb_mae_max
                report["photometric_diagnostic"]["checked_camera_frames"] += 1
                report["photometric_diagnostic"]["failed_camera_frames"] += int(
                    not photometric_passed
                )
                _, storage_valid, _ = encode_depth(
                    actual["depth_m"], actual["valid"], spec["depth_storage"]
                )
                fresh_encoding = encoding_statistics(
                    actual["depth_m"], actual["valid"], spec["depth_storage"]
                )
                recorded_encoding = row["cameras"][camera]["encoding"]
                same_encoding_counts = all(
                    fresh_encoding[k] == recorded_encoding[k] for k in ENCODING_COUNTS
                )
                same_mask = np.array_equal(saved["valid"], storage_valid)
                valid = saved["valid"] & storage_valid
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
                spatial_camera_pass = (
                    same_mask
                    and same_encoding_counts
                    and depth_error is not None
                    and depth_error <= quantization_tolerance
                    and max(matrix_errors.values()) <= 1e-5
                    and geometry["status"] == "PASS"
                    and projection is not None
                    and projection <= 1e-7
                )
                spatial_passed = spatial_passed and spatial_camera_pass
                frame_report["cameras"][camera] = {
                    "status": "PASS" if spatial_camera_pass else "FAIL",
                    "spatial_alignment_gate": "PASS" if spatial_camera_pass else "FAIL",
                    "photometric_diagnostic": "PASS" if photometric_passed else "FAIL",
                    "rgb": metrics,
                    "depth": depth_statistics(saved["depth_m"], saved["valid"]),
                    "valid_mask_matches_replay": same_mask,
                    "valid_mask_scope": "STORAGE_REPRESENTABLE_NOT_RAW_RENDERER",
                    "renderer_valid_pixels": int(actual["valid"].sum()),
                    "fresh_encoding": fresh_encoding,
                    "encoding_counts_match_replay": same_encoding_counts,
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
    report["camera_pose_motion"] = {
        camera: pose_motion(values) for camera, values in transforms.items()
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
    # Keep the old field as an automatic-spatial alias, explicitly versioned by
    # acceptance_policy. Never rewrite/relabel reports produced by the old tool.
    report["geometry_gate"] = report["spatial_alignment_gate"] = (
        "PASS" if spatial_passed else "FAIL_OR_INCONCLUSIVE"
    )
    report["photometric_diagnostic"]["status"] = (
        "FAIL" if report["photometric_diagnostic"]["failed_camera_frames"] else "PASS"
    )
    report["status"] = (
        (
            "SPATIAL_REPLAY_CHECKS_PASS"
            if native
            else "SYNTHETIC_SPATIAL_REPLAY_CHECKS_PASS"
        )
        if spatial_passed
        else "SPATIAL_REPLAY_CHECKS_NOT_ACCEPTED"
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
    parser.add_argument(
        "--rgb-mae-max",
        type=float,
        default=5.0,
        help="photometric diagnostic threshold only; does not gate spatial checks",
    )
    parser.add_argument(
        "--owner-visual-review-ref",
        help="external review provenance only; never automatically asserts visual PASS",
    )
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
            owner_visual_review_ref=args.owner_visual_review_ref,
        )
    except Exception as exc:
        result = {
            "schema": SCHEMA,
            "status": "VERIFICATION_FAILED",
            "geometry_gate": "NOT_ACCEPTED",
            "acceptance_policy": ACCEPTANCE_POLICY,
            "acceptance_policy_authority": POLICY_AUTHORITY,
            "spatial_alignment_gate": "NOT_ACCEPTED",
            "spatial_alignment_scope": SPATIAL_SCOPE,
            "photometric_diagnostic": _photometric_diagnostic(args.rgb_mae_max),
            "owner_visual_review": _owner_visual_review(args.owner_visual_review_ref),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    durable_json(report_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return (
        0
        if result["status"]
        in {"OFFLINE_CACHE_VALID_NOT_PHYSICAL_ACCEPTANCE", "SPATIAL_REPLAY_CHECKS_PASS"}
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
