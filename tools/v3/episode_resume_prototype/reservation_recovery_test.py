"""Synthetic persistent-file recovery; no real rollout/DCP or production writes."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys

import pytest

from tools.v3.episode_resume_prototype.reservation_recovery import (
    ReservationRecoveryError,
    read_recovery_document,
    recover_pending_slots,
)

TASK = "CloseFridge"


def completed(slots):
    """Already-verified scanner outputs at this helper's upstream trust boundary."""
    return [
        {
            "task": TASK,
            "logical_episode_index": slot,
            "source_episode": slot,
            "source_ref": {
                "path": f"/synthetic/{TASK}/attempt_0001/rollout{slot:02d}_episode.json",
                "original_digest": "a" * 64,
                "attempt": "attempt_0001",
                "source_episode": slot,
                "hashes": {"core": f"{slot:064x}"},
            },
        }
        for slot in slots
    ]


def recover(history, **changes):
    return recover_pending_slots(task=TASK, completed_slots=history, requested_episodes=5, **changes)


def persist(tmp_path, document, name="logical_slots.json"):
    path = tmp_path / name
    path.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    return path, read_recovery_document(path)


def row(slot=2, *, attempt="attempt_0002", reservation="CloseFridge:slot:2", **extra):
    return {
        "task": TASK,
        "logical_episode_index": slot,
        "attempt": attempt,
        "source_episode": 0,
        "reservation_id": reservation,
        **extra,
    }


def test_missing_reservation_file_sparse_completed_catalog_automatically_recovers_gap():
    history = completed([0, 1, 3, 4])
    before = copy.deepcopy(history)
    result = recover(history)
    assert result["pending_slots"] == [2]
    assert result["next_slot_floor"] == 5
    assert result["diagnostics"][0]["code"] == "INFERRED_FROM_PERSISTENT_COMPLETED_SLOT_GAP"
    assert result["diagnostics"][0]["source_refs"]
    assert result["reservation_identities"]["2"]["stable_identity"] == {"task": TASK, "logical_episode_index": 2}
    assert history == before


def test_multiple_catalog_holes_are_pending_in_logical_order():
    result = recover(completed([1, 3, 6]))
    assert result["pending_slots"] == [0, 2, 4, 5]
    assert result["next_slot_floor"] == 7


def test_contiguous_completed_prefix_needs_no_reservation_to_append_safely():
    assert recover(completed([0, 1, 2]))["next_slot_floor"] == 3
    assert recover(completed([0, 1, 2]))["pending_slots"] == []
    assert recover([])["next_slot_floor"] == 0


def test_explicit_reservation_and_original_progress_tail_recover_from_disk(tmp_path):
    path, document = persist(
        tmp_path,
        {"task": TASK, "reservations": [row()], "progress_diagnostics": [row(event="start")]},
    )
    before_bytes, before_stat = path.read_bytes(), path.stat()
    result = recover(
        completed([0, 1, 3, 4]),
        reservations=document["reservations"],
        progress_diagnostics=document["progress_diagnostics"],
    )
    assert result["pending_slots"] == [2]
    assert result["reservation_identities"]["2"]["reservation_id"] == "CloseFridge:slot:2"
    assert result["diagnostics"][0]["code"] == "RECOVERED_PENDING_FROM_PERSISTENT_RESERVATION_OR_PROGRESS"
    assert document["source_ref"] == {"path": str(path), "sha256": hashlib.sha256(before_bytes).hexdigest()}
    assert path.read_bytes() == before_bytes
    after_stat = path.stat()
    assert (before_stat.st_ino, before_stat.st_mtime_ns, before_stat.st_ctime_ns) == (
        after_stat.st_ino,
        after_stat.st_mtime_ns,
        after_stat.st_ctime_ns,
    )


def test_persisted_completed_claim_only_reserves_a_slot_and_cannot_prove_outcome(tmp_path):
    _, document = persist(tmp_path, {"task": TASK, "completed_slots": list(range(5))})
    result = recover(completed([0, 1, 3, 4]), reservations=document["reservations"])
    assert result["authority"]["completed_slots"] == [0, 1, 3, 4]
    assert result["pending_slots"] == [2]
    assert document["reservations"] == document["completed_slots"]


def test_crash_rebuild_reopens_files_without_an_in_memory_pending_argument(tmp_path):
    catalog, _ = persist(
        tmp_path,
        {"task": TASK, "completed_slots": list(range(5)), "progress_diagnostics": [row(event="start")]},
    )
    history = tmp_path / "upstream_verified_history_fixture.json"
    history.write_text(json.dumps(completed([0, 1, 3, 4])), encoding="utf-8")
    program = """
import json, sys
from pathlib import Path
from tools.v3.episode_resume_prototype.reservation_recovery import read_recovery_document, recover_pending_slots
catalog = read_recovery_document(Path(sys.argv[1]))
history = json.loads(Path(sys.argv[2]).read_text())
result = recover_pending_slots(task='CloseFridge', completed_slots=history,
    reservations=catalog['reservations'], progress_diagnostics=catalog['progress_diagnostics'], requested_episodes=5)
print(json.dumps(result, sort_keys=True))
"""
    command = [sys.executable, "-c", program, str(catalog), str(history)]
    # Independent OS interpreters cannot inherit the first process's local lists.
    processes = [subprocess.run(command, check=True, capture_output=True, text=True, timeout=10) for _ in range(2)]
    first, rebuilt = [json.loads(process.stdout) for process in processes]
    assert first == rebuilt
    assert rebuilt["pending_slots"] == [2]
    assert rebuilt["next_slot_floor"] == 5
    assert rebuilt["authority"]["source_refs"]
    assert "pending_slots" not in json.loads(catalog.read_text())


def test_shrink_then_expand_preserves_unfinished_identity_and_allocation_floor(tmp_path):
    _, document = persist(tmp_path, {"task": TASK, "reservations": [row()]})
    outputs = [
        recover_pending_slots(
            task=TASK,
            completed_slots=completed([0, 1, 3, 4]),
            reservations=document["reservations"],
            requested_episodes=requested,
        )
        for requested in (3, 5, 8)
    ]
    assert [output["pending_slots"] for output in outputs] == [[2], [2], [2]]
    assert [output["next_slot_floor"] for output in outputs] == [5, 5, 5]
    assert len({json.dumps(output["reservation_identities"]["2"], sort_keys=True) for output in outputs}) == 1


def test_retry_new_attempt_keeps_same_slot_and_reservation_identity(tmp_path):
    _, document = persist(
        tmp_path,
        {"task": TASK, "reservations": [row(), row(attempt="attempt_0003")], "progress_diagnostics": []},
    )
    result = recover(completed([0, 1]), reservations=document["reservations"])
    assert result["pending_slots"] == [2]
    assert result["next_slot_floor"] == 3
    assert result["reservation_identities"]["2"]["reservation_id"] == "CloseFridge:slot:2"


def test_progress_without_slot_uses_persistent_attempt_physical_mapping(tmp_path):
    progress = row(event="start")
    del progress["logical_episode_index"]
    _, document = persist(tmp_path, {"reservations": [row()], "progress_diagnostics": [progress]})
    result = recover(
        completed([0, 1]),
        reservations=document["reservations"],
        progress_diagnostics=document["progress_diagnostics"],
    )
    assert result["pending_slots"] == [2]


def test_progress_only_with_explicit_logical_slot_is_persistent_authority(tmp_path):
    _, document = persist(tmp_path, {"progress_diagnostics": [row(event="start")]})
    result = recover(completed([0, 1]), progress_diagnostics=document["progress_diagnostics"])
    assert result["pending_slots"] == [2]


def test_unmapped_progress_is_an_explicit_error_instead_of_appending_slot5(tmp_path):
    progress = row(event="start")
    del progress["logical_episode_index"]
    _, document = persist(tmp_path, {"progress_diagnostics": [progress]})
    with pytest.raises(ReservationRecoveryError, match="RECOVERY_LOGICAL_MAPPING_MISSING"):
        recover(completed([0, 1, 3, 4]), progress_diagnostics=document["progress_diagnostics"])


@pytest.mark.parametrize(
    "rows,code",
    [
        ([row(), row(3)], "RECOVERY_MAPPING_CONFLICT"),
        ([row(), row(attempt="attempt_0003", reservation="different")], "RECOVERY_RESERVATION_CONFLICT"),
        ([row(), row(3, attempt="attempt_0003")], "RECOVERY_RESERVATION_CONFLICT"),
    ],
)
def test_conflicting_mapping_or_reservation_is_never_silently_renumbered(tmp_path, rows, code):
    _, document = persist(tmp_path, {"reservations": rows})
    with pytest.raises(ReservationRecoveryError, match=code):
        recover(completed([0, 1]), reservations=document["reservations"])


def test_same_attempt_name_in_distinct_original_manifests_is_not_a_mapping_collision(tmp_path):
    rows = [row(original_digest="a" * 64), row(3, reservation="slot3", original_digest="b" * 64)]
    _, document = persist(tmp_path, {"reservations": rows})
    assert recover(completed([0, 1]), reservations=document["reservations"])["pending_slots"] == [2, 3]


def test_bare_test_integers_do_not_fabricate_durable_gap_evidence():
    with pytest.raises(ReservationRecoveryError, match="RECOVERY_AUTHORITY_MISSING"):
        recover([0, 1, 3, 4])
    result = recover([0, 1, 2])
    assert result["authority"]["source_refs"] == []
    assert result["diagnostics"][0]["code"] == "BARE_COMPLETED_INTS_ARE_ALGORITHM_INPUT_NOT_PERSISTENT_PROOF"


@pytest.mark.parametrize("value", [True, False, -1, 1.5, "2", None])
def test_invalid_logical_slot_rejected(value):
    history = completed([0])
    history[0]["logical_episode_index"] = value
    with pytest.raises(ReservationRecoveryError, match="INVALID_LOGICAL_SLOT"):
        recover(history)


@pytest.mark.parametrize("source", [None, {}, {"path": "relative", "sha256": "a" * 64}, {"path": "/abs"}])
def test_missing_or_untrusted_source_is_not_recovery_authority(source):
    reservation = row(source_ref=source)
    with pytest.raises(ReservationRecoveryError, match="RECOVERY_SOURCE_"):
        recover(completed([0, 1]), reservations=[reservation])


def test_other_task_pending_does_not_leak_into_current_task(tmp_path):
    _, document = persist(tmp_path, {"reservations": [row(8, task="NavigateKitchen")]})
    result = recover(completed([0, 1]), reservations=document["reservations"])
    assert result["pending_slots"] == []
    assert result["next_slot_floor"] == 2


def test_read_preserves_original_episode_reference_and_attaches_catalog_witness(tmp_path):
    original = completed([2])[0]
    _, document = persist(tmp_path, {"completed_slots": [original]})
    observed = document["reservations"][0]
    assert observed["source_ref"] == original["source_ref"]
    assert observed["recovery_document_source_ref"] == document["source_ref"]
    result = recover(completed([0, 1]), reservations=document["reservations"])
    assert result["pending_slots"] == [2]
    assert original["source_ref"] in result["authority"]["source_refs"]
    assert document["source_ref"] in result["authority"]["source_refs"]


@pytest.mark.parametrize(
    "content", ["not JSON", "[]", '{"reservations":{},"task":"CloseFridge"}', '{"task":1,"task":2}']
)
def test_corrupt_document_rejected(tmp_path, content):
    path = tmp_path / "broken.json"
    path.write_text(content)
    with pytest.raises(ReservationRecoveryError, match="RECOVERY_DOCUMENT_INVALID"):
        read_recovery_document(path)


def test_symlink_document_is_not_read(tmp_path):
    path, _ = persist(tmp_path, {})
    link = tmp_path / "linked.json"
    link.symlink_to(path)
    with pytest.raises(ReservationRecoveryError, match="RECOVERY_DOCUMENT_INVALID"):
        read_recovery_document(link)


def test_read_does_not_create_missing_files(tmp_path):
    before = sorted(os.listdir(tmp_path))
    with pytest.raises(ReservationRecoveryError, match="RECOVERY_DOCUMENT_INVALID"):
        read_recovery_document(tmp_path / "missing.json")
    assert sorted(os.listdir(tmp_path)) == before
