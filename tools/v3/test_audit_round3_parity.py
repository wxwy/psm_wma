"""CPU-only tests for strict legacy and DS_PRO prefixed Round-3 JSON schemas."""
from __future__ import annotations

import unittest

from audit_round3_parity import EvidenceError, audit


def window(task: str, episode: int, start: int, a_b: float, a_c: float | None = None, b_c: float = 0.0):
    if a_c is None:
        a_c = a_b
    def metric(v: float):
        return {"exact_equal": v == 0, "max_abs": v}
    return {"task_class": task, "episode_index": episode, "start_frame": start,
            "comparisons": {"A_vs_B": metric(a_b), "A_vs_C": metric(a_c), "B_vs_C": metric(b_c)}}


def ds_prefixed_window(task: str, episode: int, start: int, z_diff: float, visual_diff: float):
    row = window(task, episode, start, z_diff)
    metrics = row.pop("comparisons")
    for name, value in metrics.items():
        row[f"z0_{name}"] = value
        row[f"visual96_{name}"] = {"exact_equal": visual_diff == 0, "max_abs": visual_diff} if name != "B_vs_C" else {"exact_equal": True, "max_abs": 0.0}
    return row


class AuditTests(unittest.TestCase):
    def test_reported_4_vs_3_mismatch(self):
        rows = [
            window("CloseBlenderLid", 0, 0, 0),
            window("CloseBlenderLid", 0, 172, 0.015625),
            window("CloseBlenderLid", 0, 344, 0),
            window("CloseFridge", 502, 0, 0),
            window("CloseFridge", 502, 206, 0),
            window("CloseFridge", 502, 412, 0),
            window("CloseToasterOvenDoor", 1015, 0, 0.015625),
            window("CloseToasterOvenDoor", 1015, 50, 0.015625),
            window("CloseToasterOvenDoor", 1015, 100, 0),
        ]
        failed = audit({"windows": rows}, {"A_vs_B": 4, "A_vs_C": 4, "B_vs_C": 0})
        self.assertEqual(failed["status"], "FAIL")
        self.assertEqual(failed["comparison_counts"]["A_vs_B"]["non_exact"], 3)
        self.assertEqual(failed["comparison_counts"]["A_vs_B"]["exact"], 6)
        self.assertEqual(len(failed["claimed_count_mismatches"]), 2)
        self.assertEqual(audit({"windows": rows}, {"A_vs_B": 3, "A_vs_C": 3, "B_vs_C": 0})["status"], "PASS")

    def test_actual_ds_prefixed_schema_both_features(self):
        rows = [ds_prefixed_window("A", 7, i, 0.015625 if i < 3 else 0, 0.0007 if i < 3 else 0) for i in range(9)]
        result = audit({"windows": rows}, {"A_vs_B": 3, "A_vs_C": 3, "B_vs_C": 0})
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["comparison_counts"]["A_vs_B"]["non_exact"], 3)
        self.assertEqual(result["comparison_counts"]["B_vs_C"]["non_exact"], 0)
        visual = audit({"windows": rows}, {"A_vs_B": 3, "A_vs_C": 3}, feature="visual96")
        self.assertEqual(visual["status"], "PASS")
        self.assertEqual(visual["comparison_counts"]["A_vs_B"]["max_abs"], 0.0007)

    def test_nested_feature_group(self):
        row = ds_prefixed_window("A", 0, 0, 0.015625, 0.0007)
        nested = {"z0": {}, "visual96": {}}
        for name in ("A_vs_B", "A_vs_C", "B_vs_C"):
            nested["z0"][name] = row.pop("z0_" + name)
            nested["visual96"][name] = row.pop("visual96_" + name)
        row["comparisons"] = nested
        self.assertEqual(audit({"windows": [row]})["status"], "PASS")
        self.assertEqual(audit({"windows": [row]}, feature="visual96")["status"], "PASS")

    def test_visual_cannot_fallback_to_z0(self):
        row = window("A", 0, 0, 0)
        with self.assertRaises(EvidenceError):
            audit({"windows": [row]}, feature="visual96")

    def test_duplicate_fails(self):
        row = window("A", 1, 2, 0.0)
        with self.assertRaises(EvidenceError):
            audit({"windows": [row, row]})

    def test_metric_contradiction_fails(self):
        row = window("A", 1, 2, 0.0)
        row["comparisons"]["A_vs_B"]["exact_equal"] = False
        with self.assertRaises(EvidenceError):
            audit({"windows": [row]})

    def test_mismatch_alias_fails(self):
        row = ds_prefixed_window("A", 1, 2, 0.015625, 0.0007)
        row["A_vs_B"] = {"exact_equal": True, "max_abs": 0.0}
        with self.assertRaises(EvidenceError):
            audit({"windows": [row]})

    def test_b_c_exact_invariant(self):
        row = window("A", 1, 2, 0.015625, 0, 0)
        with self.assertRaises(EvidenceError):
            audit({"windows": [row]})

    def test_missing_comparison_fails(self):
        row = window("A", 1, 2, 0.0)
        del row["comparisons"]["A_vs_C"]
        with self.assertRaises(EvidenceError):
            audit({"windows": [row]})

    def test_nan_fails(self):
        row = window("A", 1, 2, float("nan"))
        with self.assertRaises(EvidenceError):
            audit({"windows": [row]})

    def test_claim_noninteger_fails(self):
        with self.assertRaises(EvidenceError):
            audit({"windows": [window("A", 0, 0, 0)]}, {"A_vs_B": 1.0})


if __name__ == "__main__":
    unittest.main()
