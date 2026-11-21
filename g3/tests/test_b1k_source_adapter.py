"""CPU-only regression for B1K Task0 source binding (no Isaac Sim)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from g3.behavior1k.source_adapter import (
    SourceBindingError,
    bind_episodes,
    initial_scene,
)


def _state(x):
    return {"root_link": {"pos": [x, 2.0, 0.5], "ori": [0.0, 0.0, 0.0, 1.0]}}


class TaskSourceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.scene_file = self.root / "scene.json"
        self.inst_dir = self.root / "task_instances"
        self.inst_dir.mkdir()
        self.raw_dir = self.root / "raw"
        self.raw_dir.mkdir()
        self.annotations = self.root / "datasets/2026-challenge-demos/annotations/task-0000"
        self.annotations.mkdir(parents=True)
        for rid in (10, 20):
            (self.raw_dir / f"episode_{rid:08d}.hdf5").write_bytes(b"fixture")
            (self.annotations / f"episode_{rid:08d}.json").write_text("{}")
        self.scene = {
            "metadata": {"task": {"inst_to_name": {
                "agent.n.01_1": "robot",
                "radio_receiver.n.01_1": "radio_1",
                "table.n.02_1": "table_1",
            }}},
            "objects_info": {"init_info": {
                name: {"args": {"name": name, "category": category, "model": "demo",
                                "scale": [1.0, 1.0, 1.0]}}
                for name, category in (("radio_1", "radio"), ("table_1", "table"))
            }},
            "state": {"registry": {"object_registry": {
                "radio_1": _state(1.0), "table_1": _state(2.0)
            }}},
        }
        self.scene_file.write_text(json.dumps(self.scene))
        self.rows = [
            {"episode_index": 0, "task_index": 0, "tasks": ["turning_on_radio"],
             "task_instance_id": 1, "raw_episode_id": 10,
             "annotation_path": "annotations/task-0000/episode_00000010.json"},
            {"episode_index": 1, "task_index": 0, "tasks": ["turning_on_radio"],
             "task_instance_id": 2, "raw_episode_id": 20,
             "annotation_path": "annotations/task-0000/episode_00000020.json"},
        ]
        self.inst_file = self.inst_dir / (
            "house_double_floor_lower_task_turning_on_radio_0_1_template-tro_state.json"
        )
        self.inst_file.write_text(json.dumps({
            "radio_receiver.n.01_1": _state(3.0),
            "table.n.02_1": _state(4.0),
            "robot_poses": {"R1Pro": [
                {"position": [5, 5, 0], "orientation": [0, 0, 0, 1]}
            ]},
        }))

    def _bind(self, rows=None):
        return bind_episodes(
            root=self.root,
            scene=initial_scene(self.root, self.scene_file),
            rows=self.rows if rows is None else rows,
            task_name="turning_on_radio",
            task_index=0,
            scene_model="house_double_floor_lower",
            scene_instance_dir=self.inst_dir,
            raw_data_dir=self.raw_dir,
            annotations_dir=self.annotations,
        )

    def test_present_and_missing_task_instance_not_invented(self):
        scene = initial_scene(self.root, self.scene_file)
        self.assertEqual(len(scene["objects"]), 2)
        self.assertFalse(scene["full_map_ready"])
        self.assertIsNone(scene["native_room_geometry"])
        index = self._bind()
        self.assertEqual(index["counts"], {
            "total": 2, "task_initial_state_present": 1,
            "missing_public_task_state": 1,
        })
        self.assertEqual(index["gate"], "SOURCE_BINDING_PARTIAL")
        self.assertFalse(index["full_map_ready"])
        first = index["episodes"][0]
        self.assertEqual(
            first["task_object_states"]["radio_receiver.n.01_1"]["pose_raw"]["pos_raw"],
            [3.0, 2.0, 0.5],
        )
        self.assertEqual(index["episodes"][1]["task_object_states"], None)
        self.assertIsNone(index["episodes"][1]["state_file_sha256"])

    def test_task_mapping_missing_object_rejected(self):
        self.scene["metadata"]["task"]["inst_to_name"][
            "radio_receiver.n.01_1"
        ] = "nonexistent_object"
        self.scene_file.write_text(json.dumps(self.scene))
        with self.assertRaises(SourceBindingError):
            initial_scene(self.root, self.scene_file)

    def test_nonfinite_geometry_frame_pose_rejected(self):
        self.scene["state"]["registry"]["object_registry"][
            "radio_1"
        ]["root_link"]["pos"][0] = float("nan")
        self.scene_file.write_text(json.dumps(self.scene))
        with self.assertRaises(SourceBindingError):
            initial_scene(self.root, self.scene_file)

    def test_duplicate_episode_task_instance_rejected(self):
        bad_rows = [dict(row) for row in self.rows]
        bad_rows[1]["task_instance_id"] = 1
        with self.assertRaises(SourceBindingError):
            self._bind(bad_rows)

    def test_missing_target_in_task_state_rejected(self):
        self.inst_file.write_text(json.dumps({"robot_poses": {
            "R1Pro": [{"position": [5, 5, 0], "orientation": [0, 0, 0, 1]}]
        }}))
        with self.assertRaises(SourceBindingError):
            self._bind()


if __name__ == "__main__":
    unittest.main()
