import threading
import unittest

from tools.psm_wma.stage1_host_boundary import (
    FakeStage1HostV27,
    FakeStage1OrchestratorV27,
    State,
    mutate,
)


class HostBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.host = FakeStage1HostV27("generation-a", root="root", child="child")
        self.record = self.host.create("review-a")
        self.orchestrator = FakeStage1OrchestratorV27(self.host)
        self.approval = self.orchestrator.attest(self.record)

    def _assert_bad_approval(self, **changes):
        self.assertFalse(self.host.approve(mutate(self.approval, **changes)))
        self.assertEqual(self.host.state(self.record.host_session_id), State.TERMINAL)
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 0)

    def test_exact_route_is_once(self):
        self.assertTrue(self.host.approve(self.approval))
        self.assertTrue(self.host.resume_once(self.record.host_session_id, self.record.host_lease_id))
        self.assertFalse(self.host.resume_once(self.record.host_session_id, self.record.host_lease_id))
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 1)

    def test_all_attestation_fields_terminalize_before_apply(self):
        for field in ("gate", "root", "child", "record_digest", "host_generation_id", "live_plan_id", "live_plan_digest", "host_lease_id", "binding_digest", "nonce", "counter"):
            with self.subTest(field=field):
                self.setUp()
                self._assert_bad_approval(**{field: "wrong:value" if field != "counter" else 2})

    def test_each_category_field_drift_rejects_attestation(self):
        for category_index, (_, fields) in enumerate(self.record.authority_rows):
            for field_index, (name, value) in enumerate(fields):
                with self.subTest(category=category_index, field=name):
                    self.setUp()
                    rows = list(self.record.authority_rows)
                    category, old_fields = rows[category_index]
                    drifted = list(old_fields)
                    drifted[field_index] = (name, value + "-drift")
                    object.__setattr__(self.record, "authority_rows", tuple(rows[:category_index] + [(category, tuple(drifted))] + rows[category_index + 1:]))
                    with self.assertRaises(ValueError):
                        self.orchestrator.attest(self.record)

    def test_schema_rejects_missing_extra_reordered_and_malformed_fields(self):
        rows = self.record.authority_rows
        candidates = [rows[:-1], rows + (("extra", (("x", "identity:x"),)),), tuple(reversed(rows))]
        category, fields = rows[0]
        candidates.extend([
            ((category, fields[:-1]),) + rows[1:],
            ((category, fields + (("extra", "identity:x"),)),) + rows[1:],
            ((category, tuple(reversed(fields))),) + rows[1:],
            ((category, ((fields[0][0], "malformed"),) + fields[1:]),) + rows[1:],
        ])
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    self.host.create(candidate)

    def test_client_base_mutation_never_mutates_private_snapshot(self):
        object.__setattr__(self.record, "authority_rows", ())
        with self.assertRaises(ValueError):
            self.orchestrator.attest(self.record)
        clean = self.host.create("review-b")
        approval = self.orchestrator.attest(clean)
        object.__setattr__(clean, "host_lease_id", "attacker:lease")
        self.assertTrue(self.host.approve(approval))
        self.assertFalse(self.host.resume_once(clean.host_session_id, clean.host_lease_id))
        self.assertEqual(self.host.apply_count(approval.host_session_id), 0)

    def test_prior_session_and_generation_replay_zero_apply(self):
        other = self.host.create("review-b")
        self.assertFalse(self.host.approve(mutate(self.approval, host_session_id=other.host_session_id)))
        self.assertEqual(self.host.apply_count(other.host_session_id), 0)
        foreign = FakeStage1HostV27("generation-old", root="root", child="child")
        old_record = foreign.create("review")
        self.assertFalse(self.host.approve(FakeStage1OrchestratorV27(foreign).attest(old_record)))

    def test_parallel_resume_has_one_apply(self):
        self.assertTrue(self.host.approve(self.approval))
        barrier = threading.Barrier(3)
        results = []
        def run():
            barrier.wait()
            results.append(self.host.resume_once(self.record.host_session_id, self.record.host_lease_id))
        threads = [threading.Thread(target=run) for _ in range(2)]
        for thread in threads: thread.start()
        barrier.wait()
        for thread in threads: thread.join()
        self.assertEqual(results.count(True), 1)
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 1)

    def test_terminal_failure_matrix(self):
        for kwargs, expected_applies in (({"fresh": False}, 0), ({"apply_ok": False}, 0), ({"verify_ok": False}, 1)):
            with self.subTest(kwargs=kwargs):
                self.setUp()
                self.assertTrue(self.host.approve(self.approval))
                self.assertFalse(self.host.resume_once(self.record.host_session_id, self.record.host_lease_id, **kwargs))
                self.assertEqual(self.host.state(self.record.host_session_id), State.TERMINAL)
                self.assertEqual(self.host.apply_count(self.record.host_session_id), expected_applies)


if __name__ == "__main__":
    unittest.main()
