"""Fresh official RoboCasa discovery without flat mapping or pre-exported Depth."""
import json
from pathlib import Path

import pytest

from g2.offline import atomic_6views_catalog as catalog


def official(root, task, ids):
    top = root / task / "20250820" / "lerobot"
    meta = top / "meta"
    meta.mkdir(parents=True, exist_ok=True)
    with (meta / "episodes.jsonl").open("w", encoding="utf-8") as f:
        for eid, length in ids:
            f.write(json.dumps({"episode_index": eid, "length": length}) + "\n")
            extra = top / "extras" / f"episode_{eid:06d}"
            extra.mkdir(parents=True, exist_ok=True)
            for name in catalog.REQUIRED:
                (extra / name).write_bytes(b"source")
    return top


def test_fresh_raw_dataset_without_mapping_and_depth(tmp_path):
    raw = tmp_path / "atomic"
    official(raw, "OpenDrawer", [(0, 21), (1, 32), (2, 10)])
    official(raw, "CloseFridge", [(0, 24), (1, 15)])
    records, roots, source = catalog.discover_flat(tmp_path / "missing.parquet", raw, log=None)
    assert source == "official_episodes_jsonl"
    assert [row["task_class"] for row in records] == ["CloseFridge"] * 2 + ["OpenDrawer"] * 3
    assert [row["global_episode_index"] for row in records] == list(range(5))
    assert [row["length"] for row in records] == [24, 15, 21, 32, 10]
    assert len(roots) == 2
    from g2.offline import atomic_6views_plan as planner
    # Fresh raw archive: no pre-exported data, no mapping parquet, no Depth.
    for i, row in enumerate(records):
        source = roots[row["task_class"]] / "extras" / f"episode_{row['local_episode_index']:06d}"
        (source / "ep_meta.json").write_text(
            json.dumps({"layout_id": i + 1, "style_id": 1}))
    found, layouts = planner.discover(tmp_path / "missing.parquet", raw,
                                       tmp_path / "missing_depth", expected=5, log=None)
    assert len(found) == 5 and len(layouts) == 5
    assert all(row["depth"] is None for row in found)
    chosen, counts = planner.select(found, tasks=["OpenDrawer"], episodes_per_task=None)
    assert len(chosen) == 3 and counts == {"OpenDrawer": 3}
    summary = planner.build(tmp_path / "missing.parquet", raw, tmp_path / "missing_depth",
                            tmp_path / "plan", tmp_path / "published", expected=5,
                            tasks=["OpenDrawer"], episodes_per_task=None)
    assert summary["mapping_source"] == "official_episodes_jsonl"
    assert summary["episodes_total"] == 3
    assert summary["production_started"] is False
    assert not (tmp_path / "missing.parquet").exists()
    assert not (tmp_path / "published").exists()


def test_fresh_catalog_rejects_gaps_and_missing_originals(tmp_path):
    raw = tmp_path / "atomic"
    top = official(raw, "OpenDrawer", [(0, 20), (2, 25)])
    with pytest.raises(catalog.CatalogError, match="missing/duplicate"):
        catalog.discover_raw(raw, log=None)
    (top / "meta/episodes.jsonl").write_text(
        json.dumps({"episode_index": 0, "length": 20}) + "\n"
        + json.dumps({"episode_index": 1, "length": 21}) + "\n")
    with pytest.raises(catalog.CatalogError, match="inventory differ"):
        catalog.discover_raw(raw, log=None)


def test_fresh_catalog_rejects_ambiguous_roots(tmp_path):
    raw = tmp_path / "atomic"
    official(raw, "OpenDrawer", [(0, 20)])
    (raw / "OpenDrawer/20250821/lerobot").mkdir(parents=True)
    with pytest.raises(catalog.CatalogError, match="exactly one"):
        catalog.discover_raw(raw, log=None)


def test_raw_catalog_rejects_invalid_episode_number(tmp_path):
    raw = tmp_path / "atomic"
    root = official(raw, "OpenDrawer", [(0, 20)])
    (root / "meta/episodes.jsonl").write_text(json.dumps({
        "episode_index": True, "length": 20}) + "\n")
    with pytest.raises(catalog.CatalogError, match="invalid official"):
        catalog.discover_raw(raw, log=None)
