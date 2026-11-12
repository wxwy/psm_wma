"""G2 batch scheduler correctness without touching real H100 workloads."""

import json
from pathlib import Path
import sys
import threading
import time

import pytest

from g2.io import ContractError, digest
from g2.offline import batch_render as batch


FAKE_RENDER = r"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

inputs, dst, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
print("PHYSICAL_EGL="+os.environ.get("MUJOCO_EGL_DEVICE_ID",""),
      "CUDA="+os.environ.get("CUDA_VISIBLE_DEVICES",""),
      "PLATFORM="+os.environ.get("PYOPENGL_PLATFORM",""),flush=True)
if mode == "fail":
    sys.exit(17)
if mode == "sleep":
    time.sleep(7)
    sys.exit(0)
dst.mkdir(parents=True, exist_ok=False)
if mode == "no_receipt":
    sys.exit(0)
source=json.loads(inputs.read_text())
frames=[r["frame"] for r in source["states"]]
states=[]
for i, frame in enumerate(frames):
    root=dst/f"state_{i:06d}_frame_{frame:06d}"
    (root/"sixview").mkdir(parents=True)
    image=root/"sixview/floor_top.png"
    image.write_bytes(b"fake-png-bytes-no-GPU")
    sha=hashlib.sha256(image.read_bytes()).hexdigest()
    manifest={
       "frame_id":frame, "training_ready":False,
       "visual_geometry_source":"SOURCE_BOUND_MUJOCO_VISUAL_MESH",
       "view_count":1,
       "views":[{"rgb_file":"sixview/floor_top.png","sha256":sha}],
    }
    (root/"direct_color_views.json").write_text(json.dumps(manifest))
    (root/"alpha_source_layer").mkdir()
    alpha_dir=root/"alpha_source_layer/rooms/0/floor_top"
    alpha_dir.mkdir(parents=True)
    rgba=alpha_dir/"source_rgba.png"
    preview=alpha_dir/"checkerboard_unknown_preview.png"
    rgba.write_bytes(b"source-alpha-diagnostic")
    preview.write_bytes(b"source-alpha-preview")
    files={
       "source_rgba_file":"rooms/0/floor_top/source_rgba.png",
       "source_rgba_sha256":hashlib.sha256(rgba.read_bytes()).hexdigest(),
       "checkerboard_preview_file":"rooms/0/floor_top/checkerboard_unknown_preview.png",
       "checkerboard_preview_sha256":hashlib.sha256(preview.read_bytes()).hexdigest(),
    }
    (root/"alpha_source_layer/alpha_sidecar_manifest.json").write_text(json.dumps(
       {"frame_id":frame, "training_ready":False, "view_count":1,
        "source_visual_mesh_for_transparency":True,
        "view_alpha_layers":[{"view":"rooms/0/floor_top",
                              "frame_id":frame,"alpha_pixel_count":0,**files}]}))
    states.append({"frame":frame, "state_id":i,"view_count":1,
       "view_opaque_visual_geometry_from_source":True,
       "source_surfel_geom_color_training_ready":False})
if mode == "bad_frames":
    states.pop()
receipt={
  "schema":"g2_repository_native_view_episode_v1",
  "complete":True, "training_ready":False,
  "source_inputs_sha256":hashlib.sha256(inputs.read_bytes()).hexdigest(),
  "spatial_state_count":len(frames),
  "view_opaque_geometry_source":"SOURCE_BOUND_VISUAL_MESH",
  "states":states,
}
(dst/"episode_receipt.json").write_text(json.dumps(receipt))
"""


@pytest.fixture
def sample_job(tmp_path):
    def make(job_id="ep00", frame_count=2, layout=1):
        root = tmp_path / f"source_{job_id}"
        root.mkdir()
        input_file = root / "input.json"
        frames = [i * 10 for i in range(frame_count)]
        source = {"layout": layout, "states": [{"frame": frame} for frame in frames]}
        input_file.write_text(json.dumps(source))
        color = root / "color"
        native = root / "native"
        color.mkdir()
        native.mkdir()
        (color / "color_manifest.json").write_text(
            json.dumps(
                {
                    "complete": True,
                    "training_ready": False,
                    "source_inputs_sha256": digest(input_file),
                    "layout": layout,
                    "frames": frames,
                    "complete_episode_states": frame_count,
                    "states": [
                        {"frame": x, "state_id": i} for i, x in enumerate(frames)
                    ],
                }
            )
        )
        (native / "F24_NATIVE_FULL_EPISODE_COMPLETE.json").write_text(
            json.dumps(
                {
                    "complete_state_count": frame_count,
                    "native_color_full_F22_sha_equal_every_state": True,
                    "native_dual_map_same_process": True,
                    "source_known_region_is_TEST_ONLY_NOT_CERTIFIED": True,
                }
            )
        )
        return {
            "id": job_id,
            "inputs": str(input_file),
            "prepared": str(color),
            "native_output": str(native),
        }

    return make


@pytest.fixture
def child_file(tmp_path):
    path = tmp_path / "mock_egl_renderer.py"
    path.write_text(FAKE_RENDER)
    return path


def prepare_root(path):
    path.mkdir()
    for name in ("_logs", "_receipts", "_attempts"):
        (path / name).mkdir()
    return path


def factory(script, mode="ok"):
    def make(py, episode, dest):
        return [str(py), str(script), str(episode.inputs), str(dest), mode]

    return make


def test_gpu_matrix_supports_one_to_eight_cards_and_one_to_eight_workers():
    for gpu_count in (1, 4, 8):
        for workers in range(1, 9):
            slots = batch.available_slots(list(range(gpu_count)), workers)
            assert len(slots) == gpu_count * workers
            assert len(set(s.label for s in slots)) == len(slots)
            assert all(s.gpu in range(gpu_count) for s in slots)
    assert [s.label for s in batch.available_slots([4, 5, 6, 7], 2)][:4] == [
        "GPU4_worker00",
        "GPU5_worker00",
        "GPU6_worker00",
        "GPU7_worker00",
    ]
    for gpus, n in [([0] * 2, 1), (list(range(9)), 1), ([0], 9), ([], 1), ([True], 1)]:
        with pytest.raises(ContractError):
            batch.available_slots(gpus, n)
    assert batch.MAX_GPUS == 8


def test_cli_has_no_hard_vram_cpu_or_timeout_limits_by_default():
    opts = batch.build_parser().parse_args(
        [
            "run",
            "--manifest",
            "/tmp/input.json",
            "--output-root",
            "/tmp/output",
            "--gpus",
            "4,5,6,7",
            "--workers-per-gpu",
            "8",
        ]
    )
    assert opts.workers_per_gpu == 8
    assert opts.timeout_seconds == 0
    assert opts.min_free_mib == 0
    assert opts.gpus == "4,5,6,7"
    assert not hasattr(opts, "cpu_limit")
    assert opts.max_jobs == 0  # explicit launch size to avoid accidental all-data run


def test_manifest_hashes_pin_source_and_reject_obsolete_pixel_reference(
    sample_job, tmp_path
):
    record = sample_job()
    manifest = tmp_path / "jobs.json"
    manifest.write_text(
        json.dumps({"schema": batch.SCHEMA, "training_ready": False, "jobs": [record]})
    )
    path, jobs = batch.read_plan_manifest(manifest)
    assert path == manifest.resolve() and len(jobs) == 1
    assert jobs[0].count == 2
    assert jobs[0].prepared_sha256 == digest(
        Path(record["prepared"]) / "color_manifest.json"
    )
    content = json.loads(Path(record["inputs"]).read_text())
    content["states"][0]["reference_views"] = [{"path": "obsolete"}]
    Path(record["inputs"]).write_text(json.dumps(content))
    with pytest.raises(ContractError, match="obsolete"):
        batch.read_plan_manifest(manifest)


def test_manifest_rejects_wrong_color_source_and_duplicate_episodes(
    sample_job, tmp_path
):
    a = sample_job()
    file = Path(a["prepared"]) / "color_manifest.json"
    data = json.loads(file.read_text())
    data["source_inputs_sha256"] = "a" * 64
    file.write_text(json.dumps(data))
    with pytest.raises(ContractError, match="provenance"):
        batch.pinned_episode(a)
    data["source_inputs_sha256"] = digest(Path(a["inputs"]))
    file.write_text(json.dumps(data))
    root = tmp_path / "jobs.json"
    root.write_text(
        json.dumps({"schema": batch.SCHEMA, "training_ready": False, "jobs": [a, a]})
    )
    with pytest.raises(ContractError, match="duplicate"):
        batch.read_plan_manifest(root)


def test_subprocess_uses_physical_egl_gpu_and_validates_receipt(
    sample_job, tmp_path, child_file
):
    e = batch.pinned_episode(sample_job())
    root = prepare_root(tmp_path / "out")
    slot = batch.Slot(7, 3)
    result = batch.process_job(
        slot,
        e,
        root,
        python=Path(sys.executable),
        repo=tmp_path,
        max_attempts=1,
        timeout_seconds=0,
        min_free_mib=0,
        cancel=threading.Event(),
        command_factory=factory(child_file),
    )
    assert result["status"] == "DONE_NOT_TRAINING_CERTIFIED"
    assert result["attempt"] == 1 and result["view_images"] == 2
    assert result["training_ready"] is False
    log = (root / "_logs/ep00_attempt_0001.log").read_text()
    assert "PHYSICAL_EGL=7" in log and "CUDA=7" in log
    assert "PLATFORM=egl" in log
    assert batch.inspect_existing(root, e)[0]["status"] == "DONE_NOT_TRAINING_CERTIFIED"


def test_retry_and_resume_use_new_immutable_attempt_folders(
    sample_job, tmp_path, child_file
):
    e = batch.pinned_episode(sample_job())
    root = prepare_root(tmp_path / "out")
    slot = batch.Slot(4, 0)

    def fail_first(py, episode, dest):
        mode = "fail" if dest.name == "attempt_0001" else "ok"
        return factory(child_file, mode)(py, episode, dest)

    res = batch.process_job(
        slot,
        e,
        root,
        python=Path(sys.executable),
        repo=tmp_path,
        max_attempts=2,
        timeout_seconds=0,
        min_free_mib=0,
        cancel=threading.Event(),
        command_factory=fail_first,
    )
    assert res["status"] == "DONE_NOT_TRAINING_CERTIFIED"
    assert res["attempt"] == 2
    assert not (root / "ep00/attempt_0001").exists()
    assert (root / "_attempts/ep00_attempt_0001.json").exists()
    assert (root / "ep00/attempt_0002/episode_receipt.json").exists()
    assert batch.inspect_existing(root, e)[1] == 2
    second = batch.process_job(
        slot,
        e,
        root,
        python=Path(sys.executable),
        repo=tmp_path,
        max_attempts=2,
        timeout_seconds=0,
        min_free_mib=0,
        cancel=threading.Event(),
        command_factory=fail_first,
    )
    assert second["reused_existing"] is True
    assert not (root / "ep00/attempt_0003").exists()


def test_exit_zero_without_full_evidence_is_not_success(
    sample_job, tmp_path, child_file
):
    e = batch.pinned_episode(sample_job())
    root = prepare_root(tmp_path / "out")
    result = batch.process_job(
        batch.Slot(4, 0),
        e,
        root,
        python=Path(sys.executable),
        repo=tmp_path,
        max_attempts=1,
        timeout_seconds=0,
        min_free_mib=0,
        cancel=threading.Event(),
        command_factory=factory(child_file, "no_receipt"),
    )
    assert result["status"] == "FAILED_VALIDATION"
    assert batch.inspect_existing(root, e) == (None, 1)
    assert result["training_ready"] is False


def test_timeout_is_optional_and_kills_child_process_group(
    sample_job, tmp_path, child_file
):
    e = batch.pinned_episode(sample_job())
    root = prepare_root(tmp_path / "out")
    started = time.monotonic()
    r = batch.process_job(
        batch.Slot(4, 0),
        e,
        root,
        python=Path(sys.executable),
        repo=tmp_path,
        max_attempts=1,
        timeout_seconds=1,
        min_free_mib=0,
        cancel=threading.Event(),
        command_factory=factory(child_file, "sleep"),
    )
    assert r["status"] == "TIMEOUT"
    assert time.monotonic() - started < 6
    assert r["training_ready"] is False


def test_four_gpu_two_workers_and_eight_workers_are_real_slot_queues(
    sample_job, tmp_path, child_file
):
    jobs = [batch.pinned_episode(sample_job(f"ep{i:02d}")) for i in range(8)]
    root = prepare_root(tmp_path / "out")
    resources = batch.available_slots([4, 5, 6, 7], 2)
    assert len(resources) == 8
    run = batch.run_jobs(
        jobs,
        root,
        resources,
        python=Path(sys.executable),
        repo=tmp_path,
        max_attempts=1,
        timeout_seconds=0,
        min_free_mib=0,
        cancel=threading.Event(),
        command_factory=factory(child_file),
    )
    assert run["selected_jobs"] == 8
    assert run["completed"] == 8 and run["not_done"] == 0
    assert run["remaining_unstarted"] == 0
    assert sum(run["completed_by_gpu"].values()) == 8
    assert len(list((root / "_receipts").glob("*.json"))) == 8
    large = batch.available_slots(list(range(8)), 8)
    assert len(large) == 64
    assert len(set(s.label for s in large)) == 64


def test_pin_plan_detects_repository_or_manifest_changes(
    sample_job, tmp_path, monkeypatch
):
    job = batch.pinned_episode(sample_job())
    repo = tmp_path / "repo"
    repo.mkdir()
    input_manifest = tmp_path / "manifest.json"
    input_manifest.write_text(
        json.dumps(
            {
                "schema": batch.SCHEMA,
                "training_ready": False,
                "jobs": [
                    {
                        "id": job.episode_id,
                        "inputs": str(job.inputs),
                        "prepared": str(job.prepared),
                        "native_output": str(job.native),
                    }
                ],
            }
        )
    )
    monkeypatch.setattr(batch, "source_commit", lambda _: "a" * 64)
    first = batch.pinned_plan(input_manifest, [job], repo, python=Path(sys.executable))
    root = prepare_root(tmp_path / "out")
    batch.ensure_root_plan(root, first)
    batch.ensure_root_plan(root, first)
    monkeypatch.setattr(batch, "source_commit", lambda _: "b" * 64)
    newer = batch.pinned_plan(input_manifest, [job], repo, python=Path(sys.executable))
    with pytest.raises(ContractError, match="another immutable"):
        batch.ensure_root_plan(root, newer)


def test_memory_guard_is_optional_and_avoids_launch(sample_job, tmp_path, monkeypatch):
    e = batch.pinned_episode(sample_job())
    root = prepare_root(tmp_path / "out")
    monkeypatch.setattr(batch, "gpu_free_mib", lambda gpu: 500)
    r = batch.process_job(
        batch.Slot(4, 0),
        e,
        root,
        python=Path(sys.executable),
        repo=tmp_path,
        max_attempts=1,
        timeout_seconds=0,
        min_free_mib=1024,
        cancel=threading.Event(),
        command_factory=lambda *a: pytest.fail("shouldn't launch"),
    )
    assert r["status"] == "BLOCKED_GPU_RESOURCE"
    assert r["available_mib"] == 500
    assert not (root / "ep00").exists()


def test_corrupted_output_does_not_resume_as_success(sample_job, tmp_path, child_file):
    e = batch.pinned_episode(sample_job())
    root = prepare_root(tmp_path / "out")
    kwargs = dict(
        python=Path(sys.executable),
        repo=tmp_path,
        timeout_seconds=0,
        min_free_mib=0,
        cancel=threading.Event(),
        command_factory=factory(child_file),
    )
    slot = batch.Slot(4, 0)
    r = batch.process_job(slot, e, root, max_attempts=1, **kwargs)
    assert r["status"] == "DONE_NOT_TRAINING_CERTIFIED"
    img = root / "ep00/attempt_0001/state_000000_frame_000000/sixview/floor_top.png"
    img.write_bytes(b"malicious-tamper")
    assert batch.inspect_existing(root, e) == (None, 1)
    r = batch.process_job(slot, e, root, max_attempts=2, **kwargs)
    assert r["status"] == "DONE_NOT_TRAINING_CERTIFIED"
    assert r["attempt"] == 2
    assert (root / "ep00/attempt_0001").is_dir()  # immutable history
    assert (root / "ep00/attempt_0002").is_dir()
