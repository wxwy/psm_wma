"""CPU-only regressions for the injected immutable collection seam."""
from __future__ import annotations
import unittest
import hashlib
import json
import pickle
from dataclasses import replace
import stat
from copy import deepcopy
from tools.psm_wma.immutable_source_collection import EntryStat, RollbackUnavailable, SELECTION_PATH, derive_candidates, _source_handoff
from tools.psm_wma.immutable_source_collection import COLLECTION_PATHS, RECEIPT_PATH, CandidateHandoff, CollectionError, MemoryEvidenceSink, OneShotHandoff, SOURCE_PATHS, SyntheticEntry, SyntheticRootFd, TemporaryGitFixture, _null_collection, _null_receipt, _sha, collect_synthetic, verify_evidence, verify_synthetic_rollback

class ImmutableSourceCollectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "schema": "canonical_native_local_ttt_config_v2", "local_memory_enabled": True,
            "local_memory_dim": 32, "local_history_enabled": True,
            "local_history_backend": "ttt_fast_weight", "local_history_evidence_dim": 106,
            "local_history_state_enabled": False, "local_ttt_enabled": True,
            "enable_input_bias": False, "ttt_tbptt_steps": 16, "ttt_inner_lr": 0.01,
            "k_local": 1, "local_evidence_feature_version": "causal_visual96_executed_action10_v1",
            "local_fast_state_dtype": "fp32", "local_runtime_resume_mode": "slow_only_no_mid_episode_resume",
        }
        self.config_raw = json.dumps(self.config, sort_keys=True, separators=(",", ":")).encode()
        self.paths = {name: f"fixture/{name}" for name in SOURCE_PATHS}
        self.fd = SyntheticRootFd({path: name.encode() for name, path in self.paths.items()})
        selection = {"schema": "immutable_source_selection_request_v1",
                     "source_kind": "checkpoint_source_manifest_v1",
                     "entries": [{"ordinal": i, "relative_path": path}
                                 for i, path in enumerate(sorted(self.paths.values()))]}
        selection_raw = json.dumps(selection, sort_keys=True, separators=(",", ":")).encode()
        def oid(raw: bytes) -> str:
            return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        self.authority = {
            "root_revision": "a" * 40, "selection_path": SELECTION_PATH,
            "selection_blob_native_oid": oid(selection_raw),
            "selection_raw_sha256": hashlib.sha256(selection_raw).hexdigest(),
            "config_path": COLLECTION_PATHS[1], "config_blob_native_oid": oid(self.config_raw),
            "config_raw_sha256": hashlib.sha256(self.config_raw).hexdigest(),
        }
        self.lineage = {"target_ref": "refs/heads/fixture", "expected_base_root_revision": "b" * 40,
                        "expected_child_gitlink": "c" * 40, "authority_approval_formal_root_revision": "d" * 40}
        self.git = TemporaryGitFixture(
            {"refs/heads/fixture": "b" * 40},
            parents={"a" * 40: "d" * 40},
            trees={"a" * 40: {"README.md": "e" * 40, "cosmos-framework": "c" * 40,
                             SELECTION_PATH: oid(selection_raw), COLLECTION_PATHS[1]: oid(self.config_raw)},
                   "d" * 40: {"README.md": "e" * 40, "cosmos-framework": "c" * 40}, "b" * 40: {}},
            blobs={oid(selection_raw): selection_raw, oid(self.config_raw): self.config_raw},
            gitlinks={"b" * 40: "c" * 40},
        )
    def test_exact_pass_evidence(self) -> None:
        sink = MemoryEvidenceSink(); record = collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths, git=self.git, root_fd=self.fd, sink=sink)
        self.assertEqual(record["status"], "PASS"); self.assertEqual(record["execution"]["phase"], "complete"); self.assertEqual(sink.records, [record])
    def test_retained_evidence_does_not_alias_returned_record(self) -> None:
        sink = MemoryEvidenceSink()
        record = collect_synthetic(authority=self.authority, lineage=self.lineage,
                                   paths=self.paths, git=self.git, root_fd=self.fd, sink=sink)
        retained = deepcopy(sink.records[0])
        record["execution"]["phase"] = "source_read"
        record["source_entries"][0]["sha256"] = "0" * 64
        self.assertEqual(sink.records, [retained])
        verify_evidence(sink.records[0])

    def test_pass_sink_failure_restores_transaction_or_fails_closed(self) -> None:
        class RejectingSink:
            def emit(self, record):
                verify_evidence(record)
                raise OSError("合成 sink 不可用")

        class FailedRollbackGit(TemporaryGitFixture):
            def rollback(self, snapshot):
                raise OSError("合成 rollback 不可用")

        for rollback_fails in (False, True):
            with self.subTest(rollback_fails=rollback_fails):
                git = deepcopy(self.git)
                if rollback_fails:
                    git = FailedRollbackGit(**vars(git))
                before = deepcopy(git.snapshot())
                expected = "ROLLBACK_INCOMPLETE" if rollback_fails else "EVIDENCE_SINK_FAILED"
                with self.assertRaisesRegex(CollectionError, expected):
                    collect_synthetic(authority=self.authority, lineage=self.lineage,
                                      paths=self.paths, git=git, root_fd=self.fd, sink=RejectingSink())
                self.assertEqual(len(git.commits), 2)
                if not rollback_fails:
                    self.assertEqual(git.snapshot(), before)
                    self.assertEqual(git.resolve(self.lineage["target_ref"]),
                                     self.lineage["expected_base_root_revision"])

    def test_authority_lineage_allowlist_drift_fails(self) -> None:
        with self.assertRaises(CollectionError): collect_synthetic(authority={**self.authority, "x": "x"}, lineage=self.lineage, paths=self.paths, git=self.git, root_fd=self.fd, sink=MemoryEvidenceSink())
        with self.assertRaises(CollectionError): collect_synthetic(authority=self.authority, lineage=self.lineage, paths={name: "same" for name in SOURCE_PATHS}, git=self.git, root_fd=self.fd, sink=MemoryEvidenceSink())
        bad_gitlink = deepcopy(self.git)
        bad_gitlink.gitlinks = {"b" * 40: "f" * 40}
        with self.assertRaises(CollectionError): collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths, git=bad_gitlink, root_fd=self.fd, sink=MemoryEvidenceSink())

    def test_atomic_sink_partial_and_after_write_leave_no_stale_pass(self) -> None:
        for stage in ("partial_write", "after_write"):
            with self.subTest(stage=stage):
                git = deepcopy(self.git)
                before = git.snapshot()
                sink = MemoryEvidenceSink(failure_stage=stage)
                with self.assertRaisesRegex(CollectionError, "EVIDENCE_SINK_FAILED"):
                    collect_synthetic(authority=self.authority, lineage=self.lineage,
                                      paths=self.paths, git=git, root_fd=self.fd, sink=sink)
                self.assertEqual(git.snapshot(), before)
                self.assertEqual(sink.records, [])
                self.assertEqual(len(git.commits), 2)
                sink.failure_stage = None
                record = collect_synthetic(authority=self.authority, lineage=self.lineage,
                                           paths=self.paths, git=git, root_fd=self.fd, sink=sink)
                sink.failure_stage = stage
                with self.assertRaises(OSError):
                    sink.emit(record)
                self.assertEqual(sink.records, [record])

    def test_unavailable_rollback_snapshot_is_non_authoritative_fail_stop(self) -> None:
        for invalid_snapshot in (False, True):
            for restore_raises in (False, True):
                class UnavailableSnapshot(TemporaryGitFixture):
                    def commit(self, paths, parent, blobs):
                        super().commit(paths, parent, blobs)
                        raise OSError("合成 commit 后失败")

                    def rollback(self, snapshot):
                        self.after_unavailable = True
                        if restore_raises:
                            raise OSError("合成 restore 失败")
                        return super().rollback(snapshot)

                    def snapshot(self):
                        if getattr(self, "after_unavailable", False):
                            if invalid_snapshot:
                                return {"unavailable": True}
                            raise OSError("合成 snapshot 无法读取")
                        return super().snapshot()

                with self.subTest(invalid=invalid_snapshot, restore_raises=restore_raises):
                    git = UnavailableSnapshot(**deepcopy(vars(self.git)))
                    sink = MemoryEvidenceSink()
                    with self.assertRaisesRegex(RollbackUnavailable, "^ROLLBACK_INCOMPLETE$") as raised:
                        collect_synthetic(authority=self.authority, lineage=self.lineage,
                                          paths=self.paths, git=git, root_fd=self.fd, sink=sink)
                    self.assertEqual(raised.exception.primary_phase, "collection")
                    self.assertEqual(sink.records, [])
                    self.assertEqual(len(git.commits), 1)
    def test_descriptor_and_digest_drift_fail(self) -> None:
        files = dict(self.fd.files); files[self.paths["checkpoint"]] = SyntheticEntry(b"x", reads=[b"x", b"y"])
        with self.assertRaises(CollectionError): collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths, git=self.git, root_fd=SyntheticRootFd(files), sink=MemoryEvidenceSink())
        files[self.paths["checkpoint"]] = SyntheticEntry(b"x", stats=[EntryStat(1, 1, 1, 0, 0), EntryStat(2, 1, 1, 0, 0)])
        with self.assertRaises(CollectionError): collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths, git=self.git, root_fd=SyntheticRootFd(files), sink=MemoryEvidenceSink())
        record = collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths, git=self.git, root_fd=self.fd, sink=MemoryEvidenceSink()); record["status"] = "FAIL"
        with self.assertRaises(CollectionError): verify_evidence(record)
    def test_escape_and_transaction_allowlist_fail(self) -> None:
        with self.assertRaises(CollectionError): SyntheticRootFd({}).open_regular("../escape")
        with self.assertRaises(CollectionError): self.git.commit(("wrong",), "b" * 40, {})
        with self.assertRaisesRegex(CollectionError, "component is a symlink"):
            SyntheticRootFd({}, frozenset({"fixture"})).open_regular("fixture/checkpoint")
        with self.assertRaisesRegex(CollectionError, "non-regular"):
            SyntheticRootFd({"fixture/checkpoint": "directory"}).open_regular("fixture/checkpoint")

    def test_every_fstat_field_drift_closes_handle(self) -> None:
        before = EntryStat(1, 1, 1, 0, 0)
        for field_name in ("device", "inode", "size", "mtime_ns", "ctime_ns"):
            with self.subTest(field=field_name):
                after = replace(before, **{field_name: getattr(before, field_name) + 1})
                entry = SyntheticEntry(b"x", stats=[before, after, after])
                files = {**self.fd.files, self.paths["checkpoint"]: entry}
                with self.assertRaises(CollectionError):
                    collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                                      git=self.git, root_fd=SyntheticRootFd(files), sink=MemoryEvidenceSink())
                self.assertTrue(entry.closed)
        nonregular = SyntheticEntry(b"x", identity=replace(before, mode=stat.S_IFDIR))
        with self.assertRaises(CollectionError):
            collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                git=self.git, root_fd=SyntheticRootFd({**self.fd.files, self.paths["checkpoint"]: nonregular}), sink=MemoryEvidenceSink())
        self.assertTrue(nonregular.closed)

    def test_streamed_source_hash_and_successful_close(self) -> None:
        data = b"abc" * 50000
        entry = SyntheticEntry(data)
        record = collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
            git=self.git, root_fd=SyntheticRootFd({**self.fd.files, self.paths["checkpoint"]: entry}), sink=MemoryEvidenceSink())
        self.assertEqual(record["source_entries"][0], {"ordinal": 0, "byte_length": len(data),
                                                     "sha256": hashlib.sha256(data).hexdigest()})
        self.assertTrue(entry.closed)
    def test_committed_tree_relookup_drift_fails(self) -> None:
        class DriftingGit(TemporaryGitFixture):
            def lookup(self, revision: str) -> dict[str, str]:
                return {**super().lookup(revision), "tree_native_oid": "d" * 40}
        with self.assertRaises(CollectionError):
            collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths, git=DriftingGit(**vars(self.git)), root_fd=self.fd, sink=MemoryEvidenceSink())

    def test_raw_blob_transaction_and_receipt_binding(self) -> None:
        record = collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                                   git=self.git, root_fd=self.fd, sink=MemoryEvidenceSink())
        collection, receipt = record["collection"], record["receipt"]
        self.assertEqual(collection["parent_revision"], "b" * 40)
        self.assertEqual(receipt["parent_revision"], collection["revision"])
        collection_tree = self.git.tree_entries(collection["revision"])
        receipt_tree = self.git.tree_entries(receipt["revision"])
        self.assertEqual(set(collection_tree), set(COLLECTION_PATHS))
        self.assertEqual(set(receipt_tree) - set(collection_tree), {RECEIPT_PATH})
        raw = self.git.blob_bytes(receipt_tree[RECEIPT_PATH])
        value = json.loads(raw)
        self.assertEqual(value["schema"], "immutable_source_collection_receipt_v1")
        self.assertEqual(value["collection_formal_root_revision"], collection["revision"])
        self.assertEqual(value["source_input_artifact_path"], "docs/build/PSM-WMA_immutable_source_input_descriptor_v1.json")
        self.assertEqual(value["source_input_artifact_blob_native_oid"], collection_tree[value["source_input_artifact_path"]])
        for prefix in ("collection_artifact", "source_input_artifact", "source_manifest_artifact",
                       "checkpoint_source_descriptor_artifact", "canonical_model_config_artifact"):
            path = value[prefix + "_path"]
            blob = self.git.blob_bytes(collection_tree[path])
            self.assertEqual(value[prefix + "_sha256"], hashlib.sha256(blob).hexdigest())
            self.assertEqual(value[prefix + "_blob_native_oid"], hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest())
        self.assertEqual(self.git.resolve(self.lineage["target_ref"]), receipt["revision"])

    def test_preflight_failure_has_zero_live_mutations(self) -> None:
        class FailedPreflight(TemporaryGitFixture):
            def preflight(self, paths, parent, blobs):
                super().preflight(paths, parent, blobs)
                raise CollectionError("INJECTED_PREFLIGHT_FAILURE")
        git = FailedPreflight(**deepcopy(vars(self.git)))
        before = git.snapshot()
        with self.assertRaisesRegex(CollectionError, "INJECTED_PREFLIGHT_FAILURE"):
            collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                              git=git, root_fd=self.fd, sink=MemoryEvidenceSink())
        self.assertEqual(git.snapshot(), before)
        self.assertEqual(git.commits, [])

    def test_partial_collection_and_receipt_failures_restore_snapshot(self) -> None:
        for failed_paths in (COLLECTION_PATHS, (RECEIPT_PATH,)):
            class PartialCommit(TemporaryGitFixture):
                def commit(self, paths, parent, blobs):
                    row = super().commit(paths, parent, blobs)
                    if paths == failed_paths:
                        raise CollectionError("INJECTED_PARTIAL_COMMIT")
                    return row
            with self.subTest(paths=failed_paths):
                git = PartialCommit(**deepcopy(vars(self.git)))
                before = git.snapshot()
                sink = MemoryEvidenceSink()
                with self.assertRaisesRegex(CollectionError, "INJECTED_PARTIAL_COMMIT"):
                    collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                                      git=git, root_fd=self.fd, sink=sink)
                self.assertEqual(git.snapshot(), before)
                self.assertEqual(git.resolve(self.lineage["target_ref"]), self.lineage["expected_base_root_revision"])
                self.assertEqual(len(sink.records), 1)
                failure = sink.records[0]
                self.assertEqual(failure["status"], "FAIL")
                self.assertEqual(failure["execution"]["phase"], "collection" if failed_paths == COLLECTION_PATHS else "receipt")
                self.assertTrue(failure["rollback"]["verified"])
                verify_evidence(failure)

    def test_incomplete_rollback_fail_stops(self) -> None:
        class FailedRollback(TemporaryGitFixture):
            def commit(self, paths, parent, blobs):
                super().commit(paths, parent, blobs)
                raise CollectionError("INJECTED_PARTIAL_COMMIT")
            def rollback(self, snapshot):
                return self.snapshot()
        git = FailedRollback(**deepcopy(vars(self.git)))
        sink = MemoryEvidenceSink()
        with self.assertRaisesRegex(CollectionError, "ROLLBACK_INCOMPLETE"):
            collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                              git=git, root_fd=self.fd, sink=sink)
        failure = sink.records[0]
        self.assertEqual(failure["execution"]["phase"], "collection")
        self.assertEqual(failure["execution"]["failure_code"], "ROLLBACK_INCOMPLETE")
        self.assertIs(failure["rollback"]["verified"], False)
        verify_evidence(failure)

    def test_source_failure_emits_completed_prefix_without_paths(self) -> None:
        files = dict(self.fd.files)
        del files[self.paths["manifest"]]
        sink = MemoryEvidenceSink()
        with self.assertRaises(CollectionError):
            collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                              git=self.git, root_fd=SyntheticRootFd(files), sink=sink)
        failure = sink.records[0]
        self.assertEqual(failure["execution"]["phase"], "source_read")
        self.assertEqual([row["ordinal"] for row in failure["source_entries"]], [0, 1])
        self.assertTrue(all(value is None for value in failure["candidates"].values()))
        self.assertTrue(all(value is None for value in failure["rollback"].values()))
        self.assertEqual(self.git.commits, [])
        verify_evidence(failure)
        serialized = json.dumps(failure)
        for path in self.paths.values():
            self.assertNotIn(path, serialized)

    def test_observed_execution_identity_drift_fails_before_source(self) -> None:
        for section, key, bad in (("tool", "raw_sha256", "e" * 64),
                                  ("execution", "command_argv", ["wrong"]),
                                  ("environment", "cpu_only", False)):
            class Drift(TemporaryGitFixture):
                def execution_metadata(self):
                    metadata = super().execution_metadata()
                    metadata[section][key] = bad
                    return metadata
            class Unopened:
                def open_regular(self, path):
                    raise AssertionError("identity 失败不得读取 source")
            with self.subTest(section=section):
                sink = MemoryEvidenceSink()
                git = Drift(**deepcopy(vars(self.git)))
                with self.assertRaises(CollectionError):
                    collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                                      git=git, root_fd=Unopened(), sink=sink)
                failure = sink.records[0]
                self.assertEqual(failure["execution"]["phase"], "environment" if section == "environment" else "tool_identity")
                verify_evidence(failure)
                self.assertEqual(git.commits, [])

    def test_publication_violation_and_observation_failure_rollback(self) -> None:
        for observation, phase in (({"pushed": True, "published": False}, "push_publication"),
                                    ({"pushed": 1, "published": False}, "post_check")):
            class Published(TemporaryGitFixture):
                def publication_state(self):
                    return observation
            with self.subTest(observation=observation):
                git = Published(**deepcopy(vars(self.git)))
                before = git.snapshot()
                sink = MemoryEvidenceSink()
                with self.assertRaises(CollectionError):
                    collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                                      git=git, root_fd=self.fd, sink=sink)
                failure = sink.records[0]
                self.assertEqual(failure["execution"]["phase"], phase)
                self.assertEqual(git.snapshot(), before)
                self.assertIs(failure["rollback"]["verified"], True)
                verify_evidence(failure)

    def test_frozen_candidate_paths_and_raw_byte_chain(self) -> None:
        entries = ({"ordinal": 0, "byte_length": 3, "sha256": hashlib.sha256(b"abc").hexdigest()},)
        artifacts, digests = derive_candidates(entries, self.config_raw)
        blobs = dict(artifacts)
        expected_paths = {
            "docs/build/PSM-WMA_immutable_source_collection_v1.json",
            "docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json",
            "docs/build/PSM-WMA_immutable_source_input_descriptor_v1.json",
            "docs/build/PSM-WMA_immutable_source_manifest_v1.json",
            "docs/build/PSM-WMA_immutable_source_checkpoint_descriptor_v1.json",
        }
        self.assertEqual(set(blobs), expected_paths)
        input_raw = blobs["docs/build/PSM-WMA_immutable_source_input_descriptor_v1.json"]
        manifest_raw = blobs["docs/build/PSM-WMA_immutable_source_manifest_v1.json"]
        input_value, manifest = json.loads(input_raw), json.loads(manifest_raw)
        self.assertEqual(set(input_value), {"schema", "source_kind", "source_entries"})
        self.assertEqual(set(manifest), {"schema", "source_kind", "source_entries", "source_input_sha256"})
        self.assertEqual(input_value["source_entries"], list(entries))
        self.assertEqual(manifest["source_entries"], list(entries))
        self.assertEqual(manifest["source_input_sha256"], hashlib.sha256(input_raw).hexdigest())
        identifier_raw = json.dumps({"schema": "immutable_source_identifier_v1",
            "source_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "source_input_sha256": hashlib.sha256(input_raw).hexdigest()},
            sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(digests["identifier_sha256"], hashlib.sha256(identifier_raw).hexdigest())
        descriptor_raw = blobs["docs/build/PSM-WMA_immutable_source_checkpoint_descriptor_v1.json"]
        descriptor = json.loads(descriptor_raw)
        self.assertEqual(set(descriptor), {"schema", "source_kind", "immutable_source_identifier", "source_manifest_sha256", "source_input_sha256"})
        self.assertEqual(descriptor["immutable_source_identifier"], digests["identifier_sha256"])
        collection = json.loads(blobs["docs/build/PSM-WMA_immutable_source_collection_v1.json"])
        self.assertEqual(collection["checkpoint_source_descriptor_sha256"], hashlib.sha256(descriptor_raw).hexdigest())
        self.assertEqual(blobs["docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json"], self.config_raw)
        for value in blobs.values():
            self.assertEqual(value, json.dumps(json.loads(value), sort_keys=True, separators=(",", ":")).encode())

    def test_candidate_rejects_invalid_entries_and_config(self) -> None:
        valid = {"ordinal": 0, "byte_length": 1, "sha256": hashlib.sha256(b"x").hexdigest()}
        for key, value in (("ordinal", True), ("byte_length", False), ("byte_length", 0), ("sha256", "X" * 64)):
            with self.subTest(key=key, value=value), self.assertRaises(CollectionError):
                derive_candidates(({**valid, key: value},), self.config_raw)
        with self.assertRaises(CollectionError):
            derive_candidates((valid,), json.dumps(self.config, indent=2).encode())
        with self.assertRaises(CollectionError):
            derive_candidates((valid,), b"{}")

    def test_config_failure_precedes_source_open(self) -> None:
        class UnopenedSource:
            def open_regular(self, path: str) -> object:
                self.fail_open = True
                raise AssertionError("config 失败前不应打开 source")
        source = UnopenedSource()
        for raw in (b"{}", self.config_raw + b"\n"):
            with self.subTest(raw=raw):
                oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                self.git.blobs[oid] = raw
                self.git.trees["a" * 40][COLLECTION_PATHS[1]] = oid
                self.authority["config_blob_native_oid"] = oid
                self.authority["config_raw_sha256"] = hashlib.sha256(raw).hexdigest()
                with self.assertRaises(CollectionError):
                    collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                                      git=self.git, root_fd=source, sink=MemoryEvidenceSink())
                self.assertFalse(hasattr(source, "fail_open"))

    def test_authority_object_drift_precedes_all_source_reads(self) -> None:
        class UnopenedSource:
            def open_regular(self, path: str) -> object:
                raise AssertionError("authority 检查失败时不得读取 source")

        cases = []
        git = deepcopy(self.git)
        git.trees["d" * 40][SELECTION_PATH] = self.authority["selection_blob_native_oid"]
        cases.append((git, self.authority, "两个固定"))
        for path in ("README.md", "cosmos-framework"):
            for removed in (True, False):
                git = deepcopy(self.git)
                if removed:
                    del git.trees["a" * 40][path]
                else:
                    git.trees["a" * 40][path] = "f" * 40
                cases.append((git, self.authority, "两个固定"))
        git = deepcopy(self.git)
        git.parents["a" * 40] = "e" * 40
        cases.append((git, self.authority, "parent"))
        git = deepcopy(self.git)
        git.trees["a" * 40]["extra.json"] = "e" * 40
        cases.append((git, self.authority, "两个固定"))
        git = deepcopy(self.git)
        git.trees["a" * 40][SELECTION_PATH] = "e" * 40
        cases.append((git, self.authority, "tree/blob"))
        git = deepcopy(self.git)
        git.blobs[self.authority["selection_blob_native_oid"]] += b" "
        cases.append((git, self.authority, "raw bytes"))
        git = deepcopy(self.git)
        git.revisions[self.lineage["target_ref"]] = "e" * 40
        cases.append((git, self.authority, "ref/base"))
        git = deepcopy(self.git)
        git.gitlinks["b" * 40] = "e" * 40
        cases.append((git, self.authority, "Gitlink"))
        cases.append((self.git, {**self.authority, "selection_path": "wrong.json"}, "固定路径"))
        cases.append((self.git, {**self.authority, "selection_raw_sha256": "e" * 64}, "raw bytes"))
        for git, authority, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(CollectionError, reason):
                    collect_synthetic(authority=authority, lineage=self.lineage, paths=self.paths,
                                      git=git, root_fd=UnopenedSource(), sink=MemoryEvidenceSink())
                self.assertEqual(git.commits, [])

    def test_authority_delta_preserves_parent_and_postcheck_revalidates(self) -> None:
        git = deepcopy(self.git)
        # 两个路径也允许是实际修改，而不仅是新建；继承项必须完整保留。
        git.trees["d" * 40].update({SELECTION_PATH: "f" * 40, COLLECTION_PATHS[1]: "f" * 40})
        result = collect_synthetic(authority=self.authority, lineage=self.lineage,
                                   paths=self.paths, git=git, root_fd=self.fd, sink=MemoryEvidenceSink())
        self.assertEqual(result["status"], "PASS")

        class LateAuthorityDrift(TemporaryGitFixture):
            def commit(self, paths, parent, blobs):
                row = super().commit(paths, parent, blobs)
                if paths == (RECEIPT_PATH,):
                    self.trees["a" * 40]["README.md"] = "f" * 40
                return row

        git = LateAuthorityDrift(**deepcopy(vars(self.git)))
        before = git.snapshot()
        sink = MemoryEvidenceSink()
        with self.assertRaisesRegex(CollectionError, "post-check 失败: authority"):
            collect_synthetic(authority=self.authority, lineage=self.lineage,
                              paths=self.paths, git=git, root_fd=self.fd, sink=sink)
        self.assertEqual(git.snapshot(), before)
        self.assertIs(sink.records[0]["post_checks"]["authority"], False)

    def test_handoff_rejects_changed_candidate_bytes(self) -> None:
        activation = object()
        entries = ({"ordinal": 0, "byte_length": 1, "sha256": hashlib.sha256(b"x").hexdigest()},)
        handoff = _source_handoff(self.authority, entries, self.config_raw, activation)
        handoff._artifacts = ((COLLECTION_PATHS[0], b"{}"),) + handoff._artifacts[1:]
        with self.assertRaises(CollectionError):
            handoff.take(activation)
        with self.assertRaises(CollectionError):
            handoff.take(activation)

    def test_canonical_roundtrip_does_not_depend_on_dict_order(self) -> None:
        record = collect_synthetic(authority=json.loads(json.dumps(self.authority, sort_keys=True)),
                                  lineage=json.loads(json.dumps(self.lineage, sort_keys=True)),
                                  paths=self.paths, git=self.git, root_fd=self.fd, sink=MemoryEvidenceSink())
        verify_evidence(json.loads(json.dumps(record, sort_keys=True)))
    def test_handoff_and_retained_rollback_are_one_shot(self) -> None:
        activation = object()
        entries = ({"ordinal": 0, "byte_length": 1, "sha256": hashlib.sha256(b"x").hexdigest()},)
        handoff = _source_handoff(self.authority, entries, self.config_raw, activation)
        with self.assertRaises(CollectionError):
            OneShotHandoff()
        with self.assertRaises(CollectionError):
            handoff.take(object())
        with self.assertRaises(CollectionError):
            pickle.dumps(handoff)
        bundle = handoff.take(activation)
        self.assertEqual(bundle.source_entries, entries)
        self.assertEqual(dict(bundle.artifact_bytes)[COLLECTION_PATHS[1]], self.config_raw)
        with self.assertRaises(CollectionError): handoff.take(activation)
        paths = sorted((*COLLECTION_PATHS, RECEIPT_PATH), key=lambda path: path.encode())
        worktree = [{"path": path, "mode": "100644", "kind": "regular", "sha256": "a" * 64} for path in paths]
        snapshot = {"target_ref": "refs/heads/V2", "target_ref_revision": "a" * 40, "head_mode": "symbolic", "head_symbolic_ref": "refs/heads/V2", "head_revision": "b" * 40, "index_tree_native_oid": "c" * 40, "worktree_entries": worktree, "worktree_sha256": _sha(worktree)}
        witness = verify_synthetic_rollback(snapshot, dict(snapshot), completed=True)
        self.assertTrue(witness["verified"])
        with self.assertRaisesRegex(CollectionError, "ROLLBACK_INCOMPLETE"):
            verify_synthetic_rollback(snapshot, {**snapshot, "target_ref": "other"}, completed=True)
        with self.assertRaises(CollectionError):
            verify_synthetic_rollback({**snapshot, "head_mode": "detached", "head_symbolic_ref": "refs/heads/V2"}, snapshot, completed=True)
        # canonical JSON 解码按 key 排序，字典插入顺序不应成为合同的一部分。
        reordered = json.loads(json.dumps(snapshot, sort_keys=True))
        self.assertTrue(verify_synthetic_rollback(reordered, snapshot, completed=True)["verified"])
        with self.assertRaises(CollectionError):
            verify_synthetic_rollback({**snapshot, "worktree_sha256": "f" * 64}, snapshot, completed=True)
        with self.assertRaises(CollectionError):
            verify_synthetic_rollback({**snapshot, "head_revision": "z" * 40}, snapshot, completed=True)
    def test_fail_phase_nullability_is_checked(self) -> None:
        record = collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths, git=self.git, root_fd=self.fd, sink=MemoryEvidenceSink())
        record["status"] = "FAIL"; record["execution"] = {**record["execution"], "phase": "authority", "failure_code": "AUTHORITY_DRIFT"}; record["source_entries"] = []; record["collection"] = _null_collection(); record["receipt"] = _null_receipt(); record["evidence_sha256"] = _sha({key: value for key, value in record.items() if key != "evidence_sha256"})
        for name in ("authority", "lineage", "handoff", "candidates", "post_checks", "push_publication"):
            record[name] = {key: None for key in record[name]}
        record["evidence_sha256"] = _sha({key: value for key, value in record.items() if key != "evidence_sha256"})
        verify_evidence(record)
        record["source_entries"] = [{"ordinal": 0}]; record["evidence_sha256"] = _sha({key: value for key, value in record.items() if key != "evidence_sha256"})
        with self.assertRaises(CollectionError): verify_evidence(record)

    def test_all_failure_phases_follow_frozen_reachability(self) -> None:
        passed = collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                                   git=self.git, root_fd=self.fd, sink=MemoryEvidenceSink())
        phases = ("tool_identity", "environment", "authority", "lineage", "source_read",
                  "candidate_construction", "candidate_verification", "collection", "receipt",
                  "post_check", "push_publication")
        worktree = [{"path": path, "mode": None, "kind": "absent", "sha256": None}
                    for path in sorted((*COLLECTION_PATHS, RECEIPT_PATH))]
        snapshot = {"target_ref": "refs/heads/fixture", "target_ref_revision": "b" * 40,
                    "head_mode": "symbolic", "head_symbolic_ref": "refs/heads/fixture",
                    "head_revision": "b" * 40, "index_tree_native_oid": "c" * 40,
                    "worktree_entries": worktree, "worktree_sha256": _sha(worktree)}
        for index, phase in enumerate(phases):
            with self.subTest(phase=phase):
                value = deepcopy(passed)
                value["status"] = "FAIL"
                value["execution"].update(phase=phase, failure_code="INJECTED_FAILURE")
                for i, section in enumerate(("tool", "environment", "authority", "lineage")):
                    if index <= i:
                        value[section] = {key: None for key in value[section]}
                if index < 4:
                    value["source_entries"] = []
                if index < 6:
                    value["handoff"] = {key: None for key in value["handoff"]}
                    value["candidates"] = {key: None for key in value["candidates"]}
                if index <= 7:
                    value["collection"] = _null_collection()
                if index <= 8:
                    value["receipt"] = _null_receipt()
                if index < 9:
                    value["post_checks"] = {key: None for key in value["post_checks"]}
                if index == 9:
                    value["post_checks"] = {"authority": True, "lineage": False,
                                            "derivation": None, "collection": None, "receipt": None}
                if index < 10:
                    value["push_publication"] = {"pushed": None, "published": None}
                else:
                    value["push_publication"] = {"pushed": True, "published": False}
                if index >= 7:
                    value["rollback"] = verify_synthetic_rollback(snapshot, snapshot, completed=True)
                value["evidence_sha256"] = _sha({key: item for key, item in value.items() if key != "evidence_sha256"})
                verify_evidence(json.loads(json.dumps(value, sort_keys=True)))
                # 外层摘要重新签名也不能掩盖不允许的后续状态或缺失 key。
                bad = deepcopy(value)
                if index < 6:
                    bad["handoff"]["consumed_once"] = True
                elif index < 9:
                    bad["post_checks"]["authority"] = True
                elif index == 9:
                    bad["post_checks"]["lineage"] = 0
                else:
                    bad["push_publication"]["pushed"] = 1
                bad["evidence_sha256"] = _sha({key: item for key, item in bad.items() if key != "evidence_sha256"})
                with self.assertRaises(CollectionError):
                    verify_evidence(bad)

    def test_resigned_pass_nested_type_drift_is_rejected(self) -> None:
        passed = collect_synthetic(authority=self.authority, lineage=self.lineage, paths=self.paths,
                                   git=self.git, root_fd=self.fd, sink=MemoryEvidenceSink())
        for section, field_name, replacement in (("environment", "cpu_only", 1),
                ("tool", "raw_sha256", "X" * 64), ("handoff", "consumed_once", 1),
                ("post_checks", "authority", 1), ("collection", "delta_paths", ["wrong"]),
                ("receipt", "blob_native_oid", "q" * 40)):
            with self.subTest(section=section, field=field_name):
                value = deepcopy(passed)
                value[section][field_name] = replacement
                value["evidence_sha256"] = _sha({key: item for key, item in value.items() if key != "evidence_sha256"})
                with self.assertRaises(CollectionError):
                    verify_evidence(value)

if __name__ == "__main__": unittest.main()
