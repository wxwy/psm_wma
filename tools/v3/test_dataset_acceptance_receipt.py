"""Receipt is a signed review witness, not a replacement for raw training-window checks."""
from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from dataset_acceptance_receipt import (
    ACCEPT_LITERAL, ReceiptError, _sha, approve, draft, verify,
)


H = "a" * 64
S = "b" * 64
V = "c" * 64
R = "d" * 40
B = "e" * 40


class ReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.cache = root / "cache"
        self.source = root / "source"
        self.cache.mkdir()
        for base, relative in ((self.source, "meta/info.json"), (self.source, "meta/tasks.parquet"),
                               (self.source, "data/chunk-000.parquet"), (self.source, "videos/camera.mp4")):
            path = base / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode())
        episode = self.cache / "tasks" / "CloseFridge" / "episodes" / "episode_000001.pt"
        episode.parent.mkdir(parents=True)
        episode.write_bytes(b"fake tensor bytes")
        self.manifest = self.cache / "dataset_manifest.json"
        self.manifest.write_text(json.dumps({
            "schema_version": "exact_window_v1", "source_format": "lerobot_v3",
            "camera_set": "left_wrist", "chunk_length": 16,
            "task_class_count": 1, "episode_count": 1, "window_count": 2,
            "tasks": [{"task_class": "CloseFridge", "task_slug": "CloseFridge",
                       "episodes": [{"task_class": "CloseFridge", "task_slug": "CloseFridge",
                                     "episode_index": 1, "window_count": 2}]}],
        }))
        self.audit_files = []
        for name in ("B3", "B4", "B5", "P3P5"):
            p = root / f"{name}.json"
            p.write_text(json.dumps({"gate": {"status": "PASS"}, "name": name}))
            self.audit_files.append(p)
        self.evidence_index = root / "index.json"
        self._index()
        self.key_file = root / "key"
        self.key_file.write_bytes(b"a secret used only by unit tests " * 2)
        self.review = root / "approved.md"
        self.review.write_text(f"{ACCEPT_LITERAL}\nmanifest {_sha(self.manifest)}\nsource {S}\n")
        self.draft_path = root / "draft.json"
        self.accepted_path = root / "accepted.json"

    def _index(self, bad_status: str | None = None) -> None:
        rows = []
        for name, path in zip(("B3", "B4", "B5", "P3P5"), self.audit_files):
            rows.append({"name": name, "status": bad_status if name == "P3P5" and bad_status else "PASS",
                         "evidence_path": str(path)})
        self.evidence_index.write_text(json.dumps({
            "schema": "psm_v3_acceptance_evidence_index_v1",
            "cache_manifest_sha256": _sha(self.manifest), "cache_corpus_digest": H,
            "source_binding_digest": S, "vae_weights_sha256": V, "runtime_commit": R,
            "gates": rows,
        }))

    def _draft(self, include_videos: bool = True):
        return draft(argparse.Namespace(
            cache_root=self.cache, source_root=self.source, evidence_index=self.evidence_index,
            corpus_digest=H, source_binding_digest=S, vae_sha256=V, runtime_commit=R,
            builder_commit=B, include_videos=include_videos, workers=2, output=self.draft_path,
        ))

    def _approve(self, receipt):
        self.draft_path.write_text(json.dumps(receipt))
        return approve(argparse.Namespace(draft=self.draft_path, review_file=self.review, key_file=self.key_file))

    def _verify(self, receipt, *, mode="full", trust=False, **kwargs):
        self.accepted_path.write_text(json.dumps(receipt))
        return verify(argparse.Namespace(
            receipt=self.accepted_path, cache_root=self.cache, source_root=self.source,
            key_file=self.key_file, runtime_commit=kwargs.get("runtime_commit", R),
            vae_sha256=kwargs.get("vae_sha256", V), source_binding_digest=kwargs.get("source_binding_digest", S),
            require_gate=["P3P5"], mode=mode, trust_immutable_storage=trust,
        ))

    def test_full_roundtrip(self):
        draft_receipt = self._draft()
        self.assertEqual(draft_receipt["status"], "EVIDENCE_ONLY")
        accepted = self._approve(draft_receipt)
        self.assertEqual(self._verify(accepted)["status"], "VERIFIED")
        self.assertEqual(self._verify(accepted, mode="fast", trust=True)["status"], "VERIFIED")

    def test_open_gate_cannot_be_approved(self):
        self._index(bad_status="OPEN")
        with self.assertRaises(ReceiptError):
            self._approve(self._draft())

    def test_no_video_scope_cannot_approve_parity(self):
        with self.assertRaises(ReceiptError):
            self._approve(self._draft(include_videos=False))

    def test_modified_cache_bytes_full_fails(self):
        accepted = self._approve(self._draft())
        cache_file = self.cache / "tasks/CloseFridge/episodes/episode_000001.pt"
        cache_file.write_bytes(b"tampered")
        with self.assertRaisesRegex(ReceiptError, "content changed"):
            self._verify(accepted)

    def test_modified_source_bytes_full_fails(self):
        accepted = self._approve(self._draft())
        (self.source / "data/chunk-000.parquet").write_bytes(b"changed")
        with self.assertRaisesRegex(ReceiptError, "content changed"):
            self._verify(accepted)

    def test_missing_and_extra_file_fail(self):
        accepted = self._approve(self._draft())
        (self.cache / "tasks/CloseFridge/episodes/episode_000002.pt").write_bytes(b"extra")
        with self.assertRaises(ReceiptError):
            self._verify(accepted)

    def test_unapproved_fails(self):
        with self.assertRaisesRegex(ReceiptError, "unapproved"):
            self._verify(self._draft())

    def test_bad_signature_fails(self):
        accepted = self._approve(self._draft())
        accepted["authority"]["runtime_commit"] = "f" * 40
        with self.assertRaisesRegex(ReceiptError, "signature"):
            self._verify(accepted)

    def test_runtime_vae_source_change_fails(self):
        accepted = self._approve(self._draft())
        for field, new in (("runtime_commit", "f" * 40), ("vae_sha256", "f" * 64),
                           ("source_binding_digest", "f" * 64)):
            with self.assertRaisesRegex(ReceiptError, "authority changed"):
                self._verify(accepted, **{field: new})

    def test_fast_requires_immutable_trust(self):
        accepted = self._approve(self._draft())
        with self.assertRaisesRegex(ReceiptError, "--trust-immutable-storage"):
            self._verify(accepted, mode="fast")

    def test_fast_detects_touch(self):
        accepted = self._approve(self._draft())
        p = self.source / "data/chunk-000.parquet"
        st = p.stat()
        import os
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns+1_000))
        with self.assertRaisesRegex(ReceiptError, "size/mtime changed"):
            self._verify(accepted, mode="fast", trust=True)

    def test_manifest_change_fails(self):
        accepted = self._approve(self._draft())
        self.manifest.write_text(self.manifest.read_text() + "\n")
        with self.assertRaisesRegex(ReceiptError, "cache manifest changed"):
            self._verify(accepted)

    def test_lied_evidence_status_fails(self):
        self._index()
        self.audit_files[-1].write_text(json.dumps({"gate": {"status": "FAIL"}, "name": "P3P5"}))
        with self.assertRaisesRegex(ReceiptError, "contradicts"):
            self._draft()

    def test_evidence_index_mismatch_fails(self):
        self._index()
        index = json.loads(self.evidence_index.read_text())
        index["vae_weights_sha256"] = "f" * 64
        self.evidence_index.write_text(json.dumps(index))
        with self.assertRaises(ReceiptError):
            self._draft()


if __name__ == "__main__":
    unittest.main()
