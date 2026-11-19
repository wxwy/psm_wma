"""CPU-only filesystem safety tests for the G2 formal checkpoint watcher."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.g2.maintain_formal_checkpoints import (
    KEEP,
    SafetyRefusal,
    job_root,
    sweep,
)


class CheckpointRetentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.profile = "r1"
        self.tag = "reviewed_spawn8"
        self.job = job_root(self.output, self.profile, self.tag)
        self.ckpts = self.job / "checkpoints"
        self.ckpts.mkdir(parents=True)
        self._identity()

    def _identity(self, *, profile: str | None = None, diagnostic: bool = False, namespace: str | None = None) -> None:
        profile = profile or self.profile
        root = "a" * 40
        child = "b" * 40
        (self.job / "v3_job_identity.json").write_text(json.dumps({
            "schema": "corrected_phase5_f0_v1",
            "namespace": namespace or str(self.job),
            "diagnostic_only_do_not_resume": diagnostic,
            "root": root,
            "child": child,
            "semantic": {"training_profile": "g2_" + profile.upper(), "root": root, "child": child},
        }), encoding="utf-8")

    def _checkpoint(self, iteration: int, *, complete: bool = True) -> Path:
        name = f"iter_{iteration:09d}"
        directory = self.ckpts / name
        directory.mkdir()
        for part in ("model", "optim", "scheduler", "trainer"):
            sub = directory / part
            sub.mkdir()
            (sub / ".metadata").write_bytes(b"fixture")
        sidecars = directory / "dataloader"
        sidecars.mkdir()
        for rank in range(4):
            (sidecars / f"rank_{rank}.pkl").write_bytes(b"fixture")
        if complete:
            (directory / "complete.v1.json").write_text(json.dumps({
                "schema": "psm_v3_sync_local_v1",
                "complete": True,
                "checkpoint": name,
                "iteration": iteration,
                "world_size": 4,
                "components": {k: {} for k in ("model", "optim", "scheduler", "trainer")},
                "sidecars": {str(k): {} for k in range(4)},
            }), encoding="utf-8")
        return directory

    def _latest(self, iteration: int) -> None:
        (self.ckpts / "latest_checkpoint.txt").write_text(f"iter_{iteration:09d}\n", encoding="utf-8")

    def _sweep(self, apply: bool = True) -> dict:
        return sweep(self.output, self.profile, self.tag, apply=apply, min_age_seconds=0)

    def test_keep_exact_requested_steps(self) -> None:
        self.assertEqual(KEEP, {1000, 5000, 10000, 15000, 20000, 25000, 30000})

    def test_latest_is_never_deleted_and_pointer_never_edited(self) -> None:
        a = self._checkpoint(100)
        self._latest(100)
        self.assertEqual(self._sweep()["deleted"], [])
        self.assertTrue(a.exists())
        b = self._checkpoint(200)
        self._latest(200)
        pointer = (self.ckpts / "latest_checkpoint.txt").read_bytes()
        self.assertEqual(self._sweep()["deleted"], ["iter_000000100"])
        self.assertFalse(a.exists())
        self.assertTrue(b.is_dir())
        self.assertEqual((self.ckpts / "latest_checkpoint.txt").read_bytes(), pointer)

    def test_keeps_milestones_at_all_five_thousand_intervals(self) -> None:
        for value in (900, 1000, 1100, 4900, 5000, 5100, 9900, 10000, 10100, 14900, 15000, 15100, 19900, 20000, 20100, 24900, 25000, 25100, 29900, 30000):
            self._checkpoint(value)
        self._latest(30000)
        result = self._sweep()
        self.assertEqual(result["status"], "APPLIED")
        remaining = {p.name for p in self.ckpts.glob("iter_*") if p.is_dir()}
        self.assertEqual(remaining, {f"iter_{k:09d}" for k in KEEP})

    def test_incomplete_or_staging_is_never_deleted(self) -> None:
        incomplete = self._checkpoint(100, complete=False)
        stage = self.ckpts / ".iter_000000100.inprogress_training"
        stage.mkdir()
        (stage / "partial").write_text("writing", encoding="utf-8")
        self._checkpoint(200)
        self._latest(200)
        report = self._sweep()
        self.assertEqual(report["deleted"], [])
        self.assertTrue(incomplete.exists())
        self.assertTrue(stage.exists())

    def test_current_latest_must_have_full_publication(self) -> None:
        old = self._checkpoint(100)
        self._checkpoint(200, complete=False)
        self._latest(200)
        self.assertEqual(self._sweep()["status"], "WAIT_COMPLETE_LATEST")
        self.assertTrue(old.exists())

    def test_dry_run_reports_without_deletion(self) -> None:
        a = self._checkpoint(100)
        self._checkpoint(200)
        self._latest(200)
        report = self._sweep(apply=False)
        self.assertEqual(report["eligible"], ["iter_000000100"])
        self.assertEqual(report["deleted"], [])
        self.assertTrue(a.exists())

    def test_missing_checkpoint_pointer_is_safe(self) -> None:
        a = self._checkpoint(100)
        self.assertEqual(self._sweep()["status"], "WAIT_FIRST_DCP")
        self.assertTrue(a.exists())

    def test_wrong_namespace_and_diagnostic_job_are_rejected(self) -> None:
        a = self._checkpoint(100)
        self._checkpoint(200)
        self._latest(200)
        self._identity(diagnostic=True)
        with self.assertRaises(SafetyRefusal):
            self._sweep()
        self._identity(namespace=str(self.output / "wrong-job"))
        with self.assertRaises(SafetyRefusal):
            self._sweep()
        self.assertTrue(a.exists())

    def test_invalid_pointer_is_rejected(self) -> None:
        self._checkpoint(100)
        self._checkpoint(200)
        (self.ckpts / "latest_checkpoint.txt").write_text("../other\n", encoding="utf-8")
        with self.assertRaises(SafetyRefusal):
            self._sweep()

    def test_symlink_candidate_and_pointer_are_not_traversed(self) -> None:
        external = self.output / "external-to-keep"
        external.mkdir()
        (external / "valuable").write_text("keep", encoding="utf-8")
        (self.ckpts / "iter_000000100").symlink_to(external, target_is_directory=True)
        self._checkpoint(200)
        self._latest(200)
        self.assertEqual(self._sweep()["deleted"], [])
        self.assertTrue((external / "valuable").exists())
        (self.ckpts / "latest_checkpoint.txt").unlink()
        (self.ckpts / "latest_checkpoint.txt").symlink_to(external / "valuable")
        with self.assertRaises(SafetyRefusal):
            self._sweep()

    def test_only_named_r2_job_is_in_scope(self) -> None:
        a = self._checkpoint(100)
        self._checkpoint(200)
        self._latest(200)
        self.assertEqual(sweep(self.output, "r2", "reviewed_spawn8", apply=True)["status"], "WAIT_JOB")
        self.assertTrue(a.exists())

    def test_missing_job_is_not_error(self) -> None:
        self.assertEqual(sweep(self.output, "r1", "different_tag", apply=True)["status"], "WAIT_JOB")

    def test_recent_publication_has_grace_period(self) -> None:
        first = self._checkpoint(100)
        self._checkpoint(200)
        self._latest(200)
        report = sweep(self.output, "r1", "reviewed_spawn8", apply=True, min_age_seconds=3600)
        self.assertEqual(report["deleted"], [])
        self.assertTrue(first.exists())
        self.assertIn(["iter_000000100", "recent_publish"], report["skipped"])


if __name__ == "__main__":
    unittest.main()
