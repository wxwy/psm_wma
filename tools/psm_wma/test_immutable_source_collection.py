"""CPU-only regressions for immutable_source_collection's injected seam."""

from __future__ import annotations

import unittest

from tools.psm_wma.immutable_source_collection import (
    CollectionError, MemoryEvidenceSink, SOURCE_PATHS, SyntheticRootFd,
    OneShotHandoff, TemporaryGitFixture, collect_synthetic, verify_synthetic_rollback,
)


class ImmutableSourceCollectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = {"formal_root": "root", "formal_child": "child", "base": "b", "target": "t"}
        self.paths = {name: f"fixture/{name}.bin" for name in SOURCE_PATHS}
        self.git = TemporaryGitFixture({"base": "b", "target": "t"})
        self.fd = SyntheticRootFd({path: name.encode() for name, path in self.paths.items()})

    def test_pass_record_has_exact_contract(self) -> None:
        sink = MemoryEvidenceSink()
        record = collect_synthetic(authority=self.authority, paths=self.paths, git=self.git, root_fd=self.fd, sink=sink)
        self.assertEqual(set(record), {"schema_version", "phase", "status", "authority", "candidate", "snapshot"})
        self.assertEqual(record["status"], "PASS")
        self.assertEqual(sink.records, [record])

    def test_authority_lineage_and_allowlist_drift_fail(self) -> None:
        for authority, paths in (({**self.authority, "extra": "x"}, self.paths),
                                 (self.authority, {name: "same" for name in SOURCE_PATHS})):
            with self.subTest(authority=authority, paths=paths), self.assertRaises(CollectionError):
                collect_synthetic(authority=authority, paths=paths, git=self.git, root_fd=self.fd, sink=MemoryEvidenceSink())
        with self.assertRaises(CollectionError):
            collect_synthetic(authority=self.authority, paths=self.paths,
                              git=TemporaryGitFixture({"base": "wrong", "target": "t"}), root_fd=self.fd, sink=MemoryEvidenceSink())

    def test_fd_escape_missing_and_nonregular_fail(self) -> None:
        for path in ("../escape", "/absolute", "missing"):
            with self.subTest(path=path), self.assertRaises(CollectionError):
                SyntheticRootFd({}).read_regular(path)
        with self.assertRaises(CollectionError):
            SyntheticRootFd({"regular": b"x", "dir": "not-bytes"}).read_regular("dir")

    def test_same_fd_race_and_single_use_handoff_fail(self) -> None:
        class RacingFd(SyntheticRootFd):
            reads = 0

            def read_regular(self, relative_path: str) -> bytes:
                self.reads += 1
                value = super().read_regular(relative_path)
                return value if self.reads <= len(SOURCE_PATHS) else value + b"drift"

        with self.assertRaises(CollectionError):
            collect_synthetic(authority=self.authority, paths=self.paths, git=self.git,
                              root_fd=RacingFd(self.fd.files), sink=MemoryEvidenceSink())
        handoff = OneShotHandoff()
        record = collect_synthetic(authority=self.authority, paths=self.paths, git=self.git,
                                   root_fd=self.fd, sink=MemoryEvidenceSink())
        self.assertEqual(handoff.take(record)["status"], "PASS")
        with self.assertRaises(CollectionError):
            handoff.take(record)

    def test_retained_snapshot_rollback_contract(self) -> None:
        snapshot = {"target": "t", "worktree": "digest"}
        verify_synthetic_rollback(snapshot, dict(snapshot), completed=True)
        with self.assertRaisesRegex(CollectionError, "snapshot mismatch"):
            verify_synthetic_rollback(snapshot, {"target": "other"}, completed=True)
        with self.assertRaisesRegex(CollectionError, "ROLLBACK_INCOMPLETE"):
            verify_synthetic_rollback(snapshot, snapshot, completed=False)


if __name__ == "__main__":
    unittest.main()
