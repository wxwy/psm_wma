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
    src_id="TEST_ONLY_FAKE_SOURCE_SHA"
    scene_id="TEST_ONLY_FAKE_LAYOUT"
    native_name="rooms/0/floor_top"
    native_dir=root/"g2_original_gpu"/native_name
    native_dir.mkdir(parents=True)
    for filename in ("geometry.npz","view.json","geometry_valid.png","color_valid.png"):
        (native_dir/filename).write_bytes(b"FAKE_PROOF_CONTENT_NOT_REAL_RENDER")
    (root/"g2_original_gpu/views.json").write_text(json.dumps({
        "frame_id":frame,"source_sha256":src_id,"training_ready":False,
        "views":{native_name:{"image_generated":True}}
    }))
    (root/"surface_registry.json").write_text(json.dumps({
        "schema":"g2_surface_registry_v1","frame_id":frame,
        "scene_id":scene_id,"source_sha256":src_id,
        "native_scene_graph_modified":False,
        "surfaces":[{"surface_id":1}],"uncertain_surface_ids":[]
    }))
    manifest={
       "frame_id":frame, "training_ready":False,
       "scene_id":scene_id, "source_sha256":src_id,
       "visual_geometry_source":"SURFACE_REGISTRY_VISUAL_GEOMETRY",
       "surface_material_identity_per_pixel":True,
       "source_scene_graph_unchanged":True,
       "unknown_visual_color_regions_retained":True,
       "transparent_visible_pixels":0,"unbound_visible_pixels":0,
       "view_count":1,
       "views":[{"rgb_file":"sixview/floor_top.png","sha256":sha,
                 "native_view":native_name}],
    }
    (root/"direct_color_views.json").write_text(json.dumps(manifest))
    states.append({"frame":frame, "state_id":i,"view_count":1,
       "view_opaque_visual_geometry_from_source":True,
       "source_surfel_geom_color_training_ready":False,
       "surface_registry_count":1,"transparent_visible_pixels":0,
       "alpha_sidecar_count":0,"unbound_visible_pixels":0})
if mode == "bad_frames":
    states.pop()
receipt={
  "schema":"g2_repository_native_view_episode_v1",
  "complete":True, "training_ready":False,
  "source_inputs_sha256":hashlib.sha256(inputs.read_bytes()).hexdigest(),
  "spatial_state_count":len(frames),
  "view_opaque_geometry_source":("SOURCE_BOUND_VISUAL_MESH"
                                 if mode=="legacy" else "SURFACE_REGISTRY_VISUAL_GEOMETRY"),
  "semantic_owner_optional":True,
  "source_material_identity_per_pixel":True,
  "native_scene_graph_modified":False,
  "source_alpha_model":"FRONT_SURFACE_PER_GEOM_SORTED_ALPHA_NO_REFRACTION",
  "renderer_backend":"gpu",
  "view_meters_per_pixel":0.01,
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


def test_corrupted_receipt_does_not_resume_as_success(sample_job, tmp_path, child_file):
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
    receipt = root / "ep00/attempt_0001/episode_receipt.json"
    content = json.loads(receipt.read_text())
    content["complete"] = False
    receipt.write_text(json.dumps(content))
    assert batch.inspect_existing(root, e) == (None, 1)
    r = batch.process_job(slot, e, root, max_attempts=2, **kwargs)
    assert r["status"] == "DONE_NOT_TRAINING_CERTIFIED"
    assert r["attempt"] == 2
    assert (root / "ep00/attempt_0001").is_dir()  # immutable history
    assert (root / "ep00/attempt_0002").is_dir()


@pytest.mark.parametrize("sha", ["a" * 40, "b" * 64])
def test_git_head_accepts_git_sha1_and_sha256_repository_modes(
    monkeypatch, tmp_path, sha
):
    class Result:
        stdout = sha + "\n"

    monkeypatch.setattr(batch.subprocess, "run", lambda *args, **kwargs: Result())
    assert batch.source_commit(tmp_path) == sha


@pytest.mark.parametrize("bad_sha", ["a" * 39, "b" * 41, "c" * 65, "g" * 40])
def test_git_head_rejects_invalid_or_truncated_object_ids(
    monkeypatch, tmp_path, bad_sha
):
    class Result:
        stdout = bad_sha + "\n"

    monkeypatch.setattr(batch.subprocess, "run", lambda *args, **kwargs: Result())
    with pytest.raises(ContractError, match="pin repository"):
        batch.source_commit(tmp_path)



def test_renderer_is_configurable_and_f27_is_default(sample_job, tmp_path):
    e = batch.pinned_episode(sample_job())
    parser = batch.build_parser()
    base = ["plan", "--manifest", str(tmp_path / "input.json"),
            "--output-root", str(tmp_path / "out")]
    assert parser.parse_args(base).renderer == "f27"
    assert parser.parse_args(base + ["--renderer", "legacy"]).renderer == "legacy"
    default = batch.child_command(Path(sys.executable), e, tmp_path / "output")
    old = batch.child_command(Path(sys.executable), e, tmp_path / "output", "legacy")
    assert "--surface-registry-source" in default and "--visual-mesh-source" not in default
    assert "--visual-mesh-source" in old and "--surface-registry-source" not in old
    with pytest.raises(ContractError, match="renderer"):
        batch.child_command(Path(sys.executable), e, tmp_path / "output", "other")


def test_legacy_receipt_is_rejected_by_f27_batch(sample_job, tmp_path, child_file):
    e = batch.pinned_episode(sample_job())
    root = prepare_root(tmp_path / "out")
    result = batch.process_job(
        batch.Slot(4, 0), e, root,
        python=Path(sys.executable), repo=tmp_path,
        max_attempts=1, timeout_seconds=0, min_free_mib=0,
        cancel=threading.Event(),
        command_factory=factory(child_file, "legacy"),
    )
    assert result["status"] == "FAILED_VALIDATION"
    assert result["training_ready"] is False


def test_explicit_legacy_renderer_can_accept_legacy_receipt(sample_job, tmp_path, child_file):
    e = batch.pinned_episode(sample_job())
    root = prepare_root(tmp_path / "out")
    result = batch.process_job(
        batch.Slot(4, 0), e, root,
        python=Path(sys.executable), repo=tmp_path,
        max_attempts=1, timeout_seconds=0, min_free_mib=0,
        cancel=threading.Event(),
        renderer="legacy",
        command_factory=factory(child_file, "legacy"),
    )
    assert result["status"] == "DONE_NOT_TRAINING_CERTIFIED"
    assert result["renderer"] == "legacy"
    assert batch.inspect_existing(root, e, renderer="legacy")[0]["renderer"] == "legacy"
    assert batch.inspect_existing(root, e, renderer="f27") == (None, 1)


def test_receipt_validation_does_not_rehash_images(sample_job, tmp_path, child_file, monkeypatch):
    e = batch.pinned_episode(sample_job())
    root = prepare_root(tmp_path / "out")
    result = batch.process_job(
        batch.Slot(4, 0), e, root,
        python=Path(sys.executable), repo=tmp_path,
        max_attempts=1, timeout_seconds=0, min_free_mib=0,
        cancel=threading.Event(),
        command_factory=factory(child_file),
    )
    assert result["status"] == "DONE_NOT_TRAINING_CERTIFIED"
    def never_digest(*args, **kwargs):
        raise AssertionError("completion rehashed output files")
    monkeypatch.setattr(batch, "digest", never_digest)
    check = batch.validate_episode_receipt(root/"ep00/attempt_0001", e)
    assert check["view_images"] == 2
    assert check["renderer"] == "f27"
