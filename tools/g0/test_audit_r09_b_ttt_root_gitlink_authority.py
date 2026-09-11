"""Temporary Git-fixture regressions for root Gitlink authority source-audit tooling."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stdout

from tools.g0 import audit_r09_b_ttt_root_gitlink_authority as audit


def canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


class RootGitlinkAuthorityAuditTest(unittest.TestCase):
    def git(self, path: Path, *args: str) -> str:
        return subprocess.run(
            ["/usr/bin/git", "-C", str(path), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def fixture(
        self, base: Path, *, canonical_publication: bool = True
    ) -> tuple[Path, Path, str, Path]:
        child = base / "child"
        root = base / "root"
        for repo in (child, root):
            subprocess.run(["/usr/bin/git", "init", "-q", str(repo)], check=True)
            self.git(repo, "config", "user.email", "fixture@example.invalid")
            self.git(repo, "config", "user.name", "fixture")
        (child / "payload").write_text("child\n")
        self.git(child, "add", "payload")
        self.git(child, "commit", "-qm", "child")
        child_commit = self.git(child, "rev-parse", "HEAD")
        config = {
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
        }
        descriptor = {
            "schema": "root_gitlink_checkpoint_source_descriptor_v1",
            "source_kind": "checkpoint_source_manifest_v1",
            "immutable_source_identifier": "a" * 64,
            "source_manifest_sha256": "b" * 64,
            "source_input_sha256": "c" * 64,
        }
        publication = {
            "schema": "root_gitlink_authority_publication_v1",
            "canonical_model_config": config,
            "checkpoint_source_descriptor": descriptor,
        }
        publication_path = root / audit.PUBLICATION_PATH
        publication_path.parent.mkdir(parents=True)
        publication_path.write_bytes(
            canonical(publication)
            if canonical_publication
            else json.dumps(publication, indent=2).encode()
        )
        (root / "README").write_text("fixture\n")
        self.git(root, "add", "README", audit.PUBLICATION_PATH)
        subprocess.run(
            [
                "/usr/bin/git",
                "-C",
                str(root),
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{child_commit},{audit.SUBMODULE_PATH}",
            ],
            check=True,
        )
        self.git(root, "commit", "-qm", "root")
        return (
            root,
            child / ".git",
            self.git(root, "rev-parse", "HEAD"),
            root / "output.json",
        )

    def invoke_raw(
        self, root: Path, child_git: Path, formal: str, output: Path
    ) -> int:
        return audit.main(
            [
                "--repo-root",
                str(root),
                "--formal-root-revision",
                formal,
                "--child-git-dir",
                str(child_git),
                "--output",
                str(output),
            ]
        )

    def invoke(self, root: Path, child_git: Path, formal: str, output: Path) -> int:
        with redirect_stdout(io.StringIO()):
            return self.invoke_raw(root, child_git, formal, output)

    def invoke_payload(
        self, root: Path, child_git: Path, formal: str, output: Path
    ) -> tuple[int, dict[str, object]]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = self.invoke_raw(root, child_git, formal, output)
        return code, json.loads(stdout.getvalue())

    def assert_failure_rows(
        self, payload: dict[str, object], index: int, reason: str
    ) -> None:
        checks = payload["checks"]
        self.assertEqual(
            [row["status"] for row in checks],
            ["PASS"] * index + ["FAIL"] + ["SKIPPED"] * (12 - index - 1),
        )
        self.assertEqual(checks[index]["reason"], reason)

    def test_valid_fixture_writes_exact_pass_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, child_git, formal, output = self.fixture(Path(temp))
            self.assertEqual(self.invoke(root, child_git, formal, output), 0)
            evidence = json.loads(output.read_bytes())
            self.assertEqual(
                evidence["schema"], "root_gitlink_source_audit_evidence_v1"
            )
            self.assertEqual(evidence["status"], "PASS")
            self.assertEqual(
                [item["name"] for item in evidence["checks"]], list(audit.CHECK_NAMES)
            )
            self.assertTrue(
                all(item["status"] == "PASS" for item in evidence["checks"])
            )
            self.assertEqual(
                hashlib.sha256(canonical(evidence["audit_record"])).hexdigest(),
                evidence["audit_record_sha256"],
            )
            self.assertEqual(
                set(evidence["audit_record"]), set(audit.AUDIT_RECORD_KEYS)
            )
            self.assertEqual(
                evidence["command_identity"]["git_executable"], "/usr/bin/git"
            )

    def test_noncanonical_publication_and_bad_revision_fail_without_mutation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, child_git, formal, output = self.fixture(
                Path(temp), canonical_publication=False
            )
            output.write_bytes(b"preserve")
            self.assertEqual(self.invoke(root, child_git, formal, output), 2)
            self.assertEqual(output.read_bytes(), b"preserve")
            self.assertEqual(self.invoke(root, child_git, "A" * 40, output), 2)
            self.assertEqual(output.read_bytes(), b"preserve")

    def test_failure_evidence_preserves_ordered_pass_fail_skipped_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, child_git, formal, output = self.fixture(
                Path(temp), canonical_publication=False
            )
            code, payload = self.invoke_payload(root, child_git, formal, output)
            self.assertEqual(code, 2)
            checks = payload["checks"]
            self.assertEqual(
                [row["status"] for row in checks],
                ["PASS"] * 5 + ["FAIL"] + ["SKIPPED"] * 6,
            )
            self.assertEqual(checks[5]["reason"], "PUBLICATION_NOT_CANONICAL")
            self.assertFalse(output.exists())

    def test_unreachable_child_commit_marks_child_commit_after_prior_passes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, _, formal, output = self.fixture(Path(temp))
            foreign = Path(temp) / "foreign"
            subprocess.run(["/usr/bin/git", "init", "-q", str(foreign)], check=True)
            code, payload = self.invoke_payload(root, foreign / ".git", formal, output)
            self.assertEqual(code, 2)
            checks = payload["checks"]
            self.assertEqual(
                [row["status"] for row in checks],
                ["PASS"] * 8 + ["FAIL"] + ["SKIPPED"] * 3,
            )
            self.assertEqual(checks[8]["reason"], "GIT_COMMAND_FAILURE")

    def test_hostile_environment_cannot_redirect_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, child_git, formal, output = self.fixture(Path(temp))
            with mock.patch.dict(
                "os.environ",
                {
                    "GIT_DIR": "/missing",
                    "GIT_OBJECT_DIRECTORY": "/missing",
                    "GIT_ALTERNATE_OBJECT_DIRECTORIES": "/missing-alt",
                    "GIT_REPLACE_REF_BASE": "refs/replace",
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "alias.cat-file=!false",
                },
                clear=False,
            ):
                self.assertEqual(self.invoke(root, child_git, formal, output), 0)
            self.assertEqual(json.loads(output.read_bytes())["status"], "PASS")

    def test_success_uses_the_single_pre_audit_bootstrap_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, child_git, formal, output = self.fixture(Path(temp))
            original = audit.bootstrap_git
            with mock.patch.object(audit, "bootstrap_git", wraps=original) as bootstrap:
                self.assertEqual(self.invoke(root, child_git, formal, output), 0)
            self.assertEqual(bootstrap.call_count, 1)

    def test_bootstrap_failures_have_null_command_identity_and_preserve_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, child_git, formal, output = self.fixture(Path(temp))
            output.write_bytes(b"existing")
            for name, executable, reason in (
                ("missing", Path(temp) / "missing", "GIT_MISSING"),
                ("nonexec", Path(temp) / "nonexec", "GIT_NOT_REGULAR_EXECUTABLE"),
            ):
                if name == "nonexec":
                    executable.write_text("not executable")
                with (
                    self.subTest(name=name),
                    mock.patch.object(audit, "GIT_EXECUTABLE", executable),
                ):
                    with mock.patch("builtins.print") as printed:
                        self.assertEqual(
                            self.invoke(root, child_git, formal, output), 3
                        )
                    payload = json.loads(printed.call_args.args[0])
                    self.assertEqual(payload["command_identity"], None)
                    self.assertEqual(payload["bootstrap"]["reason"], reason)
                    self.assertEqual(output.read_bytes(), b"existing")

    def test_bootstrap_unreadable_and_invalid_version_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            executable = Path(temp) / "bad-git"
            executable.write_text("#!/bin/sh\nprintf 'git version one\\ntwo\\n'\n")
            executable.chmod(0o755)
            with mock.patch.object(audit, "GIT_EXECUTABLE", executable):
                self.assertEqual(audit.bootstrap_git()["reason"], "GIT_VERSION_INVALID")
            with (
                mock.patch.object(audit, "GIT_EXECUTABLE", executable),
                mock.patch.object(Path, "read_bytes", side_effect=OSError("denied")),
            ):
                self.assertEqual(audit.bootstrap_git()["reason"], "GIT_UNREADABLE")

    def test_symlink_root_and_child_substitution_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, child_git, formal, output = self.fixture(Path(temp))
            root_link = Path(temp) / "root-link"
            root_link.symlink_to(root)
            self.assertEqual(self.invoke(root_link, child_git, formal, output), 3)
            self.assertFalse(output.exists())

    def test_ancestor_symlink_root_child_and_output_escape_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root, child_git, formal, output = self.fixture(base)
            for label, candidate in (
                ("root", root),
                ("child", child_git),
            ):
                link_parent = base / f"{label}-parent"
                link_parent.symlink_to(candidate.parent)
                escaped = link_parent / candidate.name
                with self.subTest(label=label):
                    self.assertEqual(
                        self.invoke(
                            escaped if label == "root" else root,
                            escaped if label == "child" else child_git,
                            formal,
                            output,
                        ),
                        3,
                    )
            output_parent = base / "output-parent"
            output_parent.symlink_to(base)
            escaped_output = output_parent / "escaped.json"
            self.assertEqual(self.invoke(root, child_git, formal, escaped_output), 3)
            self.assertFalse((base / "escaped.json").exists())

    def test_dangling_ancestor_symlink_and_relative_paths_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root, child_git, formal, output = self.fixture(base)
            for label, value in (
                ("root", Path("relative-root")),
                ("child", Path("relative-child")),
                ("output", Path("relative-output.json")),
            ):
                with self.subTest(label=label):
                    args = (
                        value if label == "root" else root,
                        value if label == "child" else child_git,
                        formal,
                        value if label == "output" else output,
                    )
                    code, payload = self.invoke_payload(*args)
                    self.assertEqual(code, 3)
                    if label == "output":
                        with self.assertRaisesRegex(audit.AuditFailure, "OUTPUT_PATH"):
                            audit.path_arg(value, "OUTPUT", must_exist=False)
                    else:
                        self.assertEqual(
                            payload["checks"][0]["reason"],
                            f"{label.upper() if label != 'child' else 'CHILD_GIT_DIR'}_PATH",
                        )
                    self.assertFalse(output.exists())
            for label, value in (
                ("root", base / "dangling-root" / "root"),
                ("child", base / "dangling-child" / ".git"),
                ("output", base / "dangling-output" / "output.json"),
            ):
                value.parent.symlink_to(base / f"missing-{label}")
                with self.subTest(label=f"dangling-{label}"):
                    args = (
                        value if label == "root" else root,
                        value if label == "child" else child_git,
                        formal,
                        value if label == "output" else output,
                    )
                    code, payload = self.invoke_payload(*args)
                    self.assertEqual(code, 3)
                    if label == "output":
                        with self.assertRaisesRegex(audit.AuditFailure, "OUTPUT_PATH"):
                            audit.path_arg(value, "OUTPUT", must_exist=False)
                    else:
                        self.assertEqual(
                            payload["checks"][0]["reason"],
                            f"{label.upper() if label != 'child' else 'CHILD_GIT_DIR'}_PATH",
                        )
                    self.assertFalse(output.exists())

    def test_direct_schema_and_raw_object_negative_matrix(self) -> None:
        config = {
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
        }
        descriptor = {
            "schema": "root_gitlink_checkpoint_source_descriptor_v1",
            "source_kind": "checkpoint_source_manifest_v1",
            "immutable_source_identifier": "a" * 64,
            "source_manifest_sha256": "b" * 64,
            "source_input_sha256": "c" * 64,
        }
        for mapping, validator, changed, reason in (
            (config, audit.validate_config, {"unknown": True}, "CONFIG_KEYS"),
            (config, audit.validate_config, {"local_memory_dim": True}, "CONFIG_DIM"),
            (descriptor, audit.validate_descriptor, {"unknown": True}, "SOURCE_KEYS"),
            (descriptor, audit.validate_descriptor, {"source_input_sha256": "A" * 64}, "SOURCE_DIGEST"),
        ):
            bad = dict(mapping)
            bad.update(changed)
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(audit.AuditFailure, reason):
                    validator(bad)
        with self.assertRaises(audit.AuditFailure):
            audit.parse_ls_tree(
                b"100644 blob " + b"a" * 40 + b"\tcosmos-framework\n",
                b"160000",
                b"commit",
                b"cosmos-framework",
            )
        with self.assertRaises(audit.AuditFailure):
            audit.tree_record("a" * 40, b"raw", b"blob\n", b"3\n")

    def test_all_config_and_source_rejection_families_are_direct(self) -> None:
        config = {
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
        }
        descriptor = {
            "schema": "root_gitlink_checkpoint_source_descriptor_v1",
            "source_kind": "checkpoint_source_manifest_v1",
            "immutable_source_identifier": "a" * 64,
            "source_manifest_sha256": "b" * 64,
            "source_input_sha256": "c" * 64,
        }
        for key in tuple(config):
            bad = dict(config)
            bad.pop(key)
            with self.subTest(config_missing=key):
                with self.assertRaisesRegex(audit.AuditFailure, "CONFIG_KEYS"):
                    audit.validate_config(bad)
        for key in (
            "local_memory_enabled",
            "local_history_enabled",
            "local_history_state_enabled",
            "local_ttt_enabled",
            "enable_input_bias",
        ):
            bad = dict(config)
            bad[key] = "true"
            with self.subTest(config_bool=key):
                with self.assertRaisesRegex(audit.AuditFailure, "CONFIG_BOOL"):
                    audit.validate_config(bad)
        for changed, reason in (
            ({"schema": "wrong"}, "CONFIG_SCHEMA"),
            ({"local_memory_dim": 31}, "CONFIG_DIM"),
            ({"local_history_backend": "wrong"}, "CONFIG_BACKEND"),
            ({"local_history_evidence_dim": True}, "CONFIG_INTEGER"),
            ({"ttt_tbptt_steps": 0}, "CONFIG_INTEGER"),
            ({"k_local": 0}, "CONFIG_INTEGER"),
            ({"ttt_inner_lr": 0}, "CONFIG_LR"),
            ({"local_evidence_feature_version": "wrong"}, "CONFIG_FIXED_VALUE"),
            ({"local_fast_state_dtype": "wrong"}, "CONFIG_FIXED_VALUE"),
            ({"local_runtime_resume_mode": "wrong"}, "CONFIG_FIXED_VALUE"),
            ({"local_memory_enabled": False}, "CONFIG_ACTIVE_MAPPING"),
        ):
            bad = dict(config)
            bad.update(changed)
            with self.subTest(config_changed=changed):
                with self.assertRaisesRegex(audit.AuditFailure, reason):
                    audit.validate_config(bad)
        self.assertNotEqual(
            audit.validate_config(config)[1],
            audit.validate_config({**config, "ttt_inner_lr": 0.02})[1],
        )
        for key in tuple(descriptor):
            bad = dict(descriptor)
            bad.pop(key)
            with self.subTest(source_missing=key):
                with self.assertRaisesRegex(audit.AuditFailure, "SOURCE_KEYS"):
                    audit.validate_descriptor(bad)
        for changed, reason in (
            ({"schema": "wrong"}, "SOURCE_SCHEMA"),
            ({"source_kind": "wrong"}, "SOURCE_SCHEMA"),
            ({"immutable_source_identifier": 1}, "SOURCE_DIGEST"),
            ({"source_manifest_sha256": "A" * 64}, "SOURCE_DIGEST"),
            ({"source_input_sha256": "a" * 63}, "SOURCE_DIGEST"),
        ):
            bad = dict(descriptor)
            bad.update(changed)
            with self.subTest(source_changed=changed):
                with self.assertRaisesRegex(audit.AuditFailure, reason):
                    audit.validate_descriptor(bad)
        self.assertNotEqual(
            audit.validate_descriptor(descriptor)[1],
            audit.validate_descriptor({**descriptor, "source_input_sha256": "d" * 64})[1],
        )

    def test_publication_tree_and_raw_record_witness_families_are_direct(self) -> None:
        config = {
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
        }
        descriptor = {
            "schema": "root_gitlink_checkpoint_source_descriptor_v1",
            "source_kind": "checkpoint_source_manifest_v1",
            "immutable_source_identifier": "a" * 64,
            "source_manifest_sha256": "b" * 64,
            "source_input_sha256": "c" * 64,
        }
        publication = {
            "schema": "root_gitlink_authority_publication_v1",
            "canonical_model_config": config,
            "checkpoint_source_descriptor": descriptor,
        }
        for changed, reason in (
            ({"extra": "self-reference"}, "PUBLICATION_KEYS"),
            ({"schema": "wrong"}, "PUBLICATION_SCHEMA"),
        ):
            bad = dict(publication)
            bad.update(changed)
            with self.subTest(publication_changed=changed):
                with self.assertRaisesRegex(audit.AuditFailure, reason):
                    audit.validate_publication(canonical(bad))
        with self.assertRaisesRegex(audit.AuditFailure, "PUBLICATION_NOT_CANONICAL"):
            audit.validate_publication(json.dumps(publication, indent=2).encode())
        for raw in (
            b"",
            b"100644 blob " + b"a" * 40 + b"\twrong\n",
            b"100644 tree " + b"a" * 40 + b"\t" + audit.PUBLICATION_PATH.encode() + b"\n",
            b"100644 blob " + b"a" * 40 + b"\t" + audit.PUBLICATION_PATH.encode() + b"\nextra\n",
        ):
            with self.subTest(tree_raw=raw):
                with self.assertRaises(audit.AuditFailure):
                    audit.parse_ls_tree(
                        raw,
                        b"100644",
                        b"blob",
                        audit.PUBLICATION_PATH.encode(),
                    )
        record, record_sha = audit.tree_record("a" * 40, b"raw", b"tree\n", b"3\n")
        changed, changed_sha = audit.tree_record("a" * 40, b"raw!", b"tree\n", b"4\n")
        self.assertEqual(record["byte_length"], 3)
        self.assertEqual(record["tree_content_sha256"], hashlib.sha256(b"raw").hexdigest())
        self.assertNotEqual(record["tree_content_sha256"], changed["tree_content_sha256"])
        self.assertNotEqual(record_sha, changed_sha)
        with self.assertRaisesRegex(audit.AuditFailure, "TREE_OBJECT"):
            audit.tree_record("a" * 40, b"raw", b"tree\n", b"4\n")

    def test_git_and_fixture_failure_witnesses_preserve_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, child_git, formal, output = self.fixture(Path(temp))
            root_tree = self.git(root, "rev-parse", f"{formal}^{{tree}}")
            original = audit.run_git

            def invoke_with(change: object, index: int, reason: str) -> None:
                output.write_bytes(b"preserve")

                def altered(
                    root_arg: Path | None,
                    child_arg: Path | None,
                    args: tuple[str, ...],
                ) -> bytes:
                    replacement = change(root_arg, child_arg, args)
                    return original(root_arg, child_arg, args) if replacement is None else replacement

                with mock.patch.object(audit, "run_git", side_effect=altered):
                    code, payload = self.invoke_payload(root, child_git, formal, output)
                self.assertEqual(code, 2)
                self.assert_failure_rows(payload, index, reason)
                self.assertEqual(output.read_bytes(), b"preserve")

            def publication_missing(
                root_arg: Path | None, _: Path | None, args: tuple[str, ...]
            ) -> bytes | None:
                if root_arg == root and args[-1] == audit.PUBLICATION_PATH:
                    return b""
                return None

            def publication_wrong_type(
                root_arg: Path | None, _: Path | None, args: tuple[str, ...]
            ) -> bytes | None:
                if root_arg == root and args[-1] == audit.PUBLICATION_PATH:
                    return b"100644 tree " + b"a" * 40 + b"\t" + audit.PUBLICATION_PATH.encode() + b"\n"
                return None

            def root_unexpected_stdout(
                root_arg: Path | None, _: Path | None, args: tuple[str, ...]
            ) -> bytes | None:
                if root_arg == root and args == ("cat-file", "-e", f"{formal}^{{commit}}"):
                    return b"unexpected"
                return None

            gitlink = self.git(root, "ls-tree", root_tree, "--", audit.SUBMODULE_PATH).split()[2]

            def child_unexpected_stdout(
                _: Path | None, child_arg: Path | None, args: tuple[str, ...]
            ) -> bytes | None:
                if child_arg == child_git and args == ("cat-file", "-e", f"{gitlink}^{{commit}}"):
                    return b"unexpected"
                return None

            def child_tree_drift(
                _: Path | None, child_arg: Path | None, args: tuple[str, ...]
            ) -> bytes | None:
                if child_arg == child_git and args == ("rev-parse", f"{gitlink}^{{tree}}"):
                    return b"not-a-tree\n"
                return None

            def root_tree_type_drift(
                root_arg: Path | None, _: Path | None, args: tuple[str, ...]
            ) -> bytes | None:
                if root_arg == root and args == ("cat-file", "-t", root_tree):
                    return b"blob\n"
                return None

            for change, index, reason in (
                (publication_missing, 4, "TREE_ENTRY_COUNT"),
                (publication_wrong_type, 4, "TREE_ENTRY_MISMATCH"),
                (root_unexpected_stdout, 0, "ROOT_COMMIT_OUTPUT"),
                (child_unexpected_stdout, 8, "CHILD_COMMIT_OUTPUT"),
                (child_tree_drift, 9, "CHILD_TREE_OID"),
                (root_tree_type_drift, 2, "TREE_OBJECT"),
            ):
                with self.subTest(reason=reason):
                    invoke_with(change, index, reason)
            output.write_bytes(b"preserve")
            code, payload = self.invoke_payload(root, child_git.parent, formal, output)
            self.assertEqual(code, 2)
            self.assert_failure_rows(payload, 8, "GIT_COMMAND_FAILURE")
            self.assertEqual(output.read_bytes(), b"preserve")

    def test_success_atomically_replaces_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, child_git, formal, output = self.fixture(Path(temp))
            output.write_bytes(b"old-authority-record")
            self.assertEqual(self.invoke(root, child_git, formal, output), 0)
            self.assertNotEqual(output.read_bytes(), b"old-authority-record")
            self.assertEqual(json.loads(output.read_bytes())["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
