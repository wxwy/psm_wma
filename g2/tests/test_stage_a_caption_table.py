"""Authoritative task-table contracts independent of Arrow availability."""

import pytest

from g2.io import ContractError
from g2.offline.language_context import normalize_task_table, resolve_caption_rows

ORIGINAL = "  Place the café cup on the shelf.\n保留原文\t"


@pytest.mark.parametrize(
    "rows,columns",
    [
        (
            [
                {"task_index": 19, "task": "Other instruction"},
                {"task_index": 7, "task": ORIGINAL},
            ],
            ["task_index", "task"],
        ),
        (
            [
                {"task_index": 19, "__index_level_0__": "Other instruction"},
                {"task_index": 7, "__index_level_0__": ORIGINAL},
            ],
            ["task_index", "__index_level_0__"],
        ),
        (
            [
                {"__index_level_0__": 19, "task": "Other instruction"},
                {"__index_level_0__": 7, "task": ORIGINAL},
            ],
            ["__index_level_0__", "task"],
        ),
        (
            [{"task_index": 7, "task": ORIGINAL, "__index_level_0__": ORIGINAL}],
            ["task_index", "task", "__index_level_0__"],
        ),
        (
            [{"task_index": 7, "task": ORIGINAL, "__index_level_0__": 0}],
            ["task_index", "task", "__index_level_0__"],
        ),
    ],
)
def test_explicit_layouts_preserve_caption_bytes_and_nonordinal_task_ids(rows, columns):
    table = normalize_task_table(rows, columns)
    frame_rows = [dict(episode_index=9, frame_index=f, task_index=7) for f in (0, 1)]
    captions = resolve_caption_rows(
        frame_rows, table, frames=[0, 1], episode_id=9, ep_meta_lang=ORIGINAL
    )
    assert captions[0]["original_text"].encode() == ORIGINAL.encode()
    assert captions[1]["original_text"] == ORIGINAL
    assert captions[1]["task_index"] == 7
    assert captions[1]["episode_index"] == 9 and captions[1]["frame_index"] == 1


@pytest.mark.parametrize(
    "rows,columns",
    [
        (
            [{"task_index": 7, "task": "canonical", "__index_level_0__": "conflict"}],
            ["task_index", "task", "__index_level_0__"],
        ),
        (
            [{"task_index": 7, "task": ORIGINAL}, {"task_index": 7, "task": ORIGINAL}],
            ["task_index", "task"],
        ),
        ([{"task_index": 7, "task": ORIGINAL}], ["task_index", "task", "task"]),
        ([{"__index_level_0__": ORIGINAL}], ["__index_level_0__"]),
        ([{"task": ORIGINAL}], ["task"]),
        ([{"task_index": 7}], ["task_index"]),
        (
            [{"task_index": True, "__index_level_0__": ORIGINAL}],
            ["task_index", "__index_level_0__"],
        ),
        (
            [{"task_index": "7", "__index_level_0__": ORIGINAL}],
            ["task_index", "__index_level_0__"],
        ),
        ([{"__index_level_0__": "7", "task": ORIGINAL}], ["__index_level_0__", "task"]),
        ([{"task_index": -1, "task": ORIGINAL}], ["task_index", "task"]),
        (
            [{"task_index": 7, "__index_level_0__": None}],
            ["task_index", "__index_level_0__"],
        ),
        (
            [{"task_index": 7, "__index_level_0__": 12}],
            ["task_index", "__index_level_0__"],
        ),
        (
            [{"task_index": 7, "task": None, "__index_level_0__": ORIGINAL}],
            ["task_index", "task", "__index_level_0__"],
        ),
    ],
)
def test_incomplete_ambiguous_or_invalid_tables_never_infer_ids_or_fallback_text(
    rows, columns
):
    with pytest.raises(ContractError):
        normalize_task_table(rows, columns)


def test_authority_crosschecks_still_reject_text_episode_frame_and_unknown_task():
    table = normalize_task_table(
        [{"task_index": 7, "__index_level_0__": ORIGINAL}],
        ["task_index", "__index_level_0__"],
    )
    row = dict(episode_index=9, frame_index=0, task_index=7)
    for change, frames, episode, text in [
        ({}, [0], 9, ORIGINAL.strip()),
        ({"episode_index": 10}, [0], 9, ORIGINAL),
        ({"task_index": 0}, [0], 9, ORIGINAL),
        ({}, [1], 9, ORIGINAL),
    ]:
        with pytest.raises(ContractError):
            resolve_caption_rows(
                [dict(row, **change)],
                table,
                frames=frames,
                episode_id=episode,
                ep_meta_lang=text,
            )
