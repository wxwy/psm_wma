"""CPU-only temporary-repository coverage for the native authority adapter."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.psm_wma.materialize_immutable_source_authority_root import NativeAuthorityGit, write_pending_evidence


class NativeAuthorityGitTest(unittest.TestCase):
    def test_pending_evidence_unlinks_only_through_commit(self):
        class Commit:
            def __init__(self): self.callback = None
            def seal_for_guard(self, callback): self.callback = callback
            def consume_by_unlink(self): self.callback()
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            write_pending_evidence(path, {"status": "PASS"}, Commit())
            self.assertTrue(path.is_file())
            self.assertFalse(path.with_name("evidence.json.pending").exists())

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
            tx = NativeAuthorityGit(git, root, str(remote), root / "temporary.index")
            parent = tx._run("rev-parse", "HEAD")
            revision = tx.create_detached_commit(parent, {"proof.json": b"{}"})
            self.assertEqual(tx.parents(revision), (parent,))
            self.assertTrue(tx.cas_create_local("refs/heads/test", revision))
            self.assertTrue(tx.cas_create_remote("refs/heads/test", revision))
            self.assertTrue(tx.cas_delete_remote("refs/heads/test", revision))
            self.assertTrue(tx.cas_delete_local("refs/heads/test", revision))


if __name__ == "__main__":
    unittest.main()
