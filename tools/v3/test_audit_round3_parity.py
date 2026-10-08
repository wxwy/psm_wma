"""Synthetic tests: the real DS_PRO Round 3 JSON was not committed to V3."""
from __future__ import annotations

import unittest

from audit_round3_parity import EvidenceError, audit


def window(task: str, episode: int, start: int, a_b: float, a_c: float | None = None, b_c: float = 0.0) -> dict:
    if a_c is None:
        a_c = a_b
    def metric(value: float) -> dict:
        return {"exact_equal": value == 0, "max_abs": value}
    return {
        "task_class": task, "episode_index": episode, "start_frame": start,
        "comparisons": {"A_vs_B": metric(a_b), "A_vs_C": metric(a_c), "B_vs_C": metric(b_c)},
    }


class AuditTests(unittest.TestCase):
    def test_mismatched_4_claim_vs_3_rows_fails(self) -> None:
        data = {"windows": [
            window("CloseBlenderLid", 0, 0, 0),
            window("CloseBlenderLid", 0, 172, 0.015625),
            window("CloseBlenderLid", 0, 344, 0),
            window("CloseFridge", 502, 0, 0),
            window("CloseFridge", 502, 206, 0),
            window("CloseFridge", 502, 412, 0),
            window("CloseToasterOvenDoor", 1015, 0, 0.015625),
            window("CloseToasterOvenDoor", 1015, 50, 0.015625),
            window("CloseToasterOvenDoor", 1015, 100, 0),
        ]}
        failed = audit(data, {"A_vs_B": 4, "A_vs_C": 4, "B_vs_C": 0})
        self.assertEqual(failed["status"], "FAIL")
        self.assertEqual(failed["comparison_counts"]["A_vs_B"]["non_exact"], 3)
        self.assertEqual(failed["comparison_counts"]["A_vs_B"]["exact"], 6)
        self.assertEqual(len(failed["claimed_count_mismatches"]), 2)
        passed = audit(data, {"A_vs_B": 3, "A_vs_C": 3, "B_vs_C": 0})
        self.assertEqual(passed["status"], "PASS")

    def test_duplicate_fails(self) -> None:
        row = window("A", 1, 2, 0.0)
        with self.assertRaises(EvidenceError):
            audit({"windows": [row, row]})

    def test_metric_contradiction_fails(self) -> None:
        row = window("A", 1, 2, 0.0)
        row["comparisons"]["A_vs_B"]["exact_equal"] = False
        with self.assertRaises(EvidenceError):
            audit({"windows": [row]})

    def test_missing_comparison_fails(self) -> None:
        row = window("A", 1, 2, 0.0)
        del row["comparisons"]["A_vs_C"]
        with self.assertRaises(EvidenceError):
            audit({"windows": [row]})

    def test_nan_fails(self) -> None:
        row = window("A", 1, 2, float("nan"))
        with self.assertRaises(EvidenceError):
            audit({"windows": [row]})


if __name__ == "__main__":
    unittest.main()
