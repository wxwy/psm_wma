import threading
import unittest

from tools.psm_wma.stage1_host_boundary import (
    FakeStage1HostV27,
    FakeStage1OrchestratorV27,
    State,
    _digest_rows,
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

    def test_exact_attestation_categories_terminalize_before_apply(self):
        for field in (
            "gate", "root", "child", "record_digest", "host_generation_id",
            "live_plan_id", "live_plan_digest", "host_lease_id", "binding_digest",
            "nonce", "counter",
        ):
            with self.subTest(field=field):
                self.setUp()
                self._assert_bad_approval(**{field: "wrong" if field != "counter" else 2})

    def test_every_record_category_drift_is_rejected(self):
        for index in range(len(self.record.authority_rows)):
            with self.subTest(index=index):
                self.setUp()
                rows = list(self.record.authority_rows)
                name, values = rows[index]
                rows[index] = (name, ("drift",))
                self._assert_bad_approval(record_digest=_digest_rows(tuple(rows)))

    def test_malformed_missing_extra_and_reordered_record_rejected(self):
        rows = self.record.authority_rows
        for candidate in (rows[:-1], rows + (("extra", ("x",)),), tuple(reversed(rows))):
            with self.assertRaises(ValueError):
                self.host.create(candidate)

    def test_prior_session_and_generation_replay_zero_apply(self):
        other = self.host.create("review-b")
        self.assertFalse(self.host.approve(mutate(self.approval, host_session_id=other.host_session_id)))
        self.assertEqual(self.host.apply_count(other.host_session_id), 0)
        foreign = FakeStage1HostV27("generation-old", root="root", child="child")
        old_record = foreign.create("review")
        self.assertFalse(self.host.approve(FakeStage1OrchestratorV27(foreign).attest(old_record)))
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 0)

    def test_parallel_resume_has_one_apply(self):
        self.assertTrue(self.host.approve(self.approval))
        barrier = threading.Barrier(3)
        results = []

        def run():
            barrier.wait()
            results.append(self.host.resume_once(self.record.host_session_id, self.record.host_lease_id))

        threads = [threading.Thread(target=run) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()
        self.assertEqual(results.count(True), 1)
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 1)

    def test_terminal_failure_matrix(self):
        for kwargs, expected_applies in (
            ({"fresh": False}, 0),
            ({"apply_ok": False}, 0),
            ({"verify_ok": False}, 1),
        ):
            with self.subTest(kwargs=kwargs):
                self.setUp()
                self.assertTrue(self.host.approve(self.approval))
                self.assertFalse(
                    self.host.resume_once(self.record.host_session_id, self.record.host_lease_id, **kwargs)
                )
                self.assertEqual(self.host.state(self.record.host_session_id), State.TERMINAL)
                self.assertEqual(self.host.apply_count(self.record.host_session_id), expected_applies)
                self.assertFalse(self.host.resume_once(self.record.host_session_id, self.record.host_lease_id))

    def test_foreign_lease_is_zero_apply(self):
        self.assertTrue(self.host.approve(self.approval))
        self.assertFalse(self.host.resume_once(self.record.host_session_id, "foreign"))
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 0)


if __name__ == "__main__":
    unittest.main()
