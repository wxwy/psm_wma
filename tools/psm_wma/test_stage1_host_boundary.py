import unittest

from tools.psm_wma.stage1_host_boundary import FakeStage1HostV27, ReviewApprovalV27


class HostBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.host = FakeStage1HostV27("generation-a")
        self.record = self.host.create("review-a")
        self.approval = self.host.approval_for_test(self.record, "root", "child")

    def test_exact_route_is_once(self):
        self.assertTrue(self.host.approve(self.approval))
        self.assertTrue(self.host.resume_once(self.record.host_session_id, self.record.host_lease_id))
        self.assertFalse(self.host.resume_once(self.record.host_session_id, self.record.host_lease_id))
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 1)

    def test_prior_generation_approval_terminalizes(self):
        bad = ReviewApprovalV27(**{**self.approval.__dict__, "host_generation_id": "old"})
        self.assertFalse(self.host.approve(bad))
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 0)

    def test_foreign_lease_is_zero_apply(self):
        self.assertTrue(self.host.approve(self.approval))
        self.assertFalse(self.host.resume_once(self.record.host_session_id, "foreign"))
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 0)

    def test_stale_is_zero_apply(self):
        self.assertTrue(self.host.approve(self.approval))
        self.assertFalse(self.host.resume_once(self.record.host_session_id, self.record.host_lease_id, fresh=False))
        self.assertEqual(self.host.apply_count(self.record.host_session_id), 0)


if __name__ == "__main__":
    unittest.main()
