"""Install the source-controlled G2 replay viewer into an existing compact output.

The browser discovers completed Episodes from the live HTTP directory listing.
The mapping catalog is immutable; videos are symlinked, never copied.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile

SAFE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
CAMERAS = {
    "left": "observation.images.robot0_agentview_left",
    "right": "observation.images.robot0_agentview_right",
    "wrist": "observation.images.robot0_eye_in_hand",
}
FILES = ("index.html", "viewer.css", "viewer.js", "directory_picker.js")


def _phrase(value):
    if isinstance(value, str):
        return value
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (tuple, list)):
        return str(value[0]) if value else ""
    return str(value or "")


def _write_atomic(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".viewer_tmp_", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as writer:
            writer.write(data)
            writer.flush()
            os.fsync(writer.fileno())
        os.chmod(temp, 0o644)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def build_catalog(mapping: Path, raw_root: Path):
    import pandas as pd

    frame = pd.read_parquet(mapping)
    cols = {"task_class", "local_episode_index", "global_episode_index",
            "tasks_phrasing", "length"}
    if not cols.issubset(frame.columns) or len(frame) != 9126:
        raise ValueError("expected exactly 9,126 RoboCasa target-atomic mappings")
    tasks, global_ids = [], set()
    for task, group in frame.groupby("task_class", sort=True):
        if not SAFE_NAME.fullmatch(task):
            raise ValueError("unsafe task name " + repr(task))
        info_paths = sorted((raw_root / task).glob("*/lerobot/meta/info.json"))
        if len(info_paths) != 1:
            raise ValueError(f"{task}: expected one LeRobot source; found {len(info_paths)}")
        info_path = info_paths[0]
        info = json.loads(info_path.read_text())
        if int(info["fps"]) != 20 or int(info["chunks_size"]) < 1:
            raise ValueError(f"unexpected video fps/chunk size for {task}")
        template = info["video_path"]
        expected = "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4"
        if template != expected:
            raise ValueError("unrecognized source video template: " + template)
        episodes, local_ids = [], set()
        for ep in group.sort_values("local_episode_index").itertuples(index=False):
            gid, lid, frames = int(ep.global_episode_index), int(ep.local_episode_index), int(ep.length)
            if gid in global_ids or lid in local_ids or frames < 1:
                raise ValueError("invalid or duplicate Episode ID")
            global_ids.add(gid)
            local_ids.add(lid)
            episodes.append({"global_id": gid, "local_id": lid,
                             "frames": frames, "instruction": _phrase(ep.tasks_phrasing)})
        tasks.append({
            "name": task, "count": len(episodes),
            "source_dir": info_path.parent.parent.relative_to(raw_root).as_posix(),
            "chunks_size": int(info["chunks_size"]), "video_path": template,
            "episodes": episodes,
        })
    if len(global_ids) != 9126:
        raise ValueError("global index coverage incomplete")
    return {"schema": "g2_replay_viewer_catalog_v1", "source_fps": 20,
            "spatial_fps": 2, "total_episodes": 9126,
            "cameras": CAMERAS, "tasks": tasks}


def install(mapping: Path, raw_root: Path, output_root: Path) -> Path:
    mapping, raw_root, output_root = (
        mapping.resolve(strict=True), raw_root.resolve(strict=True),
        output_root.resolve(strict=True))
    if not (output_root / "tasks").is_dir():
        raise ValueError("output root must contain tasks/")
    catalog = build_catalog(mapping, raw_root)
    view = output_root / "view"
    if view.is_symlink():
        raise ValueError("view path may not be a symlink")
    view.mkdir(exist_ok=True)
    for name in FILES:
        _write_atomic(view / name, (Path(__file__).parent / name).read_bytes())
    _write_atomic(view / "catalog.json", json.dumps(
        catalog, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    link = view / "source_videos"
    if link.is_symlink():
        if link.resolve(strict=True) != raw_root:
            raise ValueError("existing source video link differs from expected root")
    elif link.exists():
        raise ValueError("source_videos already exists and is not a symlink")
    else:
        link.symlink_to(raw_root, target_is_directory=True)
    return view


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    view = install(args.mapping, args.raw_root, args.output_root)
    print("G2_VIEWER_READY", view)
    print("Videos symlinked; no changes made to production Episodes.")


if __name__ == "__main__":
    main()
