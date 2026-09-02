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
from tools.g0.export_r09_b2_p5_resolved_config import PYTHON_CHILD_LOCALE, p5_effective_environment
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

    def _interpreter(self, temporary: str, *, launcher: Path | None = None) -> tuple[dict[str, object], dict[str, object]]:
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
        launcher = launcher or Path(sys.executable).absolute()
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

    def test_host_git_closure_reads_each_dependency_once_without_pathname_reopen(self):
        with tempfile.TemporaryDirectory() as temporary:
            interpreter, _ = self._interpreter(temporary)
            host_git = interpreter["host_git"]
            bound_raw = {Path(host_git["path"]): r09_b2_p4_v4_execution_preflight._read_regular_nofollow(
                Path(host_git["path"]), "git"
            )}
            original_reader = r09_b2_p4_v4_execution_preflight._read_canonical_regular_nofollow
            original_parser = r09_b2_p4_v4_execution_preflight.parse_elf_dynamic_raw

            def read_dependency(path: Path, error: str) -> tuple[Path, bytes]:
                canonical, raw = original_reader(path, error)
                bound_raw[canonical] = raw
                return canonical, raw

            def parse_bound(path: Path, raw: bytes) -> dict[str, object]:
                self.assertEqual(raw, bound_raw[path])
                return original_parser(path, raw)

            with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("path re-read")), \
                 mock.patch.object(r09_b2_p4_v4_execution_preflight, "_read_canonical_regular_nofollow", side_effect=read_dependency) as reader, \
                 mock.patch.object(r09_b2_p4_v4_execution_preflight, "parse_elf_dynamic_raw", side_effect=parse_bound):
                r09_b2_p4_v4_execution_preflight.validate_host_git(host_git)
            dependency_paths = [Path(call.args[0]).resolve() for call in reader.call_args_list]
            self.assertGreater(len(dependency_paths), 0)
            self.assertEqual(len(dependency_paths), len(set(dependency_paths)))

    def test_interpreter_rejects_retargeted_lexical_launcher(self):
        with tempfile.TemporaryDirectory() as temporary:
            launcher_dir = Path(temporary) / "venv"
            launcher_dir.mkdir()
            base_a, base_b = launcher_dir / "base-A", launcher_dir / "base-B"
            shutil.copyfile(sys.executable, base_a)
            shutil.copyfile(sys.executable, base_b)
            launcher = launcher_dir / "venv-python"
            launcher.symlink_to(base_a.name)
            interpreter, source = self._interpreter(temporary, launcher=launcher)
            launcher.unlink()
            launcher.symlink_to(base_b.name)
            with self.assertRaisesRegex(ValueError, "lexical interpreter differs"):
                r09_b2_p4_v4_execution_preflight.validate_interpreter(interpreter, source)

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


class EnvironmentAuthorityTest(unittest.TestCase):
    def _records(self):
        values = {key: "x" for key in r09_b2_p4_v4_execution_preflight.REQUIRED_ENV}
        values.update({"PYTHONPATH": "/framework", "IMAGINAIRE_OUTPUT_ROOT": "/output/recurrent", "PSM_R09_B1_TTT_ENABLED": "0"})
        recurrent = {"backend": "recurrent", "environment": {"set": values}, "d005_sha256": "a" * 64}
        ttt_values = dict(values); ttt_values["IMAGINAIRE_OUTPUT_ROOT"] = "/output/ttt"; ttt_values["PSM_R09_B1_TTT_ENABLED"] = "1"
        return recurrent, {"backend": "ttt_fast_weight", "environment": {"set": ttt_values}, "d005_sha256": "b" * 64}

    def _section(self, record, backend):
        projected, projection = r09_b2_p4_v4_execution_preflight._project_d005_environment(record, backend)
        effective_core = {"set": projected, "unset": list(r09_b2_p4_v4_execution_preflight.P5_FORBIDDEN_ENVIRONMENT), "inherit_allowlist": []}
        native_core = {"set": {}, "unset": list(r09_b2_p4_v4_execution_preflight.P5_FORBIDDEN_ENVIRONMENT), "inherit_allowlist": []}
        effective = {**effective_core, "sha256": r09_b2_p4_v4_execution_preflight.canonical_sha256(effective_core)}
        native = {**native_core, "sha256": r09_b2_p4_v4_execution_preflight.canonical_sha256(native_core)}
        value = {"effective_environment": effective, "native_loader_environment": native, "d005_projection": projection}
        return {**value, "identity_sha256": r09_b2_p4_v4_execution_preflight.canonical_sha256(value)}

    def _pair(self):
        recurrent, ttt = self._records()
        return {"recurrent": self._section(recurrent, "recurrent"), "ttt_fast_weight": self._section(ttt, "ttt_fast_weight")}, recurrent, ttt

    def _reidentity(self, section):
        for name in ("effective_environment", "native_loader_environment"):
            section[name]["sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: item for key, item in section[name].items() if key != "sha256"}
            )
        projection = section["d005_projection"]
        if set(projection) == r09_b2_p4_v4_execution_preflight.D005_PROJECTION_KEYS:
            projection["sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: item for key, item in projection.items() if key != "sha256"}
            )
        section["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in section.items() if key != "identity_sha256"}
        )

    def _section_identity(self, section):
        section["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in section.items() if key != "identity_sha256"}
        )

    def _assert_rejected(self, value, recurrent, ttt, error):
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "verify_d005_pair", return_value={"status": "PASS"}):
            with self.assertRaisesRegex(ValueError, error):
                r09_b2_p4_v4_execution_preflight.validate_environment_pair(value, recurrent, ttt, Path("/unused"))

    def test_environment_requires_verified_d005_projection_and_p3_only_difference(self):
        value, recurrent, ttt = self._pair()
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "verify_d005_pair", return_value={"status": "PASS"}):
            r09_b2_p4_v4_execution_preflight.validate_environment_pair(value, recurrent, ttt, Path("/unused"))

    def test_environment_rejects_unverified_d005_and_projection_drift(self):
        value, recurrent, ttt = self._pair()
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "verify_d005_pair", return_value={"status": "FAIL"}):
            with self.assertRaisesRegex(ValueError, "not verified"):
                r09_b2_p4_v4_execution_preflight.validate_environment_pair(value, recurrent, ttt, Path("/unused"))
        value["recurrent"]["effective_environment"]["set"]["UNREVIEWED_ENV"] = "x"
        value["recurrent"]["effective_environment"]["sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in value["recurrent"]["effective_environment"].items() if key != "sha256"})
        value["recurrent"]["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in value["recurrent"].items() if key != "identity_sha256"})
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "verify_d005_pair", return_value={"status": "PASS"}):
            with self.assertRaisesRegex(ValueError, "projection differs"):
                r09_b2_p4_v4_execution_preflight.validate_environment_pair(value, recurrent, ttt, Path("/unused"))

    def test_environment_rejects_projection_schema_and_digest_drift(self):
        for key, replacement in (("ambient", "x"), ("d005_sha256", "not-a-sha256")):
            with self.subTest(key=key):
                value, recurrent, ttt = self._pair()
                value["recurrent"]["d005_projection"][key] = replacement
                value["recurrent"]["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                    {name: item for name, item in value["recurrent"].items() if name != "identity_sha256"}
                )
                with mock.patch.object(r09_b2_p4_v4_execution_preflight, "verify_d005_pair", return_value={"status": "PASS"}):
                    with self.assertRaisesRegex(ValueError, "projection differs"):
                        r09_b2_p4_v4_execution_preflight.validate_environment_pair(value, recurrent, ttt, Path("/unused"))

    def test_environment_rejects_identity_and_p5_grammar_drift(self):
        mutations = (
            ("effective digest", lambda value: value["recurrent"]["effective_environment"].__setitem__("sha256", "0" * 64), "object identity"),
            ("native digest", lambda value: value["recurrent"]["native_loader_environment"].__setitem__("sha256", "0" * 64), "object identity"),
            ("projection digest", lambda value: value["recurrent"]["d005_projection"].__setitem__("sha256", "0" * 64), "projection differs"),
            ("section digest", lambda value: value["recurrent"].__setitem__("identity_sha256", "0" * 64), "environment identity"),
            ("missing forbidden", lambda value: value["recurrent"]["effective_environment"].__setitem__("unset", []), "object identity"),
            ("reordered forbidden", lambda value: value["recurrent"]["effective_environment"].__setitem__("unset", list(reversed(r09_b2_p4_v4_execution_preflight.P5_FORBIDDEN_ENVIRONMENT))), "object identity"),
            ("inherit", lambda value: value["recurrent"]["effective_environment"].__setitem__("inherit_allowlist", ["PATH"]), "object identity"),
            ("native set", lambda value: value["recurrent"]["native_loader_environment"].__setitem__("set", {"PATH": "/bin"}), "native loader environment"),
            ("forbidden effective", lambda value: value["recurrent"]["effective_environment"]["set"].__setitem__(r09_b2_p4_v4_execution_preflight.P5_FORBIDDEN_ENVIRONMENT[0], "x"), "forbidden key"),
        )
        for name, mutate, error in mutations:
            with self.subTest(name=name):
                value, recurrent, ttt = self._pair()
                mutate(value)
                if name in {"effective digest", "native digest", "projection digest"}:
                    self._section_identity(value["recurrent"])
                elif name != "section digest":
                    self._reidentity(value["recurrent"])
                self._assert_rejected(value, recurrent, ttt, error)

    def test_environment_rejects_d005_source_projection_and_pair_drift(self):
        mutations = (
            ("added D005 key", lambda recurrent, ttt: recurrent["environment"]["set"].__setitem__("AMBIENT", "x"), "D005 environment"),
            ("removed D005 key", lambda recurrent, ttt: recurrent["environment"]["set"].pop(next(iter(r09_b2_p4_v4_execution_preflight.REQUIRED_ENV))), "D005 environment"),
            ("changed D005 projected value", lambda recurrent, ttt: recurrent["environment"]["set"].__setitem__("HF_HUB_OFFLINE", "changed"), "projection differs"),
            ("wrong backend", lambda recurrent, ttt: recurrent.__setitem__("backend", "ttt_fast_weight"), "D005 environment"),
            ("well formed D005 digest", lambda recurrent, ttt: recurrent.__setitem__("d005_sha256", "c" * 64), "projection differs"),
            ("wrong input digest", lambda recurrent, ttt: value["recurrent"]["d005_projection"].__setitem__("input_set_sha256", "c" * 64), "projection differs"),
            ("wrong projected digest", lambda recurrent, ttt: value["recurrent"]["d005_projection"].__setitem__("projected_set_sha256", "c" * 64), "projection differs"),
            ("reordered exclusions", lambda recurrent, ttt: value["recurrent"]["d005_projection"].__setitem__("excluded_keys", list(reversed(r09_b2_p4_v4_execution_preflight.D005_EXCLUDED_ENVIRONMENT_KEYS))), "projection differs"),
        )
        for name, mutate, error in mutations:
            with self.subTest(name=name):
                value, recurrent, ttt = self._pair()
                mutate(recurrent, ttt)
                self._reidentity(value["recurrent"])
                self._assert_rejected(value, recurrent, ttt, error)

    def test_environment_rejects_excluded_key_pair_and_locale_drift(self):
        mutations = (
            ("PYTHONPATH leak", lambda value: value["recurrent"]["effective_environment"]["set"].__setitem__("PYTHONPATH", "/framework"), "forbidden key"),
            ("output leak", lambda value: value["recurrent"]["effective_environment"]["set"].__setitem__("IMAGINAIRE_OUTPUT_ROOT", "/output/recurrent"), "projection differs"),
            ("missing P3 key", lambda value: value["recurrent"]["effective_environment"]["set"].pop("PSM_R09_B1_TTT_ENABLED"), "projection differs"),
            ("reversed P3", lambda value: value["recurrent"]["effective_environment"]["set"].__setitem__("PSM_R09_B1_TTT_ENABLED", "1"), "projection differs"),
            ("third difference", lambda value: value["ttt_fast_weight"]["effective_environment"]["set"].__setitem__("CUDA_DEVICE_MAX_CONNECTIONS", "other"), "projection differs"),
            ("locale request", lambda value: value["recurrent"]["effective_environment"]["set"].__setitem__("LC_CTYPE", "C.UTF-8"), "projection differs"),
        )
        for name, mutate, error in mutations:
            with self.subTest(name=name):
                value, recurrent, ttt = self._pair()
                mutate(value)
                self._reidentity(value["recurrent"])
                self._reidentity(value["ttt_fast_weight"])
                self._assert_rejected(value, recurrent, ttt, error)

    def test_environment_rejects_third_backend_roster(self):
        value, recurrent, ttt = self._pair()
        value["unexpected"] = value["recurrent"]
        self._assert_rejected(value, recurrent, ttt, "environment pair schema")

    def test_environment_leaves_locale_to_p5_projection(self):
        value, recurrent, ttt = self._pair()
        self.assertNotIn("LC_CTYPE", value["recurrent"]["effective_environment"]["set"])
        self.assertNotIn("LC_CTYPE", value["ttt_fast_weight"]["effective_environment"]["set"])
        with mock.patch.dict(os.environ, {"PYTHONPATH": "/ambient", "LC_CTYPE": "bad"}, clear=True), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "verify_d005_pair", return_value={"status": "PASS"}):
            r09_b2_p4_v4_execution_preflight.validate_environment_pair(value, recurrent, ttt, Path("/unused"))
            effective = p5_effective_environment(value["recurrent"], value["ttt_fast_weight"], backend="recurrent")
        self.assertEqual(effective, {**dict(sorted(value["recurrent"]["effective_environment"]["set"].items())), **PYTHON_CHILD_LOCALE})
        self.assertEqual(effective["LC_CTYPE"], "C.UTF-8")

    def test_environment_is_independent_of_ambient_parent(self):
        value, recurrent, ttt = self._pair()
        frozen = json.loads(json.dumps(value))
        with mock.patch.dict(os.environ, {"PYTHONPATH": "/ambient", "PATH": "/ambient", "LC_CTYPE": "bad"}, clear=True), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "verify_d005_pair", return_value={"status": "PASS"}):
            r09_b2_p4_v4_execution_preflight.validate_environment_pair(value, recurrent, ttt, Path("/unused"))
        self.assertEqual(value, frozen)


class AuthoritiesAuthorityTest(unittest.TestCase):
    def _reidentity(self, value):
        value["d005_pair"]["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in value["d005_pair"].items() if key != "identity_sha256"}
        )
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({"d005_pair": value["d005_pair"]})
    def _authorities(self):
        pair = {"model": "historical_d005_v2"}
        for name in ("recurrent", "ttt_fast_weight", "verification"):
            pair[name] = r09_b2_p4_v4_execution_preflight._historical_binding(name)
        pair["historical_source"] = r09_b2_p4_v4_execution_preflight._historical_source()
        pair["historical_verifier"] = r09_b2_p4_v4_execution_preflight._historical_verifier()
        pair["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(pair)
        value = {"d005_pair": pair}
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(value)
        return value

    def _request(self):
        root = Path(__file__).resolve().parents[2]
        records = {}
        for backend in ("recurrent", "ttt_fast_weight"):
            path, _ = r09_b2_p4_v4_execution_preflight._HISTORICAL_ARTIFACTS[backend]
            records[backend] = json.loads((root / path).read_bytes())
        environment = {}
        for backend, record in records.items():
            projected, projection = r09_b2_p4_v4_execution_preflight._project_d005_environment(record, backend)
            effective_core = {"set": projected, "unset": list(r09_b2_p4_v4_execution_preflight.P5_FORBIDDEN_ENVIRONMENT), "inherit_allowlist": []}
            native_core = {"set": {}, "unset": list(r09_b2_p4_v4_execution_preflight.P5_FORBIDDEN_ENVIRONMENT), "inherit_allowlist": []}
            section = {"effective_environment": {**effective_core, "sha256": r09_b2_p4_v4_execution_preflight.canonical_sha256(effective_core)}, "native_loader_environment": {**native_core, "sha256": r09_b2_p4_v4_execution_preflight.canonical_sha256(native_core)}, "d005_projection": projection}
            environment[backend] = {**section, "identity_sha256": r09_b2_p4_v4_execution_preflight.canonical_sha256(section)}
        git = Path(shutil.which("git") or "").resolve()
        return root, {"environment": environment, "interpreter": {"host_git": {"path": str(git)}}}, git

    def test_authorities_bind_historical_bytes_verifier_and_environment(self):
        root, request, git = self._request()
        r09_b2_p4_v4_execution_preflight.validate_authorities_pair(self._authorities(), request, root, git)

    def test_authorities_reject_identity_binding_and_verification_drift(self):
        root, request, git = self._request()
        for mutate, error in (
            (lambda value: value["d005_pair"]["recurrent"].__setitem__("sha256", "0" * 64), "binding differs"),
            (lambda value: value.__setitem__("identity_sha256", "0" * 64), "authorities identity"),
        ):
            with self.subTest(error=error):
                value = self._authorities()
                mutate(value)
                if error == "binding differs":
                    value["d005_pair"]["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                        {key: item for key, item in value["d005_pair"].items() if key != "identity_sha256"}
                    )
                    value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({"d005_pair": value["d005_pair"]})
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_authorities_pair(value, request, root, git)

    def test_authorities_reject_historical_verification_nested_roster_drift(self):
        root, _, _ = self._request()
        raw = (root / r09_b2_p4_v4_execution_preflight._HISTORICAL_ARTIFACTS["verification"][0]).read_bytes()
        original = json.loads(raw)
        mutations = (
            lambda value: value.__setitem__("extra", True),
            lambda value: value["checks"].__setitem__("extra", True),
            lambda value: value["checks"].__setitem__("distinct_outputs", False),
            lambda value: value["checks"]["matched"].__setitem__("budget", "true"),
            lambda value: value["checks"]["recurrent"].pop("argv"),
            lambda value: value["checks"]["ttt_fast_weight"].__setitem__("argv", 1),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                value = json.loads(json.dumps(original)); mutate(value)
                r09_b2_p4_v4_execution_preflight._validate_historical_verification(value)

    def test_authorities_reject_historical_artifact_lexical_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); target = root / "target.json"; target.write_text("{}\n")
            link = root / "artifact.json"; link.symlink_to(target.name)
            expected = {"relative_path": "artifact.json", "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
            with self.assertRaisesRegex(ValueError, "path differs"):
                r09_b2_p4_v4_execution_preflight._read_historical_artifact(root, expected, expected, "test")

    def test_authorities_reject_historical_artifact_directory_and_reads_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); directory = root / "artifact"; directory.mkdir()
            expected = {"relative_path": "artifact", "sha256": "0" * 64}
            with self.assertRaisesRegex(ValueError, "path differs"):
                r09_b2_p4_v4_execution_preflight._read_historical_artifact(root, expected, expected, "test")

    def test_authorities_reject_source_host_git_and_verifier_blob_drift(self):
        root, request, git = self._request()
        value = self._authorities()
        value["d005_pair"]["historical_source"]["root_revision"] = "0" * 40
        value["d005_pair"]["historical_source"]["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in value["d005_pair"]["historical_source"].items() if key != "identity_sha256"}
        )
        self._reidentity(value)
        with self.assertRaisesRegex(ValueError, "historical source differs"):
            r09_b2_p4_v4_execution_preflight.validate_authorities_pair(value, request, root, git)
        with self.assertRaisesRegex(ValueError, "historical host Git differs"):
            r09_b2_p4_v4_execution_preflight.validate_authorities_pair(self._authorities(), request, root, Path("/bin/true"))
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "_git", return_value=b"bad"):
            with self.assertRaisesRegex(ValueError, "historical verifier bytes differ"):
                r09_b2_p4_v4_execution_preflight.validate_authorities_pair(self._authorities(), request, root, git)

    def test_authorities_reject_environment_cross_binding_drift(self):
        root, request, git = self._request()
        request["environment"]["recurrent"]["effective_environment"]["set"]["HF_HUB_OFFLINE"] = "0"
        section = request["environment"]["recurrent"]
        section["effective_environment"]["sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in section["effective_environment"].items() if key != "sha256"})
        section["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in section.items() if key != "identity_sha256"})
        with self.assertRaisesRegex(ValueError, "projection differs"):
            r09_b2_p4_v4_execution_preflight.validate_authorities_pair(self._authorities(), request, root, git)

    def test_authorities_reject_historical_record_field_drift(self):
        root, request, git = self._request()
        records = {}
        for backend in ("recurrent", "ttt_fast_weight"):
            path, _ = r09_b2_p4_v4_execution_preflight._HISTORICAL_ARTIFACTS[backend]
            records[backend] = json.loads((root / path).read_bytes())
        verification = json.loads((root / r09_b2_p4_v4_execution_preflight._HISTORICAL_ARTIFACTS["verification"][0]).read_bytes())
        verifier = r09_b2_p4_v4_execution_preflight._git(root, "show", f"{r09_b2_p4_v4_execution_preflight._HISTORICAL_REVISION}:{r09_b2_p4_v4_execution_preflight._HISTORICAL_VERIFIER[0]}", git_executable=git)
        mutations = (
            lambda record: record.__setitem__("backend", "wrong"),
            lambda record: record.__setitem__("schema_version", "wrong"),
            lambda record: record.__setitem__("status", "PASS"),
            lambda record: record["source"].__setitem__("root_revision", "0" * 40),
            lambda record: record.__setitem__("d005_sha256", "0" * 64),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                rows = json.loads(json.dumps(records)); mutate(rows["recurrent"])
                def fake_read(_, __, ___, name):
                    item = verification if name == "verification" else rows[name]
                    return (json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n").encode(), item
                with mock.patch.object(r09_b2_p4_v4_execution_preflight, "_read_historical_artifact", side_effect=fake_read), \
                     mock.patch.object(r09_b2_p4_v4_execution_preflight, "_git", return_value=verifier):
                    with self.assertRaisesRegex(ValueError, "historical record differs"):
                        r09_b2_p4_v4_execution_preflight.validate_authorities_pair(self._authorities(), request, root, git)


if __name__ == "__main__":
    unittest.main()
