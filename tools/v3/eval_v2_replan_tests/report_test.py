"""Media completion is an explicit diagnostic gate, never a new Core/SR judge."""

import json
from pathlib import Path

import pytest
import yaml
from cosmos_framework.evaluation.robocasa_v2.generated_video import (
    atomic_json,
    write_generated,
)
from robocasa_eval_v2.cli import main
from robocasa_eval_v2.generated_media import publish

from tools.v3.eval_v2_production_tests.entry_test import (
    CpuRuntime,
    config,
    fake_prepare,
)
from tools.v3.eval_v2_production_tests.store_test import close_streams, complete, fresh
from tools.v3.eval_v2_replan_tests.support import png_frames


def completed(tmp_path):
    store = fresh(tmp_path, episodes=1)
    with store.locked():
        store.begin_task("CloseFridge")
        complete(store, "CloseFridge", 0, success=False)
        close_streams(store, "CloseFridge")
    return store


def media_for(store):
    row = store.rows("CloseFridge")[0]
    directory = store._slot("CloseFridge", 0)
    identity = {k: row[k] for k in ("task", "episode", "attempt_id", "generation")}
    for index in range(row["replans"]):
        frames = png_frames()
        from cosmos_framework.evaluation.robocasa_v2.generated_video import sha

        write_generated(
            directory / "media",
            dict(
                index=index,
                video=frames,
                binding={
                    "episode": identity,
                    "index": index,
                    "transfer": None,
                    "video_sha256": sha(frames),
                },
            ),
            20,
        )
    completion = dict(
        status="COMPLETE",
        task="CloseFridge",
        episode=0,
        attempt_id=row["attempt_id"],
        expected=row["replans"],
        saved=row["replans"],
        acknowledged=row["replans"],
        missing=[],
        server_ack_required=False,
    )
    atomic_json(directory / "generated_media_completion.json", completion)
    return directory, row, completion


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "missing_completion",
        "missing_receipt",
        "missing_MP4",
        "wrong_episode",
        "wrong_ack_authority",
        "truncated_MP4",
    ],
)
def test_media_inventory_changes_only_diagnostic_status_never_Core_SR(tmp_path, fault):
    store = completed(tmp_path)
    directory, row, completion = media_for(store)
    core = (directory / "result.json").read_bytes()
    with store.locked():
        before = store.publish_views()
        scientific = (store.root / "summary.json").read_bytes()
        if fault == "missing_completion":
            (directory / "generated_media_completion.json").unlink()
        elif fault == "wrong_episode":
            atomic_json(
                directory / "generated_media_completion.json",
                {**completion, "episode": 99},
            )
        elif fault == "wrong_ack_authority":
            atomic_json(
                directory / "generated_media_completion.json",
                {**completion, "server_ack_required": True},
            )
        elif fault == "missing_receipt":
            (directory / "media/generated/replan_0000.receipt.json").unlink()
        elif fault == "missing_MP4":
            (directory / "media/generated/replan_0000.mp4").unlink()
        elif fault == "truncated_MP4":
            (directory / "media/generated/replan_0000.mp4").write_bytes(b"truncated")
        report = publish(store)
        assert report["status"] == ("COMPLETE" if fault is None else "MEDIA_INCOMPLETE")
        assert report["independent_of_SR"] is True
        assert (store.root / "summary.json").read_bytes() == scientific
        assert (directory / "result.json").read_bytes() == core
        assert store.publish_views()["failure"] == before["failure"] == 1
    assert row["replans"] > 0


@pytest.mark.parametrize("mode", ["none", "first", "all"])
def test_actual_CLI_explicit_media_failure_exit_does_not_change_qualified_SR(
    tmp_path, capsys, mode
):
    path, cfg = config(tmp_path)
    cfg.update(save_generated_video=mode)
    path.write_text(yaml.safe_dump(cfg))
    code = main(
        ["fresh", "--config", str(path)],
        prepare_inputs=fake_prepare,
        runtime_type=CpuRuntime,
    )
    console = capsys.readouterr()
    report = json.loads(console.out)
    assert code == (1 if mode == "all" else 0)
    assert report["results_qualified"] is True
    stored = json.loads((Path(cfg["output_dir"]) / "summary.json").read_bytes())
    assert "generated_media" not in stored
    assert stored["sr"] == report["sr"]
    if mode == "all":
        assert report["generated_media"]["status"] == "MEDIA_INCOMPLETE"
        assert "MEDIA_INCOMPLETE" in console.err
    else:
        assert "generated_media" not in report and "MEDIA_INCOMPLETE" not in console.err
