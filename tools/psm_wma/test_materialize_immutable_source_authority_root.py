"""CPU-only temporary-repository coverage for the native authority adapter."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from tools.psm_wma.immutable_source_authority_root import EvidenceCleanupIncomplete
from tools.psm_wma.materialize_immutable_source_authority_root import (
    NativeAuthorityGit,
    NativeGitError,
    verify_evidence_bytes,
    verify_evidence_path,
    write_pending_evidence,
)


def _sha(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _pass_evidence() -> dict[str, object]:
    sha1 = "a" * 40
    execution = {
        "formal_root_revision": sha1,
        "child_gitlink": "b" * 40,
        "adapter": {"path": "tools/psm_wma/materialize_immutable_source_authority_root.py", "blob_native_oid": "c" * 40, "raw_sha256": _sha("adapter")},
        "authority_module": {"path": "tools/psm_wma/immutable_source_authority_root.py", "blob_native_oid": "d" * 40, "raw_sha256": _sha("authority")},
        "interpreter": {"path": "/usr/bin/python3", "raw_sha256": _sha("python"), "version": "Python fixture"},
        "git_executable": {"path": "/usr/bin/git", "raw_sha256": _sha("git"), "version": "git fixture"},
        "cwd": "/temporary/fixture",
        "sanitized_env_sha256": _sha("environment"),
        "argv_sha256": _sha("argv"),
        "commit_metadata": {"author_name": "fixture", "author_email": "fixture@example.invalid", "author_date": "0 +0000", "committer_name": "fixture", "committer_email": "fixture@example.invalid", "committer_date": "0 +0000", "message": "fixture"},
        "remote_identity_sha256": _sha("remote"),
        "fixed_ref": "refs/psm-wma/authority",
    }
    record: dict[str, object] = {
        "schema": "immutable_source_authority_root_materialization_evidence_v1",
        "status": "PASS",
        "execution": execution,
        "authority": {"root_revision": sha1, "selection_path": "artifacts/selection.json", "selection_blob_native_oid": "e" * 40, "selection_raw_sha256": _sha("selection"), "config_path": "artifacts/config.json", "config_blob_native_oid": "f" * 40, "config_raw_sha256": _sha("config")},
        "candidate": {"revision": "1" * 40, "parents": [sha1], "tree_native_oid": "2" * 40, "verifier_pass": True, "binding_sha256": _sha("binding")},
        "pre_publication": {"local_observation": {"state": "absent", "revision": None, "error": None}, "remote_observation": {"state": "absent", "revision": None, "error": None}, "both_absent": True},
        "publication": {"local_create_attempted": True, "local_create_succeeded": True, "remote_create_attempted": True, "remote_create_succeeded": True, "local_owned": True, "remote_owned": True},
        "post_publication": {"local_observation": {"state": "revision", "revision": "1" * 40, "error": None}, "remote_observation": {"state": "revision", "revision": "1" * 40, "error": None}, "both_candidate": True, "committed_binding_reverified": True},
        "rollback": {"entered": False, "required": False, "remote_delete_attempted": False, "remote_delete_succeeded": False, "local_delete_attempted": False, "local_delete_succeeded": False, "final_local_observation": None, "final_remote_observation": None, "complete": False},
        "failure": {"primary_phase": None, "primary_code": None, "rollback_phase": None, "rollback_code": None},
    }
    record["evidence_sha256"] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return record


def _redigest(record: dict[str, object]) -> bytes:
    without_digest = dict(record)
    without_digest.pop("evidence_sha256")
    record["evidence_sha256"] = hashlib.sha256(
        json.dumps(without_digest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode()


def _rollback_incomplete_evidence() -> dict[str, object]:
    record = deepcopy(_pass_evidence())
    record["status"] = "ROLLBACK_INCOMPLETE"
    record["rollback"] = {
        "entered": True,
        "required": True,
        "remote_delete_attempted": True,
        "remote_delete_succeeded": True,
        "local_delete_attempted": True,
        "local_delete_succeeded": False,
        "final_local_observation": {"state": "unreadable", "revision": None, "error": "READ_ERROR"},
        "final_remote_observation": {"state": "absent", "revision": None, "error": None},
        "complete": False,
    }
    record["failure"] = {
        "primary_phase": "evidence_write",
        "primary_code": "WRITE_FAILED",
        "rollback_phase": "rollback",
        "rollback_code": "LOCAL_DELETE_FAILED",
    }
    _redigest(record)
    return record


def _preflight_failure_evidence() -> dict[str, object]:
    record = deepcopy(_pass_evidence())
    record["status"] = "FAIL"
    record["authority"] = {key: None for key in record["authority"]}
    record["candidate"] = {
        "revision": None,
        "parents": None,
        "tree_native_oid": None,
        "verifier_pass": False,
        "binding_sha256": None,
    }
    record["pre_publication"] = {
        "local_observation": None,
        "remote_observation": None,
        "both_absent": False,
    }
    record["publication"] = {key: False for key in record["publication"]}
    record["post_publication"] = {
        "local_observation": None,
        "remote_observation": None,
        "both_candidate": False,
        "committed_binding_reverified": False,
    }
    record["failure"] = {
        "primary_phase": "preflight",
        "primary_code": "PREFLIGHT_FAILED",
        "rollback_phase": None,
        "rollback_code": None,
    }
    _redigest(record)
    return record


def _local_cas_failure_evidence() -> dict[str, object]:
    record = deepcopy(_pass_evidence())
    record["status"] = "FAIL"
    record["publication"] = {
        "local_create_attempted": True,
        "local_create_succeeded": False,
        "remote_create_attempted": False,
        "remote_create_succeeded": False,
        "local_owned": False,
        "remote_owned": False,
    }
    record["post_publication"] = {
        "local_observation": None,
        "remote_observation": None,
        "both_candidate": False,
        "committed_binding_reverified": False,
    }
    record["rollback"] = {
        "entered": True,
        "required": False,
        "remote_delete_attempted": False,
        "remote_delete_succeeded": False,
        "local_delete_attempted": False,
        "local_delete_succeeded": False,
        "final_local_observation": {"state": "absent", "revision": None, "error": None},
        "final_remote_observation": {"state": "absent", "revision": None, "error": None},
        "complete": True,
    }
    record["failure"] = {
        "primary_phase": "local_cas",
        "primary_code": "LOCAL_CAS_FAILED",
        "rollback_phase": None,
        "rollback_code": None,
    }
    _redigest(record)
    return record


def _remote_cas_failure_evidence() -> dict[str, object]:
    record = deepcopy(_local_cas_failure_evidence())
    record["publication"] = {
        "local_create_attempted": True,
        "local_create_succeeded": True,
        "remote_create_attempted": True,
        "remote_create_succeeded": False,
        "local_owned": True,
        "remote_owned": False,
    }
    record["rollback"] = {
        "entered": True,
        "required": True,
        "remote_delete_attempted": False,
        "remote_delete_succeeded": False,
        "local_delete_attempted": True,
        "local_delete_succeeded": True,
        "final_local_observation": {"state": "absent", "revision": None, "error": None},
        "final_remote_observation": {"state": "absent", "revision": None, "error": None},
        "complete": True,
    }
    record["failure"] = {
        "primary_phase": "remote_cas",
        "primary_code": "REMOTE_CAS_FAILED",
        "rollback_phase": None,
        "rollback_code": None,
    }
    _redigest(record)
    return record


def _post_publication_failure_evidence(phase: str) -> dict[str, object]:
    record = deepcopy(_pass_evidence())
    record["status"] = "FAIL"
    revision = record["candidate"]["revision"]
    if phase == "post_publication":
        record["post_publication"] = {
            "local_observation": {"state": "revision", "revision": revision, "error": None},
            "remote_observation": {"state": "unreadable", "revision": None, "error": "REMOTE_READ_FAILED"},
            "both_candidate": False,
            "committed_binding_reverified": False,
        }
    else:
        record["post_publication"]["committed_binding_reverified"] = False
    record["rollback"] = {
        "entered": True,
        "required": True,
        "remote_delete_attempted": True,
        "remote_delete_succeeded": True,
        "local_delete_attempted": True,
        "local_delete_succeeded": True,
        "final_local_observation": {"state": "absent", "revision": None, "error": None},
        "final_remote_observation": {"state": "absent", "revision": None, "error": None},
        "complete": True,
    }
    record["failure"] = {
        "primary_phase": phase,
        "primary_code": phase.upper() + "_FAILED",
        "rollback_phase": None,
        "rollback_code": None,
    }
    _redigest(record)
    return record


class NativeAuthorityGitTest(unittest.TestCase):
    def test_pending_evidence_unlinks_only_through_commit(self):
        class Commit:
            def __init__(self): self.callback = None
            def seal_for_guard(self, callback): self.callback = callback
            def consume_by_unlink(self): self.callback()
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            write_pending_evidence(path, _pass_evidence(), Commit())
            self.assertTrue(path.is_file())
            self.assertFalse(path.with_name("evidence.json.pending").exists())
            self.assertEqual(verify_evidence_path(path)["status"], "PASS")

    def test_evidence_verifier_rejects_digest_and_chronology_drift(self):
        record = _pass_evidence()
        raw = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(verify_evidence_bytes(raw)["status"], "PASS")
        record["publication"]["remote_owned"] = False
        broken = _redigest(record)
        with self.assertRaises(NativeGitError):
            verify_evidence_bytes(broken)

    def test_path_verifier_rejects_visible_record_while_guard_exists(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            path.write_bytes(_redigest(_pass_evidence()))
            path.with_name("evidence.json.pending").write_bytes(b"")
            with self.assertRaises(NativeGitError):
                verify_evidence_path(path)

    def test_evidence_verifier_requires_reachable_failure_terminals(self):
        incomplete = _rollback_incomplete_evidence()
        self.assertEqual(
            verify_evidence_bytes(_redigest(incomplete))["status"],
            "ROLLBACK_INCOMPLETE",
        )
        ordinary = deepcopy(incomplete)
        ordinary["status"] = "FAIL"
        ordinary["rollback"]["complete"] = True
        ordinary["rollback"]["final_local_observation"] = {
            "state": "absent", "revision": None, "error": None,
        }
        ordinary["failure"]["rollback_phase"] = None
        ordinary["failure"]["rollback_code"] = None
        self.assertEqual(verify_evidence_bytes(_redigest(ordinary))["status"], "FAIL")
        missing_rollback = _pass_evidence()
        missing_rollback["status"] = "FAIL"
        missing_rollback["failure"] = {
            "primary_phase": "evidence_write", "primary_code": "WRITE_FAILED",
            "rollback_phase": None, "rollback_code": None,
        }
        with self.assertRaises(NativeGitError):
            verify_evidence_bytes(_redigest(missing_rollback))

    def test_no_mutation_failure_rows_reject_publication_witnesses(self):
        preflight = _preflight_failure_evidence()
        self.assertEqual(verify_evidence_bytes(_redigest(preflight))["status"], "FAIL")
        drifted = deepcopy(preflight)
        drifted["publication"]["local_create_attempted"] = True
        with self.assertRaises(NativeGitError):
            verify_evidence_bytes(_redigest(drifted))

    def test_local_cas_failure_requires_its_exact_witness_shape(self):
        local_cas = _local_cas_failure_evidence()
        self.assertEqual(verify_evidence_bytes(_redigest(local_cas))["status"], "FAIL")
        drifted = deepcopy(local_cas)
        drifted["publication"]["remote_create_attempted"] = True
        with self.assertRaises(NativeGitError):
            verify_evidence_bytes(_redigest(drifted))

    def test_remote_cas_failure_requires_local_only_rollback(self):
        remote_cas = _remote_cas_failure_evidence()
        self.assertEqual(verify_evidence_bytes(_redigest(remote_cas))["status"], "FAIL")
        drifted = deepcopy(remote_cas)
        drifted["publication"]["remote_owned"] = True
        with self.assertRaises(NativeGitError):
            verify_evidence_bytes(_redigest(drifted))

    def test_post_and_binding_failures_require_their_distinct_post_witnesses(self):
        for phase in ("post_publication", "binding_reverify"):
            with self.subTest(phase=phase):
                record = _post_publication_failure_evidence(phase)
                self.assertEqual(verify_evidence_bytes(_redigest(record))["status"], "FAIL")
                drifted = deepcopy(record)
                if phase == "post_publication":
                    drifted["publication"]["remote_owned"] = False
                else:
                    drifted["post_publication"]["both_candidate"] = False
                with self.assertRaises(NativeGitError):
                    verify_evidence_bytes(_redigest(drifted))

    def test_writer_cleans_precommit_files_after_directory_fsync_or_rename_failure(self):
        class Commit:
            def seal_for_guard(self, _callback):
                raise AssertionError("seal must not be reached")

        for failure in ("directory_fsync", "rename"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as raw:
                path = Path(raw) / "evidence.json"
                if failure == "directory_fsync":
                    with patch(
                        "tools.psm_wma.materialize_immutable_source_authority_root._fsync_directory",
                        side_effect=(OSError("fixture"), None),
                    ):
                        with self.assertRaises(OSError):
                            write_pending_evidence(path, _pass_evidence(), Commit())
                else:
                    with patch(
                        "tools.psm_wma.materialize_immutable_source_authority_root.os.replace",
                        side_effect=OSError("fixture"),
                    ):
                        with self.assertRaises(OSError):
                            write_pending_evidence(path, _pass_evidence(), Commit())
                self.assertFalse(path.exists())
                self.assertFalse(path.with_name("evidence.json.pending").exists())
                self.assertFalse(path.with_name("evidence.json.tmp").exists())

    def test_writer_cleans_postrename_reread_failure_before_guard_unlink(self):
        class Commit:
            def seal_for_guard(self, _callback):
                raise AssertionError("seal must not be reached")

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            with patch(
                "tools.psm_wma.materialize_immutable_source_authority_root._read_regular_evidence",
                side_effect=OSError("fixture"),
            ), self.assertRaises(OSError):
                write_pending_evidence(path, _pass_evidence(), Commit())
            self.assertFalse(path.exists())
            self.assertFalse(path.with_name("evidence.json.pending").exists())
            self.assertFalse(path.with_name("evidence.json.tmp").exists())

    def test_writer_cleans_when_unlink_commit_does_not_happen(self):
        class Commit:
            committed = False

            def seal_for_guard(self, _callback):
                pass

            def consume_by_unlink(self):
                raise OSError("fixture")

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            with self.assertRaises(OSError):
                write_pending_evidence(path, _pass_evidence(), Commit())
            self.assertFalse(path.exists())
            self.assertFalse(path.with_name("evidence.json.pending").exists())

    def test_writer_reports_cleanup_that_cannot_be_proven(self):
        class Commit:
            def seal_for_guard(self, _callback):
                raise AssertionError("seal must not be reached")

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            with patch(
                "tools.psm_wma.materialize_immutable_source_authority_root._fsync_directory",
                side_effect=OSError("fixture"),
            ), self.assertRaises(EvidenceCleanupIncomplete):
                write_pending_evidence(path, _pass_evidence(), Commit())

    def test_temporary_index_commit_and_exact_ref_cas(self):
        git = Path(shutil.which("git") or "")
        self.assertTrue(git.is_absolute())
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "root"
            remote = Path(raw) / "remote.git"
            subprocess.run([str(git), "init", "-q", str(root)], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.name", "fixture"], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
            (root / "README").write_text("x")
            subprocess.run([str(git), "-C", str(root), "add", "README"], check=True)
            subprocess.run([str(git), "-C", str(root), "commit", "-qm", "root"], check=True)
            subprocess.run([str(git), "init", "--bare", "-q", str(remote)], check=True)
            tx = NativeAuthorityGit(git, root, str(remote), root / "temporary.index")
            parent = tx._run("rev-parse", "HEAD")
            revision = tx.create_detached_commit(parent, {"proof.json": b"{}"})
            self.assertEqual(tx.parents(revision), (parent,))
            self.assertTrue(tx.cas_create_local("refs/heads/test", revision))
            self.assertTrue(tx.cas_create_remote("refs/heads/test", revision))
            self.assertTrue(tx.cas_delete_remote("refs/heads/test", revision))
            self.assertTrue(tx.cas_delete_local("refs/heads/test", revision))

    def test_absent_remote_lease_rejects_fast_forwardable_foreign_ref(self):
        git = Path(shutil.which("git") or "")
        self.assertTrue(git.is_absolute())
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "root"
            remote = Path(raw) / "remote.git"
            subprocess.run([str(git), "init", "-q", str(root)], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.name", "fixture"], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
            (root / "README").write_text("x")
            subprocess.run([str(git), "-C", str(root), "add", "README"], check=True)
            subprocess.run([str(git), "-C", str(root), "commit", "-qm", "root"], check=True)
            subprocess.run([str(git), "init", "--bare", "-q", str(remote)], check=True)
            tx = NativeAuthorityGit(git, root, str(remote), root / "temporary.index")
            parent = tx._run("rev-parse", "HEAD")
            candidate = tx.create_detached_commit(parent, {"candidate.json": b"{}"})
            foreign = tx.create_detached_commit(candidate, {"foreign.json": b"{}"})
            ref = "refs/heads/lease"
            self.assertTrue(tx.cas_create_remote(ref, candidate))
            self.assertFalse(tx.cas_create_remote(ref, foreign))
            self.assertEqual(tx.remote_ref(ref), candidate)
            self.assertFalse(tx.cas_delete_remote(ref, foreign))
            self.assertEqual(tx.remote_ref(ref), candidate)


if __name__ == "__main__":
    unittest.main()
