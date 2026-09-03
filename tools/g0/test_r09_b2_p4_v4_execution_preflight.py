"""CPU-only regression tests for the non-executing P4-v4 entry foundation."""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from tools.g0 import r09_b2_p4_v4_execution_preflight
from tools.g0.export_r09_b2_p5_resolved_config import PYTHON_CHILD_LOCALE, p5_effective_environment
from tools.g0.r09_b2_p4_v4_execution_preflight import main


class MaterializationReservationTest(unittest.TestCase):
    def _admitted(self, namespace: Path):
        composition = FullAdmissionCompositionTest()
        value, git = composition._request()
        for backend in ("recurrent", "ttt_fast_weight"):
            identity = value["run"][backend]["identity"]
            root = namespace / backend
            identity.update({"root": str(root), "resolved_root": str(root)})
            composition._reidentity(identity)
            value["candidates"][backend]["run"] = value["run"][backend]
        CandidatesAuthorityTest()._reidentity(value["candidates"])
        return composition._load(value, git, admit=True)

    def test_reservation_creates_exact_ordered_six_path_footprint_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            namespace = Path(temporary); admitted = self._admitted(namespace)
            result = r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
            self.assertEqual(result.status, "RESERVED")
            self.assertEqual([path.relative_to(namespace).as_posix() for path in result.created_paths], [
                "recurrent", "recurrent/import_staging", "recurrent/import_staging/" + "a" * 64,
                "ttt_fast_weight", "ttt_fast_weight/import_staging", "ttt_fast_weight/import_staging/" + "c" * 64,
            ])
            with self.assertRaisesRegex(ValueError, "consumed"):
                r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)

    def test_capability_constructor_and_bare_instance_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            namespace = Path(temporary)
            with self.assertRaisesRegex(TypeError, "factory-only"):
                r09_b2_p4_v4_execution_preflight._AdmittedRequest()
            forged = object.__new__(r09_b2_p4_v4_execution_preflight._AdmittedRequest)
            with self.assertRaisesRegex(ValueError, "requires an admitted request"):
                r09_b2_p4_v4_execution_preflight._reserve_staging(forged, namespace)
            self.assertFalse(hasattr(r09_b2_p4_v4_execution_preflight, "_issued_admitted_request"))
            with self.assertRaisesRegex(ValueError, "schema differs"):
                r09_b2_p4_v4_execution_preflight._admit_execution_request(b"{}\n")

    def test_hidden_authority_rejects_object_setattr_forgery(self):
        with tempfile.TemporaryDirectory() as temporary:
            namespace = Path(temporary)
            forged = object.__new__(r09_b2_p4_v4_execution_preflight._AdmittedRequest)
            raw = b"{}\n"; digest = hashlib.sha256(raw).hexdigest()
            for name, value in (("raw", raw), ("request_sha256", digest), ("_consumed", False), ("_locked", True)):
                object.__setattr__(forged, name, value)
            with self.assertRaisesRegex(ValueError, "requires an admitted request"):
                r09_b2_p4_v4_execution_preflight._reserve_staging(forged, namespace)

    def test_capability_fields_reject_ordinary_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            admitted = self._admitted(Path(temporary))
            with self.assertRaises(AttributeError):
                admitted.raw = b"{}\n"
            with self.assertRaises(AttributeError):
                admitted._consumed = False

    def test_hidden_authority_ignores_object_setattr_and_remains_consumed(self):
        with tempfile.TemporaryDirectory() as temporary:
            namespace = Path(temporary); admitted = self._admitted(namespace)
            object.__setattr__(admitted, "raw", b"{}\n")
            object.__setattr__(admitted, "request_sha256", "0" * 64)
            object.__setattr__(admitted, "_consumed", False)
            result = r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
            self.assertEqual(result.status, "RESERVED")
            object.__setattr__(admitted, "_consumed", False)
            with self.assertRaisesRegex(ValueError, "consumed"):
                r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)

    def test_existing_direct_child_rejects_before_any_mkdir(self):
        with tempfile.TemporaryDirectory() as temporary:
            namespace = Path(temporary); (namespace / "recurrent").mkdir()
            admitted = self._admitted(namespace)
            with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "mkdir", side_effect=AssertionError("mutation")):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)

    def test_second_direct_child_rejects_before_any_mkdir(self):
        with tempfile.TemporaryDirectory() as temporary:
            namespace = Path(temporary); (namespace / "ttt_fast_weight").mkdir()
            admitted = self._admitted(namespace)
            with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "mkdir", side_effect=AssertionError("mutation")):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
            self.assertFalse((namespace / "recurrent").exists())

    def test_symlink_namespace_rejects_before_any_mkdir(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); target = root / "target"; target.mkdir(); namespace = root / "namespace"; namespace.mkdir()
            admitted = self._admitted(namespace)
            moved = root / "moved"; namespace.rename(moved); namespace.symlink_to(target, target_is_directory=True)
            with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "mkdir", side_effect=AssertionError("mutation")):
                with self.assertRaisesRegex(ValueError, "namespace differs"):
                    r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)

    def test_mkdir_and_stat_failure_preserve_distinct_poison_prefixes(self):
        with tempfile.TemporaryDirectory() as temporary:
            namespace = Path(temporary); admitted = self._admitted(namespace)
            with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "mkdir", side_effect=OSError("mkdir")):
                with self.assertRaises(r09_b2_p4_v4_execution_preflight.ReservationPoisonedError) as failure:
                    r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
            self.assertEqual(failure.exception.created_paths, ())
        with tempfile.TemporaryDirectory() as temporary:
            namespace = Path(temporary); admitted = self._admitted(namespace)
            with mock.patch.object(r09_b2_p4_v4_execution_preflight, "_open_created_directory", side_effect=OSError("stat")):
                with self.assertRaises(r09_b2_p4_v4_execution_preflight.ReservationPoisonedError) as failure:
                    r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
            self.assertEqual(len(failure.exception.created_paths), 1)

    def test_all_six_mkdir_and_verification_faults_preserve_exact_prefixes(self):
        for fault_index in range(6):
            with self.subTest(kind="mkdir", fault_index=fault_index), tempfile.TemporaryDirectory() as temporary:
                namespace = Path(temporary); admitted = self._admitted(namespace)
                real_mkdir = os.mkdir; calls = 0
                def fail_mkdir(name, *args, **kwargs):
                    nonlocal calls
                    if calls == fault_index:
                        calls += 1; raise OSError("mkdir")
                    calls += 1; return real_mkdir(name, *args, **kwargs)
                with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "mkdir", side_effect=fail_mkdir):
                    with self.assertRaises(r09_b2_p4_v4_execution_preflight.ReservationPoisonedError) as failure:
                        r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
                self.assertEqual(len(failure.exception.created_paths), fault_index)
            with self.subTest(kind="verify", fault_index=fault_index), tempfile.TemporaryDirectory() as temporary:
                namespace = Path(temporary); admitted = self._admitted(namespace)
                real_open = r09_b2_p4_v4_execution_preflight._open_created_directory; calls = 0
                def fail_verify(name, parent_fd):
                    nonlocal calls
                    if calls == fault_index:
                        calls += 1; raise OSError("verify")
                    calls += 1; return real_open(name, parent_fd)
                with mock.patch.object(r09_b2_p4_v4_execution_preflight, "_open_created_directory", side_effect=fail_verify):
                    with self.assertRaises(r09_b2_p4_v4_execution_preflight.ReservationPoisonedError) as failure:
                        r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
                self.assertEqual(len(failure.exception.created_paths), fault_index + 1)

    def test_component_acquisition_retarget_keeps_external_target_unwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); parent = base / "parent"; namespace = parent / "namespace"
            parent.mkdir(); namespace.mkdir(); external = base / "external"; external.mkdir()
            admitted = self._admitted(namespace); moved = base / "moved"; real_open = os.open; swapped = False

            def retarget_open(name, flags, *args, **kwargs):
                nonlocal swapped
                descriptor = real_open(name, flags, *args, **kwargs)
                if name == "parent" and not swapped and "dir_fd" in kwargs:
                    swapped = True; parent.rename(moved); parent.symlink_to(external, target_is_directory=True)
                return descriptor

            with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "open", side_effect=retarget_open):
                r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
            self.assertTrue((moved / "namespace" / "recurrent").is_dir())
            self.assertEqual(list(external.iterdir()), [])

    def test_post_anchor_retarget_keeps_external_target_unwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); namespace = base / "namespace"; namespace.mkdir(); external = base / "external"; external.mkdir()
            admitted = self._admitted(namespace); moved = base / "moved"
            original_anchor = r09_b2_p4_v4_execution_preflight._open_namespace_anchor

            def retarget_after_anchor(path):
                descriptor = original_anchor(path)
                namespace.rename(moved); namespace.symlink_to(external, target_is_directory=True)
                return descriptor

            with mock.patch.object(r09_b2_p4_v4_execution_preflight, "_open_namespace_anchor", side_effect=retarget_after_anchor):
                r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
            self.assertTrue((moved / "recurrent").is_dir())
            self.assertEqual(list(external.iterdir()), [])

    def test_reservation_never_uses_ambient_subprocess_p5_or_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            namespace = Path(temporary); admitted = self._admitted(namespace)
            with mock.patch.dict(os.environ, {"PATH": "/hostile", "PYTHONPATH": "/hostile"}, clear=True), \
                 mock.patch.object(r09_b2_p4_v4_execution_preflight.subprocess, "run", side_effect=AssertionError("subprocess")), \
                 mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "execve", side_effect=AssertionError("child")):
                result = r09_b2_p4_v4_execution_preflight._reserve_staging(admitted, namespace)
            self.assertEqual(result.status, "RESERVED")
        helper_source = inspect.getsource(r09_b2_p4_v4_execution_preflight._reserve_staging)
        self.assertNotIn("subprocess", helper_source)
        self.assertNotIn("p5", helper_source.lower())
        self.assertNotIn("exec", helper_source)


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
        self._authorities_validation = mock.patch.object(
            r09_b2_p4_v4_execution_preflight, "validate_authorities_pair"
        )
        self.source_validation = self._source_validation.start()
        self.interpreter_validation = self._interpreter_validation.start()
        self.host_git_validation = self._host_git_validation.start()
        self.authorities_validation = self._authorities_validation.start()

    def tearDown(self):
        self._source_validation.stop()
        self._interpreter_validation.stop()
        self._host_git_validation.stop()
        self._authorities_validation.stop()

    def _entry(self) -> dict[str, str]:
        entry = {"tool_path": "tools/g0/r09_b2_p4_v4_execution_preflight.py",
                 "root_revision": "a" * 40, "git_blob_sha256": "b" * 64,
                 "current_sha256": "c" * 64}
        entry["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(entry)
        return entry

    def _run_item(self, backend: str) -> dict[str, object]:
        root = f"/future/{backend}"
        identity = {"root": root, "resolved_root": root, "kind": "run_root"}
        identity["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(identity)
        return {"identity": identity, "run_token": ("a" if backend == "recurrent" else "b") * 64,
                "roster_sha256": ("c" if backend == "recurrent" else "d") * 64}

    def _run(self) -> dict[str, object]:
        return {backend: self._run_item(backend) for backend in ("recurrent", "ttt_fast_weight")}

    def _candidates(self, run: dict[str, object]) -> dict[str, object]:
        root = {"root": "/candidates", "resolved_root": "/candidates", "kind": "candidate_root"}
        root["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(root)
        value = {"root": root, "attempt_id": "e" * 64}
        for backend in ("recurrent", "ttt_fast_weight"):
            item = {"backend": backend, "candidate_root": f"/candidates/{value['attempt_id']}/{backend}", "run": run[backend]}
            item["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(item)
            value[backend] = item
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(value)
        return value

    def _backends(self) -> dict[str, object]:
        return BackendsAuthorityTest()._value()

    def _request(self) -> bytes:
        run = self._run()
        return (json.dumps({"schema_version": "r09_b2_p4_v4_execution_request_v1",
                            "entry": self._entry(),
                            **{key: {} for key in ("interpreter", "environment", "authorities")},
                            "source": {"root": "/source"},
                            "run": run, "candidates": self._candidates(run), "backends": self._backends(),
                            "execution_contract": {"network": False, "gpu": False, "torch": False,
                                                   "model_data_checkpoint_io": False, "one_shot": True,
                                                   "cleanup_retry_repair": False}},
                           sort_keys=True, separators=(",", ":")) + "\n").encode()

    def test_requires_matching_regular_request_and_never_executes(self):
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            request.write_bytes(self._request())
            digest = hashlib.sha256(request.read_bytes()).hexdigest()
            with mock.patch.object(r09_b2_p4_v4_execution_preflight, "_reserve_staging", side_effect=AssertionError("helper")) as reserve:
                with self.assertRaisesRegex(RuntimeError, "separately reviewed"):
                    main(["--request", str(request), "--request-sha256", digest])
            reserve.assert_not_called()
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

    def test_full_route_reuses_host_git_and_canonical_source_root(self):
        raw = self._request()
        with mock.patch.object(
            r09_b2_p4_v4_execution_preflight,
            "validate_environment_pair",
            side_effect=AssertionError("legacy environment route"),
        ), mock.patch.object(
            r09_b2_p4_v4_execution_preflight,
            "verify_d005_pair",
            side_effect=AssertionError("legacy D005 route"),
        ):
            with self.assertRaisesRegex(RuntimeError, "separately reviewed"):
                main(["--request", str(self._write_request(raw)), "--request-sha256", hashlib.sha256(raw).hexdigest()])
        git_path = self.source_validation.call_args.args[2]
        self.assertIs(self.interpreter_validation.call_args.args[2], git_path)
        authorities, request, source_root, authority_git = self.authorities_validation.call_args.args
        self.assertIs(authority_git, git_path)
        self.assertEqual(source_root, Path(request["source"]["root"]))
        self.assertIs(authorities, request["authorities"])

    def test_full_route_calls_frozen_validator_order(self):
        raw = self._request()
        calls = []

        def record(name, result=None):
            def validator(*_args):
                calls.append(name)
                return result
            return validator

        git_path = Path("/usr/bin/git")
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_entry", side_effect=record("entry")), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_host_git", side_effect=record("host_git", git_path)), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_source", side_effect=record("source")), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_interpreter", side_effect=record("interpreter")), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_run_pair", side_effect=record("run")), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_candidates", side_effect=record("candidates")), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_backends", side_effect=record("backends")), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_authorities_pair", side_effect=record("authorities")):
            r09_b2_p4_v4_execution_preflight.load_execution_request(raw)
        self.assertEqual(calls, ["entry", "host_git", "source", "interpreter", "run", "candidates", "backends", "authorities"])

    def _write_request(self, raw):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        request = Path(temporary.name) / "request.json"
        request.write_bytes(raw)
        return request

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


class FullAdmissionCompositionTest(unittest.TestCase):
    """Composition fixture: real D005 authorities, no request or execution I/O."""

    def _reidentity(self, value):
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in value.items() if key != "identity_sha256"}
        )

    def _request(self):
        root, authority_request, git = AuthoritiesAuthorityTest()._request()
        git_raw = r09_b2_p4_v4_execution_preflight._read_regular_nofollow(git, "git")
        host_git = {"path": str(git), "elf_sha256": hashlib.sha256(git_raw).hexdigest(),
                    "closure_sha256": r09_b2_p4_v4_execution_preflight._host_git_closure(git, git_raw)}
        entry_raw = b"composition entry\n"
        entry = {"tool_path": "tools/g0/r09_b2_p4_v4_execution_preflight.py",
                 "root_revision": "a" * 40, "git_blob_sha256": hashlib.sha256(entry_raw).hexdigest(),
                 "current_sha256": hashlib.sha256(entry_raw).hexdigest()}
        self._reidentity(entry)
        source = {"root": str(root), "root_revision": entry["root_revision"], "gitlink": "b" * 40,
                  "entry_git_blob_sha256": entry["git_blob_sha256"], "entry_current_sha256": entry["current_sha256"]}
        self._reidentity(source)
        with tempfile.TemporaryDirectory() as temporary:
            interpreter, _ = InterpreterAuthorityTest()._interpreter(temporary)
        interpreter["host_git"] = host_git
        interpreter["loader_argv"][8] = str(root)
        self._reidentity(interpreter)
        run = RunAuthorityTest()._pair()
        value = {"schema_version": "r09_b2_p4_v4_execution_request_v1", "entry": entry,
                 "source": source, "interpreter": interpreter, "environment": authority_request["environment"],
                 "authorities": AuthoritiesAuthorityTest()._authorities(), "run": run,
                 "candidates": CandidatesAuthorityTest()._value(run), "backends": BackendsAuthorityTest()._value(),
                 "execution_contract": {"network": False, "gpu": False, "torch": False,
                                        "model_data_checkpoint_io": False, "one_shot": True,
                                        "cleanup_retry_repair": False}}
        return value, git

    def _load(self, value, git, *, admit=False):
        root = Path(value["source"]["root"])
        entry_raw = b"composition entry\n"
        original_git = r09_b2_p4_v4_execution_preflight._git
        original_reader = r09_b2_p4_v4_execution_preflight._read_regular_nofollow
        expected_argv = value["interpreter"]["loader_argv"]

        def source_git(root_arg, *args, git_executable=None):
            if args == ("show", f"{r09_b2_p4_v4_execution_preflight._HISTORICAL_REVISION}:{r09_b2_p4_v4_execution_preflight._HISTORICAL_VERIFIER[0]}"):
                return original_git(root_arg, *args, git_executable=git_executable)
            if root_arg == root / "cosmos-framework" and args == ("rev-parse", "HEAD"):
                return ("b" * 40 + "\n").encode()
            if args == ("rev-parse", "HEAD") or args == ("rev-parse", "--verify", f"{'a' * 40}^{{commit}}"):
                return ("a" * 40 + "\n").encode()
            if args == ("ls-tree", "a" * 40, "cosmos-framework"):
                return ("160000 commit " + "b" * 40 + "\tcosmos-framework\n").encode()
            if args == ("ls-files", "--error-unmatch", "--", r09_b2_p4_v4_execution_preflight.ENTRY_TOOL_PATH):
                return b""
            if args == ("show", f"{'a' * 40}:{r09_b2_p4_v4_execution_preflight.ENTRY_TOOL_PATH}"):
                return entry_raw
            raise AssertionError(f"unexpected source Git call: {root_arg!s} {args!r}")

        def source_reader(path, error):
            if path == root / r09_b2_p4_v4_execution_preflight.ENTRY_TOOL_PATH:
                return entry_raw
            return original_reader(path, error)

        raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "_clean_git_root"), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "_git", side_effect=source_git), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "_read_regular_nofollow", side_effect=source_reader), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "verified_loader_argv", return_value=expected_argv):
            if admit:
                return r09_b2_p4_v4_execution_preflight._admit_execution_request(raw)
            return r09_b2_p4_v4_execution_preflight.load_execution_request(raw)

    def test_full_route_executes_authorities_and_rejects_reidentified_sections(self):
        value, git = self._request()
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_authorities_pair", wraps=r09_b2_p4_v4_execution_preflight.validate_authorities_pair) as authorities, \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_environment_pair", side_effect=AssertionError("legacy route")), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "verify_d005_pair", side_effect=AssertionError("legacy route")):
            self._load(value, git)
        self.assertEqual(authorities.call_count, 1)
        self.assertEqual(authorities.call_args.args[0], value["authorities"])
        self.assertEqual(authorities.call_args.args[2], Path(value["source"]["root"]))
        self.assertEqual(authorities.call_args.args[3], git)

        def entry_mutation(item):
            item["entry"]["tool_path"] = "other.py"; self._reidentity(item["entry"])
        def source_mutation(item):
            item["source"]["root_revision"] = "c" * 40
            self._reidentity(item["source"])
        def interpreter_mutation(item):
            item["interpreter"]["lexical_interpreter"]["sha256"] = "0" * 64
            self._reidentity(item["interpreter"])
        def environment_mutation(item):
            section = item["environment"]["recurrent"]
            section["effective_environment"]["set"]["HF_HUB_OFFLINE"] = "0"
            effective = section["effective_environment"]
            effective["sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: entry for key, entry in effective.items() if key != "sha256"})
            self._reidentity(section)
        def authorities_mutation(item):
            item["authorities"]["d005_pair"]["recurrent"]["sha256"] = "0" * 64
            AuthoritiesAuthorityTest()._reidentity(item["authorities"])
        def candidates_mutation(item):
            CandidatesAuthorityTest()._set_attempt(item["candidates"], "g" * 64)
        def backends_mutation(item):
            item["backends"]["recurrent"]["p3_contract"]["artifact_sha256"] = "0" * 64
            BackendsAuthorityTest()._reidentity(item["backends"])
        cases = (("entry", entry_mutation), ("source", source_mutation),
                 ("interpreter", interpreter_mutation), ("environment", environment_mutation),
                 ("authorities", authorities_mutation),
                 ("run", lambda item: item["run"]["recurrent"].__setitem__("run_token", "g" * 64)),
                 ("candidates", candidates_mutation), ("backends", backends_mutation))
        for name, mutate in cases:
            with self.subTest(section=name):
                candidate = json.loads(json.dumps(value)); mutate(candidate)
                expected = "source cross-binding" if name == "source" else ""
                with self.assertRaisesRegex(ValueError, expected):
                    self._load(candidate, git)


class RunAuthorityTest(unittest.TestCase):
    def _item(self, root: str, token: str, roster: str) -> dict[str, object]:
        identity = {"root": root, "resolved_root": root, "kind": "run_root"}
        identity["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(identity)
        return {"identity": identity, "run_token": token * 64, "roster_sha256": roster * 64}

    def _pair(self) -> dict[str, object]:
        return {"recurrent": self._item("/future/recurrent", "a", "b"),
                "ttt_fast_weight": self._item("/future/ttt", "c", "d")}

    def test_run_accepts_exact_future_pair_without_creating_roots(self):
        value = self._pair()
        r09_b2_p4_v4_execution_preflight.validate_run_pair(value, {"root": "/source"})
        self.assertFalse(Path("/future/recurrent").exists())
        self.assertFalse(Path("/future/ttt").exists())

    def test_run_rejects_schema_identity_digest_and_pair_reuse(self):
        mutations = (
            ("third backend", lambda value: value.__setitem__("extra", {}), "pair schema"),
            ("extra item key", lambda value: value["recurrent"].__setitem__("extra", "x"), "item schema"),
            ("extra identity key", lambda value: value["recurrent"]["identity"].__setitem__("extra", "x"), "identity schema"),
            ("missing identity key", lambda value: value["recurrent"]["identity"].pop("resolved_root"), "identity schema"),
            ("wrong kind", lambda value: value["recurrent"]["identity"].__setitem__("kind", "staging"), "identity differs"),
            ("identity drift", lambda value: value["recurrent"]["identity"].__setitem__("identity_sha256", "0" * 64), "identity differs"),
            ("resolved root differs", lambda value: value["recurrent"]["identity"].__setitem__("resolved_root", "/future/other"), "identity differs"),
            ("token grammar", lambda value: value["recurrent"].__setitem__("run_token", "A" * 64), "digest differs"),
            ("roster reuse", lambda value: value["ttt_fast_weight"].__setitem__("roster_sha256", value["recurrent"]["roster_sha256"]), "pair reuse"),
            ("token reuse", lambda value: value["ttt_fast_weight"].__setitem__("run_token", value["recurrent"]["run_token"]), "pair reuse"),
            ("identity reuse", lambda value: value["ttt_fast_weight"].__setitem__("identity", value["recurrent"]["identity"]), "pair reuse"),
        )
        for name, mutate, error in mutations:
            with self.subTest(name=name):
                value = self._pair()
                mutate(value)
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_run_pair(value, {"root": "/source"})

    def test_run_rejects_every_token_and_roster_digest_grammar_variant(self):
        mutations = (
            ("token nonhex", "run_token", "g" * 64),
            ("token short", "run_token", "a" * 63),
            ("token long", "run_token", "a" * 65),
            ("roster uppercase", "roster_sha256", "A" * 64),
            ("roster nonhex", "roster_sha256", "g" * 64),
            ("roster short", "roster_sha256", "b" * 63),
            ("roster long", "roster_sha256", "b" * 65),
        )
        for name, key, replacement in mutations:
            with self.subTest(name=name):
                value = self._pair()
                value["recurrent"][key] = replacement
                with self.assertRaisesRegex(ValueError, "digest differs"):
                    r09_b2_p4_v4_execution_preflight.validate_run_pair(value, {"root": "/source"})

    def test_run_is_independent_of_ambient_environment(self):
        value = self._pair()
        frozen = json.loads(json.dumps(value))
        with mock.patch.dict(os.environ, {"PATH": "/hostile", "PYTHONPATH": "/hostile", "LC_CTYPE": "bad"}, clear=True):
            r09_b2_p4_v4_execution_preflight.validate_run_pair(value, {"root": "/source"})
        self.assertEqual(value, frozen)

    def test_run_rejects_nonlexical_paths_symlink_ancestors_and_source_overlap(self):
        cases = (
            ("relative", "future/recurrent", "path differs"),
            ("dot", "/future/./recurrent", "path differs"),
            ("parent", "/future/../recurrent", "path differs"),
            ("repeated separator", "/future//recurrent", "path differs"),
            ("double leading separator", "//future/recurrent", "path differs"),
            ("source overlap", "/source/future", "source overlap"),
            ("submodule overlap", "/source/cosmos-framework/future", "source overlap"),
            ("source ancestor overlap", "/", "source overlap"),
        )
        for name, root, error in cases:
            with self.subTest(name=name):
                value = self._pair()
                value["recurrent"]["identity"]["root"] = root
                value["recurrent"]["identity"]["resolved_root"] = root
                identity = value["recurrent"]["identity"]
                identity["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                    {key: item for key, item in identity.items() if key != "identity_sha256"}
                )
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_run_pair(value, {"root": "/source"})
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"; source.mkdir()
            linked = Path(temporary) / "linked"; linked.symlink_to(source, target_is_directory=True)
            value = self._pair()
            root = str(linked / "future")
            value["recurrent"]["identity"].update({"root": root, "resolved_root": root})
            identity = value["recurrent"]["identity"]
            identity["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: item for key, item in identity.items() if key != "identity_sha256"}
            )
            with self.assertRaisesRegex(ValueError, "path differs"):
                r09_b2_p4_v4_execution_preflight.validate_run_pair(value, {"root": str(source)})


class CandidatesAuthorityTest(unittest.TestCase):
    def _run(self):
        return RunAuthorityTest()._pair()

    def _value(self, run, root_path="/candidates"):
        root = {"root": root_path, "resolved_root": root_path, "kind": "candidate_root"}
        root["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(root)
        value = {"root": root, "attempt_id": "e" * 64}
        for backend in ("recurrent", "ttt_fast_weight"):
            item = {"backend": backend, "candidate_root": f"{root_path}/{value['attempt_id']}/{backend}", "run": run[backend]}
            item["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(item)
            value[backend] = item
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(value)
        return value

    def _reidentity(self, value):
        root = value.get("root")
        if isinstance(root, dict) and set(root) == r09_b2_p4_v4_execution_preflight.CANDIDATE_ROOT_KEYS:
            root["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: item for key, item in root.items() if key != "identity_sha256"}
            )
        for backend in ("recurrent", "ttt_fast_weight"):
            item = value.get(backend)
            if isinstance(item, dict) and set(item) == r09_b2_p4_v4_execution_preflight.CANDIDATE_ITEM_KEYS:
                item["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                    {key: entry for key, entry in item.items() if key != "identity_sha256"}
                )
        if set(value) == r09_b2_p4_v4_execution_preflight.CANDIDATES_KEYS:
            self._outer_identity(value)

    def _outer_identity(self, value):
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in value.items() if key != "identity_sha256"}
        )

    def _set_root(self, value, root_path):
        value["root"].update({"root": root_path, "resolved_root": root_path})
        for backend in ("recurrent", "ttt_fast_weight"):
            value[backend]["candidate_root"] = f"{root_path}/{value['attempt_id']}/{backend}"
        self._reidentity(value)

    def _set_attempt(self, value, attempt_id):
        value["attempt_id"] = attempt_id
        root_path = value["root"]["root"]
        for backend in ("recurrent", "ttt_fast_weight"):
            value[backend]["candidate_root"] = f"{root_path}/{attempt_id}/{backend}"
        self._reidentity(value)

    def test_candidates_accept_exact_static_pair_without_creating_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"; source.mkdir()
            candidate = Path(temporary) / "candidates"
            run = self._run(); value = self._value(run, str(candidate))
            r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": str(source)}, run)
            self.assertFalse(candidate.exists())

    def test_candidates_reject_exact_schema_and_identity_drift(self):
        def root_identity(value, run):
            value["root"]["identity_sha256"] = "0" * 64; self._outer_identity(value)
        def backend_identity(value, run):
            value["recurrent"]["identity_sha256"] = "0" * 64; self._outer_identity(value)
        mutations = (
            ("outer extra", lambda value, run: value.__setitem__("extra", {}), "candidates schema"),
            ("outer missing", lambda value, run: value.pop("ttt_fast_weight"), "candidates schema"),
            ("outer retyped", lambda value, run: value.__setitem__("attempt_id", 1), "candidates attempt"),
            ("outer identity", lambda value, run: value.__setitem__("identity_sha256", "0" * 64), "candidates identity"),
            ("root identity", root_identity, "candidates root identity"),
            ("backend identity", backend_identity, "candidates backend identity"),
        )
        for name, mutate, error in mutations:
            with self.subTest(name=name):
                run = self._run(); value = self._value(run); mutate(value, run)
                if name == "outer retyped": self._outer_identity(value)
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": "/source"}, run)

    def test_candidates_reject_reidentified_binding_and_namespace_drift(self):
        def attempt_recurrent(value, run): self._set_attempt(value, run["recurrent"]["run_token"])
        def attempt_ttt(value, run): self._set_attempt(value, run["ttt_fast_weight"]["run_token"])
        def backend_label(value, run):
            value["recurrent"]["backend"] = "ttt_fast_weight"; self._reidentity(value)
        def run_binding(value, run):
            value["recurrent"]["run"] = run["ttt_fast_weight"]; self._reidentity(value)
        def leaf_mapping(value, run):
            value["recurrent"]["candidate_root"] = "/other"; self._reidentity(value)
        mutations = (
            ("attempt recurrent token", attempt_recurrent, "candidates reuse"),
            ("attempt ttt token", attempt_ttt, "candidates reuse"),
            ("attempt uppercase", lambda value, run: self._set_attempt(value, "E" * 64), "candidates attempt"),
            ("attempt short", lambda value, run: self._set_attempt(value, "e" * 63), "candidates attempt"),
            ("attempt long", lambda value, run: self._set_attempt(value, "e" * 65), "candidates attempt"),
            ("attempt grammar", lambda value, run: self._set_attempt(value, "g" * 64), "candidates attempt"),
            ("backend label", backend_label, "candidates backend"),
            ("run binding", run_binding, "candidates backend"),
            ("leaf mapping", leaf_mapping, "candidates path"),
        )
        for name, mutate, error in mutations:
            with self.subTest(name=name):
                run = self._run(); value = self._value(run); mutate(value, run)
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": "/source"}, run)

    def test_candidates_reject_candidate_specific_lexical_and_identity_reuse_drift(self):
        root_cases = (
            ("root relative", "future", "candidates root path"),
            ("root dot", "/candidates/./future", "candidates root path"),
            ("root parent", "/candidates/../future", "candidates root path"),
            ("root repeated", "/candidates//future", "candidates root path"),
            ("root double leading", "//candidates/future", "candidates root path"),
        )
        for name, root_path, error in root_cases:
            with self.subTest(name=name):
                run = self._run(); value = self._value(run); self._set_root(value, root_path)
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": "/source"}, run)
        leaf_cases = (
            ("leaf relative", "future", "candidates recurrent path"),
            ("leaf dot", "/candidates/./future", "candidates recurrent path"),
            ("leaf parent", "/candidates/../future", "candidates recurrent path"),
            ("leaf repeated", "/candidates//future", "candidates recurrent path"),
            ("leaf double leading", "//candidates/future", "candidates recurrent path"),
        )
        for name, leaf, error in leaf_cases:
            with self.subTest(name=name):
                run = self._run(); value = self._value(run)
                value["recurrent"]["candidate_root"] = leaf; self._reidentity(value)
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": "/source"}, run)
        run = self._run(); value = self._value(run)
        value["ttt_fast_weight"]["identity_sha256"] = value["recurrent"]["identity_sha256"]
        self._outer_identity(value)
        with self.assertRaisesRegex(ValueError, "candidates backend identity"):
            r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": "/source"}, run)

    def test_candidates_reject_source_run_overlap_and_symlink_ancestor(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"; source.mkdir()
            run = self._run()
            cases = (
                ("source descendant", str(source / "candidate"), "source overlap"),
                ("source ancestor", str(Path(temporary)), "source overlap"),
                ("run ancestor", "/future", "run overlap"),
                ("run descendant", "/future/recurrent/candidate", "run overlap"),
            )
            for name, root_path, error in cases:
                with self.subTest(name=name):
                    value = self._value(run); self._set_root(value, root_path)
                    with self.assertRaisesRegex(ValueError, error):
                        r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": str(source)}, run)
            linked = Path(temporary) / "linked"
            linked.symlink_to(source, target_is_directory=True)
            value = self._value(run); self._set_root(value, str(linked / "candidate"))
            with self.assertRaisesRegex(ValueError, "candidates root path"):
                r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": str(source)}, run)
            root = Path(temporary) / "candidate-root"; root.mkdir()
            target = Path(temporary) / "target"; target.mkdir()
            value = self._value(run, str(root))
            (root / value["attempt_id"]).symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "candidates recurrent path"):
                r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": str(source)}, run)

    def test_candidates_are_independent_of_ambient_environment(self):
        run = self._run(); value = self._value(run); frozen = json.loads(json.dumps(value))
        with mock.patch.dict(os.environ, {"PATH": "/hostile", "PYTHONPATH": "/hostile"}, clear=True):
            r09_b2_p4_v4_execution_preflight.validate_candidates(value, {"root": "/source"}, run)
        self.assertEqual(value, frozen)


class BackendsAuthorityTest(unittest.TestCase):
    def _value(self):
        value = {}
        for backend in ("recurrent", "ttt_fast_weight"):
            core = json.loads(json.dumps(r09_b2_p4_v4_execution_preflight.P3_CORE_SNAPSHOTS[backend]))
            contract = {**core, "identity_sha256": r09_b2_p4_v4_execution_preflight.canonical_sha256(core)}
            record = {"backend": backend, "p3_contract": contract}
            record["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(record)
            value[backend] = record
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(value)
        return value

    def _reidentity(self, value):
        for backend in ("recurrent", "ttt_fast_weight"):
            record = value.get(backend)
            if not isinstance(record, dict):
                continue
            contract = record.get("p3_contract")
            if isinstance(contract, dict) and set(contract) == r09_b2_p4_v4_execution_preflight.P3_CONTRACT_KEYS:
                contract["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                    {key: item for key, item in contract.items() if key != "identity_sha256"}
                )
            if set(record) == r09_b2_p4_v4_execution_preflight.BACKEND_ITEM_KEYS:
                record["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                    {key: item for key, item in record.items() if key != "identity_sha256"}
                )
        if set(value) == r09_b2_p4_v4_execution_preflight.BACKENDS_KEYS:
            value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: item for key, item in value.items() if key != "identity_sha256"}
            )

    def test_backends_accept_exact_snapshot_without_side_effects(self):
        value = self._value(); frozen = json.loads(json.dumps(value))
        with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("artifact read")), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight.subprocess, "run", side_effect=AssertionError("subprocess")), \
             mock.patch.dict(os.environ, {"PATH": "/hostile", "PYTHONPATH": "/hostile"}, clear=True):
            r09_b2_p4_v4_execution_preflight.validate_backends(value)
        self.assertEqual(value, frozen)

    def test_backends_reject_schema_identity_label_and_reuse_drift(self):
        mutations = (
            ("outer extra", lambda value: value.__setitem__("extra", {}), "backends schema"),
            ("outer missing", lambda value: value.pop("ttt_fast_weight"), "backends schema"),
            ("outer identity", lambda value: value.__setitem__("identity_sha256", "0" * 64), "backends identity"),
            ("record extra", lambda value: value["recurrent"].__setitem__("extra", {}), "backends record"),
            ("label swap", lambda value: value["recurrent"].__setitem__("backend", "ttt_fast_weight"), "backends record"),
            ("record reuse", lambda value: value["ttt_fast_weight"].__setitem__("identity_sha256", value["recurrent"]["identity_sha256"]), "backends reuse"),
            ("contract missing", lambda value: value["recurrent"]["p3_contract"].pop("verifier_sha256"), "P3 contract schema"),
            ("contract identity", lambda value: value["recurrent"]["p3_contract"].__setitem__("identity_sha256", "0" * 64), "P3 contract identity"),
        )
        for name, mutate, error in mutations:
            with self.subTest(name=name):
                value = self._value(); mutate(value)
                if name == "record reuse":
                    value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                        {key: item for key, item in value.items() if key != "identity_sha256"}
                    )
                elif name == "contract identity":
                    record = value["recurrent"]
                    record["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                        {key: item for key, item in record.items() if key != "identity_sha256"}
                    )
                    value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                        {key: item for key, item in value.items() if key != "identity_sha256"}
                    )
                elif name != "outer identity":
                    self._reidentity(value)
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_backends(value)

    def test_backends_reject_every_frozen_core_field_drift(self):
        value = self._value()
        for backend, core in r09_b2_p4_v4_execution_preflight.P3_CORE_SNAPSHOTS.items():
            for field in ("artifact_sha256", "verifier_sha256"):
                with self.subTest(backend=backend, field=field):
                    candidate = json.loads(json.dumps(value))
                    candidate[backend]["p3_contract"][field] = "0" * 64
                    self._reidentity(candidate)
                    with self.assertRaisesRegex(ValueError, "P3 snapshot"):
                        r09_b2_p4_v4_execution_preflight.validate_backends(candidate)
            with self.subTest(backend=backend, field="membership"):
                candidate = json.loads(json.dumps(value))
                candidate[backend]["p3_contract"]["backend_contract"]["optimizer_membership_sha256"] = "0" * 64
                self._reidentity(candidate)
                with self.assertRaisesRegex(ValueError, "P3 snapshot"):
                    r09_b2_p4_v4_execution_preflight.validate_backends(candidate)
            for index in range(len(core["backend_contract"]["selector_keys"])):
                with self.subTest(backend=backend, selector=index):
                    candidate = json.loads(json.dumps(value))
                    candidate[backend]["p3_contract"]["backend_contract"]["selector_keys"][index] = "other"
                    self._reidentity(candidate)
                    with self.assertRaisesRegex(ValueError, "P3 snapshot"):
                        r09_b2_p4_v4_execution_preflight.validate_backends(candidate)

    def test_backends_reject_core_grammar_swap_and_pair_binding_drift(self):
        grammar_mutations = (
            ("selector empty", lambda value: value["recurrent"]["p3_contract"]["backend_contract"].__setitem__("selector_keys", []), "P3 backend contract"),
            ("selector duplicate", lambda value: value["recurrent"]["p3_contract"]["backend_contract"].__setitem__("selector_keys", ["x", "x"]), "P3 backend contract"),
            ("selector retyped", lambda value: value["recurrent"]["p3_contract"]["backend_contract"].__setitem__("selector_keys", [1]), "P3 backend contract"),
            ("membership grammar", lambda value: value["recurrent"]["p3_contract"]["backend_contract"].__setitem__("optimizer_membership_sha256", "A" * 64), "P3 backend contract"),
        )
        for name, mutate, error in grammar_mutations:
            with self.subTest(name=name):
                value = self._value(); mutate(value); self._reidentity(value)
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_backends(value)
        value = self._value()
        selectors = value["recurrent"]["p3_contract"]["backend_contract"]["selector_keys"]
        selectors[0], selectors[1] = selectors[1], selectors[0]
        self._reidentity(value)
        with self.assertRaisesRegex(ValueError, "P3 snapshot"):
            r09_b2_p4_v4_execution_preflight.validate_backends(value)
        value = self._value()
        recurrent_contract = value["recurrent"]["p3_contract"]
        value["recurrent"]["p3_contract"] = value["ttt_fast_weight"]["p3_contract"]
        value["ttt_fast_weight"]["p3_contract"] = recurrent_contract
        self._reidentity(value)
        with self.assertRaisesRegex(ValueError, "P3 snapshot"):
            r09_b2_p4_v4_execution_preflight.validate_backends(value)
        snapshots = json.loads(json.dumps(r09_b2_p4_v4_execution_preflight.P3_CORE_SNAPSHOTS))
        snapshots["ttt_fast_weight"]["artifact_sha256"] = "f" * 64
        value = self._value()
        value["ttt_fast_weight"]["p3_contract"]["artifact_sha256"] = "f" * 64
        self._reidentity(value)
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "P3_CORE_SNAPSHOTS", snapshots):
            with self.assertRaisesRegex(ValueError, "P3 pair binding"):
                r09_b2_p4_v4_execution_preflight.validate_backends(value)


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

    def test_authorities_reject_pair_source_verifier_and_binding_identity_drift(self):
        root, request, git = self._request()
        cases = (
            (lambda value: value["d005_pair"].__setitem__("identity_sha256", "0" * 64), "authorities pair identity"),
            (lambda value: value["d005_pair"]["recurrent"].__setitem__("relative_path", "other.json"), "binding differs"),
            (lambda value: value["d005_pair"]["historical_source"].__setitem__("gitlink_revision", "0" * 40), "historical source differs"),
            (lambda value: value["d005_pair"]["historical_verifier"].__setitem__("relative_path", "other.py"), "historical source differs"),
            (lambda value: value["d005_pair"]["ttt_fast_weight"].update(value["d005_pair"]["recurrent"]), "binding differs"),
        )
        for mutate, error in cases:
            with self.subTest(error=error):
                value = self._authorities(); mutate(value)
                if error == "authorities pair identity":
                    value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({"d005_pair": value["d005_pair"]})
                else:
                    self._reidentity(value)
                with self.assertRaisesRegex(ValueError, error):
                    r09_b2_p4_v4_execution_preflight.validate_authorities_pair(value, request, root, git)

    def test_authorities_reject_historical_verification_nested_roster_drift(self):
        root, _, _ = self._request()
        raw = (root / r09_b2_p4_v4_execution_preflight._HISTORICAL_ARTIFACTS["verification"][0]).read_bytes()
        original = json.loads(raw)
        mutations = (
            lambda value: value.__setitem__("extra", True),
            lambda value: value.pop("status"),
            lambda value: value.__setitem__("status", False),
            lambda value: value.__setitem__("schema_version", 1),
            lambda value: value["checks"].__setitem__("extra", True),
            lambda value: value["checks"].pop("distinct_outputs"),
            lambda value: value["checks"].__setitem__("distinct_outputs", False),
            lambda value: value["checks"].__setitem__("distinct_outputs", "true"),
            lambda value: value["checks"]["matched"].__setitem__("extra", True),
            lambda value: value["checks"]["matched"].pop("budget"),
            lambda value: value["checks"]["matched"].__setitem__("budget", False),
            lambda value: value["checks"]["matched"].__setitem__("budget", "true"),
            lambda value: value["checks"]["recurrent"].__setitem__("extra", True),
            lambda value: value["checks"]["recurrent"].pop("argv"),
            lambda value: value["checks"]["recurrent"].__setitem__("argv", False),
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

    def test_authorities_reject_historical_artifact_fifo_without_hanging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); fifo = root / "artifact"; os.mkfifo(fifo)
            expected = {"relative_path": "artifact", "sha256": "0" * 64}
            writer_ready = threading.Event()

            def open_writer():
                descriptor = os.open(fifo, os.O_WRONLY)
                writer_ready.set()
                os.close(descriptor)

            writer = threading.Thread(target=open_writer, daemon=True); writer.start()
            with self.assertRaisesRegex(ValueError, "path differs"):
                r09_b2_p4_v4_execution_preflight._read_historical_artifact(root, expected, expected, "test")
            writer.join(timeout=1)
            self.assertTrue(writer_ready.is_set())
            self.assertFalse(writer.is_alive())

    def test_authorities_historical_artifact_opens_lexical_path_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); artifact = root / "artifact"
            raw = b'{"ok":true}\n'; artifact.write_bytes(raw)
            expected = {"relative_path": "artifact", "sha256": hashlib.sha256(raw).hexdigest()}
            original_open = os.open; seen = []

            def observe(path, flags, *args):
                seen.append((Path(path), flags))
                return original_open(path, flags, *args)

            with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "open", side_effect=observe):
                read_raw, decoded = r09_b2_p4_v4_execution_preflight._read_historical_artifact(root, expected, expected, "test")
            self.assertEqual(read_raw, raw)
            self.assertEqual(decoded, {"ok": True})
            self.assertEqual(seen, [(artifact, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))])

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

    def test_authorities_reject_environment_native_p3_and_missing_drift(self):
        root, request, git = self._request()
        mutations = (
            lambda value: value["recurrent"]["native_loader_environment"].__setitem__("set", {"X": "1"}),
            lambda value: value["ttt_fast_weight"]["effective_environment"]["set"].__setitem__("PSM_R09_B1_TTT_ENABLED", "0"),
            lambda value: value.pop("ttt_fast_weight"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value = json.loads(json.dumps(request["environment"])); mutate(value)
                for section in value.values():
                    for name in ("effective_environment", "native_loader_environment"):
                        section[name]["sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in section[name].items() if key != "sha256"})
                    section["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in section.items() if key != "identity_sha256"})
                candidate = {**request, "environment": value}
                with self.assertRaises(ValueError):
                    r09_b2_p4_v4_execution_preflight.validate_authorities_pair(self._authorities(), candidate, root, git)

    def test_authorities_host_git_argv_and_path_shadow_are_fixed(self):
        root, request, git = self._request()
        seen = []
        original = r09_b2_p4_v4_execution_preflight._git
        def observe(root_arg, *args, git_executable=None):
            seen.append((root_arg, args, git_executable))
            return original(root_arg, *args, git_executable=git_executable)
        with tempfile.TemporaryDirectory() as temporary:
            shadow = Path(temporary); (shadow / "git").write_text("#!/bin/sh\nexit 99\n"); (shadow / "git").chmod(0o755)
            with mock.patch.dict(os.environ, {"PATH": str(shadow), "UNTRUSTED": "x"}, clear=True), \
                 mock.patch.object(r09_b2_p4_v4_execution_preflight, "_git", side_effect=observe):
                r09_b2_p4_v4_execution_preflight.validate_authorities_pair(self._authorities(), request, root, git)
        self.assertEqual(seen[-1], (root, ("show", f"{r09_b2_p4_v4_execution_preflight._HISTORICAL_REVISION}:{r09_b2_p4_v4_execution_preflight._HISTORICAL_VERIFIER[0]}"), git))

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

    def test_authorities_reject_historical_record_noncanonical_raw(self):
        root, request, git = self._request()
        records = {}
        for backend in ("recurrent", "ttt_fast_weight"):
            path, _ = r09_b2_p4_v4_execution_preflight._HISTORICAL_ARTIFACTS[backend]
            records[backend] = json.loads((root / path).read_bytes())
        verification_path, _ = r09_b2_p4_v4_execution_preflight._HISTORICAL_ARTIFACTS["verification"]
        verification = json.loads((root / verification_path).read_bytes())
        verifier = r09_b2_p4_v4_execution_preflight._git(root, "show", f"{r09_b2_p4_v4_execution_preflight._HISTORICAL_REVISION}:{r09_b2_p4_v4_execution_preflight._HISTORICAL_VERIFIER[0]}", git_executable=git)

        def fake_read(_, __, ___, name):
            item = verification if name == "verification" else records[name]
            raw = json.dumps(item, indent=2, sort_keys=True).encode() + b"\n"
            return raw, item

        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "_read_historical_artifact", side_effect=fake_read), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "_git", return_value=verifier):
            with self.assertRaisesRegex(ValueError, "historical record differs"):
                r09_b2_p4_v4_execution_preflight.validate_authorities_pair(self._authorities(), request, root, git)

    def test_authorities_reject_historical_verification_pretty_byte_drift(self):
        source_root, request, git = self._request()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("recurrent", "ttt_fast_weight", "verification"):
                relative, _ = r09_b2_p4_v4_execution_preflight._HISTORICAL_ARTIFACTS[name]
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
                raw = (source_root / relative).read_bytes()
                if name == "verification":
                    raw = json.dumps(json.loads(raw), indent=4, sort_keys=True).encode() + b"\n"
                    self.assertNotEqual(raw, (source_root / relative).read_bytes())
                target.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "verification bytes differ"):
                r09_b2_p4_v4_execution_preflight.validate_authorities_pair(self._authorities(), request, root, git)

class PlannedRosterCommitmentTest(unittest.TestCase):
    def _identity(self, value):
        value["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(value)
        return value

    def _raw(self):
        run = {}
        candidates = {"root": self._identity({"root": "/candidates", "resolved_root": "/candidates", "kind": "candidate_root"}), "attempt_id": "e" * 64}
        for backend, token in (("recurrent", "a" * 64), ("ttt_fast_weight", "b" * 64)):
            identity = self._identity({"root": f"/runs/{backend}", "resolved_root": f"/runs/{backend}", "kind": "run_root"})
            run[backend] = self._identity({"identity": identity, "run_token": token})
            candidates[backend] = self._identity({"backend": backend, "candidate_root": f"/candidates/{'e' * 64}/{backend}", "run_identity": identity, "run_token": token})
        candidates = self._identity(candidates)
        manifest = {"entries": [{"path": "pkg/module.py", "type": "regular", "sha256": "c" * 64}]}
        manifest["sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(manifest)
        spec = {
            "schema_version": "r09_b2_p4_v4_lock_spec_v3", "entry": {}, "source": {"root": "/source"},
            "interpreter": {"host_git": {}}, "environment": {}, "authorities": {}, "backends": {},
            "execution_contract": dict(r09_b2_p4_v4_execution_preflight._EXECUTION_CONTRACT_ITEMS), "planned_run": run, "planned_candidates": candidates,
            "payload_manifest": manifest,
        }
        spec["lock_spec_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(spec)
        return (json.dumps(spec, sort_keys=True, separators=(",", ":")) + "\n").encode()

    def _build(self, raw):
        with mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_entry"), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_host_git", return_value=Path("/usr/bin/git")), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_source"), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_interpreter"), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_backends"), \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "validate_authorities_pair"):
            return r09_b2_p4_v4_execution_preflight.build_planned_roster_commitment(raw)

    def _relock(self, value):
        """Recompute every planned-only identity after a deliberate mutation."""
        manifest = value["payload_manifest"]
        manifest["sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in manifest.items() if key != "sha256"}
        )
        for backend in ("recurrent", "ttt_fast_weight"):
            run = value["planned_run"][backend]
            identity = run["identity"]
            identity["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: item for key, item in identity.items() if key != "identity_sha256"}
            )
            run["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: item for key, item in run.items() if key != "identity_sha256"}
            )
            candidate = value["planned_candidates"][backend]
            candidate["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
                {key: item for key, item in candidate.items() if key != "identity_sha256"}
            )
        candidates = value["planned_candidates"]
        candidates["root"]["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in candidates["root"].items() if key != "identity_sha256"}
        )
        candidates["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in candidates.items() if key != "identity_sha256"}
        )
        value["lock_spec_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in value.items() if key != "lock_spec_sha256"}
        )

    def _planned_spec(self, source_root):
        """Reuse the full-admission closed sections for a planned-only lock spec."""
        request, git = FullAdmissionCompositionTest()._request()
        entry_raw = (source_root / r09_b2_p4_v4_execution_preflight.ENTRY_TOOL_PATH).read_bytes()
        request["entry"].update({
            "git_blob_sha256": hashlib.sha256(entry_raw).hexdigest(),
            "current_sha256": hashlib.sha256(entry_raw).hexdigest(),
        })
        request["entry"]["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in request["entry"].items() if key != "identity_sha256"}
        )
        request["source"].update({
            "root": str(source_root),
            "entry_git_blob_sha256": request["entry"]["git_blob_sha256"],
            "entry_current_sha256": request["entry"]["current_sha256"],
        })
        request["source"]["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in request["source"].items() if key != "identity_sha256"}
        )
        request["interpreter"]["loader_argv"][8] = str(source_root)
        request["interpreter"]["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(
            {key: item for key, item in request["interpreter"].items() if key != "identity_sha256"}
        )
        run, candidates = {}, request["candidates"]
        for backend in ("recurrent", "ttt_fast_weight"):
            item = request["run"][backend]
            run_item = {"identity": item["identity"], "run_token": item["run_token"]}
            run_item["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(run_item)
            run[backend] = run_item
        planned_candidates = {
            "root": candidates["root"], "attempt_id": candidates["attempt_id"],
        }
        for backend in ("recurrent", "ttt_fast_weight"):
            item = candidates[backend]
            planned = {
                "backend": backend, "candidate_root": item["candidate_root"],
                "run_identity": run[backend]["identity"], "run_token": run[backend]["run_token"],
            }
            planned["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(planned)
            planned_candidates[backend] = planned
        planned_candidates["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(planned_candidates)
        manifest = {"entries": [{"path": "payload.py", "type": "regular", "sha256": "c" * 64}]}
        manifest["sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(manifest)
        spec = {
            "schema_version": "r09_b2_p4_v4_lock_spec_v3",
            **{key: request[key] for key in ("entry", "source", "interpreter", "environment", "authorities", "backends", "execution_contract")},
            "planned_run": run, "planned_candidates": planned_candidates, "payload_manifest": manifest,
        }
        spec["lock_spec_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256(spec)
        return spec, git

    def test_builds_exact_v2_planned_commitment_without_roster_sha(self):
        commitment = self._build(self._raw())
        self.assertEqual(set(commitment), r09_b2_p4_v4_execution_preflight.PLANNED_COMMITMENT_KEYS)
        self.assertEqual(commitment["planned"]["root"]["root"], "/candidates")
        for backend, token in (("recurrent", "a" * 64), ("ttt_fast_weight", "b" * 64)):
            item = commitment["planned"][backend]
            self.assertEqual(item["run_token"], token)
            self.assertEqual(item["candidate_root"], f"/candidates/{'e' * 64}/{backend}")
            self.assertNotIn("roster_sha256", item)
            self.assertEqual(set(item["staging_projection"]), r09_b2_p4_v4_execution_preflight.STAGING_PROJECTION_KEYS)
            self.assertEqual(item["staging_projection"]["entries"], [
            {"path": "import_staging", "type": "directory", "mode": "0555", "sha256": ""},
            {"path": f"import_staging/{token}", "type": "directory", "mode": "0555", "sha256": ""},
            {"path": "pkg", "type": "directory", "mode": "0555", "sha256": ""},
            {"path": "pkg/module.py", "type": "regular", "mode": "0444", "sha256": "c" * 64},
            ])

    def test_rejects_final_field_and_candidate_mapping_drift(self):
        for mutation in (
            lambda value: value.__setitem__("run", {}),
            lambda value: value["planned_candidates"]["recurrent"].__setitem__("candidate_root", "/wrong"),
        ):
            with self.subTest(mutation=mutation):
                value = json.loads(self._raw()); mutation(value)
                value["lock_spec_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in value.items() if key != "lock_spec_sha256"})
                with self.assertRaises(ValueError):
                    self._build((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())

    def test_rejects_execution_contract_path_and_pair_reuse_drift(self):
        mutations = (
            ("contract value", lambda value: value["execution_contract"].__setitem__("gpu", True)),
            ("contract missing", lambda value: value["execution_contract"].pop("torch")),
            ("contract extra", lambda value: value["execution_contract"].__setitem__("extra", False)),
            ("run relative", lambda value: value["planned_run"]["recurrent"]["identity"].update({"root": "relative", "resolved_root": "relative"})),
            ("run source overlap", lambda value: value["planned_run"]["recurrent"]["identity"].update({"root": "/source/run", "resolved_root": "/source/run"})),
            ("candidate source overlap", lambda value: value["planned_candidates"]["root"].update({"root": "/source/candidates", "resolved_root": "/source/candidates"})),
            ("shared run root", lambda value: value["planned_run"]["ttt_fast_weight"].__setitem__("identity", value["planned_run"]["recurrent"]["identity"])),
        )
        for name, mutate in mutations:
            with self.subTest(name=name):
                value = json.loads(self._raw()); mutate(value)
                for backend in ("recurrent", "ttt_fast_weight"):
                    identity = value["planned_run"][backend]["identity"]
                    identity["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in identity.items() if key != "identity_sha256"})
                    item = value["planned_run"][backend]
                    item["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: entry for key, entry in item.items() if key != "identity_sha256"})
                    candidate = value["planned_candidates"][backend]
                    candidate["run_identity"] = item["identity"]
                    candidate["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: entry for key, entry in candidate.items() if key != "identity_sha256"})
                root = value["planned_candidates"]["root"]
                root["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in root.items() if key != "identity_sha256"})
                candidates = value["planned_candidates"]
                candidates["identity_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in candidates.items() if key != "identity_sha256"})
                value["lock_spec_sha256"] = r09_b2_p4_v4_execution_preflight.canonical_sha256({key: item for key, item in value.items() if key != "lock_spec_sha256"})
                with self.assertRaises(ValueError):
                    self._build((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())

    def test_output_create_and_post_create_faults_are_terminal(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary); descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "open", side_effect=OSError("EACCES")):
                    with self.assertRaisesRegex(ValueError, "NOT_LOCKED"):
                        r09_b2_p4_v4_execution_preflight._write_planned_commitment_at(descriptor, "denied.json", {})
                for name, target, method in (
                    ("write", "write.json", "write"), ("fsync", "fsync.json", "fsync"),
                    ("seek", "seek.json", "lseek"), ("read", "read.json", "read"),
                    ("chmod", "chmod.json", "fchmod"), ("fstat", "fstat.json", "fstat"),
                ):
                    with self.subTest(name=name), mock.patch.object(r09_b2_p4_v4_execution_preflight.os, method, side_effect=OSError(name)):
                        with self.assertRaisesRegex(RuntimeError, "POISONED_NOT_LOCKED"):
                            r09_b2_p4_v4_execution_preflight._write_planned_commitment_at(descriptor, target, {})
                        self.assertTrue((parent / target).exists())
                with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "close", side_effect=OSError("close")):
                    with self.assertRaisesRegex(RuntimeError, "POISONED_NOT_LOCKED"):
                        r09_b2_p4_v4_execution_preflight._write_planned_commitment_at(descriptor, "close.json", {})
                    self.assertTrue((parent / "close.json").exists())
            finally:
                os.close(descriptor)

    def test_output_target_short_write_and_mode_faults_are_terminal(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary); descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                (parent / "existing.json").write_text("old")
                with self.assertRaisesRegex(ValueError, "NOT_LOCKED"):
                    r09_b2_p4_v4_execution_preflight._write_planned_commitment_at(descriptor, "existing.json", {})
                self.assertEqual((parent / "existing.json").read_text(), "old")
                (parent / "target.json").write_text("old")
                (parent / "linked.json").symlink_to(parent / "target.json")
                with self.assertRaisesRegex(ValueError, "NOT_LOCKED"):
                    r09_b2_p4_v4_execution_preflight._write_planned_commitment_at(descriptor, "linked.json", {})
                with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "write", return_value=1):
                    with self.assertRaisesRegex(RuntimeError, "POISONED_NOT_LOCKED"):
                        r09_b2_p4_v4_execution_preflight._write_planned_commitment_at(descriptor, "short.json", {"x": "y"})
                self.assertTrue((parent / "short.json").exists())
                original_fstat = os.fstat
                with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "fstat", side_effect=lambda fd: type("S", (), {"st_mode": 0o444})()):
                    with self.assertRaisesRegex(RuntimeError, "POISONED_NOT_LOCKED"):
                        r09_b2_p4_v4_execution_preflight._write_planned_commitment_at(descriptor, "not-regular.json", {})
                self.assertTrue((parent / "not-regular.json").exists())
            finally:
                os.close(descriptor)

    def test_spec_fd_walk_rejects_intermediate_and_final_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"; root.mkdir(); nested = root / "nested"; nested.mkdir()
            (nested / "spec.json").write_bytes(b"{}\n")
            descriptor = r09_b2_p4_v4_execution_preflight._open_absolute_directory_chain(str(root), "source")
            try:
                self.assertEqual(r09_b2_p4_v4_execution_preflight._read_lock_spec_at(descriptor, "nested/spec.json"), b"{}\n")
                (root / "linked").symlink_to(nested, target_is_directory=True)
                with self.assertRaises(ValueError):
                    r09_b2_p4_v4_execution_preflight._read_lock_spec_at(descriptor, "linked/spec.json")
                (nested / "linked.json").symlink_to(nested / "spec.json")
                with self.assertRaises(ValueError):
                    r09_b2_p4_v4_execution_preflight._read_lock_spec_at(descriptor, "nested/linked.json")
            finally:
                os.close(descriptor)

    def test_spec_fd_parent_retarget_keeps_original_chain(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"; root.mkdir(); nested = root / "nested"; nested.mkdir()
            (nested / "spec.json").write_bytes(b"original\n")
            external = Path(temporary) / "external"; external.mkdir(); (external / "spec.json").write_bytes(b"external\n")
            descriptor = r09_b2_p4_v4_execution_preflight._open_absolute_directory_chain(str(root), "source")
            moved = root / "moved"; original_open = os.open; swapped = False
            def retarget(name, flags, *args, **kwargs):
                nonlocal swapped
                child = original_open(name, flags, *args, **kwargs)
                if name == "nested" and not swapped and "dir_fd" in kwargs:
                    swapped = True; nested.rename(moved); nested.symlink_to(external, target_is_directory=True)
                return child
            try:
                with mock.patch.object(r09_b2_p4_v4_execution_preflight.os, "open", side_effect=retarget):
                    self.assertEqual(r09_b2_p4_v4_execution_preflight._read_lock_spec_at(descriptor, "nested/spec.json"), b"original\n")
                self.assertEqual((external / "spec.json").read_bytes(), b"external\n")
            finally:
                os.close(descriptor)

    def test_projection_and_self_sha_drift_are_rejected(self):
        mutations = (
            ("manifest order", lambda value: value["payload_manifest"]["entries"].extend([
                {"path": "zzz.py", "type": "regular", "sha256": "d" * 64},
                {"path": "aaa.py", "type": "regular", "sha256": "e" * 64},
            ])),
            ("escaping path", lambda value: value["payload_manifest"]["entries"][0].__setitem__("path", "../escape.py")),
            ("type drift", lambda value: value["payload_manifest"]["entries"][0].__setitem__("type", "directory")),
            ("malformed regular SHA", lambda value: value["payload_manifest"]["entries"][0].__setitem__("sha256", "g" * 64)),
            ("nested run token", lambda value: value["planned_run"]["recurrent"].__setitem__("run_token", "f" * 64)),
            ("outer SHA", lambda value: value.__setitem__("lock_spec_sha256", "0" * 64)),
        )
        for name, mutation in mutations:
            with self.subTest(name=name):
                value = json.loads(self._raw()); mutation(value)
                if name != "outer SHA":
                    self._relock(value)
                with self.assertRaises(ValueError):
                    self._build((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())

    def test_authorized_public_lock_runs_real_closed_sections_and_rejects_each_binding(self):
        """The non-None authority fixture remains test-local; production stays absent."""
        repository = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary); source = temporary_root / "source"; output = temporary_root / "output"
            entry = source / r09_b2_p4_v4_execution_preflight.ENTRY_TOOL_PATH
            entry.parent.mkdir(parents=True); shutil.copyfile(repository / r09_b2_p4_v4_execution_preflight.ENTRY_TOOL_PATH, entry)
            (source / "cosmos-framework").mkdir(parents=True); output.mkdir()
            for name, (relative, _) in r09_b2_p4_v4_execution_preflight._HISTORICAL_ARTIFACTS.items():
                target = source / relative; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(repository / relative, target)
            spec, git = self._planned_spec(source)
            raw = (json.dumps(spec, sort_keys=True, separators=(",", ":")) + "\n").encode()
            spec_path = "locks/spec.json"; target = source / spec_path; target.parent.mkdir()
            target.write_bytes(raw)
            authority = {
                "schema_version": "r09_b2_p4_v4_lock_authority_v1", "source_root": str(source),
                "source_commit": "a" * 40, "source_tree_oid": "c" * 40, "gitlink": "b" * 40,
                "spec_path": spec_path, "spec_git_blob_sha256": hashlib.sha256(raw).hexdigest(),
                "spec_current_sha256": hashlib.sha256(raw).hexdigest(), "spec_raw_sha256": hashlib.sha256(raw).hexdigest(),
                "output_parent": str(output), "output_basename": "commitment.json",
            }
            original_git = r09_b2_p4_v4_execution_preflight._git
            original_run = subprocess.run; commands = []

            def source_git(root_arg, *args, git_executable=None):
                if args == ("show", f"{r09_b2_p4_v4_execution_preflight._HISTORICAL_REVISION}:{r09_b2_p4_v4_execution_preflight._HISTORICAL_VERIFIER[0]}"):
                    return original_git(repository, *args, git_executable=git_executable)
                if root_arg == source / "cosmos-framework" and args == ("rev-parse", "HEAD"):
                    return ("b" * 40 + "\n").encode()
                if args in (("rev-parse", "HEAD"), ("rev-parse", "--verify", f"{'a' * 40}^{{commit}}")):
                    return ("a" * 40 + "\n").encode()
                if args == ("rev-parse", f"{'a' * 40}^{{tree}}"):
                    return ("c" * 40 + "\n").encode()
                if args == ("ls-tree", "a" * 40, "cosmos-framework"):
                    return ("160000 commit " + "b" * 40 + "\tcosmos-framework\n").encode()
                if args == ("ls-files", "--error-unmatch", "--", r09_b2_p4_v4_execution_preflight.ENTRY_TOOL_PATH):
                    return b""
                if args == ("show", f"{'a' * 40}:{r09_b2_p4_v4_execution_preflight.ENTRY_TOOL_PATH}"):
                    return entry.read_bytes()
                if args == ("show", f"{'a' * 40}:{spec_path}"):
                    return raw
                raise AssertionError(f"unexpected source Git call: {root_arg!s} {args!r}")

            def observe_run(command, *args, **kwargs):
                commands.append(command)
                self.assertEqual(command[0], str(git))
                return original_run(command, *args, **kwargs)

            expected_argv = spec["interpreter"]["loader_argv"]
            patches = (
                mock.patch.object(r09_b2_p4_v4_execution_preflight, "_clean_git_root"),
                mock.patch.object(r09_b2_p4_v4_execution_preflight, "_git", side_effect=source_git),
                mock.patch.object(r09_b2_p4_v4_execution_preflight, "verified_loader_argv", return_value=expected_argv),
                mock.patch.object(r09_b2_p4_v4_execution_preflight.subprocess, "run", side_effect=observe_run),
            )
            with mock.patch.dict(os.environ, {"PATH": "/hostile", "PYTHONPATH": "/hostile", "LC_CTYPE": "bad"}, clear=True), \
                 mock.patch.object(r09_b2_p4_v4_execution_preflight, "AUTHORIZED_P4_V4_LOCK_SPEC", authority), \
                 patches[0], patches[1], patches[2], patches[3]:
                result = r09_b2_p4_v4_execution_preflight.lock_authorized_planned_roster_commitment()
            self.assertEqual(result, output / "commitment.json")
            expected = self._build(raw)
            self.assertEqual(result.read_bytes(), (json.dumps(expected, sort_keys=True, separators=(",", ":")) + "\n").encode())
            self.assertEqual(stat.S_IMODE(result.stat().st_mode), 0o444)
            self.assertTrue(stat.S_ISREG(result.stat().st_mode))
            self.assertFalse({"run", "candidates", "roster_sha256"} & set(json.loads(result.read_bytes())))
            self.assertTrue(commands)
            for name, mutate in (
                ("source root", lambda item: item.__setitem__("source_root", str(source / "missing"))),
                ("source commit", lambda item: item.__setitem__("source_commit", "d" * 40)),
                ("source tree", lambda item: item.__setitem__("source_tree_oid", "d" * 40)),
                ("Gitlink", lambda item: item.__setitem__("gitlink", "d" * 40)),
                ("spec path", lambda item: item.__setitem__("spec_path", "locks/missing.json")),
                ("spec blob", lambda item: item.__setitem__("spec_git_blob_sha256", "d" * 64)),
                ("spec current", lambda item: item.__setitem__("spec_current_sha256", "d" * 64)),
                ("spec raw", lambda item: item.__setitem__("spec_raw_sha256", "d" * 64)),
                ("output parent", lambda item: item.__setitem__("output_parent", str(output / "missing"))),
                ("output basename", lambda item: item.__setitem__("output_basename", "nested/file.json")),
            ):
                with self.subTest(binding=name), tempfile.TemporaryDirectory() as negative:
                    candidate = dict(authority); candidate["output_parent"] = negative; mutate(candidate)
                    with mock.patch.object(r09_b2_p4_v4_execution_preflight, "AUTHORIZED_P4_V4_LOCK_SPEC", candidate), \
                         patches[0], patches[1], patches[2], patches[3]:
                        with self.assertRaises((ValueError, OSError)):
                            r09_b2_p4_v4_execution_preflight.lock_authorized_planned_roster_commitment()
                    self.assertEqual(list(Path(negative).iterdir()), [])
        self.assertIsNone(r09_b2_p4_v4_execution_preflight.AUTHORIZED_P4_V4_LOCK_SPEC)

    def test_default_authority_creates_no_output(self):
        with tempfile.TemporaryDirectory() as temporary, \
             mock.patch.object(r09_b2_p4_v4_execution_preflight, "AUTHORIZED_P4_V4_LOCK_SPEC", None):
            with self.assertRaisesRegex(ValueError, "authority is absent"):
                r09_b2_p4_v4_execution_preflight.lock_authorized_planned_roster_commitment()
            self.assertEqual(list(Path(temporary).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
