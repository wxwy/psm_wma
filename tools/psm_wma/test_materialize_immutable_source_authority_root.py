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

from tools.psm_wma.immutable_source_authority_root import (
    AuthorityRequest,
    EvidenceCleanupIncomplete,
)
from tools.psm_wma.materialize_immutable_source_authority_root import (
    NativeAuthorityGit,
    CommitMetadata,
    main,
    NativeGitError,
    AuthorityAdapterInvocation,
    ExecutableIdentity,
    GitConfigurationAuthority,
    ModuleIdentity,
    preflight_authority_invocation,
    _tool_version,
    verify_evidence_bytes,
    verify_evidence_path,
    classify_pass_restart,
    write_pending_evidence,
    write_failure_evidence,
    _read_input_fd,
    _cleanup_pending_evidence,
    _unlink_owned,
    _path_identity,
    _fd_identity,
    _validate_https_endpoint,
    _read_regular_relative,
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
        "collection_module": {"path": "tools/psm_wma/immutable_source_collection.py", "blob_native_oid": "e" * 40, "raw_sha256": _sha("collection")},
        "audit_module": {"path": "tools/g0/audit_r09_b_ttt_root_gitlink_authority.py", "blob_native_oid": "f" * 40, "raw_sha256": _sha("audit")},
        "interpreter": {"path": "/usr/bin/python3", "raw_sha256": _sha("python"), "version": "Python fixture"},
        "git_executable": {"path": "/usr/bin/git", "raw_sha256": _sha("git"), "version": "git fixture"},
        "cwd": "/temporary/fixture",
        "sanitized_env_sha256": _sha("environment"),
        "argv_sha256": _sha("argv"),
        "bootstrap": {
            "declared_raw_sha256": _sha("bootstrap-raw"),
            "declared_argv_sha256": _sha("bootstrap-argv"),
            "observed_raw_sha256": _sha("bootstrap-raw"),
            "observed_argv_sha256": _sha("bootstrap-argv"),
        },
        "git_dir": "/temporary/fixture/.git",
        "git_common_dir": "/temporary/fixture/.git",
        "git_config_path": "/temporary/fixture/.git/config",
        "git_config_raw_sha256": _sha("git-config"),
        "git_config_allowlist": {"core.bare": "false"},
        "git_isolation_fingerprint": _sha("git-isolation"),
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
    def test_no_follow_relative_module_reader_rejects_component_symlink(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "root"
            root.mkdir()
            (root / "safe").mkdir()
            (root / "safe" / "module.py").write_bytes(b"safe")
            self.assertEqual(_read_regular_relative(root, "safe/module.py"), b"safe")
            foreign = Path(raw) / "foreign"
            foreign.mkdir()
            (foreign / "module.py").write_bytes(b"foreign")
            (root / "safe").rename(root / "safe-real")
            (root / "safe").symlink_to(foreign, target_is_directory=True)
            with self.assertRaises(NativeGitError):
                _read_regular_relative(root, "safe/module.py")

    def test_fd_root_reader_survives_global_root_replacement(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "root"
            root.mkdir()
            (root / "safe").mkdir()
            (root / "safe" / "module.py").write_bytes(b"held owner bytes")
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                foreign = Path(raw) / "foreign"
                foreign.mkdir()
                (foreign / "safe").mkdir()
                (foreign / "safe" / "module.py").write_bytes(b"foreign bytes")
                root.rename(Path(raw) / "root-held")
                root.symlink_to(foreign, target_is_directory=True)
                self.assertEqual(
                    _read_regular_relative(descriptor, "safe/module.py"),
                    b"held owner bytes",
                )
            finally:
                os.close(descriptor)

    def test_fd_owner_git_consumer_inherits_only_owner_fd_and_rechecks_index(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "root"
            root.mkdir()
            index = root / ".authority-root.index"
            index.write_bytes(b"temporary index")
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                transaction = NativeAuthorityGit(
                    Path(shutil.which("git") or "").resolve(),
                    Path(f"/proc/self/fd/{descriptor}"),
                    "https://example.invalid/authority/root",
                    Path(f"/proc/self/fd/{descriptor}/.authority-root.index"),
                    COMMIT_METADATA,
                    owner_fd=descriptor,
                )
                completed = subprocess.CompletedProcess([], 0, b"ok\n", b"")
                with patch(
                    "tools.psm_wma.materialize_immutable_source_authority_root.subprocess.run",
                    return_value=completed,
                ) as run:
                    self.assertEqual(transaction._run("rev-parse", "HEAD"), "ok")
                self.assertEqual(run.call_args.kwargs["pass_fds"], (descriptor,))
                self.assertTrue(run.call_args.kwargs["close_fds"])
                index.unlink()
                index.write_bytes(b"foreign index")
                with self.assertRaisesRegex(NativeGitError, "identity 漂移"):
                    transaction._run("rev-parse", "HEAD")
            finally:
                os.close(descriptor)

    def test_https_endpoint_grammar_is_canonical_and_direct(self):
        _validate_https_endpoint("https://example.invalid/authority/root")
        for value in (
            "https://user@example.invalid/path",
            "https://user:pass@example.invalid/path",
            "https://example.invalid/path?query=1",
            "https://example.invalid/path#fragment",
            "https://EXAMPLE.invalid/path",
            "https://example.invalid:443/path",
            "origin",
            "file:///temporary/remote.git",
        ):
            with self.subTest(value=value):
                with self.assertRaises(NativeGitError):
                    _validate_https_endpoint(value)

    def test_pass_restart_never_reconstructs_acceptance_from_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            guard = path.with_name(path.name + ".pending")
            guard.write_bytes(b"pending")
            self.assertEqual(classify_pass_restart(path), "PENDING_GUARD_VISIBLE")
            guard.unlink()
            path.write_bytes(_redigest(_pass_evidence()))
            with self.assertRaisesRegex(NativeGitError, "PASS_CLOSURE_RECOVERY_REQUIRED"):
                classify_pass_restart(path)

    def test_preflight_routes_guard_absent_pass_evidence_to_recovery(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            path.write_bytes(_redigest(_pass_evidence()))
            request = AuthorityRequest("a" * 40, "b" * 40, b"{}", b"{}")
            invocation = AuthorityAdapterInvocation(
                request,
                hashlib.sha256(b"{}").hexdigest(),
                hashlib.sha256(b"{}").hexdigest(),
                ModuleIdentity("adapter.py", "c" * 40, "d" * 64),
                ModuleIdentity("authority.py", "e" * 40, "f" * 64),
                None,
                None,
                ExecutableIdentity(Path("/bin/true"), "0" * 64, "fixture"),
                ExecutableIdentity(Path("/bin/true"), "1" * 64, "fixture"),
                path,
                "2" * 64,
            )
            tree = {"cosmos-framework": ("160000", "commit", request.expected_child_gitlink)}
            transaction = type("Transaction", (), {
                "production": False,
                "verify_configuration_authority": lambda _self: GitConfigurationAuthority(
                    Path(raw) / ".git", Path(raw) / ".git", Path(raw) / ".git/config",
                    "3" * 64, {}, "4" * 64,
                ),
            })()
            with patch(
                "tools.psm_wma.materialize_immutable_source_authority_root.validate_request"
            ), patch(
                "tools.psm_wma.materialize_immutable_source_authority_root.validated_git_tree",
                return_value=tree,
            ), patch(
                "tools.psm_wma.materialize_immutable_source_authority_root._verify_module_identity"
            ), patch(
                "tools.psm_wma.materialize_immutable_source_authority_root._verify_executable_identity"
            ), patch(
                "tools.psm_wma.materialize_immutable_source_authority_root._verify_loaded_identity"
            ):
                with self.assertRaisesRegex(NativeGitError, "PASS_CLOSURE_RECOVERY_REQUIRED"):
                    preflight_authority_invocation(invocation, transaction, Path(raw))

    def test_cleanup_preserves_replaced_foreign_path(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            path = directory / "evidence.json.pending"
            path.write_bytes(b"owned")
            identity = _path_identity(path)
            path.unlink()
            path.write_bytes(b"foreign")
            with self.assertRaises(EvidenceCleanupIncomplete):
                _cleanup_pending_evidence(((path, identity),), directory)
            self.assertEqual(path.read_bytes(), b"foreign")

    def test_fd_identity_preserves_replaced_foreign_path(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            path = directory / "evidence.json.pending"
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                identity = _fd_identity(descriptor)
            finally:
                os.close(descriptor)
            path.unlink()
            path.write_bytes(b"foreign")
            with self.assertRaises(EvidenceCleanupIncomplete):
                _cleanup_pending_evidence(((path, identity),), directory)
            self.assertEqual(path.read_bytes(), b"foreign")

    def test_cleanup_handoff_preserves_boundary_foreign_replacement(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            path = directory / "evidence.json.pending"
            path.write_bytes(b"owned")
            identity = _path_identity(path)
            original_rename = os.rename
            replaced = False

            def replace_before_handoff(source, destination):
                nonlocal replaced
                if Path(source) == path and not replaced:
                    replaced = True
                    path.unlink()
                    path.write_bytes(b"foreign")
                return original_rename(source, destination)

            with patch(
                "tools.psm_wma.immutable_source_authority_root.os.rename",
                side_effect=replace_before_handoff,
            ):
                self.assertFalse(_unlink_owned(path, identity))
            self.assertEqual(path.read_bytes(), b"foreign")

    def test_failure_writer_preserves_replaced_foreign_temporary(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            original_link = os.link

            def replace_then_fail(source, destination, *args, **kwargs):
                original_link(source, destination, *args, **kwargs)
                Path(source).unlink()
                Path(source).write_bytes(b"foreign")
                raise OSError("fixture")

            with patch(
                "tools.psm_wma.materialize_immutable_source_authority_root.os.link",
                side_effect=replace_then_fail,
            ), self.assertRaises(EvidenceCleanupIncomplete):
                write_failure_evidence(path, _preflight_failure_evidence())
            self.assertEqual(path.with_name("evidence.json.tmp").read_bytes(), b"foreign")

    def _run_cli(self, root: Path, selection, config, argv):
        return self._run_cli_with_hook(
            root, selection, config, argv,
            "tool._validate_https_endpoint = lambda remote: None",
        )

    def _run_cli_with_remote_cas_failure(self, root: Path, selection, config, argv):
        return self._run_cli_with_hook(
            root, selection, config, argv,
            "tool.NativeAuthorityGit.cas_create_remote = lambda self, ref, revision: False",
        )

    def _run_cli_with_hook(self, root: Path, selection, config, argv, hook: str):
        harness = (
            "import sys; "
            "import tools.psm_wma.materialize_immutable_source_authority_root as tool; "
            "tool._validate_https_endpoint = lambda remote: None; "
            "tool._bootstrap_identity_from_runtime = lambda args, actual: tool.BootstrapIdentity('a'*64, 'b'*64, 'a'*64, 'b'*64); "
            "tool.NativeAuthorityGit._prefix = property(lambda self: (*tool._GIT_PREFIX[:-1], 'protocol.file.allow=always')); "
            "tool.NativeAuthorityGit._verify_owner_barrier = lambda self: None; "
            f"exec({hook!r}); "
            "raise SystemExit(tool.main(sys.argv[1:]))"
        )
        owner_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            procfd = "/proc/self/fd/8"
            owner_argv = list(argv)
            for option, value in (
                ("--cwd", procfd),
                ("--index", procfd + "/.authority-root.index"),
                ("--bootstrap-project-root", procfd),
            ):
                owner_argv[owner_argv.index(option) + 1] = value
            owner_argv.extend(("--bootstrap-owner-root-fd", "8"))
            (root / ".authority-root.index").write_bytes(b"")
            command = [
                str(Path(sys.executable).resolve()), "-c",
                "import os,sys; os.dup2(int(sys.argv[1]),8); os.set_inheritable(8,True); os.execv(sys.argv[2],sys.argv[2:])",
                str(owner_fd), str(Path(sys.executable).resolve()), "-c", harness,
                "--selection-fd", str(selection.fileno()),
                "--config-fd", str(config.fileno()), *owner_argv,
            ]
            return subprocess.run(
                command, cwd=root,
                pass_fds=(selection.fileno(), config.fileno(), owner_fd),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
            )
        finally:
            os.close(owner_fd)

    def _run_bootstrap_cli(
        self, root: Path, selection, config, argv, *, contract_payload=None,
        mutate_adapter_argv=None, mutate_bootstrap_argv=None, mutate_contract=None,
        owner_fd: int | None = None, mutate_root=None,
    ):
        payload = __import__(
            "tools.psm_wma.materialize_immutable_source_authority_root",
            fromlist=["bootstrap_payload"],
        ).bootstrap_payload()
        contract_path = root.parent / "bootstrap-contract.json"
        with contract_path.open("w+b") as contract:
            opened_owner_fd = None
            if owner_fd is None:
                opened_owner_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
                owner_fd = opened_owner_fd
            position = argv.index("--bootstrap-contract-fd")
            argv[position + 1] = str(contract.fileno())
            adapter_argv = [
                "--selection-fd", str(selection.fileno()), "--config-fd",
                str(config.fileno()), *argv,
            ]
            procfd = "/proc/self/fd/8"
            for option, value in (
                ("--cwd", procfd),
                ("--index", procfd + "/.authority-root.index"),
                ("--bootstrap-project-root", procfd),
            ):
                adapter_argv[adapter_argv.index(option) + 1] = value
            if "--bootstrap-owner-root-fd" not in adapter_argv:
                adapter_argv.extend(("--bootstrap-owner-root-fd", "8"))
            (root / ".authority-root.index").write_bytes(b"")
            original = [
                str(Path(sys.executable).resolve()), "-I", "-S", "-B", "-c",
                payload, "--", *adapter_argv,
            ]
            if mutate_bootstrap_argv is not None:
                mutate_bootstrap_argv(original)
            contract_argv = list(original)
            if mutate_adapter_argv is not None:
                mutate_adapter_argv(original)
            contract.write(json.dumps({
                "bootstrap_raw_sha256": hashlib.sha256(
                    (payload if contract_payload is None else contract_payload).encode()
                ).hexdigest(),
                "bootstrap_argv_sha256": hashlib.sha256(json.dumps(
                    contract_argv[6:], sort_keys=True, separators=(",", ":"),
                    ensure_ascii=False,
                ).encode()).hexdigest(),
            }, sort_keys=True, separators=(",", ":")).encode())
            contract.flush()
            if mutate_contract is not None:
                mutate_contract(contract)
                contract.flush()
            if mutate_root is not None:
                mutate_root()
            pass_fds = (selection.fileno(), config.fileno(), contract.fileno())
            pass_fds += (owner_fd,)
            original = [
                str(Path(sys.executable).resolve()), "-c",
                "import os,sys; os.dup2(int(sys.argv[1]),8); os.set_inheritable(8,True); os.execv(sys.argv[2],sys.argv[2:])",
                str(owner_fd), *original,
            ]
            try:
                return subprocess.run(
                    original, cwd=root, pass_fds=pass_fds,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
                )
            finally:
                if opened_owner_fd is not None:
                    os.close(opened_owner_fd)
    def _cli_fixture(self, directory: Path):
        git = Path(shutil.which("git") or "").resolve()
        root, remote = directory / "root", directory / "remote.git"
        subprocess.run([str(git), "init", "-q", str(root)], check=True)
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
        subprocess.run([
            str(git), "-C", str(root), "-c", "user.name=fixture",
            "-c", "user.email=fixture@example.invalid", "commit", "-qm", "formal root",
        ], check=True)
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
        selection_path, config_path = directory / "selection.json", directory / "config.json"
        selection_path.write_bytes(selection)
        config_path.write_bytes(config)
        identities = []
        for relative in (
            adapter_path,
            authority_path,
            "tools/psm_wma/immutable_source_collection.py",
            "tools/g0/audit_r09_b_ttt_root_gitlink_authority.py",
        ):
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
            "--bootstrap-contract-fd", "-1", "--bootstrap-project-root", str(root),
            "--bootstrap-module", "tools.psm_wma.materialize_immutable_source_authority_root",
            "--adapter-path", identities[0], "--adapter-blob-oid", identities[1], "--adapter-raw-sha256", identities[2],
            "--authority-module-path", identities[3], "--authority-module-blob-oid", identities[4], "--authority-module-raw-sha256", identities[5],
            "--collection-module-path", identities[6], "--collection-module-blob-oid", identities[7], "--collection-module-raw-sha256", identities[8],
            "--audit-module-path", identities[9], "--audit-module-blob-oid", identities[10], "--audit-module-raw-sha256", identities[11],
            "--author-name", COMMIT_METADATA.author_name, "--author-email", COMMIT_METADATA.author_email, "--author-date", COMMIT_METADATA.author_date,
            "--committer-name", COMMIT_METADATA.committer_name, "--committer-email", COMMIT_METADATA.committer_email, "--committer-date", COMMIT_METADATA.committer_date,
            "--commit-message", COMMIT_METADATA.message,
        ]
        return git, root, remote, selection_path, config_path, argv

    @staticmethod
    def _relocate_bootstrap_argv(argv, root: Path, destination: Path):
        source = str(root)
        target = str(destination)
        return [
            target + value[len(source):] if value.startswith(source) else value
            for value in argv
        ]

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

    def test_bootstrap_fd8_uses_procfd_owner_argv_with_temporary_git(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                procfd = "/proc/self/fd/8"
                for option, value in (
                    ("--cwd", procfd),
                    ("--index", procfd + "/.authority-root.index"),
                    ("--bootstrap-project-root", procfd),
                ):
                    argv[argv.index(option) + 1] = value
                argv.extend(("--bootstrap-owner-root-fd", "8"))
                (root / ".authority-root.index").write_bytes(b"")
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_bootstrap_cli(
                        root, selection_handle, config_handle, argv, owner_fd=descriptor,
                    )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("production remote 必须为canonical HTTPS endpoint", result.stderr)
                self.assertEqual(verify_evidence_path(root / "evidence.json")["status"], "FAIL")
            finally:
                os.close(descriptor)

    def test_fd_owner_configuration_does_not_resolve_procfd_cwd(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, _selection, _config, _argv = self._cli_fixture(Path(raw))
            index = root / ".authority-root.index"
            index.write_bytes(b"")
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                procfd = Path(f"/proc/self/fd/{descriptor}")
                transaction = NativeAuthorityGit(
                    git, procfd, str(remote), procfd / ".authority-root.index",
                    COMMIT_METADATA, owner_fd=descriptor,
                )
                authority = transaction.verify_configuration_authority()
                self.assertEqual(authority.config_path, root / ".git/config")
            finally:
                os.close(descriptor)

    def test_fd_owner_actual_git_rejects_replaced_index_before_consumer(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, _selection, _config, _argv = self._cli_fixture(Path(raw))
            index = root / ".authority-root.index"
            index.write_bytes(b"")
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                procfd = Path(f"/proc/self/fd/{descriptor}")
                transaction = NativeAuthorityGit(
                    git, procfd, str(remote), procfd / ".authority-root.index",
                    COMMIT_METADATA, owner_fd=descriptor,
                )
                self.assertTrue(transaction._run("rev-parse", "--is-inside-work-tree"))
                index.unlink()
                index.write_bytes(b"foreign index")
                with self.assertRaisesRegex(NativeGitError, "identity 漂移"):
                    transaction._run("rev-parse", "HEAD")
            finally:
                os.close(descriptor)

    def test_bootstrap_validates_before_non_https_endpoint_preflight(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(root, selection_handle, config_handle, argv)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((root / "evidence.json").exists(), result.stderr)
            self.assertEqual(verify_evidence_path(root / "evidence.json")["status"], "FAIL")
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
            self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_tampered_adapter_argv_before_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(
                    root, selection_handle, config_handle, argv,
                    mutate_adapter_argv=lambda values: values.__setitem__(
                        values.index("--remote") + 1, "https://example.invalid/drift"
                    ),
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "evidence.json").exists())
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
            self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_missing_isolation_flag_before_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(
                    root, selection_handle, config_handle, argv,
                    mutate_adapter_argv=lambda values: values.__setitem__(2, "-B"),
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "evidence.json").exists())
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
            self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_malformed_contract_before_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            def replace_contract(handle):
                handle.seek(0)
                handle.truncate()
                handle.write(b"{}")
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(
                    root, selection_handle, config_handle, argv,
                    mutate_contract=replace_contract,
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "evidence.json").exists())
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
            self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_collection_or_audit_drift_before_import(self):
        for relative in (
            "tools/psm_wma/immutable_source_collection.py",
            "tools/g0/audit_r09_b_ttt_root_gitlink_authority.py",
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as raw:
                git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
                sentinel = root / "bootstrap-imported"
                (root / relative).write_text(
                    "open('bootstrap-imported', 'w').write('imported')\n"
                )
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_bootstrap_cli(root, selection_handle, config_handle, argv)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(sentinel.exists(), result.stderr)
                self.assertFalse((root / "evidence.json").exists())
                transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
                self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
                self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_module_symlink_before_import(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            target = root.parent / "foreign-collection.py"
            target.write_text("open('bootstrap-imported', 'w').write('imported')\n")
            module_path = root / "tools/psm_wma/immutable_source_collection.py"
            module_path.unlink()
            module_path.symlink_to(target)
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(root, selection_handle, config_handle, argv)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "bootstrap-imported").exists())
            self.assertFalse((root / "evidence.json").exists())
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_hostile_local_config_before_git_or_import(self):
        for payload in (
            "\n[core]\n fsmonitor = /bin/false\n",
            "\n[include]\n path = /hostile/config\n",
            "\n[extensions]\n worktreeConfig = true\n",
        ):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as raw:
                git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
                config_path = root / ".git/config"
                config_path.write_text(config_path.read_text() + payload)
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_bootstrap_cli(root, selection_handle, config_handle, argv)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((root / "evidence.json").exists(), result.stderr)
                transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
                self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_preexisting_worktree_config_before_git_or_import(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            (root / ".git/config.worktree").write_text("[core]\n fsmonitor = /bin/false\n")
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(root, selection_handle, config_handle, argv)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "evidence.json").exists(), result.stderr)
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_common_config_symlink_before_git_or_import(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            config_path = root / ".git/config"
            target = root.parent / "foreign-config"
            target.write_bytes(config_path.read_bytes())
            config_path.unlink()
            config_path.symlink_to(target)
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(root, selection_handle, config_handle, argv)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "evidence.json").exists(), result.stderr)
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_linked_worktree_config_before_git_or_import(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            linked = root.parent / "linked"
            subprocess.run(
                [str(git), "-C", str(root), "worktree", "add", "--detach", "-q", str(linked), "HEAD"],
                check=True,
            )
            marker = (linked / ".git").read_text().strip()
            self.assertTrue(marker.startswith("gitdir: "))
            git_dir = Path(marker[8:])
            if not git_dir.is_absolute():
                git_dir = (linked / git_dir).resolve()
            (git_dir / "config.worktree").write_text("[core]\n fsmonitor = /bin/false\n")
            linked_argv = self._relocate_bootstrap_argv(argv, root, linked)
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(
                    linked, selection_handle, config_handle, linked_argv
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((linked / "evidence.json").exists(), result.stderr)
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_linked_worktree_gitdir_escape_before_import(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            linked = root.parent / "linked"
            subprocess.run(
                [str(git), "-C", str(root), "worktree", "add", "--detach", "-q", str(linked), "HEAD"],
                check=True,
            )
            foreign = root.parent / "foreign-admin"
            foreign.mkdir()
            (foreign / "gitdir").write_text(str(root.parent / "not-linked"))
            (foreign / "commondir").write_text(str(root / ".git"))
            (linked / ".git").write_text(f"gitdir: {foreign}\n")
            linked_argv = self._relocate_bootstrap_argv(argv, root, linked)
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(
                    linked, selection_handle, config_handle, linked_argv
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((linked / "evidence.json").exists(), result.stderr)
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_config_replacement_after_git_precheck(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            config_path = root / ".git/config"
            replacement = root.parent / "replacement-config"
            replacement.write_bytes(config_path.read_bytes())
            wrapper = root.parent / "git-replaces-config"
            wrapper.write_text(
                "#!" + str(Path(sys.executable).resolve()) + "\n"
                "import os, sys\n"
                f"replacement = {str(replacement)!r}\n"
                f"config = {str(config_path)!r}\n"
                f"git = {str(git)!r}\n"
                "if sys.argv[1:] != ['--version'] and os.path.exists(replacement):\n"
                "    os.replace(replacement, config)\n"
                "os.execv(git, [git, *sys.argv[1:]])\n"
            )
            wrapper.chmod(0o755)
            position = argv.index("--git")
            argv[position + 1] = str(wrapper)
            argv[argv.index("--git-raw-sha256") + 1] = hashlib.sha256(wrapper.read_bytes()).hexdigest()
            argv[argv.index("--git-version") + 1] = _tool_version(wrapper)
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(root, selection_handle, config_handle, argv)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "evidence.json").exists(), result.stderr)
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_linked_routing_replacement_after_git_precheck(self):
        for routing_name in ("marker", "commondir"):
            with self.subTest(routing_name=routing_name), tempfile.TemporaryDirectory() as raw:
                git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
                linked = root.parent / "linked"
                subprocess.run(
                    [str(git), "-C", str(root), "worktree", "add", "--detach", "-q", str(linked), "HEAD"],
                    check=True,
                )
                marker = linked / ".git"
                git_dir_text = marker.read_text().strip()
                self.assertTrue(git_dir_text.startswith("gitdir: "))
                git_dir = Path(git_dir_text[8:])
                if not git_dir.is_absolute():
                    git_dir = (linked / git_dir).resolve()
                routing_path = marker if routing_name == "marker" else git_dir / "commondir"
                replacement = root.parent / f"replacement-{routing_name}"
                replacement.write_bytes(routing_path.read_bytes())
                wrapper = root.parent / f"git-replaces-{routing_name}"
                wrapper.write_text(
                    "#!" + str(Path(sys.executable).resolve()) + "\n"
                    "import os, sys\n"
                    f"replacement = {str(replacement)!r}\n"
                    f"routing_path = {str(routing_path)!r}\n"
                    f"git = {str(git)!r}\n"
                    "if sys.argv[1:] != ['--version'] and os.path.exists(replacement):\n"
                    "    os.replace(replacement, routing_path)\n"
                    "os.execv(git, [git, *sys.argv[1:]])\n"
                )
                wrapper.chmod(0o755)
                linked_argv = self._relocate_bootstrap_argv(argv, root, linked)
                linked_argv[linked_argv.index("--git") + 1] = str(wrapper)
                linked_argv[linked_argv.index("--git-raw-sha256") + 1] = hashlib.sha256(wrapper.read_bytes()).hexdigest()
                linked_argv[linked_argv.index("--git-version") + 1] = _tool_version(wrapper)
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_bootstrap_cli(
                        linked, selection_handle, config_handle, linked_argv
                    )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((linked / "evidence.json").exists(), result.stderr)
                transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
                self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_executable_identity_drift_before_import(self):
        for option, value in (
            ("--interpreter", "/bin/false"),
            ("--interpreter-raw-sha256", "0" * 64),
            ("--interpreter-version", "hostile-version"),
            ("--git-version", "hostile-version"),
        ):
            with self.subTest(option=option), tempfile.TemporaryDirectory() as raw:
                git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
                def mutate(command):
                    position = command.index(option)
                    command[position + 1] = value
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_bootstrap_cli(
                        root, selection_handle, config_handle, argv,
                        mutate_bootstrap_argv=mutate,
                    )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((root / "evidence.json").exists(), result.stderr)
                transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
                self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_bootstrap_rejects_tampered_c_payload_before_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            original_payload = __import__(
                "tools.psm_wma.materialize_immutable_source_authority_root",
                fromlist=["bootstrap_payload"],
            ).bootstrap_payload()
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                with patch(
                    "tools.psm_wma.materialize_immutable_source_authority_root.bootstrap_payload",
                    return_value=original_payload + "\n# tampered\n",
                ):
                    result = self._run_bootstrap_cli(
                        root, selection_handle, config_handle, argv,
                        contract_payload=original_payload,
                    )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "evidence.json").exists())

    def test_bootstrap_rejects_intermediate_module_symlink_before_import(self):
        with tempfile.TemporaryDirectory() as raw:
            _git, root, _remote, selection, config, argv = self._cli_fixture(Path(raw))
            foreign = root.parent / "foreign-tools"
            foreign.mkdir()

            def replace_component():
                (root / "tools").rename(root.parent / "held-tools")
                (root / "tools").symlink_to(foreign, target_is_directory=True)

            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_bootstrap_cli(
                    root, selection_handle, config_handle, argv,
                    mutate_root=replace_component,
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "evidence.json").exists())
            transaction = NativeAuthorityGit(_git, root, str(_remote), root / "read.index", COMMIT_METADATA)
            self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
            self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_common_config_authority_rejects_forbidden_and_worktree_drift(self):
        mutations = {
            "forbidden": "\n[remote \"origin\"]\n url = https://example.invalid/rewrite\n",
            "worktree_config": "\n[extensions]\n worktreeConfig = true\n",
        }
        for name, payload in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as raw:
                git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
                common_config = root / ".git/config"
                common_config.write_text(common_config.read_text() + payload)
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_cli(root, selection_handle, config_handle, argv)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(verify_evidence_path(root / "evidence.json")["status"], "FAIL")
                transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
                self.assertIsNone(transaction.local_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))
                self.assertIsNone(transaction.remote_ref("refs/heads/authority/r09-b-ttt-v035-immutable-source-v1"))

    def test_linked_worktree_uses_common_config_and_rejects_worktree_config(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, _selection, _config, _argv = self._cli_fixture(Path(raw))
            linked = root.parent / "linked"
            subprocess.run([str(git), "-C", str(root), "worktree", "add", "--detach", "-q", str(linked), "HEAD"], check=True)
            transaction = NativeAuthorityGit(git, linked, str(remote), linked / "read.index", COMMIT_METADATA)
            authority = transaction.verify_configuration_authority()
            self.assertEqual(authority.git_common_dir, (root / ".git").resolve())
            self.assertEqual(authority.config_path, (root / ".git/config").resolve())
            authority.git_dir.joinpath("config.worktree").write_text("[core]\n filemode = false\n")
            with self.assertRaisesRegex(NativeGitError, "config.worktree"):
                transaction.verify_configuration_authority()

    def test_common_config_authority_rejects_symlink_and_git_view_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, _selection, _config, _argv = self._cli_fixture(Path(raw))
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            config_path = root / ".git/config"
            config_raw = config_path.read_bytes()
            escape = root / "escape-config"
            escape.write_bytes(config_raw)
            config_path.unlink()
            config_path.symlink_to(escape)
            with self.assertRaisesRegex(NativeGitError, "non-symlink"):
                transaction.verify_configuration_authority()
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, _selection, _config, _argv = self._cli_fixture(Path(raw))
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            original = transaction._run_bytes
            def drift(*args, **kwargs):
                if args[:1] == ("config",):
                    return b"core.bare\nfalse\0"
                return original(*args, **kwargs)
            with patch.object(transaction, "_run_bytes", side_effect=drift):
                with self.assertRaisesRegex(NativeGitError, "raw/Git view"):
                    transaction.verify_configuration_authority()
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, _selection, _config, _argv = self._cli_fixture(Path(raw))
            transaction = NativeAuthorityGit(git, root, str(remote), root / "read.index", COMMIT_METADATA)
            config_path = root / ".git/config"
            original_raw = config_path.read_bytes()
            original = transaction._run_bytes
            def replace_after_view(*args, **kwargs):
                value = original(*args, **kwargs)
                if args[:1] == ("config",):
                    config_path.unlink()
                    config_path.write_bytes(original_raw)
                return value
            with patch.object(transaction, "_run_bytes", side_effect=replace_after_view):
                with self.assertRaisesRegex(NativeGitError, "bytes 在Git view期间漂移"):
                    transaction.verify_configuration_authority()

    def test_linked_worktree_common_config_rejects_forbidden_remote(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, _selection, _config, _argv = self._cli_fixture(Path(raw))
            linked = root.parent / "linked"
            subprocess.run([str(git), "-C", str(root), "worktree", "add", "--detach", "-q", str(linked), "HEAD"], check=True)
            (root / ".git/config").write_text(
                (root / ".git/config").read_text()
                + "\n[remote \"origin\"]\n url = https://example.invalid/rewrite\n"
            )
            transaction = NativeAuthorityGit(git, linked, str(remote), linked / "read.index", COMMIT_METADATA)
            with self.assertRaises(NativeGitError):
                transaction.verify_configuration_authority()

    def test_cli_preflight_rejects_input_and_identity_drift_before_mutation(self):
        cases = (
            ("--selection-raw-sha256", "0" * 64),
            ("--formal-root", "0" * 40),
            ("--child-gitlink", "0" * 40),
            ("--git-raw-sha256", "0" * 64),
            ("--interpreter-raw-sha256", "0" * 64),
            ("--adapter-raw-sha256", "0" * 64),
            ("--collection-module-raw-sha256", "0" * 64),
            ("--audit-module-raw-sha256", "0" * 64),
        )
        for option, value in cases:
            with self.subTest(option=option), tempfile.TemporaryDirectory() as raw:
                git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
                position = argv.index(option)
                argv[position + 1] = value
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_cli(root, selection_handle, config_handle, argv)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(verify_evidence_path(root / "evidence.json")["status"], "FAIL")
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

    def test_cli_tool_preflight_failure_writes_fail_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            _git, root, _remote, selection, config, argv = self._cli_fixture(Path(raw))
            position = argv.index("--git-raw-sha256")
            argv[position + 1] = "0" * 64
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_cli(root, selection_handle, config_handle, argv)
            self.assertNotEqual(result.returncode, 0, result.stderr)
            if not (root / "evidence.json").exists():
                self.fail(result.stderr)
            self.assertEqual(verify_evidence_path(root / "evidence.json")["status"], "FAIL")

    def test_cli_remote_cas_failure_writes_verified_failure_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            _git, root, _remote, selection, config, argv = self._cli_fixture(Path(raw))
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_cli_with_remote_cas_failure(
                    root, selection_handle, config_handle, argv
                )
            self.assertNotEqual(result.returncode, 0, result.stderr)
            record = verify_evidence_path(root / "evidence.json")
            self.assertEqual(record["status"], "FAIL")
            self.assertEqual(record["failure"]["primary_phase"], "remote_cas")
            self.assertTrue(record["rollback"]["complete"])

    def test_cli_pass_writer_preserves_replaced_foreign_final(self):
        hook = """
original = tool.os.link
def replace_then_fail(source, destination, *args, **kwargs):
    original(source, destination, *args, **kwargs)
    if str(destination).endswith('evidence.json'):
        tool.os.unlink(destination)
        with open(destination, 'wb') as handle:
            handle.write(b'foreign')
        raise OSError('final replacement fixture')
tool.os.link = replace_then_fail
"""
        with tempfile.TemporaryDirectory() as raw:
            _git, root, _remote, selection, config, argv = self._cli_fixture(Path(raw))
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                result = self._run_cli_with_hook(
                    root, selection_handle, config_handle, argv, hook
                )
            self.assertNotEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / "evidence.json").read_bytes(), b"foreign")

    def test_cli_other_publication_failures_write_verified_evidence(self):
        hooks = {
            "verify": """
def failing(*args):
    raise tool.NativeGitError('verify fixture')
tool.verify_candidate = failing
""",
            "local_cas": """
tool.NativeAuthorityGit.cas_create_local = lambda self, ref, revision: False
""",
            "pre_publication": """
original = tool.NativeAuthorityGit.local_ref
calls = 0
def failing(self, ref):
    global calls
    calls += 1
    if calls == 2:
        raise OSError('pre-publication fixture')
    return original(self, ref)
tool.NativeAuthorityGit.local_ref = failing
""",
            "post_publication": """
original = tool.NativeAuthorityGit.remote_ref
calls = 0
def failing(self, ref):
    global calls
    calls += 1
    if calls == 4:
        raise OSError('post-publication fixture')
    return original(self, ref)
tool.NativeAuthorityGit.remote_ref = failing
""",
            "binding_reverify": """
original = tool.verify_candidate
calls = 0
def failing(*args):
    global calls
    calls += 1
    if calls == 3:
        raise tool.NativeGitError('binding fixture')
    return original(*args)
tool.verify_candidate = failing
tool.authority_module.verify_candidate = failing
""",
            "evidence_write": """
def failing(*args, **kwargs):
    raise OSError('evidence fixture')
tool.write_pending_evidence = failing
""",
            "evidence_cleanup_incomplete": """
original = tool._fsync_directory
calls = 0
def failing(directory):
    global calls
    calls += 1
    if calls <= 2:
        raise OSError('cleanup fixture')
    return original(directory)
tool._fsync_directory = failing
""",
            "post_publication_rollback_incomplete": """
original = tool.NativeAuthorityGit.remote_ref
calls = 0
def failing(self, ref):
    global calls
    calls += 1
    if calls >= 4:
        raise OSError('persistent post-publication fixture')
    return original(self, ref)
tool.NativeAuthorityGit.remote_ref = failing
""",
        }
        for phase, hook in hooks.items():
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as raw:
                _git, root, _remote, selection, config, argv = self._cli_fixture(Path(raw))
                with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                    result = self._run_cli_with_hook(
                        root, selection_handle, config_handle, argv, hook
                    )
                self.assertNotEqual(result.returncode, 0, result.stderr)
                record = verify_evidence_path(root / "evidence.json")
                expected_status = (
                    "ROLLBACK_INCOMPLETE"
                    if phase in {"post_publication_rollback_incomplete", "evidence_cleanup_incomplete"}
                    else "FAIL"
                )
                expected_phase = (
                    "post_publication" if phase.startswith("post_")
                    else "evidence_write" if phase == "evidence_cleanup_incomplete"
                    else phase
                )
                self.assertEqual(record["status"], expected_status)
                self.assertEqual(record["failure"]["primary_phase"], expected_phase)
                if expected_phase != "verify" and phase != "evidence_cleanup_incomplete":
                    self.assertEqual(
                        record["rollback"]["complete"], expected_status == "FAIL"
                    )
                else:
                    if expected_phase == "verify":
                        self.assertFalse(record["rollback"]["entered"])
                    else:
                        self.assertTrue(record["rollback"]["complete"])
                        self.assertEqual(
                            record["failure"]["rollback_code"],
                            "EVIDENCE_CLEANUP_INCOMPLETE",
                        )
                    self.assertIsNotNone(record["candidate"]["revision"])

    def test_cli_rejects_pristine_formal_copy_when_loaded_adapter_differs(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, selection, config, argv = self._cli_fixture(Path(raw))
            with selection.open("rb") as selection_handle, config.open("rb") as config_handle:
                with self.assertRaises(SystemExit):
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
        remote_drift = deepcopy(record)
        remote_drift["execution"]["remote_identity_sha256"] = _sha("foreign-remote")
        with self.assertRaises(NativeGitError):
            verify_evidence_bytes(
                json.dumps(remote_drift, sort_keys=True, separators=(",", ":")).encode()
            )
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

    def test_production_git_view_ignores_native_replace_ref(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, _selection, _config, _argv = self._cli_fixture(Path(raw))
            transaction = NativeAuthorityGit(git, root, str(remote), root / "replace.index", COMMIT_METADATA)
            parent = transaction._run("rev-parse", "HEAD")
            replacement = transaction.create_detached_commit(parent, {"replace-proof": b"foreign"})
            subprocess.run([str(git), "-C", str(root), "replace", parent, replacement], check=True)
            self.assertNotIn("replace-proof", transaction.tree_entries(parent))
            visible = subprocess.run(
                [str(git), "-C", str(root), "ls-tree", "-r", parent],
                check=True, stdout=subprocess.PIPE, text=True,
            ).stdout
            self.assertIn("replace-proof", visible)

    def test_native_git_environment_does_not_inherit_hostile_parent_config(self):
        with tempfile.TemporaryDirectory() as raw:
            git, root, remote, _selection, _config, _argv = self._cli_fixture(Path(raw))
            transaction = NativeAuthorityGit(git, root, str(remote), root / "environment.index", COMMIT_METADATA)
            with patch.dict(os.environ, {
                "GIT_CONFIG_GLOBAL": "/hostile/global",
                "GIT_CONFIG_SYSTEM": "/hostile/system",
                "GIT_REPLACE_REF_BASE": "refs/replace/hostile",
            }):
                self.assertEqual(transaction._run("rev-parse", "HEAD"), transaction._run("rev-parse", "HEAD"))
            self.assertNotIn("GIT_REPLACE_REF_BASE", transaction.env)
            self.assertEqual(transaction.env["GIT_CONFIG_GLOBAL"], "/dev/null")
            self.assertEqual(transaction.env["GIT_CONFIG_SYSTEM"], "/dev/null")

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
