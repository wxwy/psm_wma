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
