"""Send current MuJoCo states to an isolated native nav_sg ROS1 process."""

from __future__ import annotations

import hashlib
import json
import math
import os
import select
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np

from g2.io import ContractError, canonical, digest, read_json, sha
from g2.nav_bridge.snapshot import validate_snapshot
from g2.offline.atomic_6views_geometry import grid_from_source
from g2.offline.atomic_6views_metadata import derive
from g2.offline.atomic_6views_snapshots import _native_source

FRAME_NS = 50_000_000
STATE_ENCODING = "mujoco_fullphysics_with_mocap_f64le_v1"
PERIOD_FRAMES = 20


class NativeSession:
    def __init__(
        self, *, nav_checkout, nav_revision, ros_setup, scratch_root, render_f27=False
    ):
        self.nav_checkout = Path(nav_checkout).resolve(strict=True)
        if (
            not isinstance(nav_revision, str)
            or len(nav_revision) != 40
            or any(char not in "0123456789abcdef" for char in nav_revision)
        ):
            raise ContractError("a full nav_sg commit SHA is required")
        self.nav_revision = nav_revision
        self.ros_setup = Path(ros_setup).resolve(strict=True)
        self.scratch_root = Path(scratch_root).resolve(strict=True)
        tracked_revision = subprocess.check_output(
            ["git", "-C", self.nav_checkout, "rev-parse", "HEAD"], text=True
        ).strip()
        changes = subprocess.check_output(
            ["git", "-C", self.nav_checkout, "status", "--porcelain", "-uno"],
            text=True,
        )
        if tracked_revision != self.nav_revision or changes:
            raise ContractError(
                "nav_sg checkout must match its clean candidate revision"
            )
        self.work = None
        self.process = None
        self.render_f27 = render_f27
        self.live_f27 = None
        self.views = None
        self._output_buffer = bytearray()

    def observe(self, env, frame):
        """Read the real simulator, forwarding only a private MjData copy."""
        if env is not self.env or env.sim.model._model is not self.model:
            raise ContractError("live simulator or compiled model changed")
        row = np.empty(self.state_size, dtype="<f8")
        self.mujoco.mj_getState(self.model, env.sim.data._data, row, self.state_spec)
        if not np.isfinite(row).all() or not math.isclose(
            float(row[0]) - self.start_time,
            frame * FRAME_NS * 1e-9,
            rel_tol=0,
            abs_tol=1e-6,
        ):
            raise ContractError("MuJoCo state time does not match the 20 Hz frontier")
        return row

    def start(self, env, *, episode_id, ep_meta):
        import mujoco

        if self.work is not None or getattr(env, "control_freq", None) != 20:
            raise ContractError("one native session requires one 20 Hz RoboCasa reset")
        self.env = env
        self.episode_id = episode_id
        self.model = env.sim.model._model
        self.mujoco = mujoco
        self.data = mujoco.MjData(self.model)
        # FULLPHYSICS (the training archive format) omits positions and
        # orientations of externally moved mocap bodies in the live model.
        self.state_spec = (
            mujoco.mjtState.mjSTATE_FULLPHYSICS
            | mujoco.mjtState.mjSTATE_MOCAP_POS
            | mujoco.mjtState.mjSTATE_MOCAP_QUAT
        )
        self.state_size = mujoco.mj_stateSize(self.model, self.state_spec)
        self.start_time = float(env.sim.data._data.time)
        row = self.observe(env, 0)
        work = self.work = Path(
            tempfile.mkdtemp(prefix="g2-online-", dir=self.scratch_root)
        )
        compiled = np.empty(mujoco.mj_sizeModel(self.model), dtype=np.uint8)
        mujoco.mj_saveModel(self.model, None, compiled)
        model_sha = hashlib.sha256(compiled).hexdigest()
        del compiled
        self.scene_id = (
            "live_"
            + hashlib.sha256(
                canonical(
                    {"episode_id": episode_id, "compiled_model_sha256": model_sha}
                )
            ).hexdigest()
        )
        self._forward(row)
        role_map, self.geo_meta, _ = derive(
            self.model,
            ep_meta,
            scene_id=self.scene_id,
            state_sha256=hashlib.sha256(row.tobytes()).hexdigest(),
            model_source_sha256=model_sha,
            state_data=self.data,
        )
        grid_plan = grid_from_source(self.model, self.data, self.geo_meta)
        self.source_sha256 = hashlib.sha256(
            canonical(
                {
                    "schema": "psm_wma_live_mujoco_gt_v1",
                    "episode_id": episode_id,
                    "scene_id": self.scene_id,
                    "mujoco_version": mujoco.__version__,
                    "state_encoding": STATE_ENCODING,
                    "native_revision": self.nav_revision,
                    "native_build_source_sha256": self.native_build_sha256,
                    "compiled_model_sha256": model_sha,
                    "geometry_metadata": self.geo_meta,
                    "grid_plan": grid_plan,
                    "collision_mesh_repair_policy": "exact_collinear_edge_v1",
                }
            )
        ).hexdigest()
        if self.render_f27:
            from .live_views import LiveF27

            camera = getattr(env.sim, "_render_context_offscreen", None)
            restore_camera = getattr(
                getattr(camera, "gl_ctx", None), "make_current", None
            )
            if not callable(restore_camera):
                raise ContractError(
                    "F27 requires the active RoboCasa camera EGL context"
                )
            self.live_f27 = LiveF27(
                root=work / "f27",
                model=self.model,
                role_map=role_map,
                model_sha256=model_sha,
                restore_camera=restore_camera,
            )
        self.oracle = _native_source(self.nav_checkout)
        grid = grid_plan["grid"]
        self.grid = self.oracle.Grid(
            tuple(grid["dims"]), tuple(grid["origin"]), grid["resolution"]
        )
        self.points = self.grid.centers()
        self.known_free = self.oracle.certified_region(
            self.points, grid_plan["known_region"]
        )
        self.occupancy_cache = {}
        self.last_grid = self.last_frame = self.snapshot_path = None
        with (work / "native.log").open("wb") as log:
            self.process = subprocess.Popen(
                [
                    "bash",
                    str(self.nav_checkout / "g2/gt/live_geometry.sh"),
                    str(self.ros_setup),
                    str(work / "output"),
                    str(work / "ros"),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                start_new_session=True,
            )
        self._receive("G2_ONLINE_READY", 120)
        return self.publish(0, row)

    def _forward(self, row):
        self.mujoco.mj_setState(self.model, self.data, row, self.state_spec)
        self.mujoco.mj_forward(self.model, self.data)

    def _receive(self, prefix, timeout):
        deadline = time.monotonic() + timeout
        fd = self.process.stdout.fileno()
        while time.monotonic() < deadline:
            line, sep, rest = self._output_buffer.partition(b"\n")
            if sep:
                self._output_buffer = rest
                if line.startswith(b"G2_ONLINE_"):
                    words = line.decode("ascii").split()
                    if words[0] == prefix:
                        return words[1:]
                    raise ContractError(
                        f"unexpected native reply {words}; see {self.work}"
                    )
                continue
            ready, _, _ = select.select(
                [fd], [], [], max(0, deadline - time.monotonic())
            )
            if not ready:
                break
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            self._output_buffer.extend(chunk)
            if len(self._output_buffer) > 1 << 20:
                raise ContractError("native protocol emitted an oversized line")
        raise ContractError(
            f"native process did not acknowledge {prefix}; see {self.work}"
        )

    def publish(self, frame, row):
        if (self.last_frame is None and frame != 0) or (
            self.last_frame is not None and frame != self.last_frame + PERIOD_FRAMES
        ):
            raise ContractError(
                "native publication must follow the 1 Hz simulation schedule"
            )
        self._forward(row)
        grid_states, objects, _, _ = self.oracle.extract(
            self.model,
            self.data,
            self.grid,
            self.geo_meta,
            geometry="collision",
            include_surfaces=False,
            cached_points=self.points,
            known_free_mask=self.known_free,
            occupancy_cache=self.occupancy_cache,
            repair_exact_collinear_collision=True,
        )
        with tempfile.TemporaryDirectory(prefix="packet-", dir=self.work) as name:
            packet = Path(name)
            state_payload = row.tobytes()
            (packet / "state.bin").write_bytes(state_payload)
            state_hash = hashlib.sha256(state_payload).hexdigest()
            grid_hash = "-"
            if not np.array_equal(self.last_grid, grid_states):
                self.oracle.write_grid(
                    packet / "grid.txt",
                    self.grid,
                    grid_states,
                    self.scene_id,
                    self.source_sha256,
                    frame,
                )
                grid_hash = digest(packet / "grid.txt")
            self.oracle.write_objects(
                packet / "objects.txt",
                objects,
                self.scene_id,
                self.source_sha256,
                frame,
            )
            objects_hash = digest(packet / "objects.txt")
            stamp = frame * FRAME_NS
            manifest = {
                "schema": "nav_sg_online_oracle_frame_v1",
                "episode_id": self.episode_id,
                "scene_id": self.scene_id,
                "source_sha256": self.source_sha256,
                "frame_id": frame,
                "timestamp_ns": stamp,
                "state_sha256": state_hash,
                "state_encoding": STATE_ENCODING,
                "grid_sha256": grid_hash,
                "objects_sha256": objects_hash,
            }
            manifest_bytes = canonical(manifest)
            (packet / "manifest.json").write_bytes(manifest_bytes)
            if any(ord(char) < 32 for char in name):
                raise ContractError("native packet path contains a control character")
            self.process.stdin.write(
                (
                    f"FRAME {frame} {stamp} {state_hash} {grid_hash} {objects_hash} "
                    + json.dumps(name, ensure_ascii=False)
                    + "\n"
                ).encode()
            )
            self.process.stdin.flush()
            receipt = self._receive("G2_ONLINE_OK", 180)

        path = self.work / "output" / f"frame_{frame}" / "spatial_snapshot"
        if (
            len(receipt) != 2
            or receipt[0] != str(frame)
            or (path / "SNAPSHOT_COMPLETE").read_bytes()
            != b"nav_sg_spatial_snapshot_v1\n"
            or digest(path / "snapshot.json") != sha(receipt[1])
        ):
            raise ContractError("native snapshot publication receipt differs")
        snapshot = validate_snapshot(read_json(path / "snapshot.json"))
        binding = snapshot.get("full_map_source", {})
        if (
            snapshot["scene_id"] != self.scene_id
            or snapshot["source_sha256"] != self.source_sha256
            or snapshot["native_build_source_sha256"] != self.native_build_sha256
            or snapshot["frame_id"] != frame
            or snapshot["timestamp_ns"] != stamp
            or binding.get("live_frame") is not True
            or binding.get("online_episode_id") != self.episode_id
            or binding.get("live_state_sha256") != state_hash
            or binding.get("native_manifest_sha256")
            != hashlib.sha256(manifest_bytes).hexdigest()
        ):
            raise ContractError(
                "native snapshot does not attest the current live state"
            )
        if self.live_f27 is not None:
            self.views = self.live_f27.publish(
                snapshot, data=self.data, snapshot_path=path / "snapshot.json"
            )
        evidence = self.work / "source_frames.jsonl"
        with evidence.open("ab") as log:
            log.write(canonical(dict(manifest, snapshot_sha256=receipt[1])) + b"\n")
        if self.last_frame not in (None, 0):
            shutil.rmtree(self.snapshot_path.parent)
        self.last_grid, self.last_frame, self.snapshot_path = grid_states, frame, path
        return snapshot

    def close(self):
        process, self.process = self.process, None
        if process is None:
            if self.live_f27 is not None:
                self.live_f27.close()
            return
        try:
            if process.poll() is None:
                process.stdin.write(b"QUIT\n")
                process.stdin.flush()
                process.wait(timeout=8)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        finally:
            process.stdin.close()
            process.stdout.close()
            if self.live_f27 is not None:
                self.live_f27.close()
