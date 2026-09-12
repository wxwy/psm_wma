"""CPU-only temporary witnesses; never imports or invokes payload main()."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("witness", HERE / "PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.7_witness_core.py")
assert SPEC and SPEC.loader
W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W)
PAYLOAD_SPEC = importlib.util.spec_from_file_location("payload", HERE / "PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.7.py")
assert PAYLOAD_SPEC and PAYLOAD_SPEC.loader
P = importlib.util.module_from_spec(PAYLOAD_SPEC)
PAYLOAD_SPEC.loader.exec_module(P)


class WitnessTest(unittest.TestCase):
    def test_native_git_commondir_witness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"
            subprocess.run(["/usr/bin/git", "init", "-q", str(root)], check=True)
            admin = root / ".git"
            W.require_commondir_absent(admin)
            (admin / "commondir").write_text("../common\n")
            with self.assertRaises(W.WitnessFailure): W.require_commondir_absent(admin)

    def test_native_git_worktree_add_remove_witness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"; clean = Path(raw) / "clean"
            subprocess.run(["/usr/bin/git", "init", "-q", str(root)], check=True)
            (root / "x").write_text("x")
            subprocess.run(["/usr/bin/git", "-C", str(root), "add", "x"], check=True)
            env = {**os.environ, "GIT_AUTHOR_NAME": "w", "GIT_AUTHOR_EMAIL": "w@x", "GIT_COMMITTER_NAME": "w", "GIT_COMMITTER_EMAIL": "w@x"}
            subprocess.run(["/usr/bin/git", "-C", str(root), "commit", "-qm", "x"], check=True, env=env)
            old_root, old_clean, old_formal = P.ROOT, P.CLEAN, P.FORMAL
            try:
                P.ROOT, P.CLEAN = str(root), str(clean)
                P.FORMAL = subprocess.check_output(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
                snapshot = P.route_snapshot()
                P.check_route(snapshot)
                subprocess.run([*P.PREFIX, "-C", P.ROOT, "worktree", "add", "--detach", P.CLEAN, P.FORMAL], check=True, env=P.ENV)
                P.check_route(snapshot)
                self.assertTrue(clean.is_dir())
                subprocess.run([*P.PREFIX, "-C", P.ROOT, "worktree", "remove", "--force", P.CLEAN], check=True, env=P.ENV)
                P.check_route(snapshot)
                self.assertFalse(clean.exists())
            finally:
                P.ROOT, P.CLEAN, P.FORMAL = old_root, old_clean, old_formal
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

    def test_fd_and_cleanup_classifiers(self) -> None:
        W.require_exact_fd_set({3, 4, 5})
        with self.assertRaises(W.WitnessFailure): W.require_exact_fd_set({0, 3, 4, 5})
        self.assertEqual(W.classify_cleanup(True, True, False), "CLEANUP_PASS")
        self.assertEqual(W.classify_cleanup(False, True, False), "ROLLBACK_INCOMPLETE")
        self.assertEqual(W.classify_cleanup(True, False, False), "ROLLBACK_INCOMPLETE")
        self.assertEqual(W.classify_cleanup(True, True, True), "ROLLBACK_INCOMPLETE")


if __name__ == "__main__": unittest.main()
