"""CPU-only temporary-repository coverage for the native authority adapter."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
import hashlib
import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from tools.psm_wma.materialize_immutable_source_authority_root import (
    NativeAuthorityGit,
    CommitMetadata,
    main,
    NativeGitError,
    _tool_version,
    verify_evidence_bytes,
    verify_evidence_path,
    write_pending_evidence,
    _read_input_fd,
)


COMMIT_METADATA = CommitMetadata("fixture", "fixture@example.invalid", "@0 +0000", "fixture", "fixture@example.invalid", "@0 +0000", "fixture commit")


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
    def _run_cli(self, root: Path, selection, config, argv):
        return subprocess.run(
            [
                str(Path(sys.executable).resolve()), "-m",
                "tools.psm_wma.materialize_immutable_source_authority_root",
                "--selection-fd", str(selection.fileno()),
                "--config-fd", str(config.fileno()), *argv,
            ],
            cwd=root,
            pass_fds=(selection.fileno(), config.fileno()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def _cli_fixture(self, directory: Path):
        git = Path(shutil.which("git") or "").resolve()
        root, remote = directory / "root", directory / "remote.git"
        subprocess.run([str(git), "init", "-q", str(root)], check=True)
        subprocess.run([str(git), "-C", str(root), "config", "user.name", "fixture"], check=True)
        subprocess.run([str(git), "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
        adapter_path = "tools/psm_wma/materialize_immutable_source_authority_root.py"
        authority_path = "tools/psm_wma/immutable_source_authority_root.py"
        project_root = Path(__file__).parents[2]
        for relative in (
            adapter_path,
            authority_path,
            "tools/psm_wma/immutable_source_collection.py",
            "tools/g0/audit_r09_b_ttt_root_gitlink_authority.py",
        ):
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((project_root / relative).read_bytes())
        (root / "README").write_text("fixture")
        subprocess.run([str(git), "-C", str(root), "add", "."], check=True)
        child = "c" * 40
        subprocess.run(
            [str(git), "-C", str(root), "update-index", "--add", "--cacheinfo", f"160000,{child},cosmos-framework"],
            check=True,
        )
        subprocess.run([str(git), "-C", str(root), "commit", "-qm", "formal root"], check=True)
        subprocess.run([str(git), "init", "--bare", "-q", str(remote)], check=True)
        formal_root = subprocess.run(
            [str(git), "-C", str(root), "rev-parse", "HEAD"], check=True, stdout=subprocess.PIPE, text=True,
        ).stdout.strip()
        selection = json.dumps({
            "schema": "immutable_source_selection_request_v1",
            "source_kind": "checkpoint_source_manifest_v1",
            "entries": [{"ordinal": 0, "relative_path": "fixture/checkpoint"}],
        }, sort_keys=True, separators=(",", ":")).encode()
        config = json.dumps({
            "schema": "canonical_native_local_ttt_config_v2",
            "local_memory_enabled": True,
            "local_memory_dim": 32,
            "local_history_enabled": True,
            "local_history_backend": "ttt_fast_weight",
            "local_history_evidence_dim": 106,
            "local_history_state_enabled": False,
            "local_ttt_enabled": True,
            "enable_input_bias": False,
            "ttt_tbptt_steps": 16,
            "ttt_inner_lr": 0.01,
            "k_local": 1,
            "local_evidence_feature_version": "causal_visual96_executed_action10_v1",
            "local_fast_state_dtype": "fp32",
            "local_runtime_resume_mode": "slow_only_no_mid_episode_resume",
        }, sort_keys=True, separators=(",", ":")).encode()
        selection_path, config_path = root / "selection.json", root / "config.json"
        selection_path.write_bytes(selection)
        config_path.write_bytes(config)
        identities = []
        for relative in (adapter_path, authority_path):
            raw = (root / relative).read_bytes()
            oid = subprocess.run(
                [str(git), "-C", str(root), "rev-parse", f"HEAD:{relative}"], check=True, stdout=subprocess.PIPE, text=True,
            ).stdout.strip()
            identities.extend([relative, oid, hashlib.sha256(raw).hexdigest()])
        interpreter = Path(sys.executable).resolve()
        argv = [
            "--formal-root", formal_root, "--child-gitlink", child,
            "--selection-raw-sha256", hashlib.sha256(selection).hexdigest(),
            "--config-raw-sha256", hashlib.sha256(config).hexdigest(),
            "--cwd", str(root), "--remote", str(remote), "--index", str(root / "temporary.index"),
            "--evidence-path", str(root / "evidence.json"),
            "--git", str(git), "--git-raw-sha256", hashlib.sha256(git.read_bytes()).hexdigest(), "--git-version", _tool_version(git),
            "--interpreter", str(interpreter), "--interpreter-raw-sha256", hashlib.sha256(interpreter.read_bytes()).hexdigest(), "--interpreter-version", _tool_version(interpreter),
            "--adapter-path", identities[0], "--adapter-blob-oid", identities[1], "--adapter-raw-sha256", identities[2],
            "--authority-module-path", identities[3], "--authority-module-blob-oid", identities[4], "--authority-module-raw-sha256", identities[5],
            "--author-name", COMMIT_METADATA.author_name, "--author-email", COMMIT_METADATA.author_email, "--author-date", COMMIT_METADATA.author_date,
            "--committer-name", COMMIT_METADATA.committer_name, "--committer-email", COMMIT_METADATA.committer_email, "--committer-date", COMMIT_METADATA.committer_date,
            "--commit-message", COMMIT_METADATA.message,
        ]
        return git, root, remote, selection_path, config_path, argv

    def test_cli_preflight_then_authority_flow_uses_only_temporary_git(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_cli(root, selection_handle, config_handle, argv)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(verify_evidence_path(root / "evidence.json")["status"], "PASS")
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNotNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
            self.assertIsNotNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_cli_preflight_rejects_input_and_identity_drift_before_mutation(self):
        cases = (
            ("--selection-raw-sha256", "0" * 64),
            ("--formal-root", "0" * 40),
            ("--child-gitlink", "0" * 40),
            ("--git-raw-sha256", "0" * 64),
            ("--interpreter-raw-sha256", "0" * 64),
            ("--adapter-raw-sha256", "0" * 64),
        )
        for option, value in cases:
            with self.subTest(option=option), tempfile.TemporaryDirectory() as raw:
                git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
                position = argv.index(option)
                argv[position + 1] = value
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_cli(root, selection_handle, config_handle, argv)
                self.assertNotEqual(result.returncode, 0)
                transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
                self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
                self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_cli_preflight_rejects_noncanonical_input_before_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            selection.write_bytes(selection.read_bytes() + b"\n")
            position = argv.index("--selection-raw-sha256")
            argv[position + 1] = hashlib.sha256(selection.read_bytes()).hexdigest()
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_cli(root, selection_handle, config_handle, argv)
            self.assertNotEqual(result.returncode, 0)
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
            self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_cli_rejects_pristine_formal_copy_when_loaded_adapter_differs(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                with self.assertRaises(NativeGitError):
                    main([
                        "--selection-fd", str(selection_handle.fileno()),
                        "--config-fd", str(config_handle.fileno()), *argv,
                    ])
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
            self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_cli_preflight_rejects_preexisting_local_or_remote_ref(self):
        for endpoint in ("local", "remote"):
            with self.subTest(endpoint=endpoint), tempfile.TemporaryDirectory() as raw:
                git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
                transaction = NativeAuthorityGit(git, root, str(remote), root / "fixture.index", COMMIT_METADATA)
                revision = transaction._run("rev-parse", "HEAD")
                if endpoint == "local":
                    transaction._run("update-ref", "refs/heads/authority/r09-b-ttt-v035-immutable-source-v1", revision)
                else:
                    self.assertTrue(transaction.cas_create_remote("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1", revision))
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_cli(root, selection_handle, config_handle, argv)
                self.assertNotEqual(result.returncode, 0)
    def test_input_fd_requires_regular_file(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "input.json"
            path.write_bytes(b"{}")
            with path.open("rb") as handle:
                self.assertEqual(_read_input_fd(handle.fileno()), b"{}")
            read_end, write_end = os.pipe()
            try:
                with self.assertRaises(NativeGitError):
                    _read_input_fd(read_end)
            finally:
                os.close(read_end)
                os.close(write_end)
    def test_writer_rejects_forged_commit_before_creating_evidence(self):
        class Commit:
            def __init__(self): self.guard = None
            def seal_for_guard(self, guard, _path, _digest): self.guard = guard
            def consume_by_unlink(self): os.unlink(self.guard)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            with self.assertRaises(NativeGitError):
                write_pending_evidence(path, _pass_evidence(), None, Commit())
            self.assertFalse(path.exists())
            self.assertFalse(path.with_name("evidence.json.pending").exists())

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

        impossible_primary = _preflight_failure_evidence()
        impossible_primary["failure"]["primary_phase"] = "rollback"
        with self.assertRaises(NativeGitError):
            verify_evidence_bytes(_redigest(impossible_primary))

        secondary_on_fail = _local_cas_failure_evidence()
        secondary_on_fail["failure"]["rollback_phase"] = "rollback"
        secondary_on_fail["failure"]["rollback_code"] = "UNEXPECTED"
        with self.assertRaises(NativeGitError):
            verify_evidence_bytes(_redigest(secondary_on_fail))

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

    def test_no_owned_publication_failures_require_complete_absent_proof(self):
        for phase, record in (
            ("pre_publication", deepcopy(_local_cas_failure_evidence())),
            ("local_cas", _local_cas_failure_evidence()),
        ):
            with self.subTest(phase=phase):
                if phase == "pre_publication":
                    record["pre_publication"] = {
                        "local_observation": {"state": "revision", "revision": "a" * 40, "error": None},
                        "remote_observation": {"state": "absent", "revision": None, "error": None},
                        "both_absent": False,
                    }
                    record["publication"] = {key: False for key in record["publication"]}
                    record["failure"] = {
                        "primary_phase": "pre_publication", "primary_code": "PRECHECK_FAILED",
                        "rollback_phase": None, "rollback_code": None,
                    }
                record["rollback"]["complete"] = False
                record["rollback"]["final_local_observation"] = {
                    "state": "unreadable", "revision": None, "error": "READ_ERROR",
                }
                with self.assertRaises(NativeGitError):
                    verify_evidence_bytes(_redigest(record))

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
            def seal_for_guard(self, *_args):
                raise AssertionError("seal must not be reached")

        for failure in ("directory_fsync", "rename"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as raw:
                path = Path(raw) / "evidence.json"
                if failure == "directory_fsync":
                    with patch(
                        "tools.psm_wma.materialize_immutable_source_authority_root._fsync_directory",
                        side_effect=(OSError("fixture"), None),
                    ):
                        with self.assertRaises(NativeGitError):
                            write_pending_evidence(path, _pass_evidence(), None, Commit())
                else:
                    with patch(
                        "tools.psm_wma.materialize_immutable_source_authority_root.os.link",
                        side_effect=OSError("fixture"),
                    ):
                        with self.assertRaises(NativeGitError):
                            write_pending_evidence(path, _pass_evidence(), None, Commit())
                self.assertFalse(path.exists())
                self.assertFalse(path.with_name("evidence.json.pending").exists())
                self.assertFalse(path.with_name("evidence.json.tmp").exists())

    def test_writer_cleans_postrename_reread_failure_before_guard_unlink(self):
        class Commit:
            def seal_for_guard(self, *_args):
                raise AssertionError("seal must not be reached")

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            with patch(
                "tools.psm_wma.materialize_immutable_source_authority_root._read_regular_evidence",
                side_effect=OSError("fixture"),
            ), self.assertRaises(NativeGitError):
                write_pending_evidence(path, _pass_evidence(), None, Commit())
            self.assertFalse(path.exists())
            self.assertFalse(path.with_name("evidence.json.pending").exists())
            self.assertFalse(path.with_name("evidence.json.tmp").exists())

    def test_writer_cleans_when_unlink_commit_does_not_happen(self):
        class Commit:
            committed = False

            def seal_for_guard(self, *_args):
                pass

            def consume_by_unlink(self):
                raise OSError("fixture")

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            with self.assertRaises(NativeGitError):
                write_pending_evidence(path, _pass_evidence(), None, Commit())
            self.assertFalse(path.exists())
            self.assertFalse(path.with_name("evidence.json.pending").exists())

    def test_writer_reports_cleanup_that_cannot_be_proven(self):
        class Commit:
            def seal_for_guard(self, *_args):
                raise AssertionError("seal must not be reached")

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            with patch(
                "tools.psm_wma.materialize_immutable_source_authority_root._fsync_directory",
                side_effect=OSError("fixture"),
            ), self.assertRaises(NativeGitError):
                write_pending_evidence(path, _pass_evidence(), None, Commit())

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
            tx = NativeAuthorityGit(git, root, str(remote), root / "temporary.index", COMMIT_METADATA)
            parent = tx._run("rev-parse", "HEAD")
            revision = tx.create_detached_commit(parent, {"proof.json": b"{}"})
            self.assertEqual(tx.parents(revision), (parent,))
            self.assertTrue(tx.cas_create_local("refs/heads/test", revision))
            self.assertTrue(tx.cas_create_remote("refs/heads/test", revision))
            self.assertTrue(tx.cas_delete_remote("refs/heads/test", revision))
            self.assertTrue(tx.cas_delete_local("refs/heads/test", revision))

    def test_frozen_metadata_controls_detached_commit_identity(self):
        git = Path(shutil.which("git") or "")
        with tempfile.TemporaryDirectory() as raw:
            root, remote = Path(raw) / "root", Path(raw) / "remote.git"
            subprocess.run([str(git), "init", "-q", str(root)], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.name", "ambient-one"], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.email", "one@example.invalid"], check=True)
            (root / "README").write_text("x")
            subprocess.run([str(git), "-C", str(root), "add", "README"], check=True)
            subprocess.run([str(git), "-C", str(root), "commit", "-qm", "root"], check=True)
            subprocess.run([str(git), "init", "--bare", "-q", str(remote)], check=True)
            parent = subprocess.run([str(git), "-C", str(root), "rev-parse", "HEAD"], check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
            first = NativeAuthorityGit(git, root, str(remote), root / "first.index", COMMIT_METADATA).create_detached_commit(parent, {"proof.json": b"{}"})
            subprocess.run([str(git), "-C", str(root), "config", "user.name", "ambient-two"], check=True)
            second = NativeAuthorityGit(git, root, str(remote), root / "second.index", COMMIT_METADATA).create_detached_commit(parent, {"proof.json": b"{}"})
            changed = CommitMetadata("fixture", "fixture@example.invalid", "@1 +0000", "fixture", "fixture@example.invalid", "@1 +0000", "fixture commit")
            third = NativeAuthorityGit(git, root, str(remote), root / "third.index", changed).create_detached_commit(parent, {"proof.json": b"{}"})
            self.assertEqual(first, second)
            self.assertNotEqual(first, third)

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
            tx = NativeAuthorityGit(git, root, str(remote), root / "temporary.index", COMMIT_METADATA)
            parent = tx._run("rev-parse", "HEAD")
            candidate = tx.create_detached_commit(parent, {"candidate.json": b"{}"})
            foreign = tx.create_detached_commit(candidate, {"foreign.json": b"{}"})
            ref = "refs/heads/lease"
            self.assertTrue(tx.cas_create_remote(ref, candidate))
            self.assertFalse(tx.cas_create_remote(ref, foreign))
            self.assertEqual(tx.remote_ref(ref), candidate)
            self.assertFalse(tx.cas_delete_remote(ref, foreign))
            self.assertEqual(tx.remote_ref(ref), candidate)

    def test_failed_mutation_never_claims_same_candidate_or_absent_success(self):
        git = Path(shutil.which("git") or "")
        with tempfile.TemporaryDirectory() as raw:
            root, remote = Path(raw) / "root", Path(raw) / "remote.git"
            subprocess.run([str(git), "init", "-q", str(root)], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.name", "fixture"], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
            (root / "README").write_text("x")
            subprocess.run([str(git), "-C", str(root), "add", "README"], check=True)
            subprocess.run([str(git), "-C", str(root), "commit", "-qm", "root"], check=True)
            subprocess.run([str(git), "init", "--bare", "-q", str(remote)], check=True)
            tx = NativeAuthorityGit(git, root, str(remote), root / "temporary.index", COMMIT_METADATA)
            revision = tx._run("rev-parse", "HEAD")
            ref = "refs/heads/race"
            tx._run("update-ref", ref, revision)
            self.assertTrue(tx.cas_create_remote(ref, revision))
            mutation_succeeded = tx._mutation_succeeded
            tx._mutation_succeeded = lambda *_args, **_kwargs: False
            self.assertFalse(tx.cas_create_local(ref, revision))
            self.assertFalse(tx.cas_create_remote(ref, revision))
            tx._mutation_succeeded = mutation_succeeded
            tx._run("update-ref", "-d", ref, revision)
            self.assertTrue(tx.cas_delete_remote(ref, revision))
            tx._mutation_succeeded = lambda *_args, **_kwargs: False
            self.assertFalse(tx.cas_delete_local(ref, revision))
            self.assertFalse(tx.cas_delete_remote(ref, revision))

    def test_cas_same_candidate_and_concurrent_delete_races_require_own_success(self):
        git = Path(shutil.which("git") or "")
        with tempfile.TemporaryDirectory() as raw:
            root, remote = Path(raw) / "root", Path(raw) / "remote.git"
            subprocess.run([str(git), "init", "-q", str(root)], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.name", "fixture"], check=True)
            subprocess.run([str(git), "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
            (root / "README").write_text("x")
            subprocess.run([str(git), "-C", str(root), "add", "README"], check=True)
            subprocess.run([str(git), "-C", str(root), "commit", "-qm", "root"], check=True)
            subprocess.run([str(git), "init", "--bare", "-q", str(remote)], check=True)
            tx = NativeAuthorityGit(git, root, str(remote), root / "temporary.index", COMMIT_METADATA)
            revision = tx._run("rev-parse", "HEAD")
            local_ref, remote_ref = "refs/heads/local-race", "refs/heads/remote-race"
            tx._run("update-ref", local_ref, revision)
            self.assertFalse(tx.cas_create_local(local_ref, revision))
            self.assertEqual(tx.local_ref(local_ref), revision)
            self.assertTrue(tx.cas_create_remote(remote_ref, revision))
            self.assertFalse(tx.cas_create_remote(remote_ref, revision))
            self.assertEqual(tx.remote_ref(remote_ref), revision)
            tx._run("update-ref", "-d", local_ref, revision)
            self.assertFalse(tx.cas_delete_local(local_ref, revision))
            self.assertIsNone(tx.local_ref(local_ref))
            self.assertTrue(tx.cas_delete_remote(remote_ref, revision))
            self.assertFalse(tx.cas_delete_remote(remote_ref, revision))
            self.assertIsNone(tx.remote_ref(remote_ref))


if __name__ == "__main__":
    unittest.main()
