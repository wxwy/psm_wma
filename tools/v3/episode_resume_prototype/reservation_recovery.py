"""Read-only recovery of logical reservations; not production scheduling or writes."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import stat
from pathlib import Path

_SHA = re.compile(r"[0-9a-f]{64}\Z")


class ReservationRecoveryError(ValueError):
    """Ambiguous/untrusted recovery input must not become a new higher slot."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code


def _fail(code, message):
    raise ReservationRecoveryError(code, message)


def _slot(value):
    if type(value) is not int or value < 0:
        _fail("INVALID_LOGICAL_SLOT", f"expected a nonnegative integer, got {value!r}")
    return value


def _source(reference):
    if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
        _fail("RECOVERY_SOURCE_MISSING", "persistent input needs a source_ref with a path and hash/digest")
    if not Path(reference["path"]).is_absolute():
        _fail("RECOVERY_SOURCE_INVALID", "persistent source path must be absolute")
    hashes = [reference[name] for name in ("sha256", "original_digest") if name in reference]
    if not hashes or any(not isinstance(value, str) or not _SHA.fullmatch(value) for value in hashes):
        _fail("RECOVERY_SOURCE_INVALID", "persistent source needs a valid SHA256 or original identity digest")
    return copy.deepcopy(reference)


def _references(row):
    references = [_source(row.get("source_ref"))]
    if "recovery_document_source_ref" in row:
        references.append(_source(row["recovery_document_source_ref"]))
    return references


def _unique(references):
    by_json = {json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False): row for row in references}
    return [copy.deepcopy(by_json[key]) for key in sorted(by_json)]


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("RECOVERY_DOCUMENT_INVALID", f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _witness(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def read_recovery_document(path):
    """Read a persisted catalog/progress projection and attach its byte witness.

    The JSON object may contain completed_slots, reservations and/or
    progress_diagnostics; no new schema/version discriminator is required.
    Existing Episode source references are preserved, not relabeled as this
    catalog. Persisted completed_slots ALSO become reservation observations,
    never proof of completed Episode outcomes. This reader is not a substitute
    for the original Episode validator.
    """
    path = Path(path).absolute()
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                _fail("RECOVERY_DOCUMENT_INVALID", "persistent recovery input must be an ordinary file")
            raw = stream.read()
            after = os.fstat(stream.fileno())
        if _witness(before) != _witness(after) or _witness(after) != _witness(path.stat(follow_symlinks=False)):
            _fail("RECOVERY_DOCUMENT_CHANGED", str(path))
        document = json.loads(raw, object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReservationRecoveryError("RECOVERY_DOCUMENT_INVALID", str(error)) from error
    if not isinstance(document, dict):
        _fail("RECOVERY_DOCUMENT_INVALID", "recovery document must be a JSON object")
    reference = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
    result = {"source_ref": reference}
    for kind in ("completed_slots", "reservations", "progress_diagnostics"):
        rows = document.get(kind, [])
        if not isinstance(rows, list):
            _fail("RECOVERY_DOCUMENT_INVALID", f"{kind} must be a list")
        output = []
        for row in rows:
            if kind == "completed_slots" and type(row) is int:
                row = {"logical_episode_index": row}
            if not isinstance(row, dict):
                _fail("RECOVERY_DOCUMENT_INVALID", f"{kind} row must be an object")
            row = copy.deepcopy(row)
            if "task" not in row and "task" in document:
                row["task"] = document["task"]
            row.setdefault("source_ref", copy.deepcopy(reference))
            row["recovery_document_source_ref"] = copy.deepcopy(reference)
            output.append(row)
        result[kind] = output
    result["reservations"] = result["completed_slots"] + result["reservations"]
    return result


def _mapping(row):
    reference = row.get("source_ref", {})
    attempt = row.get("attempt", reference.get("attempt"))
    episode = row.get("source_episode", reference.get("source_episode"))
    if episode is None and "episode" in row:
        episode = row["episode"]
    if attempt is None and episode is None:
        return None
    if not isinstance(attempt, str) or not attempt or episode is None:
        _fail("RECOVERY_LOGICAL_MAPPING_MISSING", "physical Episode mapping needs attempt and source_episode")
    episode = _slot(episode)
    origin = row.get("original_digest", reference.get("original_digest", reference.get("run_dir", "")))
    return str(origin), attempt, episode


def recover_pending_slots(*, task, completed_slots, reservations=(), progress_diagnostics=(), requested_episodes=None):
    """Rebuild pending IDs from durable observations, independently of demand.

    Completed records must come from the upstream Episode verifier. Their
    source-bearing catalog observations are durable authority under the frozen
    continuous logical-ID protocol, so a lost reservation file does not hide a
    gap. Bare ints support pure algorithm tests only: no durable gap proof is
    invented from them. Provenance remains evidence, not model identity.
    """
    if not isinstance(task, str) or not task.isidentifier() or task == "all":
        _fail("INVALID_RECOVERY_TASK", repr(task))
    if requested_episodes is not None and (type(requested_episodes) is not int or requested_episodes <= 0):
        _fail("INVALID_RECOVERY_REQUEST", "requested_episodes must be a positive integer")
    completed, evidence, physical, explicit_ids, id_slots, sources = set(), {}, {}, {}, {}, []
    diagnostics = []
    bare_completed = []

    def observe(row, slot, kind):
        references = _references(row)
        sources.extend(references)
        evidence.setdefault(slot, []).extend(references)
        mapping = _mapping(row)
        if mapping is not None:
            if mapping in physical and physical[mapping] != slot:
                _fail("RECOVERY_MAPPING_CONFLICT", f"{mapping!r} maps to both {physical[mapping]} and {slot}")
            physical[mapping] = slot
        reservation_id = row.get("reservation_id")
        if reservation_id is not None:
            if not isinstance(reservation_id, str) or not reservation_id:
                _fail("RECOVERY_RESERVATION_CONFLICT", "reservation_id must be a nonempty string when present")
            if slot in explicit_ids and explicit_ids[slot] != reservation_id:
                _fail("RECOVERY_RESERVATION_CONFLICT", f"logical slot {slot} has conflicting reservation IDs")
            if reservation_id in id_slots and id_slots[reservation_id] != slot:
                _fail("RECOVERY_RESERVATION_CONFLICT", f"reservation {reservation_id!r} maps to multiple slots")
            explicit_ids[slot], id_slots[reservation_id] = reservation_id, slot
        if kind == "completed":
            completed.add(slot)

    for row in completed_slots:
        if type(row) is int:
            completed.add(_slot(row))
            bare_completed.append(row)
            continue
        if not isinstance(row, dict):
            _fail("INVALID_COMPLETED_SLOT", "completed inputs must be verified history records or test integers")
        if row.get("task", task) != task:
            continue
        value = row.get("logical_episode_index")
        if value is None and row.get("sampling_protocol") == "legacy_task_stream":
            value = row.get("source_episode")
        observe(row, _slot(value), "completed")

    for row in reservations:
        if not isinstance(row, dict):
            _fail("INVALID_RESERVATION", "reservation must be a source-bearing object")
        if row.get("task", task) == task:
            observe(row, _slot(row.get("logical_episode_index")), "reservation")

    for row in progress_diagnostics:
        if not isinstance(row, dict):
            _fail("INVALID_PROGRESS_DIAGNOSTIC", "progress observation must be a source-bearing object")
        if row.get("task", task) != task:
            continue
        value = row.get("logical_episode_index")
        if value is None:
            mapping = _mapping(row)
            if mapping not in physical:
                _fail("RECOVERY_LOGICAL_MAPPING_MISSING", f"no persistent logical mapping for progress {mapping!r}")
            value = physical[mapping]
        observe(row, _slot(value), "progress")

    known = completed | set(evidence)
    maximum = max(known, default=-1)
    # Large sparse inputs fail before materializing a range unless a persistent
    # observation actually attests the continuous logical-ID namespace.
    durable_maximum = max(evidence, default=-1)
    if maximum > durable_maximum:
        expected = 0
        for value in sorted(known):
            if value != expected and value > durable_maximum:
                _fail("RECOVERY_AUTHORITY_MISSING", f"logical gap {expected} has no persistent authority")
            expected = value + 1
    pending = sorted(set(range(maximum + 1)) - completed)
    references = _unique(sources)
    for slot in pending:
        if slot in evidence:
            code = "RECOVERED_PENDING_FROM_PERSISTENT_RESERVATION_OR_PROGRESS"
            slot_sources = _unique(evidence[slot])
        elif evidence:
            code = "INFERRED_FROM_PERSISTENT_COMPLETED_SLOT_GAP"
            slot_sources = references
        else:
            _fail("RECOVERY_AUTHORITY_MISSING", f"logical gap {slot} has no persistent authority")
        diagnostics.append({"code": code, "task": task, "logical_episode_index": slot, "source_refs": slot_sources})
    if bare_completed:
        diagnostics.append(
            {"code": "BARE_COMPLETED_INTS_ARE_ALGORITHM_INPUT_NOT_PERSISTENT_PROOF", "slots": sorted(bare_completed)}
        )
    return {
        "pending_slots": pending,
        "next_slot_floor": maximum + 1,
        "diagnostics": diagnostics,
        "reservation_identities": {
            str(slot): {
                "stable_identity": {"task": task, "logical_episode_index": slot},
                "reservation_id": explicit_ids.get(slot),
                "pending": slot not in completed,
            }
            for slot in sorted(known | set(pending))
        },
        "authority": {
            "protocol": "CONTINUOUS_LOGICAL_IDS_FROM_ZERO",
            "source_refs": references,
            "completed_slots": sorted(completed),
            "observed_slots": sorted(known),
            "requested_episodes": requested_episodes,
            "pending_is_not_filtered_by_current_demand": True,
            "observation_scope": "UPSTREAM_VERIFIED_EPISODES_AND_READONLY_PERSISTENT_MAPPING_OR_PROGRESS",
        },
    }
