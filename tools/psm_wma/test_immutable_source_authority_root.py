"""CPU-only tests for authority-root preparation, verification and publication."""

from __future__ import annotations
import hashlib
import json
import pickle
import shutil
import tempfile
import unittest
from copy import copy, deepcopy
from pathlib import Path

from tools.psm_wma.immutable_source_authority_root import (
    AuthorityBinding,
    AuthorityCandidate,
    EvidenceCleanupIncomplete,
    EvidenceCommit,
    AuthorityRequest,
    AuthorityRootError,
    PostCommitFinalizerError,
    RollbackIncomplete,
    prepare_candidate,
    publish_candidate,
    verify_candidate,
)
from tools.psm_wma.immutable_source_collection import (
    AUTHORITY_REF,
    CollectionError,
    MemoryEvidenceSink,
    SELECTION_PATH,
    SyntheticRootFd,
    TemporaryGitFixture,
    collect_synthetic,
)


def oid(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


class Git:
    def __init__(self):
        self.root, self.child = "a" * 40, "c" * 40
        self.trees = {
            self.root: {
                "README.md": ("100644", "blob", "e" * 40),
                "cosmos-framework": ("160000", "commit", self.child),
            }
        }
        self.parent_lists, self.blobs = {}, {}
        self.local, self.remote = {}, {}
        self.events, self.hook = [], None

    def tree_entries(self, revision):
        return self.trees[revision]

    def parents(self, revision):
        return self.parent_lists[revision]

    def blob_bytes(self, value):
        return self.blobs[value]

    def gitlink_at(self, revision):
        return self.trees[revision]["cosmos-framework"][2]

    def create_detached_commit(self, parent, blobs):
        tree = dict(self.trees[parent])
        tree.update({p: ("100644", "blob", oid(v)) for p, v in blobs.items()})
        revision = hashlib.sha1(json.dumps(tree, sort_keys=True).encode()).hexdigest()
        self.trees[revision], self.parent_lists[revision] = tree, (parent,)
        self.blobs.update({oid(raw): raw for raw in blobs.values()})
        return revision

    def local_ref(self, ref):
        self.events.append("read_local")
        return self.local.get(ref)

    def remote_ref(self, ref):
        self.events.append("read_remote")
        return self.remote.get(ref)

    def _create(self, endpoint, ref, revision):
        values = getattr(self, endpoint)
        self.events.append("create_" + endpoint)
        if values.get(ref) is not None:
            return False
        values[ref] = revision
        if self.hook:
            self.hook("after_create_" + endpoint, self, revision)
        return True

    def cas_create_local(self, ref, revision):
        return self._create("local", ref, revision)

    def cas_create_remote(self, ref, revision):
        return self._create("remote", ref, revision)

    def _delete(self, endpoint, ref, revision):
        values = getattr(self, endpoint)
        self.events.append("delete_" + endpoint)
        if self.hook:
            self.hook("before_delete_" + endpoint, self, revision)
        if values.get(ref) != revision:
            return False
        del values[ref]
        return True

    def cas_delete_local(self, ref, revision):
        return self._delete("local", ref, revision)

    def cas_delete_remote(self, ref, revision):
        return self._delete("remote", ref, revision)


class AuthorityRootTest(unittest.TestCase):
    def _seal_commit(self, witness, commit):
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        evidence = directory / "evidence.json"
        guard = directory / "evidence.json.pending"
        evidence.write_text(json.dumps({"evidence_sha256": "a" * 64}))
        guard.write_bytes(b"")
        commit.seal_for_guard(witness, guard, evidence, "a" * 64)
        return guard

    def setUp(self):
        selection = {
            "schema": "immutable_source_selection_request_v1",
            "source_kind": "checkpoint_source_manifest_v1",
            "entries": [{"ordinal": 0, "relative_path": "fixture/checkpoint"}],
        }
        config = {
            "schema": "canonical_native_local_ttt_config_v2",
            "local_memory_enabled": True,
            "local_memory_dim": 32,
            "local_history_enabled": True,
            "local_history_backend": "ttt_fast_weight",
            "local_history_evidence_dim": 106,
            "local_history_state_enabled": False,
            "local_ttt_enabled": True,
            "enable_input_bias": False,
            "ttt_tbptt_steps": 16,
            "ttt_inner_lr": 0.01,
            "k_local": 1,
            "local_evidence_feature_version": "causal_visual96_executed_action10_v1",
            "local_fast_state_dtype": "fp32",
            "local_runtime_resume_mode": "slow_only_no_mid_episode_resume",
        }

        def raw(value):
            return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

        self.git = Git()
        self.request = AuthorityRequest(
            self.git.root, self.git.child, raw(selection), raw(config)
        )

    def candidate(self):
        candidate = prepare_candidate(self.request, self.git)
        return candidate, verify_candidate(self.request, candidate, self.git)

    def test_prepare_verify_and_publish(self):
        candidate, binding = self.candidate()
        result = publish_candidate(self.request, candidate, binding, self.git)
        self.assertEqual(result.revision, candidate.revision)
        self.assertEqual(self.git.local[AUTHORITY_REF], candidate.revision)
        self.assertEqual(self.git.remote[AUTHORITY_REF], candidate.revision)
        self.assertLess(
            self.git.events.index("create_local"),
            self.git.events.index("create_remote"),
        )
        self.assertEqual(
            tuple(binding.as_mapping()),
            (
                "root_revision",
                "selection_path",
                "selection_blob_native_oid",
                "selection_raw_sha256",
                "config_path",
                "config_blob_native_oid",
                "config_raw_sha256",
            ),
        )

    def test_noncanonical_and_parent_fixed_path_fail_before_commit(self):
        bad = AuthorityRequest(
            self.git.root,
            self.git.child,
            self.request.selection_raw + b"\n",
            self.request.config_raw,
        )
        with self.assertRaises(AuthorityRootError):
            prepare_candidate(bad, self.git)
        self.assertEqual(self.git.parent_lists, {})
        self.git.trees[self.git.root][SELECTION_PATH] = ("100644", "blob", "f" * 40)
        with self.assertRaises(AuthorityRootError):
            prepare_candidate(self.request, self.git)

    def test_verifier_rejects_parent_delta_and_blob_drift(self):
        candidate, _ = self.candidate()
        for mutation in ("parent", "extra", "blob", "inherited", "fixed_mode"):
            git = deepcopy(self.git)
            if mutation == "parent":
                git.parent_lists[candidate.revision] = ("f" * 40,)
            elif mutation == "extra":
                git.trees[candidate.revision]["extra"] = ("100644", "blob", "f" * 40)
            elif mutation == "blob":
                git.blobs[git.trees[candidate.revision][SELECTION_PATH][2]] += b"x"
            elif mutation == "inherited":
                git.trees[candidate.revision]["README.md"] = (
                    "100755",
                    "blob",
                    "e" * 40,
                )
            else:
                entry = git.trees[candidate.revision][SELECTION_PATH]
                git.trees[candidate.revision][SELECTION_PATH] = (
                    "100755",
                    entry[1],
                    entry[2],
                )
            with self.subTest(mutation=mutation), self.assertRaises(AuthorityRootError):
                verify_candidate(self.request, candidate, git)

    def test_exact_parent_and_formal_gitlink_structure(self):
        candidate, _ = self.candidate()
        mutations = (
            (),
            (self.git.root, "f" * 40),
        )
        for parents in mutations:
            git = deepcopy(self.git)
            git.parent_lists[candidate.revision] = parents
            with self.subTest(parents=parents), self.assertRaises(AuthorityRootError):
                verify_candidate(self.request, candidate, git)
        for entry in (
            None,
            ("100644", "blob", self.git.child),
            ("160000", "blob", self.git.child),
            ("160000", "commit", "f" * 40),
        ):
            git = deepcopy(self.git)
            if entry is None:
                del git.trees[git.root]["cosmos-framework"]
            else:
                git.trees[git.root]["cosmos-framework"] = entry
            with self.subTest(entry=entry), self.assertRaises(CollectionError):
                verify_candidate(self.request, candidate, git)

    def test_prepare_revalidates_created_candidate(self):
        class CorruptCreate(Git):
            def create_detached_commit(self, parent, blobs):
                revision = super().create_detached_commit(parent, blobs)
                self.trees[revision]["README.md"] = ("100755", "blob", "e" * 40)
                return revision

        git = CorruptCreate()
        request = AuthorityRequest(
            git.root, git.child, self.request.selection_raw, self.request.config_raw
        )
        with self.assertRaises(AuthorityRootError):
            prepare_candidate(request, git)

    def test_capability_copy_and_replay_fail(self):
        candidate, binding = self.candidate()
        with self.assertRaises(AuthorityRootError):
            copy(binding)
        with self.assertRaises(AuthorityRootError):
            pickle.dumps(binding)
        with self.assertRaises(AuthorityRootError):
            AuthorityBinding(self.request, candidate, binding.as_mapping(), object())
        with self.assertRaises(TypeError):
            binding._mapping["root_revision"] = "f" * 40
        publish_candidate(self.request, candidate, binding, self.git)
        with self.assertRaises(AuthorityRootError):
            publish_candidate(self.request, candidate, binding, self.git)

    def test_finalizer_commit_and_post_commit_error_preserve_refs(self):
        candidate, binding = self.candidate()
        def finalizer(witness, commit):
            self.assertEqual(witness.revision, candidate.revision)
            self.assertIsInstance(commit, EvidenceCommit)
            guard = self._seal_commit(witness, commit)
            commit.consume_by_unlink()
            self.assertFalse(guard.exists())
            raise KeyboardInterrupt("after unlink")

        with self.assertRaises(PostCommitFinalizerError) as raised:
            publish_candidate(
                self.request, candidate, binding, self.git, finalizer=finalizer
            )
        self.assertIsInstance(raised.exception.__cause__, KeyboardInterrupt)
        self.assertEqual(self.git.local[AUTHORITY_REF], candidate.revision)
        self.assertEqual(self.git.remote[AUTHORITY_REF], candidate.revision)
        self.assertNotIn("delete_local", self.git.events)
        self.assertNotIn("delete_remote", self.git.events)

    def test_finalizer_without_commit_rolls_back(self):
        candidate, binding = self.candidate()
        with self.assertRaisesRegex(AuthorityRootError, "FINALIZER_DID_NOT_COMMIT"):
            publish_candidate(
                self.request, candidate, binding, self.git, finalizer=lambda _w, _c: object()
            )
        self.assertNotIn(AUTHORITY_REF, self.git.local)
        self.assertNotIn(AUTHORITY_REF, self.git.remote)

    def test_noop_consumer_cannot_mark_evidence_commit_committed(self):
        candidate, binding = self.candidate()

        def finalizer(_witness, commit):
            with self.assertRaises(TypeError):
                commit.seal_for_guard(lambda: None)
            self.assertFalse(commit.committed)

        with self.assertRaisesRegex(AuthorityRootError, "FINALIZER_DID_NOT_COMMIT"):
            publish_candidate(
                self.request, candidate, binding, self.git, finalizer=finalizer
            )
        self.assertNotIn(AUTHORITY_REF, self.git.local)
        self.assertNotIn(AUTHORITY_REF, self.git.remote)

    def test_stale_commit_cannot_seal_current_activation_guard(self):
        stale: list[tuple[object, EvidenceCommit]] = []
        candidate, binding = self.candidate()

        def retain(witness, commit):
            stale.append((witness, commit))

        with self.assertRaisesRegex(AuthorityRootError, "FINALIZER_DID_NOT_COMMIT"):
            publish_candidate(self.request, candidate, binding, self.git, finalizer=retain)
        candidate, binding = self.candidate()

        def finalizer(witness, commit):
            with self.assertRaises(AuthorityRootError):
                self._seal_commit(stale[0][0], stale[0][1])
            self._seal_commit(witness, commit)
            commit.consume_by_unlink()

        publish_candidate(self.request, candidate, binding, self.git, finalizer=finalizer)
        self.assertEqual(self.git.local[AUTHORITY_REF], candidate.revision)
        self.assertEqual(self.git.remote[AUTHORITY_REF], candidate.revision)

    def test_ref_drift_after_seal_cannot_unlink_guard(self):
        for endpoint in ("local", "remote"):
            with self.subTest(endpoint=endpoint):
                candidate, binding = self.candidate()
                foreign = "f" * 40

                def finalizer(witness, commit, target=endpoint):
                    guard = self._seal_commit(witness, commit)
                    getattr(self.git, target)[AUTHORITY_REF] = foreign
                    with self.assertRaises(AuthorityRootError):
                        commit.consume_by_unlink()
                    self.assertTrue(guard.exists())

                with self.assertRaises(RollbackIncomplete):
                    publish_candidate(
                        self.request, candidate, binding, self.git, finalizer=finalizer
                    )
                self.assertEqual(getattr(self.git, endpoint)[AUTHORITY_REF], foreign)
                self.git.local.clear()
                self.git.remote.clear()

    def test_guard_replacement_cannot_commit_or_delete_foreign_guard(self):
        candidate, binding = self.candidate()

        def finalizer(witness, commit):
            guard = self._seal_commit(witness, commit)
            guard.unlink()
            guard.write_bytes(b"foreign")
            with self.assertRaises(AuthorityRootError):
                commit.consume_by_unlink()
            self.assertEqual(guard.read_bytes(), b"foreign")

        with self.assertRaisesRegex(AuthorityRootError, "FINALIZER_DID_NOT_COMMIT"):
            publish_candidate(self.request, candidate, binding, self.git, finalizer=finalizer)
        self.assertNotIn(AUTHORITY_REF, self.git.local)
        self.assertNotIn(AUTHORITY_REF, self.git.remote)

    def test_committed_finalizer_ordinary_returns_preserve_refs(self):
        for returned in (None, object(), {"ignored": True}):
            with self.subTest(returned=type(returned).__name__):
                candidate, binding = self.candidate()

                def finalizer(witness, commit, result=returned):
                    self._seal_commit(witness, commit)
                    commit.consume_by_unlink()
                    return result

                witness = publish_candidate(
                    self.request, candidate, binding, self.git, finalizer=finalizer
                )
                self.assertEqual(witness.revision, candidate.revision)
                self.assertEqual(self.git.local[AUTHORITY_REF], candidate.revision)
                self.assertEqual(self.git.remote[AUTHORITY_REF], candidate.revision)
                self.git.local.clear()
                self.git.remote.clear()

    def test_committed_custom_base_exception_preserves_refs(self):
        class Cancellation(BaseException):
            pass

        candidate, binding = self.candidate()

        def finalizer(witness, commit):
            self._seal_commit(witness, commit)
            commit.consume_by_unlink()
            raise Cancellation("after commit")

        with self.assertRaises(PostCommitFinalizerError) as raised:
            publish_candidate(self.request, candidate, binding, self.git, finalizer=finalizer)
        self.assertIsInstance(raised.exception.__cause__, Cancellation)
        self.assertEqual(self.git.local[AUTHORITY_REF], candidate.revision)
        self.assertEqual(self.git.remote[AUTHORITY_REF], candidate.revision)

    def test_precommit_finalizer_base_exception_rolls_back(self):
        class Cancellation(BaseException):
            pass

        candidate, binding = self.candidate()
        with self.assertRaises(Cancellation):
            publish_candidate(
                self.request,
                candidate,
                binding,
                self.git,
                finalizer=lambda _witness, _commit: (_ for _ in ()).throw(Cancellation()),
            )
        self.assertNotIn(AUTHORITY_REF, self.git.local)
        self.assertNotIn(AUTHORITY_REF, self.git.remote)

    def test_unsealed_or_duplicate_seal_commit_rolls_back(self):
        for operation in ("unsealed", "duplicate_seal"):
            with self.subTest(operation=operation):
                candidate, binding = self.candidate()

                def finalizer(witness, commit, kind=operation):
                    if kind == "unsealed":
                        commit.consume_by_unlink()
                    else:
                        self._seal_commit(witness, commit)
                        self._seal_commit(witness, commit)

                with self.assertRaises(AuthorityRootError):
                    publish_candidate(
                        self.request, candidate, binding, self.git, finalizer=finalizer
                    )
                self.assertNotIn(AUTHORITY_REF, self.git.local)
                self.assertNotIn(AUTHORITY_REF, self.git.remote)

    def test_replayed_commit_after_unlink_preserves_refs(self):
        candidate, binding = self.candidate()

        def finalizer(witness, commit):
            self._seal_commit(witness, commit)
            commit.consume_by_unlink()
            commit.consume_by_unlink()

        with self.assertRaises(PostCommitFinalizerError) as raised:
            publish_candidate(self.request, candidate, binding, self.git, finalizer=finalizer)
        self.assertIsInstance(raised.exception.__cause__, AuthorityRootError)
        self.assertEqual(self.git.local[AUTHORITY_REF], candidate.revision)
        self.assertEqual(self.git.remote[AUTHORITY_REF], candidate.revision)

    def test_unprovable_evidence_cleanup_is_rollback_incomplete(self):
        candidate, binding = self.candidate()

        def finalizer(_witness, _commit):
            raise EvidenceCleanupIncomplete("fixture")

        with self.assertRaises(RollbackIncomplete):
            publish_candidate(self.request, candidate, binding, self.git, finalizer=finalizer)
        self.assertNotIn(AUTHORITY_REF, self.git.local)
        self.assertNotIn(AUTHORITY_REF, self.git.remote)

    def test_all_typed_boundaries_reject_copy_and_pickle(self):
        candidate, binding = self.candidate()
        witness = publish_candidate(self.request, candidate, binding, self.git)
        for value in (self.request, candidate, witness):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(AuthorityRootError):
                    copy(value)
                with self.assertRaises(AuthorityRootError):
                    pickle.dumps(value)

    def test_verifier_mapping_enters_real_collection_executor(self):
        candidate, binding = self.candidate()
        publish_candidate(self.request, candidate, binding, self.git)
        authority = binding.as_mapping()
        base = "b" * 40
        lineage = {
            "target_ref": "refs/heads/fixture",
            "expected_base_root_revision": base,
            "expected_child_gitlink": self.git.child,
            "authority_approval_formal_root_revision": self.git.root,
        }
        fixture = TemporaryGitFixture(
            {lineage["target_ref"]: base},
            parents={candidate.revision: self.git.root},
            trees={**deepcopy(self.git.trees), base: {}},
            blobs=deepcopy(self.git.blobs),
            gitlinks={base: self.git.child},
            local_refs={AUTHORITY_REF: candidate.revision},
            remote_refs={AUTHORITY_REF: candidate.revision},
        )
        pristine = deepcopy(fixture)
        result = collect_synthetic(
            authority=authority,
            lineage=lineage,
            selection_request=self.request.selection_raw,
            git=fixture,
            root_fd=SyntheticRootFd({"fixture/checkpoint": b"x"}),
            sink=MemoryEvidenceSink(),
        )
        self.assertEqual(result["status"], "PASS")
        for changed in (
            {**authority, "authority_root_revision": authority["root_revision"]},
            {
                **{k: v for k, v in authority.items() if k != "root_revision"},
                "authority_root_revision": authority["root_revision"],
            },
            {k: v for k, v in authority.items() if k != "root_revision"},
            {**authority, "extra": "x"},
        ):

            class Unopened:
                def open_regular(self, path):
                    raise AssertionError("invalid mapping不得打开source")

            bad_fixture = deepcopy(pristine)
            with self.assertRaises(CollectionError):
                collect_synthetic(
                    authority=changed,
                    lineage=lineage,
                    selection_request=self.request.selection_raw,
                    git=bad_fixture,
                    root_fd=Unopened(),
                    sink=MemoryEvidenceSink(),
                )

    def test_verifier_rejects_parent_with_either_fixed_path(self):
        fixed = (
            (SELECTION_PATH, self.request.selection_raw),
            (
                "docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json",
                self.request.config_raw,
            ),
        )
        for path, _ in fixed:
            git = Git()
            git.trees[git.root][path] = ("100644", "blob", "f" * 40)
            revision = git.create_detached_commit(git.root, dict(fixed))
            request = AuthorityRequest(
                git.root, git.child, self.request.selection_raw, self.request.config_raw
            )
            with (
                self.subTest(path=path),
                self.assertRaisesRegex(AuthorityRootError, "已含fixed path"),
            ):
                verify_candidate(request, AuthorityCandidate(revision), git)

    def test_capability_rejects_cross_request_and_candidate(self):
        candidate, binding = self.candidate()
        equivalent = AuthorityRequest(
            self.request.materialization_formal_root,
            self.request.expected_child_gitlink,
            self.request.selection_raw,
            self.request.config_raw,
        )
        with self.assertRaises(AuthorityRootError):
            publish_candidate(equivalent, candidate, binding, self.git)

    def test_remote_conflict_preserves_foreign_and_rolls_back_local(self):
        candidate, binding = self.candidate()
        foreign = "f" * 40

        def hook(stage, git, revision):
            if stage == "after_create_local":
                git.remote[AUTHORITY_REF] = foreign

        self.git.hook = hook
        reports = []
        with self.assertRaises(RollbackIncomplete) as raised:
            publish_candidate(
                self.request, candidate, binding, self.git,
                failure_reporter=reports.append,
            )
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].phase, "remote_cas")
        self.assertIs(reports[0].rollback, raised.exception.outcome)
        self.assertIsNone(reports[0].pre_local)
        self.assertIsNone(reports[0].pre_remote)
        self.assertIsNone(reports[0].post_local)
        self.assertIsNone(reports[0].post_remote)
        self.assertFalse(reports[0].binding_reverified)
        self.assertTrue(raised.exception.outcome.entered)
        self.assertTrue(raised.exception.outcome.required)
        self.assertEqual(raised.exception.outcome.final_remote, foreign)
        self.assertNotIn(AUTHORITY_REF, self.git.local)
        self.assertEqual(self.git.remote[AUTHORITY_REF], foreign)
        self.assertEqual(self.git.events[-2:], ["read_local", "read_remote"])

    def test_observation_error_still_reads_both_endpoints(self):
        class ReadFailure(Git):
            def local_ref(self, ref):
                self.events.append("read_local")
                raise OSError("injected unreadable")

        git = ReadFailure()
        request = AuthorityRequest(
            git.root, git.child, self.request.selection_raw, self.request.config_raw
        )
        candidate = prepare_candidate(request, git)
        binding = verify_candidate(request, candidate, git)
        reports = []
        with self.assertRaises(RollbackIncomplete):
            publish_candidate(request, candidate, binding, git, failure_reporter=reports.append)
        self.assertEqual(git.events[-2:], ["read_local", "read_remote"])
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].phase, "pre_publication")
        self.assertEqual(reports[0].pre_local_error, "OSERROR")
        self.assertIsNone(reports[0].pre_remote_error)
        self.assertEqual(reports[0].rollback.final_local_error, "OSERROR")

    def test_post_publication_observation_failure_retains_unreadable_witness(self):
        class PostReadFailure(Git):
            def __init__(self):
                super().__init__()
                self.fail_remote = False

            def remote_ref(self, ref):
                self.events.append("read_remote")
                if self.fail_remote:
                    raise OSError("injected unreadable")
                return self.remote.get(ref)

            def cas_create_remote(self, ref, revision):
                created = super().cas_create_remote(ref, revision)
                self.fail_remote = True
                return created

        git = PostReadFailure()
        request = AuthorityRequest(
            git.root, git.child, self.request.selection_raw, self.request.config_raw
        )
        candidate = prepare_candidate(request, git)
        binding = verify_candidate(request, candidate, git)
        reports = []
        with self.assertRaises(RollbackIncomplete):
            publish_candidate(request, candidate, binding, git, failure_reporter=reports.append)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].phase, "post_publication")
        self.assertEqual(reports[0].post_remote_error, "OSERROR")
        self.assertEqual(reports[0].rollback.final_remote_error, "OSERROR")

    def test_postcheck_and_rollback_races_never_delete_foreign(self):
        for endpoint in ("local", "remote"):
            git = Git()
            request = AuthorityRequest(
                git.root, git.child, self.request.selection_raw, self.request.config_raw
            )
            candidate = prepare_candidate(request, git)
            binding = verify_candidate(request, candidate, git)
            foreign = "f" * 40

            def hook(stage, target, revision, endpoint=endpoint):
                if stage == "after_create_remote":
                    getattr(target, endpoint)[AUTHORITY_REF] = foreign

            git.hook = hook
            with self.subTest(endpoint=endpoint), self.assertRaises(RollbackIncomplete):
                publish_candidate(request, candidate, binding, git)
            self.assertEqual(getattr(git, endpoint)[AUTHORITY_REF], foreign)

    def test_rollback_time_drift_preserves_foreign(self):
        candidate, binding = self.candidate()
        foreign = "f" * 40

        def hook(stage, git, revision):
            if stage == "after_create_remote":
                git.trees[candidate.revision]["extra"] = ("100644", "blob", foreign)
            if stage == "before_delete_remote":
                git.remote[AUTHORITY_REF] = foreign

        self.git.hook = hook
        with self.assertRaises(RollbackIncomplete):
            publish_candidate(self.request, candidate, binding, self.git)
        self.assertEqual(self.git.remote[AUTHORITY_REF], foreign)
        self.assertNotIn(AUTHORITY_REF, self.git.local)


if __name__ == "__main__":
    unittest.main()
