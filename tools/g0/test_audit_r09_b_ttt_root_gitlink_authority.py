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

    def invoke(self, root: Path, child_git: Path, formal: str, output: Path) -> int:
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

    def invoke_payload(
        self, root: Path, child_git: Path, formal: str, output: Path
    ) -> tuple[int, dict[str, object]]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = self.invoke(root, child_git, formal, output)
        return code, json.loads(stdout.getvalue())

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


if __name__ == "__main__":
    unittest.main()
