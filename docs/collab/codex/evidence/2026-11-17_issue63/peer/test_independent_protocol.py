"""Independent CPU protocol probes for frozen Issue63 Root 98172110.

Synthetic temporary data only. This file does not modify production/tests or
reuse author assertions as its expected outcome.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from g2.io import digest, read_json, write_json
from g2.latent_cache import final_source as final
from g2.latent_cache import ledger_archive
from g2.latent_cache.contract import CacheError, fingerprint
from g2.latent_cache.production import build_profile
from g2.latent_cache.storage import ViewReader, open_episode_index
from g2.tests.test_source_capsule import capsule_case, complete_working
from g2.tests.test_source_retirement_faults import acknowledged_job
from g2.tests.test_view_vae_builder import PREPROCESS
from g2.tests.test_view_vae_storage import _episode


def test_legacy_reader_needs_no_write_open_or_new_lock_file(tmp_path, monkeypatch):
    root, _ = _episode(tmp_path)
    before = {str(p.relative_to(root)): digest(p) for p in root.rglob("*") if p.is_file()}
    original = os.open
    forbidden = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC

    def read_only(path, flags, *args, **kwargs):
        candidate = Path(path)
        if candidate == root or root in candidate.parents:
            assert flags & forbidden == 0, (str(path), flags)
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", read_only)
    with ViewReader(open_episode_index(root)) as reader:
        sample = reader.read_view("sixview/floor_top", 7)
        assert sample["owner"]["owner_state_id"] == 2
    after = {str(p.relative_to(root)): digest(p) for p in root.rglob("*") if p.is_file()}
    assert before == after
    assert not (root / "vae_cache/.source.lock").exists()


def test_retired_v2_posthoc_resume_performs_no_encoding_or_file_rewrite(tmp_path, monkeypatch):
    kwargs, target, encoder, spool, job = capsule_case(tmp_path)
    complete_working(kwargs, target, encoder, spool, job)
    assert spool.adopt_completed(job)
    before = {str(p.relative_to(target)): digest(p) for p in target.rglob("*") if p.is_file()}

    def unexpected_encode(*args, **kwargs):
        raise AssertionError("retired completed cache must not run Encode1")

    monkeypatch.setattr(encoder, "encode", unexpected_encode)
    result = build_profile(target, encoder, preprocessing=PREPROCESS, resume=True, cleanup=True)
    assert result["already_complete"] is True and result["encoded_records"] == 0
    after = {str(p.relative_to(target)): digest(p) for p in target.rglob("*") if p.is_file()}
    assert before == after


@pytest.mark.parametrize("component", ["working_proof", "work_cleanup", "retired_files"])
def test_final_receipt_cannot_disagree_with_sql_bound_capsule(tmp_path, monkeypatch, component):
    _, target, _, spool, job = acknowledged_job(tmp_path, monkeypatch)

    def interrupt(phase):
        if phase == "capsule_journal_removed":
            raise RuntimeError("PEER_STOP_AFTER_JOURNAL_BEFORE_LEDGER_GC")

    with pytest.raises(RuntimeError, match="PEER_STOP"):
        ledger_archive.archive(spool, job, failpoint=interrupt)
    with spool._db() as db:
        bound = json.loads(db.execute("SELECT retirement FROM jobs WHERE id=?", (job,)).fetchone()[0])
    capsule_sha = digest(target / final.CAPSULE)
    assert bound["capsule_sha256"] == capsule_sha
    capsule = read_json(target / final.CAPSULE)
    retirement = read_json(target / final.RECEIPT)
    if component == "working_proof":
        retirement[component]["source_id"] = "0" * 64
        assert fingerprint(retirement[component]) != capsule["attestation"]["working_proof_sha256"]
    elif component == "work_cleanup":
        retirement[component] = {"status": "kept_by_explicit_config"}
        assert fingerprint(retirement[component]) != capsule["attestation"]["work_cleanup_sha256"]
    else:
        retirement[component][final.FULL] = "0" * 64
        assert retirement[component][final.FULL] != capsule["working_source"]["manifest_sha256"]
    write_json(target / final.RECEIPT, retirement)
    complete = read_json(target / "COMPLETE.json")
    complete["source_retirement_sha256"] = digest(target / final.RECEIPT)
    write_json(target / "COMPLETE.json", complete)
    assert digest(target / final.CAPSULE) == capsule_sha
    with pytest.raises(CacheError):
        spool.reap(job)
    assert spool.stats()["completed_jobs"] == 0
