"""Real Manifest/Store summary profile contract; new synthetic CPU media only."""

import copy
from types import SimpleNamespace

import pytest
from cosmos_framework.evaluation.robocasa_v2 import generated_video
from cosmos_framework.evaluation.robocasa_v2.contract import (
    EnvironmentOutcome,
    build_manifest,
    result_record,
    validate_manifest,
)
from cosmos_framework.evaluation.robocasa_v2.store import Store
from robocasa_eval_v2 import generated_media
from robocasa_eval_v2.config import execution

from tools.v3.eval_v2_production_tests.contract_test import manifest
from tools.v3.eval_v2_production_tests.store_test import (
    admitted,
    close_streams,
    fixture_core,
)
from tools.v3.eval_v2_replan_tests.support import png_frames


def manifest_for(profile):
    seed = manifest(episodes=1)
    cfg = dict(
        execution_profile=profile,
        gpu_ids=[4],
        sims_per_gpu=1,
        max_infer_batch_size=1,
        batch_wait_ms=20,
    )
    layout = None if profile == "absent" else execution(cfg)
    value = build_manifest(
        tasks=seed["tasks"],
        episodes=1,
        seed=seed["seed"],
        horizons={"CloseFridge": 32},
        experiment=seed["experiment"],
        execution=layout,
    )
    assert validate_manifest(value) == value
    if profile == "phase_b":
        assert value["execution"]["profile"] == "phase_b_native_batch_v1"
    else:
        assert "execution" not in value
    return value


def prepared(tmp_path, profile="phase_b"):
    store = Store(tmp_path / "run", manifest_for(profile))
    store.create()
    with store.locked():
        store.begin_task("CloseFridge")
        attempt = admitted(store, store.begin_episode("CloseFridge", 0))
        observation = EnvironmentOutcome(32)
        for index in range(32):
            observation.check_after_step(
                SimpleNamespace(_check_success=lambda: index == 31)
            )
        row = result_record(
            store.manifest,
            task="CloseFridge",
            episode=0,
            generation=attempt["generation"],
            stream_id=attempt["stream_id"],
            observation=observation.finish(normal=True),
            instruction="Synthetic close the fridge",
            replans=2,
            elapsed_seconds=0.5,
            attempt_id=attempt["attempt_id"],
            worker_id=attempt["worker_id"],
            seed=attempt["seed"],
            reset_index=store.events(attempt)[-1]["data"]["reset_index"],
        )
        store.commit(row, staging=fixture_core(store, attempt, row))
        close_streams(store, "CloseFridge")
        scientific = store.publish_views()
    assert scientific["success"] == scientific["valid"] == 1
    directory = store._slot("CloseFridge", 0)
    identity = {k: row[k] for k in ("task", "episode", "attempt_id", "generation")}
    frames = png_frames()
    for index in range(2):
        video = frames[index:] + frames[:index]
        generated_video.write_generated(
            directory / "media",
            dict(
                index=index,
                video=video,
                binding={
                    "episode": identity,
                    "index": index,
                    "transfer": None,
                    "video_sha256": generated_video.sha(video),
                },
            ),
            20,
        )
    completion = dict(
        status="COMPLETE",
        task="CloseFridge",
        episode=0,
        attempt_id=row["attempt_id"],
        expected=2,
        saved=2,
        acknowledged=2,
        missing=[],
        server_ack_required=profile == "phase_b",
    )
    generated_video.atomic_json(
        directory / "generated_media_completion.json", completion
    )
    return store, directory, completion


def protected(store, directory):
    return {
        p: p.read_bytes()
        for p in (
            store.root / "summary.json",
            directory / "result.json",
            store.root / "manifest.json",
        )
    }


@pytest.mark.parametrize("profile", ["phase_b", "phase_a", "absent"])
def test_real_profile_summary_enters_every_receipt_and_file_hash_check(
    tmp_path, monkeypatch, profile
):
    store, directory, _ = prepared(tmp_path, profile)
    original = protected(store, directory)
    receipts, hashes = [], []
    read_receipt = generated_media.read_receipt
    file_sha = generated_video.file_sha

    def receipt(media, index, binding):
        receipts.append(index)
        return read_receipt(media, index, binding)

    def file_hash(path):
        hashes.append(path.name)
        return file_sha(path)

    monkeypatch.setattr(generated_media, "read_receipt", receipt)
    monkeypatch.setattr(generated_video, "file_sha", file_hash)
    with store.locked():
        for _ in range(2):
            report = generated_media.publish(store)
            assert report["status"] == "COMPLETE", report
            assert report["expected"] == report["saved"] == report["acknowledged"] == 2
            assert report["errors"] == [] and report["independent_of_SR"] is True
    assert receipts == [0, 1, 0, 1]
    assert hashes == ["replan_0000.mp4", "replan_0001.mp4"] * 2
    assert protected(store, directory) == original


@pytest.mark.parametrize(
    "profile,ack",
    [
        ("phase_b", False),
        ("phase_b", None),
        ("phase_b", 1),
        ("phase_b", "true"),
        ("phase_a", True),
        ("absent", True),
    ],
)
def test_wrong_or_untyped_ACK_authority_remains_incomplete(tmp_path, profile, ack):
    store, directory, completion = prepared(tmp_path, profile)
    original = protected(store, directory)
    generated_video.atomic_json(
        directory / "generated_media_completion.json",
        {**completion, "server_ack_required": ack},
    )
    with store.locked():
        report = generated_media.publish(store)
    assert report["status"] == "MEDIA_INCOMPLETE" and report["errors"]
    assert protected(store, directory) == original


@pytest.mark.parametrize(
    "damage", ["missing_mp4", "missing_receipt", "receipt_hash", "video_hash"]
)
def test_true_native_profile_does_not_bypass_inventory_or_receipt_validation(
    tmp_path, damage
):
    store, directory, _ = prepared(tmp_path)
    original = protected(store, directory)
    video = directory / "media/generated/replan_0001.mp4"
    receipt = directory / "media/generated/replan_0001.receipt.json"
    if damage == "missing_mp4":
        video.unlink()
    elif damage == "missing_receipt":
        receipt.unlink()
    elif damage == "receipt_hash":
        import json

        value = json.loads(receipt.read_bytes())
        generated_video.atomic_json(receipt, {**value, "sha256": "f" * 64})
    else:
        body = video.read_bytes()
        video.write_bytes(bytes([body[0] ^ 1]) + body[1:])  # Same size: must check SHA.
    with store.locked():
        report = generated_media.publish(store)
    assert report["status"] == "MEDIA_INCOMPLETE" and report["errors"]
    if damage == "missing_mp4":
        assert "inventory" in report["errors"][0]["error"]
    assert protected(store, directory) == original


@pytest.mark.parametrize("invalid", ["phase_b", "unknown"])
def test_contract_refuses_CLI_or_unknown_profile_as_native_manifest(invalid):
    good = manifest_for("phase_b")
    broken = copy.deepcopy(good)
    broken["execution"]["profile"] = invalid
    with pytest.raises(ValueError, match="native batch execution identity"):
        validate_manifest(broken)
