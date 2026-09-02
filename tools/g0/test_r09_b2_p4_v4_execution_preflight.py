"""CPU-only regression tests for the non-executing P4-v4 entry foundation."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.g0 import r09_b2_p4_v4_execution_preflight
from tools.g0.r09_b2_p4_v4_execution_preflight import main


class EntryFoundationTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
