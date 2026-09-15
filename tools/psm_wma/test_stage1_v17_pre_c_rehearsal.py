import copy
import hashlib
import json
import pickle
import unittest

from tools.psm_wma.stage1_v17_pre_c_rehearsal import (
    AuthorityAbsenceV1, ClosureV1, DESIGNATED_ABSENCES, DescriptorV1, ENV, OpaquePatchCapabilityV1, PreCRehearsalError,
    QueryFactV1, ReadbackV1, RehearsalInputV1, consume_once_v05, rehearse_v05,
)


class PreCRehearsalTest(unittest.TestCase):
    def fixture(self, outcome="APPLIED", verify=True):
        calls = []
        def apply(descriptor, patch_text):
            calls.append((descriptor, patch_text)); return outcome
        cap = OpaquePatchCapabilityV1("host", "host.patch", "host/patch.py", "a" * 64,
            f"{apply.__module__}.{apply.__qualname__}", "psm.stage1.request-patch-consumer/v1",
            "opaque-patch-text-handoff/v1", apply)
        raw = json.dumps({"a": 1}, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        md = ("json_filename: docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json\n"
              f"json_bytes: {len(raw)}\njson_sha256: {hashlib.sha256(raw).hexdigest()}\n"
              "canonicalization: utf-8; recursive sorted keys; compact separators; exactly one terminal LF\n"
              f"json_git_blob_oid: {blob}\n").encode()
        def add(payload): return b"".join(b"+" + line for line in payload.splitlines(keepends=True))
        patch = (b"--- /dev/null\n+++ b/docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json\n" + add(raw) +
                 b"--- /dev/null\n+++ b/docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.md\n" + add(md))
        closure = ClosureV1(b"git", b"config", b"V2",
            QueryFactV1(("git", "ls-remote", "origin", "refs/heads/V2"), 30, 0, b"v2", b"", "remote_v2_ancestor", b"V2"),
            QueryFactV1(("git", "ls-remote", "origin", "refs/heads/stage1-authority"), 30, 0, b"", b"", "authority_absent"),
            AuthorityAbsenceV1("refs/local-authority", b"local-absent", "authority_absent", 12, hashlib.sha256(b"local-absent").hexdigest()),
            AuthorityAbsenceV1("refs/remote-authority", b"remote-absent", "authority_absent", 13, hashlib.sha256(b"remote-absent").hexdigest()),
            DescriptorV1().paths, DESIGNATED_ABSENCES)
        def verifier(json_raw, markdown_raw, paths):
            return ReadbackV1(json_raw, markdown_raw) if verify else ReadbackV1(b"bad\n", markdown_raw)
        return RehearsalInputV1(cap, DescriptorV1(), raw, md, patch, ENV, closure,
            verifier, f"{verifier.__module__}.{verifier.__qualname__}"), calls

    def test_success_is_exactly_once(self):
        value, calls = self.fixture(); plan = rehearse_v05(value)
        self.assertEqual(consume_once_v05(plan, value.closure), "HARD_STOP_PENDING_INDEPENDENT_REVIEW")
        with self.assertRaisesRegex(PreCRehearsalError, "already_consumed"): consume_once_v05(plan, value.closure)
        self.assertEqual(len(calls), 1)

    def test_every_terminal_result_consumes_plan(self):
        for outcome in ("REJECTED_NO_WRITE", "PARTIAL_OR_UNKNOWN", "OTHER"):
            value, calls = self.fixture(outcome); plan = rehearse_v05(value)
            with self.assertRaises(PreCRehearsalError): consume_once_v05(plan, value.closure)
            with self.assertRaisesRegex(PreCRehearsalError, "already_consumed"): consume_once_v05(plan, value.closure)
            self.assertEqual(len(calls), 1)

    def test_copy_and_pickle_are_rejected(self):
        value, _ = self.fixture(); plan = rehearse_v05(value)
        for thing in (value.capability, plan):
            with self.assertRaises(PreCRehearsalError): copy.copy(thing)
            with self.assertRaises(PreCRehearsalError): pickle.dumps(thing)

    def test_environment_and_closure_are_exact(self):
        value, _ = self.fixture()
        with self.assertRaisesRegex(PreCRehearsalError, "six_key_environment"):
            rehearse_v05(RehearsalInputV1(value.capability, value.descriptor, value.json_raw, value.markdown_raw,
                value.patch_raw, ENV[:-1], value.closure, value.post_write_verify, value.post_write_qualname))
        foreign = ClosureV1(value.closure.git_identity, value.closure.config_raw,
            value.closure.local_v2_raw, value.closure.remote_v2, value.closure.authority_ref,
            value.closure.local_authority_absence, value.closure.remote_authority_absence,
            ("foo", "bar"), value.closure.designated_absences)
        with self.assertRaisesRegex(PreCRehearsalError, "closure_absence"):
            rehearse_v05(RehearsalInputV1(value.capability, value.descriptor, value.json_raw, value.markdown_raw,
                value.patch_raw, ENV, foreign, value.post_write_verify, value.post_write_qualname))

    def test_canonical_witnesses_and_forbidden_values_fail_closed(self):
        value, _ = self.fixture()
        for field, raw in (("json_raw", b'{"a":1}'), ("markdown_raw", b"bad\n"), ("patch_raw", b"v0.4\n")):
            values = dict(value.__dict__); values[field] = raw
            with self.assertRaises(PreCRehearsalError): rehearse_v05(RehearsalInputV1(**values))

    def test_post_write_failure_is_terminal(self):
        value, calls = self.fixture(verify=False); plan = rehearse_v05(value)
        with self.assertRaisesRegex(PreCRehearsalError, "post_write"): consume_once_v05(plan, value.closure)
        with self.assertRaisesRegex(PreCRehearsalError, "already_consumed"): consume_once_v05(plan, value.closure)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__": unittest.main()
