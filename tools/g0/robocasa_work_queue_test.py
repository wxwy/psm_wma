from __future__ import annotations

import json
import socket
from pathlib import Path

from tools.g0.robocasa_work_queue import atomic_write_json, release_claim, task_manifest_path, try_claim_task


def test_claim_is_exclusive_and_done_manifest_blocks_reclaim(tmp_path: Path) -> None:
    first = try_claim_task(
        output_root=tmp_path,
        task_slug="CloseFridge",
        task_class="CloseFridge",
        worker_id="0",
    )
    assert first is not None

    second = try_claim_task(
        output_root=tmp_path,
        task_slug="CloseFridge",
        task_class="CloseFridge",
        worker_id="1",
    )
    assert second is None

    atomic_write_json(
        task_manifest_path(tmp_path, "CloseFridge"),
        {"tasks": [{"task_class": "CloseFridge"}]},
    )
    release_claim(first)

    assert (
        try_claim_task(
            output_root=tmp_path,
            task_slug="CloseFridge",
            task_class="CloseFridge",
            worker_id="2",
        )
        is None
    )


def test_dead_local_owner_is_reclaimed(tmp_path: Path) -> None:
    claim = try_claim_task(
        output_root=tmp_path,
        task_slug="OpenDrawer",
        task_class="OpenDrawer",
        worker_id="0",
    )
    assert claim is not None

    (claim / "owner.json").write_text(
        json.dumps(
            {
                "task_class": "OpenDrawer",
                "task_slug": "OpenDrawer",
                "worker_id": "dead",
                "hostname": socket.gethostname(),
                "pid": 999_999_999,
            }
        ),
        encoding="utf-8",
    )

    reclaimed = try_claim_task(
        output_root=tmp_path,
        task_slug="OpenDrawer",
        task_class="OpenDrawer",
        worker_id="1",
    )
    assert reclaimed is not None
    assert reclaimed == claim
    release_claim(reclaimed)
