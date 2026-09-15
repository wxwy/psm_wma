import unittest

from tools.psm_wma.stage1_v17_pre_c_rehearsal import (
    OpaquePatchCapabilityV1, PreCRehearsalError, RehearsalInputV1,
    consume_once_v05, rehearse_v05,
)


class PreCRehearsalTest(unittest.TestCase):
    def fixture(self, *, calls=None, dry_run=True, verify=True):
        calls = [] if calls is None else calls
        capability = OpaquePatchCapabilityV1(
            "host", "host.patch", "host/patch.py", "a" * 64, "PatchConsumerV1", "opaque",
            lambda descriptor, patch_text: calls.append((descriptor, patch_text)) or "APPLIED")
        snapshot = ((".git", "a"), ("local_v2", "b"), ("remote_v2", "c"), ("authority_ref", "d"))
        return RehearsalInputV1(
            capability, b"descriptor", b'{"v":"v0.5"}', b"# v0.5\n", b"patch\n",
            ("docs/build/v05.json", "docs/build/v05.md"),
            (("git", "g"), ("local_v2", "l"), ("remote_v2", "r"), ("authority_ref", "a"),
             ("config", "c"), ("project_root", "p")), snapshot, ("docs/build/v05.json",),
            lambda raw, paths: dry_run and raw == b"patch\n" and len(paths) == 2,
            lambda json_raw, markdown_raw, paths: verify and json_raw.startswith(b"{") and markdown_raw.startswith(b"#"))

    def test_rehearsal_seals_all_inputs_without_consumer(self):
        calls = []
        plan = rehearse_v05(self.fixture(calls=calls))
        self.assertEqual(calls, [])
        self.assertEqual(plan.patch_text, "patch\n")
        self.assertEqual(tuple(name for name, _, _ in plan.identities),
                         ("descriptor", "json_raw", "markdown_raw", "patch_raw"))

    def test_consume_has_fixed_success_sequence(self):
        calls = []
        plan = rehearse_v05(self.fixture(calls=calls))
        self.assertEqual(consume_once_v05(plan, dict(plan.frozen_snapshot)),
                         "HARD_STOP_PENDING_INDEPENDENT_REVIEW")
        self.assertEqual(calls, [(b"descriptor", "patch\n")])

    def test_freshness_mismatch_never_calls_capability(self):
        calls = []
        plan = rehearse_v05(self.fixture(calls=calls))
        with self.assertRaisesRegex(PreCRehearsalError, "freshness"):
            consume_once_v05(plan, {".git": "changed"})
        self.assertEqual(calls, [])

    def test_rehearsal_failures_close_before_consumer(self):
        for kwargs, category in (({"dry_run": False}, "dry_run"), ({"verify": False}, "post_write")):
            if category == "dry_run":
                with self.assertRaisesRegex(PreCRehearsalError, category): rehearse_v05(self.fixture(**kwargs))
            else:
                plan = rehearse_v05(self.fixture(**kwargs))
                with self.assertRaisesRegex(PreCRehearsalError, category): consume_once_v05(plan, dict(plan.frozen_snapshot))

    def test_v03_v04_and_bad_utf8_are_rejected(self):
        value = self.fixture()
        bad_path = RehearsalInputV1(*value.__dict__.values())
        object.__setattr__(bad_path, "output_paths", ("docs/v0.4.json", "docs/v05.md"))
        with self.assertRaisesRegex(PreCRehearsalError, "forbidden_v03_v04"): rehearse_v05(bad_path)
        object.__setattr__(value, "patch_raw", b"\xff")
        with self.assertRaisesRegex(PreCRehearsalError, "patch_utf8"): rehearse_v05(value)


if __name__ == "__main__":
    unittest.main()
