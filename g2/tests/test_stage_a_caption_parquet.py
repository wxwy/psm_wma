"""Real temporary Parquet entry tests; skip honestly if Arrow is unavailable."""

import pytest

from g2.io import ContractError
from g2.offline.language_context import load_flat_captions

ORIGINAL = "  Synthetic caption: put the café cup on the shelf.\n保留原文\t"


@pytest.fixture
def parquet(tmp_path):
    pa = pytest.importorskip(
        "pyarrow",
        reason="existing local interpreter has no PyArrow; no install/new environment permitted",
    )
    import pyarrow.parquet as pq

    (tmp_path / "meta").mkdir()
    (tmp_path / "data/chunk-000").mkdir(parents=True)
    pq.write_table(
        pa.table(
            {
                "episode_index": [9, 9, 10],
                "frame_index": [0, 1, 0],
                "task_index": [7, 7, 19],
            }
        ),
        tmp_path / "data/chunk-000/file-000.parquet",
    )

    def write(columns):
        pq.write_table(pa.table(columns), tmp_path / "meta/tasks.parquet")
        return tmp_path

    return write


@pytest.mark.parametrize(
    "columns",
    [
        {"task_index": [19, 7], "__index_level_0__": ["Other caption", ORIGINAL]},
        {"task_index": [19, 7], "task": ["Other caption", ORIGINAL]},
        {"__index_level_0__": [19, 7], "task": ["Other caption", ORIGINAL]},
        {"task_index": [7], "task": [ORIGINAL], "__index_level_0__": [ORIGINAL]},
        {"task_index": [7], "task": [ORIGINAL], "__index_level_0__": [0]},
    ],
)
def test_actual_parquet_loader_preserves_original_and_id(parquet, columns):
    root = parquet(columns)
    captions, authority = load_flat_captions(
        root, episode_id=9, frames=[0, 1], ep_meta_lang=ORIGINAL
    )
    assert captions[0]["original_text"] == ORIGINAL
    assert captions[1]["task_index"] == 7 and captions[1]["frame_index"] == 1
    assert authority["authority"] == "FLAT_FRAME_TASK_INDEX_TO_META_TASKS_PARQUET"
    assert set(authority["source_files_sha256"]) == {
        str(root / "meta/tasks.parquet"),
        str(root / "data/chunk-000/file-000.parquet"),
    }


@pytest.mark.parametrize(
    "columns",
    [
        {
            "task_index": [7],
            "task": [ORIGINAL],
            "__index_level_0__": ["Conflicting caption"],
        },
        {"task_index": [7, 7], "__index_level_0__": [ORIGINAL, ORIGINAL]},
        {"__index_level_0__": [ORIGINAL]},
        {"task_index": [True], "__index_level_0__": [ORIGINAL]},
    ],
)
def test_actual_parquet_loader_rejects_ambiguous_or_invalid_table(parquet, columns):
    root = parquet(columns)
    with pytest.raises(ContractError):
        load_flat_captions(root, episode_id=9, frames=[0, 1], ep_meta_lang=ORIGINAL)


def test_actual_parquet_loader_does_not_use_ep_meta_as_replacement(parquet):
    root = parquet({"task_index": [7], "__index_level_0__": [ORIGINAL]})
    with pytest.raises(ContractError, match="disagree"):
        load_flat_captions(
            root, episode_id=9, frames=[0, 1], ep_meta_lang=ORIGINAL.strip()
        )
