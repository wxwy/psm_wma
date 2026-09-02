"""CPU-only regression tests for the non-executing P4-v4 entry foundation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.g0 import r09_b2_p4_v4_execution_preflight
from tools.g0.r09_b2_p4_v4_execution_preflight import main


class EntryFoundationTest(unittest.TestCase):
    def setUp(self):
        self._source_validation = mock.patch.object(
            r09_b2_p4_v4_execution_preflight, "validate_source"
        )
        self._interpreter_validation = mock.patch.object(
            r09_b2_p4_v4_execution_preflight, "validate_interpreter"
        )
        self._host_git_validation = mock.patch.object(
            r09_b2_p4_v4_execution_preflight, "validate_host_git", return_value=Path("/usr/bin/git")
        )
        self._source_validation.start()
        self._interpreter_validation.start()
        self._host_git_validation.start()

    def tearDown(self):
        self._source_validation.stop()
        self._interpreter_validation.stop()
        self._host_git_validation.stop()

    def _entry(self) -> dict[str, str]:
        entry = {"tool_path": "tools/g0/r09_b2_p4_v4_execution_preflight.py",
                 "root_revision": "a" * 40, "git_blob_sha256": "b" * 64,
                 "current_sha256": "c" * 64}
        entry["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(entry)
        return entry

    def _request(self) -> bytes:
        return (json.dumps({"schema_version": "r09_b2_p4_v4_execution_request_v1",
                            "entry": self._entry(),
                            **{key: {} for key in ("source", "interpreter", "environment", "run", "candidates", "backends", "authorities")},
                            "execution_contract": {"network": False, "gpu": False, "torch": False,
                                                   "model_data_checkpoint_io": False, "one_shot": True,
                                                   "cleanup_retry_repair": False}},
                           sort_keys=True, separators=(",", ":")) + "\n").encode()

    def test_requires_matching_regular_request_and_never_executes(self):
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            request.write_bytes(self._request())
            digest = hashlib.sha256(request.read_bytes()).hexdigest()
            with self.assertRaisesRegex(RuntimeError, "separately reviewed"):
                main(["--request", str(request), "--request-sha256", digest])
            with self.assertRaises(ValueError):
                main(["--request", str(request), "--request-sha256", "0" * 64])

    def test_rejects_unknown_execution_request_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            value = json.loads(self._request())
            value["ambient"] = {}
            request.write_bytes((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
            with self.assertRaisesRegex(ValueError, "schema differs"):
                main(["--request", str(request), "--request-sha256", hashlib.sha256(request.read_bytes()).hexdigest()])

    def test_sha_bound_bytes_are_not_reopened_by_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            raw = self._request()
            request.write_bytes(raw)
            with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("path re-read")), \
                 mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "open", wraps=os.open) as open_request:
                with self.assertRaisesRegex(RuntimeError, "separately reviewed"):
                    main(["--request", str(request), "--request-sha256", hashlib.sha256(raw).hexdigest()])
            self.assertEqual(open_request.call_count, 1)

    def test_execution_contract_is_not_exported_as_mutable_authority(self):
        self.assertFalse(hasattr(r09_b2_p4_v4_execution_preflight, "EXECUTION_CONTRACT"))
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            raw = self._request()
            request.write_bytes(raw)
            with mock.patch.object(r09_b2_p4_v4_execution_preflight, "_EXECUTION_CONTRACT_ITEMS", (("network", True),)):
                with self.assertRaisesRegex(RuntimeError, "separately reviewed"):
                    main(["--request", str(request), "--request-sha256", hashlib.sha256(raw).hexdigest()])

    def test_entry_rejects_noncanonical_identity_path_and_revision(self):
        cases = (
            ("identity_sha256", "0" * 64, "identity differs"),
            ("tool_path", "tools/g0/export_r09_b2_p5_resolved_config.py", "path differs"),
            ("root_revision", "a" * 64, "digest differs"),
            ("root_revision", "a" * 39, "digest differs"),
            ("root_revision", "a" * 41, "digest differs"),
            ("root_revision", "A" * 40, "digest differs"),
            ("root_revision", "g" * 40, "digest differs"),
        )
        for key, replacement, error in cases:
            with self.subTest(key=key, replacement=replacement):
                value = json.loads(self._request())
                value["entry"][key] = replacement
                raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
                with tempfile.TemporaryDirectory() as temporary:
                    request = Path(temporary) / "request.json"
                    request.write_bytes(raw)
                    with self.assertRaisesRegex(ValueError, error):
                        main(["--request", str(request), "--request-sha256", hashlib.sha256(raw).hexdigest()])

    def test_entry_rejects_extra_key(self):
        value = json.loads(self._request())
        value["entry"]["ambient"] = "x"
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            request.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "entry schema differs"):
                main(["--request", str(request), "--request-sha256", hashlib.sha256(raw).hexdigest()])


class SourceAuthorityTest(unittest.TestCase):
    def setUp(self):
        original = r09_b2_p4_v4_execution_preflight.validate_source
        git_path = Path(shutil.which("git") or "").resolve()
        self._source_validation = mock.patch.object(
            r09_b2_p4_v4_execution_preflight, "validate_source",
            side_effect=lambda source, entry: original(source, entry, git_path),
        )
        self._source_validation.start()

    def tearDown(self):
        self._source_validation.stop()

    def _git(self, root: Path, *args: str) -> str:
        return subprocess.check_output(("git", "-C", str(root), *args), text=True).strip()

    def _fixture(self, temporary: str) -> tuple[Path, dict[str, str], dict[str, str]]:
        root = Path(temporary) / "root"
        framework = Path(temporary) / "framework"
        framework.mkdir()
        self._git(framework, "init")
        self._git(framework, "config", "user.email", "test@example.invalid")
        self._git(framework, "config", "user.name", "Test")
        (framework / "module.txt").write_text("framework\n")
        self._git(framework, "add", ".")
        self._git(framework, "commit", "-m", "framework")
        root.mkdir()
        self._git(root, "init")
        self._git(root, "config", "user.email", "test@example.invalid")
        self._git(root, "config", "user.name", "Test")
        entry_path = root / "tools/g0/r09_b2_p4_v4_execution_preflight.py"
        entry_path.parent.mkdir(parents=True)
        entry_path.write_text("entry\n")
        (root / "tracked.txt").write_text("tracked\n")
        subprocess.run(("git", "-C", str(root), "-c", "protocol.file.allow=always", "submodule", "add", str(framework), "cosmos-framework"), check=True, stdout=subprocess.PIPE)
        self._git(root, "add", ".")
        self._git(root, "commit", "-m", "root")
        revision = self._git(root, "rev-parse", "HEAD")
        gitlink = self._git(framework, "rev-parse", "HEAD")
        digest = hashlib.sha256(entry_path.read_bytes()).hexdigest()
        entry = {"tool_path": "tools/g0/r09_b2_p4_v4_execution_preflight.py", "root_revision": revision,
                 "git_blob_sha256": digest, "current_sha256": digest}
        entry["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(entry)
        source = {"root": str(root), "root_revision": revision, "gitlink": gitlink,
                  "entry_git_blob_sha256": digest, "entry_current_sha256": digest}
        source["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(source)
        return root, source, entry

    def _identity(self, value: dict[str, str]) -> None:
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in value.items() if key != "identity_sha256"}
        )

    def _set_revision(self, root: Path, source: dict[str, str], entry: dict[str, str]) -> None:
        revision = self._git(root, "rev-parse", "HEAD")
        source["root_revision"] = revision
        entry["root_revision"] = revision
        self._identity(entry)
        self._identity(source)

    def test_source_accepts_exact_head_and_rejects_unrelated_descendant(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, entry = self._fixture(temporary)
            r09_b2_p4_v4_execution_preflight.validate_source(source, entry)
            (root / "unrelated.txt").write_text("descendant\n")
            self._git(root, "add", "unrelated.txt")
            self._git(root, "commit", "-m", "descendant")
            with self.assertRaisesRegex(ValueError, "checkout revision differs"):
                r09_b2_p4_v4_execution_preflight.validate_source(source, entry)

    def test_source_rejects_dirty_and_untracked_root(self):
        for name, path in (("dirty", "tracked.txt"), ("untracked", "untracked.txt")):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root, source, entry = self._fixture(temporary)
                (root / path).write_text(f"{name}\n")
                with self.assertRaisesRegex(ValueError, "not full-clean"):
                    r09_b2_p4_v4_execution_preflight.validate_source(source, entry)

    def test_source_rejects_gitlink_and_submodule_head_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, entry = self._fixture(temporary)
            source["gitlink"] = "a" * 40
            self._identity(source)
            with self.assertRaisesRegex(ValueError, "Gitlink differs"):
                r09_b2_p4_v4_execution_preflight.validate_source(source, entry)
        with tempfile.TemporaryDirectory() as temporary:
            root, source, entry = self._fixture(temporary)
            framework = root / "cosmos-framework"
            (framework / "module.txt").write_text("drift\n")
            self._git(framework, "add", "module.txt")
            self._git(framework, "commit", "-m", "submodule drift")
            with self.assertRaisesRegex(ValueError, "not full-clean"):
                r09_b2_p4_v4_execution_preflight.validate_source(source, entry)

    def test_source_rejects_entry_git_blob_current_and_cross_binding_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, entry = self._fixture(temporary)
            entry_path = root / "tools/g0/r09_b2_p4_v4_execution_preflight.py"
            entry_path.write_text("changed entry\n")
            self._git(root, "add", str(entry_path.relative_to(root)))
            self._git(root, "commit", "-m", "entry drift")
            self._set_revision(root, source, entry)
            with self.assertRaisesRegex(ValueError, "entry bytes differ"):
                r09_b2_p4_v4_execution_preflight.validate_source(source, entry)
        with tempfile.TemporaryDirectory() as temporary:
            root, source, entry = self._fixture(temporary)
            source["entry_current_sha256"] = "a" * 64
            self._identity(source)
            with self.assertRaisesRegex(ValueError, "cross-binding differs"):
                r09_b2_p4_v4_execution_preflight.validate_source(source, entry)

    def test_source_rejects_symlink_root_and_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, entry = self._fixture(temporary)
            linked_root = Path(temporary) / "linked-root"
            linked_root.symlink_to(root, target_is_directory=True)
            source["root"] = str(linked_root)
            self._identity(source)
            with self.assertRaisesRegex(ValueError, "source root differs"):
                r09_b2_p4_v4_execution_preflight.validate_source(source, entry)
        with tempfile.TemporaryDirectory() as temporary:
            root, source, entry = self._fixture(temporary)
            entry_path = root / "tools/g0/r09_b2_p4_v4_execution_preflight.py"
            target = root / "entry-target.py"
            target.write_text("entry\n")
            entry_path.unlink()
            entry_path.symlink_to(target.name)
            self._git(root, "add", "tools/g0/r09_b2_p4_v4_execution_preflight.py", "entry-target.py")
            self._git(root, "commit", "-m", "symlink entry")
            self._set_revision(root, source, entry)
            with self.assertRaisesRegex(ValueError, "entry path differs"):
                r09_b2_p4_v4_execution_preflight.validate_source(source, entry)

    def test_source_rejects_ancestor_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, entry = self._fixture(temporary)
            ancestor = self._git(root, "rev-parse", "HEAD")
            (root / "unrelated.txt").write_text("descendant\n")
            self._git(root, "add", "unrelated.txt")
            self._git(root, "commit", "-m", "descendant")
            self._set_revision(root, source, entry)
            self._git(root, "checkout", "--detach", ancestor)
            with self.assertRaisesRegex(ValueError, "checkout revision differs"):
                r09_b2_p4_v4_execution_preflight.validate_source(source, entry)

    def test_source_reads_entry_once_without_path_reopen(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, entry = self._fixture(temporary)
            with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("path re-read")), \
                 mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "open", wraps=os.open) as open_entry:
                r09_b2_p4_v4_execution_preflight.validate_source(source, entry)
            self.assertEqual(open_entry.call_count, 1)


class InterpreterAuthorityTest(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> str:
        return subprocess.check_output(("git", "-C", str(root), *args), text=True).strip()

    def _interpreter(self, temporary: str) -> tuple[dict[str, object], dict[str, object]]:
        root = Path(temporary) / "root"
        root.mkdir()
        self._git(root, "init")
        self._git(root, "config", "user.email", "test@example.invalid")
        self._git(root, "config", "user.name", "Test")
        bootstrap = root / "tools/g0/bootstrap.py"
        bootstrap.parent.mkdir(parents=True)
        bootstrap.write_text("pass\n")
        self._git(root, "add", ".")
        self._git(root, "commit", "-m", "bootstrap")
        child_request = Path(temporary) / "child.json"
        child_request.write_text("{}\n")
        launcher = Path(sys.executable).absolute()
        lexical = r09_b2_p4_v4_execution_preflight.lexical_interpreter(launcher)
        git_path = Path(shutil.which("git") or "").resolve()
        self.assertTrue(git_path.is_absolute())
        git_raw = r09_b2_p4_v4_execution_preflight._read_regular_nofollow(git_path, "git")
        host_git = {"path": str(git_path), "elf_sha256": hashlib.sha256(git_raw).hexdigest(),
                    "closure_sha256": r09_b2_p4_v4_execution_preflight._host_git_closure(git_path, git_raw)}
        bootstrap_sha = hashlib.sha256(bootstrap.read_bytes()).hexdigest()
        argv = r09_b2_p4_v4_execution_preflight.verified_loader_argv(
            lexical, child_request, hashlib.sha256(child_request.read_bytes()).hexdigest(), root,
            "tools/g0/bootstrap.py", bootstrap_sha, git_executable=git_path,
        )
        interpreter = {"lexical_interpreter": lexical, "host_git": host_git, "loader_argv": argv}
        interpreter["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(interpreter)
        return interpreter, {"root": str(root)}

    def _reidentity(self, value: dict[str, object]) -> None:
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in value.items() if key != "identity_sha256"}
        )

    def test_interpreter_reuses_frozen_lexical_loader_and_host_git_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            interpreter, source = self._interpreter(temporary)
            r09_b2_p4_v4_execution_preflight.validate_interpreter(interpreter, source)

    def test_interpreter_rejects_identity_loader_and_host_git_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            interpreter, source = self._interpreter(temporary)
            cases = []
            lexical = json.loads(json.dumps(interpreter))
            lexical["lexical_interpreter"]["sha256"] = "0" * 64
            cases.append((lexical, "identity differs"))
            argv = json.loads(json.dumps(interpreter))
            argv["loader_argv"] = argv["loader_argv"][:10]
            argv["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: value for key, value in argv.items() if key != "identity_sha256"}
            )
            cases.append((argv, "loader argv differs"))
            host = json.loads(json.dumps(interpreter))
            host["host_git"]["elf_sha256"] = "0" * 64
            host["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: value for key, value in host.items() if key != "identity_sha256"}
            )
            cases.append((host, "host Git identity differs"))
            for value, error in cases:
                with self.subTest(error=error):
                    with self.assertRaisesRegex(ValueError, error):
                        r09_b2_p4_v4_execution_preflight.validate_interpreter(value, source)

    def test_interpreter_rejects_lexical_closure_path_and_loader_mutations(self):
        with tempfile.TemporaryDirectory() as temporary:
            interpreter, source = self._interpreter(temporary)
            cases: list[tuple[dict[str, object], str]] = []
            lexical = json.loads(json.dumps(interpreter))
            lexical["lexical_interpreter"]["sha256"] = "0" * 64
            self._reidentity(lexical)
            cases.append((lexical, "lexical interpreter differs"))
            closure = json.loads(json.dumps(interpreter))
            closure["host_git"]["closure_sha256"] = "0" * 64
            self._reidentity(closure)
            cases.append((closure, "host Git identity differs"))
            relative = json.loads(json.dumps(interpreter))
            relative["host_git"]["path"] = "git"
            self._reidentity(relative)
            cases.append((relative, "host Git path differs"))
            reordered = json.loads(json.dumps(interpreter))
            reordered["loader_argv"][1], reordered["loader_argv"][2] = reordered["loader_argv"][2], reordered["loader_argv"][1]
            self._reidentity(reordered)
            cases.append((reordered, "loader argv differs"))
            for value, error in cases:
                with self.subTest(error=error):
                    with self.assertRaisesRegex(ValueError, error):
                        r09_b2_p4_v4_execution_preflight.validate_interpreter(value, source)

    def test_host_git_root_uses_one_open_and_no_path_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            interpreter, _ = self._interpreter(temporary)
            with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("path re-read")), \
                 mock.patch.object(r09_b2_p4_v4_execution_preflight, "_read_strict_regular_nofollow", wraps=r09_b2_p4_v4_execution_preflight._read_strict_regular_nofollow) as reader:
                r09_b2_p4_v4_execution_preflight.validate_host_git(interpreter["host_git"])
            self.assertEqual(reader.call_count, 1)

    def test_interpreter_rejects_every_bound_loader_slot_and_old_grammar(self):
        with tempfile.TemporaryDirectory() as temporary:
            interpreter, source = self._interpreter(temporary)
            mutations = (
                (5, "different frozen loader"), (7, "0" * 64), (8, "/tmp"),
                (9, "other/bootstrap.py"), (10, "0" * 64), (11, "/bin/true"),
            )
            for index, replacement in mutations:
                with self.subTest(index=index):
                    value = json.loads(json.dumps(interpreter))
                    value["loader_argv"][index] = replacement
                    self._reidentity(value)
                    with self.assertRaisesRegex(ValueError, "loader argv differs"):
                        r09_b2_p4_v4_execution_preflight.validate_interpreter(value, source)
            for argv in (interpreter["loader_argv"][:11], interpreter["loader_argv"] + ["extra"],
                         [interpreter["lexical_interpreter"]["path"], "-m", "x"],
                         [interpreter["lexical_interpreter"]["path"], "tools/g0/export_r09_b2_p5_resolved_config.py"]):
                value = json.loads(json.dumps(interpreter))
                value["loader_argv"] = argv
                self._reidentity(value)
                with self.assertRaisesRegex(ValueError, "loader argv differs"):
                    r09_b2_p4_v4_execution_preflight.validate_interpreter(value, source)

    def test_interpreter_rejects_realpath_host_symlink_and_path_shadow(self):
        with tempfile.TemporaryDirectory() as temporary:
            interpreter, source = self._interpreter(temporary)
            for key in ("realpath", "realpath_sha256"):
                value = json.loads(json.dumps(interpreter))
                value["lexical_interpreter"][key] = "/tmp/other" if key == "realpath" else "0" * 64
                self._reidentity(value)
                with self.assertRaisesRegex(ValueError, "lexical interpreter differs"):
                    r09_b2_p4_v4_execution_preflight.validate_interpreter(value, source)
            value = json.loads(json.dumps(interpreter))
            link = Path(temporary) / "git-link"
            link.symlink_to(value["host_git"]["path"])
            value["host_git"]["path"] = str(link)
            self._reidentity(value)
            with self.assertRaisesRegex(ValueError, "host Git path differs"):
                r09_b2_p4_v4_execution_preflight.validate_interpreter(value, source)
            shadow = Path(temporary) / "shadow"
            shadow.mkdir()
            (shadow / "git").write_text("#!/bin/sh\nexit 99\n")
            (shadow / "git").chmod(0o755)
            with mock.patch.dict(os.environ, {"PATH": f"{shadow}:{os.environ['PATH']}"}):
                r09_b2_p4_v4_execution_preflight.validate_interpreter(interpreter, source)


if __name__ == "__main__":
    unittest.main()
