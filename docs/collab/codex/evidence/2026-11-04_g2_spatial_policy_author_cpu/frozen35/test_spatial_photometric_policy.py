"""Owner spatial-v2 contract on synthetic caches and explicit replay doubles.

No real images, server files, renderer, RoboCasa or GPU are used. Native-kind
fixtures only exercise the CLI protocol; they are not physical acceptance.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from tools.g2 import verify_robocasa_rgbd_pose as checker
from tools.g2.rgbd_pose import cache
from tools.g2.test_rgbd_pose_export import FakeReplay, bound, exported

POLICY = "g2_stage1_spatial_v2"
OWNER_REFERENCE = (
    "https://github.com/wxwy/psm_wma/blob/"
    "f63454610ec2b95617c670444875339034c3c1c7/"
    "docs/collab/chatgpt/reviews/"
    "2026-11-04_G2_GateB_Owner_Visual_Alignment_Acceptance_and_Revision.md"
)


@pytest.fixture(autouse=True)
def reset_boundary_double():
    FakeReplay.created, FakeReplay.closed = [], []


def reader(delta=0):
    return lambda ref, frame: np.full((8, 8, 3), 7 + frame + delta, np.uint8)


def replay_report(tmp_path, *, backend=FakeReplay, delta=0, **kwargs):
    raw, flat, _, directory = exported(tmp_path)
    return checker.verify(
        directory,
        replay=True,
        raw_root=raw,
        flat_root=flat,
        state_index_policy="frame_index",
        replay_factory=backend,
        rgb_reader=reader(delta),
        **kwargs,
    )


@pytest.mark.parametrize("delta", [0, 5, 6, 200])
def test_photometric_threshold_is_reported_without_blocking_spatial_checks(
    tmp_path, delta
):
    report = replay_report(tmp_path, delta=delta)
    assert report["acceptance_policy"] == POLICY
    assert (
        "f63454610ec2b95617c670444875339034c3c1c7"
        in report["acceptance_policy_authority"]
    )
    assert report["spatial_alignment_gate"] == report["geometry_gate"] == "PASS"
    assert report["status"] == "SYNTHETIC_SPATIAL_REPLAY_CHECKS_PASS"
    photo = report["photometric_diagnostic"]
    assert photo["status"] == ("PASS" if delta <= 5 else "FAIL")
    assert photo["blocking"] is False and photo["mae_max"] == 5
    cameras = [c for f in report["frames"] for c in f["cameras"].values()]
    assert photo["checked_camera_frames"] == len(cameras) == 6
    assert photo["failed_camera_frames"] == (0 if delta <= 5 else 6)
    assert all(
        c["rgb"]["mae"] == delta and "psnr_db" in c["rgb"] and "ssim" in c["rgb"]
        for c in cameras
    )
    assert all(c["spatial_alignment_gate"] == "PASS" for c in cameras)
    assert report["thresholds"] == {
        "geometry_atol_m": 0.01,
        "min_ray_samples": 16,
        "rgb_mae_max": 5.0,
    }


def test_mixed_photometric_results_keep_each_original_metric(tmp_path):
    raw, flat, _, directory = exported(tmp_path)

    def mixed(ref, frame):
        delta = 50 if frame == 1 and "agentview_left" in ref["feature"] else 0
        return np.full((8, 8, 3), 7 + frame + delta, np.uint8)

    report = checker.verify(
        directory,
        replay=True,
        raw_root=raw,
        flat_root=flat,
        state_index_policy="frame_index",
        replay_factory=FakeReplay,
        rgb_reader=mixed,
    )
    assert report["spatial_alignment_gate"] == "PASS"
    assert report["photometric_diagnostic"]["failed_camera_frames"] == 1
    assert report["photometric_diagnostic"]["status"] == "FAIL"
    assert sorted(
        c["rgb"]["mae"] for f in report["frames"] for c in f["cameras"].values()
    ) == [0, 0, 0, 0, 0, 50]


@pytest.mark.parametrize(
    "fault",
    [
        "runtime",
        "mask",
        "depth",
        "K",
        "T_world_camera_gl",
        "T_world_camera_cv",
        "ray_fail",
        "ray_inconclusive",
        "projection",
    ],
)
@pytest.mark.parametrize("delta", [0, 50])
def test_spatial_failures_remain_blocking_independently_of_photometry(
    tmp_path, monkeypatch, fault, delta
):
    class Broken(FakeReplay):
        def render(self, camera):
            value = super().render(camera)
            if fault == "mask":
                value["valid"][0, 0] = True
            elif fault == "depth":
                value["depth_m"] += 0.2
            elif fault in ("K", "T_world_camera_gl", "T_world_camera_cv"):
                value[fault][0, 0] += 0.1
            return value

        def ray_check(self, *args, **kwargs):
            assert kwargs == {"atol_m": 0.01, "min_samples": 16}
            if fault in ("ray_fail", "ray_inconclusive"):
                return {"status": "FAIL" if fault == "ray_fail" else "INCONCLUSIVE"}
            return super().ray_check(*args, **kwargs)

    if fault == "runtime":
        Broken.identity = dict(FakeReplay.identity, mismatch="wrong_runtime")
    if fault == "projection":
        monkeypatch.setattr(checker, "reprojection_error", lambda sample: 1.0)
    report = replay_report(tmp_path, backend=Broken, delta=delta)
    assert report["spatial_alignment_gate"] == "FAIL_OR_INCONCLUSIVE"
    assert report["geometry_gate"] == "FAIL_OR_INCONCLUSIVE"
    assert report["status"] == "SPATIAL_REPLAY_CHECKS_NOT_ACCEPTED"
    assert report["photometric_diagnostic"]["status"] == (
        "PASS" if delta == 0 else "FAIL"
    )


@pytest.mark.parametrize(
    "fault", ["source_changed", "cache_corrupt", "rgb_unreadable", "rgb_shape"]
)
def test_source_integrity_and_rgb_input_abi_are_not_waived(tmp_path, fault):
    raw, flat, source, directory = exported(tmp_path)
    rgb_reader = reader(50)
    if fault == "source_changed":
        with Path(source.witnesses[0]["path"]).open("ab") as stream:
            stream.write(b"changed synthetic source")
    elif fault == "cache_corrupt":
        path = next(directory.glob("cameras/*/*.npz"))
        path.write_bytes(path.read_bytes() + b"corrupt")
    elif fault == "rgb_unreadable":

        def rgb_reader(ref, frame):
            raise OSError("synthetic RGB input unavailable")
    else:

        def rgb_reader(ref, frame):
            return np.zeros((7, 8, 3), dtype=np.uint8)

    with pytest.raises((OSError, ValueError)):
        checker.verify(
            directory,
            replay=True,
            raw_root=raw,
            flat_root=flat,
            state_index_policy="frame_index",
            replay_factory=FakeReplay,
            rgb_reader=rgb_reader,
        )


@pytest.mark.parametrize("reference", [None, OWNER_REFERENCE])
def test_owner_review_reference_never_becomes_automatic_visual_acceptance(
    tmp_path, reference
):
    report = replay_report(tmp_path, delta=50, owner_visual_review_ref=reference)
    visual = report["owner_visual_review"]
    assert visual["status"] == (
        "NOT_PROVIDED" if reference is None else "EXTERNAL_RECORD_REFERENCED"
    )
    assert visual["provenance_reference"] == reference
    assert visual["verified_by_tool"] is False
    assert "PASS" not in visual["status"]
    assert (
        report["spatial_alignment_scope"]
        == "AUTOMATED_CHECKS_ONLY_VISUAL_REVIEW_EXTERNAL"
    )


def test_offline_cache_and_external_review_cannot_claim_spatial_execution(tmp_path):
    _, _, _, directory = exported(tmp_path)
    report = checker.verify(directory, owner_visual_review_ref=OWNER_REFERENCE)
    assert report["status"] == "OFFLINE_CACHE_VALID_NOT_PHYSICAL_ACCEPTANCE"
    assert report["spatial_alignment_gate"] == report["geometry_gate"] == "NOT_EXECUTED"
    assert report["photometric_diagnostic"]["status"] == "NOT_EXECUTED"
    assert report["owner_visual_review"]["verified_by_tool"] is False


@pytest.mark.parametrize("reference", [True, ""])
def test_owner_reference_must_be_explicit_text_not_a_checkbox(tmp_path, reference):
    with pytest.raises(ValueError, match="review reference"):
        replay_report(tmp_path, owner_visual_review_ref=reference)


@pytest.mark.parametrize("delta", [0, 50])
def test_native_cli_protocol_returns_new_spatial_status_and_preserves_old_report(
    tmp_path, monkeypatch, capsys, delta
):
    # Explicit native-kind boundary double: tests exit policy, never a real replay.
    class NativeProtocolDouble(FakeReplay):
        identity = dict(
            FakeReplay.identity, kind="official_state_replay", cpu_test_double=True
        )

    raw, flat, source = bound(tmp_path)
    exported_result = cache.export_episode(
        tmp_path / "cache",
        source,
        [0, 1, 3],
        storage="uint16_mm",
        chunk_frames=2,
        recipe={"synthetic": True},
        replay_factory=NativeProtocolDouble,
    )
    directory = Path(exported_result["directory"])
    legacy_path = tmp_path / "legacy_report.json"
    legacy = b'{"status":"PHYSICAL_REPLAY_NOT_ACCEPTED","geometry_gate":"FAIL_OR_INCONCLUSIVE"}\n'
    legacy_path.write_bytes(legacy)
    report_path = tmp_path / "new_spatial_report.json"
    original_verify = checker.verify

    def verify_with_boundary(*args, **kwargs):
        return original_verify(
            *args,
            **kwargs,
            replay_factory=NativeProtocolDouble,
            rgb_reader=reader(delta),
        )

    monkeypatch.setattr(checker, "verify", verify_with_boundary)
    command = [
        "--episode-dir",
        str(directory),
        "--report",
        str(report_path),
        "--replay",
        "--raw-root",
        str(raw),
        "--flat-root",
        str(flat),
        "--state-index-policy",
        "frame_index",
        "--owner-visual-review-ref",
        OWNER_REFERENCE,
    ]
    assert checker.main(command) == 0
    report = json.loads(report_path.read_text())
    assert report["status"] == "SPATIAL_REPLAY_CHECKS_PASS"
    assert report["status"] not in {
        "PHYSICAL_REPLAY_PASS",
        "PHYSICAL_REPLAY_NOT_ACCEPTED",
    }
    assert report["acceptance_policy"] == POLICY
    assert report["photometric_diagnostic"]["status"] == (
        "PASS" if delta == 0 else "FAIL"
    )
    assert report["owner_visual_review"]["verified_by_tool"] is False
    assert legacy_path.read_bytes() == legacy
    before = report_path.read_bytes()
    with pytest.raises(ValueError, match="new"):
        checker.main(command)
    assert report_path.read_bytes() == before
    capsys.readouterr()


def test_cli_error_report_retains_new_policy_and_non_success(tmp_path, capsys):
    directory = tmp_path / "missing"
    directory.mkdir()
    output = tmp_path / "new_failure.json"
    assert (
        checker.main(
            [
                "--episode-dir",
                str(directory),
                "--report",
                str(output),
                "--owner-visual-review-ref",
                OWNER_REFERENCE,
            ]
        )
        == 1
    )
    result = json.loads(output.read_text())
    assert result["acceptance_policy"] == POLICY
    assert result["spatial_alignment_gate"] == "NOT_ACCEPTED"
    assert result["status"] == "VERIFICATION_FAILED"
    assert result["photometric_diagnostic"]["status"] == "NOT_EXECUTED"
    assert result["owner_visual_review"]["verified_by_tool"] is False
    capsys.readouterr()
