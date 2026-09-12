"""CPU-only regressions for immutable_source_collection's injected seam."""

from __future__ import annotations

import unittest

from tools.psm_wma.immutable_source_collection import (
    CollectionError, MemoryEvidenceSink, SOURCE_PATHS, SyntheticRootFd,
    TemporaryGitFixture, collect_synthetic,
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


if __name__ == "__main__":
    unittest.main()
