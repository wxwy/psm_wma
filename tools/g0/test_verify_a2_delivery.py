"""Negative witnesses for the evidence verifier; no models, data, GPU or network."""

import json
import subprocess

import pytest

from tools.g0 import verify_a2_delivery as verify


def test_source_receipt_rejects_modified_source_and_false_commit(tmp_path, monkeypatch):
    repo = tmp_path / "child"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    for index in range(12):
        (repo / f"file_{index}.py").write_text(f"VALUE = {index}\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=EvidenceTest",
            "-c",
            "user.email=evidence@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=repo,
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    monkeypatch.setattr(verify, "CHILD", repo)
    receipt = {
        "child": commit,
        "dirty": "",
        "tracked_code_sha256": {
            path.name: verify.sha(path) for path in repo.glob("*.py")
        },
    }
    assert verify.source_receipt(receipt)["checked_source_files"] == 12
    (repo / "file_0.py").write_text("VALUE = 'changed'\n")
    with pytest.raises(ValueError, match="source mismatch"):
        verify.source_receipt(receipt)
    receipt["tracked_code_sha256"]["file_0.py"] = verify.sha(repo / "file_0.py")
    with pytest.raises(ValueError, match="immutable"):
        verify.source_receipt(receipt)


def test_resume_requires_saved_fast_state_bytes_not_only_equal_cursors():
    before = {"window_index": 2, "fast_state_records": 1, "fast_state_sha256": "saved"}
    after = {
        "window_index": 3,
        "actual_consumer_identity_sha256": "identity-window-3",
        "slot_epoch": {"0": 1},
        "stream_index": {"0": 0},
        "active_cursor": {"0": 1},
        "exposure": {"suite": 128},
        "group_counts": [128],
        "fast_state_before_first_group_sha256": "saved",
    }
    control = {"rows": [before, after]}
    resumed = {"rows": [dict(after)]}
    assert verify.compare_resume(control, resumed)[
        "restored_fast_state_matches_saved_bytes"
    ]
    resumed["rows"][0]["fast_state_before_first_group_sha256"] = "fresh"
    with pytest.raises(ValueError, match="fast-state"):
        verify.compare_resume(control, resumed)


def test_native_result_label_cannot_override_failed_numeric_evidence(tmp_path):
    parity = {
        "result": "PASS",
        "consumers": 128,
        "grouped_forwards": 1,
        "scalar_forwards": 8,
        "gradient_tensors": 314,
        "loss_relative_error": 0.5,
        "gradient_relative_l2": 0.0,
        "local_gradient_relative_l2": 0.0,
    }
    path = tmp_path / "native.json"
    path.write_text(
        json.dumps(
            {
                "result": "PASS",
                "native_group_parity": parity,
                "online_generation": {
                    "consumer_steps": [0, 1],
                    "slow_weights_unchanged": True,
                    "no_slow_parameter_grads": True,
                    "actions_finite": True,
                    "local_token_max_abs": 1.0,
                    "local_on_off_action_max_difference": 0.1,
                },
                "rgb_visual96_parity": {"result": "PASS"},
            }
        )
    )
    with pytest.raises(ValueError, match="numerical"):
        verify.inspect_native(path)


def test_missing_run_is_blocked_not_implicitly_passed(tmp_path):
    with pytest.raises(FileNotFoundError):
        verify.inspect_run(tmp_path)


def test_native_requires_action_path_difference_and_rgb_parity(tmp_path):
    report = {
        "result": "PASS",
        "native_group_parity": {
            "consumers": 128,
            "grouped_forwards": 1,
            "scalar_forwards": 8,
            "gradient_tensors": 314,
            "loss_relative_error": 0.0,
            "gradient_relative_l2": 0.0,
            "local_gradient_relative_l2": 0.0,
        },
        "online_generation": {
            "consumer_steps": [0, 1],
            "slow_weights_unchanged": True,
            "no_slow_parameter_grads": True,
            "actions_finite": True,
            "local_token_max_abs": 1.0,
            "local_on_off_action_max_difference": 0.0,
        },
        "rgb_visual96_parity": {"result": "PASS"},
    }
    path = tmp_path / "native.json"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="generation"):
        verify.inspect_native(path)
    report["online_generation"]["local_on_off_action_max_difference"] = 0.1
    report["rgb_visual96_parity"]["result"] = "FAIL"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="visual96"):
        verify.inspect_native(path)
