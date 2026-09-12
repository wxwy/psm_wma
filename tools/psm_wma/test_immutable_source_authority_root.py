"""CPU-only tests for authority-root preparation, verification and publication."""

from __future__ import annotations
import hashlib
import json
import pickle
import unittest
from copy import copy, deepcopy

from tools.psm_wma.immutable_source_authority_root import (
    AuthorityBinding,
    AuthorityRequest,
    AuthorityRootError,
    RollbackIncomplete,
    prepare_candidate,
    publish_candidate,
    verify_candidate,
)
from tools.psm_wma.immutable_source_collection import (
    AUTHORITY_REF,
    SELECTION_PATH,
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
        self.parents, self.blobs = {}, {}
        self.local, self.remote = {}, {}
        self.events, self.hook = [], None

    def tree_entries(self, revision):
        return self.trees[revision]

    def parent(self, revision):
        return self.parents[revision]

    def blob_bytes(self, value):
        return self.blobs[value]

    def gitlink_at(self, revision):
        return self.trees[revision]["cosmos-framework"][2]

    def create_detached_commit(self, parent, blobs):
        tree = dict(self.trees[parent])
        tree.update({p: ("100644", "blob", oid(v)) for p, v in blobs.items()})
        revision = hashlib.sha1(json.dumps(tree, sort_keys=True).encode()).hexdigest()
        self.trees[revision], self.parents[revision] = tree, parent
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
        self.assertEqual(self.git.parents, {})
        self.git.trees[self.git.root][SELECTION_PATH] = ("100644", "blob", "f" * 40)
        with self.assertRaises(AuthorityRootError):
            prepare_candidate(self.request, self.git)

    def test_verifier_rejects_parent_delta_and_blob_drift(self):
        candidate, _ = self.candidate()
        for mutation in ("parent", "extra", "blob"):
            git = deepcopy(self.git)
            if mutation == "parent":
                git.parents[candidate.revision] = "f" * 40
            elif mutation == "extra":
                git.trees[candidate.revision]["extra"] = ("100644", "blob", "f" * 40)
            else:
                git.blobs[git.trees[candidate.revision][SELECTION_PATH][2]] += b"x"
            with self.subTest(mutation=mutation), self.assertRaises(AuthorityRootError):
                verify_candidate(self.request, candidate, git)

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
        with self.assertRaises(RollbackIncomplete):
            publish_candidate(self.request, candidate, binding, self.git)
        self.assertNotIn(AUTHORITY_REF, self.git.local)
        self.assertEqual(self.git.remote[AUTHORITY_REF], foreign)

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
