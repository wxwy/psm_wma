"""CPU-only temporary witnesses; never imports or invokes payload main()."""
from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("witness", HERE / "PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.7_witness_core.py")
assert SPEC and SPEC.loader
W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W)


class WitnessTest(unittest.TestCase):
    def test_path_identity_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); path = root / "backing"; path.write_bytes(b"x"); path.chmod(0o600)
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                W.verify_handoff_path(path, fd, fd)
                path.chmod(0o644)
                with self.assertRaises(W.WitnessFailure): W.verify_handoff_path(path, fd, fd)
            finally: os.close(fd)

    def test_replacement_and_commondir(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); path = root / "backing"; path.write_bytes(b"x"); path.chmod(0o600)
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                replacement = root / "replacement"; replacement.write_bytes(b"x"); replacement.chmod(0o600); os.replace(replacement, path)
                with self.assertRaises(W.WitnessFailure): W.verify_handoff_path(path, fd, fd)
            finally: os.close(fd)
            admin = root / ".git"; admin.mkdir(); W.require_commondir_absent(admin); (admin / "commondir").write_text("../common")
            with self.assertRaises(W.WitnessFailure): W.require_commondir_absent(admin)

    def test_add_failure_classifier(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            clean = Path(raw) / "clean"
            self.assertEqual(W.classify_add_failure(clean, False), "FAIL")
            clean.mkdir()
            self.assertEqual(W.classify_add_failure(clean, False), "ROLLBACK_INCOMPLETE")
            self.assertEqual(W.classify_add_failure(clean, True), "ROLLBACK_INCOMPLETE")


if __name__ == "__main__": unittest.main()
