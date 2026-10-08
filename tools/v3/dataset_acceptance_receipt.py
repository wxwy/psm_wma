#!/usr/bin/env python3
"""Offline, fail-closed acceptance-receipt tooling for corrected V3 exact-window datasets.

This never performs VAE inference, edits a manifest, or changes the Phase1B reader.
The receipt records evidence; only an explicitly reviewed, HMAC-sealed receipt
can be used as a reusable approval witness. Quick verification requires an
operator assertion that underlying assets reside on immutable trusted storage.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "psm_v3_dataset_acceptance_receipt_v1"
EVIDENCE_SCHEMA = "psm_v3_acceptance_evidence_index_v1"
GATES = ("B3", "B4", "B5", "P3P5")
ACCEPT_LITERAL = "APPROVE_V3_DATASET_ACCEPTANCE_RECEIPT"
_HEX = re.compile(r"^[0-9a-f]{64}$")
_SLUG = re.compile(r"[^A-Za-z0-9._-]+")


class ReceiptError(ValueError):
    """Data integrity, authority, or acceptance contract failure."""


def _json(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ReceiptError(f"expected JSON object: {path}")
    return result


def _canonical(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _require_hex(value: Any, label: str) -> str:
    if not isinstance(value, str) or _HEX.fullmatch(value) is None:
        raise ReceiptError(f"{label} must be a lowercase sha256 hex digest")
    return value


def _relative(root: Path, path: Path) -> str:
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ReceiptError(f"non-file, symlink or escaping asset: {path}")
    return path.relative_to(root).as_posix()


def _files(root: Path, area: str, *, include_videos: bool) -> list[Path]:
    if not root.is_dir():
        raise ReceiptError(f"missing directory: {root}")
    if area == "cache":
        files = [root / "dataset_manifest.json", *root.glob("tasks/*/episodes/*.pt")]
    else:
        files = [*root.glob("meta/**/*"), *root.glob("data/**/*")]
        if include_videos:
            files.extend(root.glob("videos/**/*"))
        files = [file for file in files if file.is_file() or file.is_symlink()]
    paths = sorted(files, key=lambda p: str(p.relative_to(root)))
    if len(paths) != len({_relative(root, path) for path in paths}):
        raise ReceiptError(f"duplicate asset path in {area}")
    return paths


def _cache_catalog_manifest(root: Path) -> tuple[dict[str, Any], int, set[str]]:
    path = root / "dataset_manifest.json"
    manifest = _json(path)
    if manifest.get("schema_version") != "exact_window_v1" or manifest.get("source_format") != "lerobot_v3":
        raise ReceiptError("cache manifest is not corrected exact_window_v1/lerobot_v3")
    if manifest.get("camera_set") != "left_wrist" or manifest.get("chunk_length") != 16:
        raise ReceiptError("cache visual/horizon contract mismatch")
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ReceiptError("cache manifest has no tasks")
    expected = {"dataset_manifest.json"}
    episodes = 0
    windows = 0
    classes = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ReceiptError("task entry invalid")
        task_class = task.get("task_class")
        slug = task.get("task_slug")
        if not isinstance(task_class, str) or not task_class.strip() or not isinstance(slug, str):
            raise ReceiptError("task identity invalid")
        if _SLUG.sub("_", task_class).strip("_") != slug or slug in ("", ".", ".."):
            raise ReceiptError("task slug invalid")
        if task_class in classes:
            raise ReceiptError("duplicate task class")
        classes.add(task_class)
        rows = task.get("episodes")
        if not isinstance(rows, list) or not rows:
            raise ReceiptError("task has no episodes")
        for row in rows:
            if not isinstance(row, dict) or row.get("task_class") != task_class or row.get("task_slug") != slug:
                raise ReceiptError("episode/task identity mismatch")
            index = row.get("episode_index")
            count = row.get("window_count")
            if type(index) is not int or index < 0 or type(count) is not int or count <= 0:
                raise ReceiptError("episode index/window count invalid")
            rel = f"tasks/{slug}/episodes/episode_{index:06d}.pt"
            if rel in expected:
                raise ReceiptError("duplicate episode path")
            expected.add(rel)
            episodes += 1
            windows += count
    if (manifest.get("task_class_count"), manifest.get("episode_count"), manifest.get("window_count")) != (
        len(tasks), episodes, windows
    ):
        raise ReceiptError("manifest task/episode/window totals contradict entries")
    actual = {path.relative_to(root).as_posix() for path in _files(root, "cache", include_videos=False)}
    if actual != expected:
        raise ReceiptError(f"cache missing={len(expected-actual)} extra={len(actual-expected)}")
    return manifest, windows, expected


def _witness(path: Path, root: Path) -> dict[str, Any]:
    before = path.stat()
    digest = _sha(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino, before.st_dev) != (
        after.st_size, after.st_mtime_ns, after.st_ino, after.st_dev
    ):
        raise ReceiptError(f"asset mutated during hashing: {path}")
    return {"path": _relative(root, path), "size": before.st_size, "mtime_ns": before.st_mtime_ns, "sha256": digest}


def _inventory(root: Path, area: str, *, include_videos: bool, workers: int) -> list[dict[str, Any]]:
    paths = _files(root, area, include_videos=include_videos)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda p: _witness(p, root), paths))


def _evidence_index(path: Path, *, manifest_sha: str, corpus_digest: str,
                    source_binding_digest: str, vae_sha: str, runtime_sha: str) -> dict[str, Any]:
    index = _json(path)
    if index.get("schema") != EVIDENCE_SCHEMA:
        raise ReceiptError("evidence index schema mismatch")
    for key, expected in (
        ("cache_manifest_sha256", manifest_sha), ("cache_corpus_digest", corpus_digest),
        ("source_binding_digest", source_binding_digest), ("vae_weights_sha256", vae_sha),
        ("runtime_commit", runtime_sha),
    ):
        if index.get(key) != expected:
            raise ReceiptError(f"evidence authority mismatch: {key}")
    rows = index.get("gates")
    if not isinstance(rows, list) or len(rows) != len(GATES):
        raise ReceiptError("evidence must contain exactly B3, B4, B5, P3P5")
    result: dict[str, Any] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ReceiptError("invalid evidence row")
        name = row.get("name")
        status = row.get("status")
        evidence_path = row.get("evidence_path")
        if name not in GATES or name in result or status not in ("PASS", "FAIL", "OPEN"):
            raise ReceiptError(f"invalid gate/name/status: {name!r}/{status!r}")
        if not isinstance(evidence_path, str) or not Path(evidence_path).is_file():
            raise ReceiptError(f"missing evidence bytes for {name}")
        evidence_bytes = _json(Path(evidence_path))
        observed = evidence_bytes.get("status")
        if observed is None and isinstance(evidence_bytes.get("gate"), dict):
            observed = evidence_bytes["gate"].get("status")
        if observed != status:
            raise ReceiptError(f"evidence {name} status {observed!r} contradicts index {status!r}")
        result[name] = {"status": status, "evidence_sha256": _sha(Path(evidence_path))}
    return result


def draft(args: argparse.Namespace) -> dict[str, Any]:
    root, source = args.cache_root, args.source_root
    _, window_count, _ = _cache_catalog_manifest(root)
    msha = _sha(root / "dataset_manifest.json")
    corpus_digest = _require_hex(args.corpus_digest, "corpus_digest")
    source_digest = _require_hex(args.source_binding_digest, "source_binding_digest")
    vae_sha = _require_hex(args.vae_sha256, "vae_sha256")
    if not re.fullmatch(r"[0-9a-f]{40}", args.runtime_commit) or not re.fullmatch(r"[0-9a-f]{40}", args.builder_commit):
        raise ReceiptError("runtime/builder commits must be full 40-hex SHAs")
    if args.workers < 1:
        raise ReceiptError("workers must be positive")
    if args.output.resolve().is_relative_to(root.resolve()) and "tasks" in args.output.relative_to(root).parts:
        raise ReceiptError("receipt must not overwrite episode payload namespace")
    gate_results = _evidence_index(
        args.evidence_index, manifest_sha=msha, corpus_digest=corpus_digest,
        source_binding_digest=source_digest, vae_sha=vae_sha, runtime_sha=args.runtime_commit,
    )
    cache_assets = _inventory(root, "cache", include_videos=False, workers=args.workers)
    source_assets = _inventory(source, "source", include_videos=args.include_videos, workers=args.workers)
    if not source_assets:
        raise ReceiptError("empty source inventory")
    return {
        "schema": SCHEMA,
        "status": "EVIDENCE_ONLY",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "authority": {
            "cache_manifest_sha256": msha,
            "cache_corpus_digest": corpus_digest,
            "source_binding_digest": source_digest,
            "vae_weights_sha256": vae_sha,
            "runtime_commit": args.runtime_commit,
            "builder_commit": args.builder_commit,
        },
        "coverage": {"window_count": window_count, "cache_file_count": len(cache_assets) - 1,
                     "source_file_count": len(source_assets), "source_videos_included": args.include_videos},
        "gates": gate_results,
        "asset_inventory": {"cache": cache_assets, "source": source_assets},
        "decision": None,
        "signature": None,
    }


def _sign(payload: dict[str, Any], secret: bytes) -> str:
    return hmac.new(secret, _canonical({key: value for key, value in payload.items() if key != "signature"}), hashlib.sha256).hexdigest()


def _secret(path: Path) -> bytes:
    key = path.read_bytes()
    if len(key) < 32:
        raise ReceiptError("signing key file must contain at least 32 unpredictable bytes")
    return key


def approve(args: argparse.Namespace) -> dict[str, Any]:
    receipt = _json(args.draft)
    if receipt.get("schema") != SCHEMA or receipt.get("status") != "EVIDENCE_ONLY" or receipt.get("signature") is not None:
        raise ReceiptError("only fresh EVIDENCE_ONLY drafts can be approved")
    gates = receipt.get("gates")
    if not isinstance(gates, dict) or set(gates) != set(GATES) or any(gates[name].get("status") != "PASS" for name in GATES):
        raise ReceiptError("B3/B4/B5/P3P5 must all PASS before receipt approval")
    if not receipt["coverage"].get("source_videos_included"):
        raise ReceiptError("parity approval requires source video input inventory")
    review = args.review_file.read_text(encoding="utf-8")
    if ACCEPT_LITERAL not in review:
        raise ReceiptError(f"review does not contain {ACCEPT_LITERAL}")
    if receipt["authority"]["cache_manifest_sha256"] not in review or receipt["authority"]["source_binding_digest"] not in review:
        raise ReceiptError("review does not bind manifest/source digests")
    receipt["status"] = "ACCEPTED"
    receipt["decision"] = {"literal": ACCEPT_LITERAL, "review_sha256": _sha(args.review_file)}
    receipt["signature"] = _sign(receipt, _secret(args.key_file))
    return receipt


def verify(args: argparse.Namespace) -> dict[str, Any]:
    receipt = _json(args.receipt)
    if receipt.get("schema") != SCHEMA:
        raise ReceiptError("receipt schema mismatch")
    if receipt.get("status") != "ACCEPTED":
        raise ReceiptError("receipt is unapproved; evidence-only draft cannot authorize reuse")
    signature = receipt.get("signature")
    if not isinstance(signature, str) or not hmac.compare_digest(signature, _sign(receipt, _secret(args.key_file))):
        raise ReceiptError("receipt signature invalid")
    if receipt.get("decision", {}).get("literal") != ACCEPT_LITERAL:
        raise ReceiptError("decision literal invalid")
    expected = receipt["authority"]
    for key, value in (("runtime_commit", args.runtime_commit), ("vae_weights_sha256", args.vae_sha256),
                       ("source_binding_digest", args.source_binding_digest)):
        if expected.get(key) != value:
            raise ReceiptError(f"runtime/data authority changed: {key}")
    if _sha(args.cache_root / "dataset_manifest.json") != expected.get("cache_manifest_sha256"):
        raise ReceiptError("cache manifest changed")
    _cache_catalog_manifest(args.cache_root)
    if args.mode == "fast" and not args.trust_immutable_storage:
        raise ReceiptError("fast mode requires explicit --trust-immutable-storage; stat is not a content hash")
    for area, root in (("cache", args.cache_root), ("source", args.source_root)):
        included = receipt["coverage"]["source_videos_included"] if area == "source" else False
        current = _files(root, area, include_videos=included)
        listed = receipt["asset_inventory"][area]
        if [path.relative_to(root).as_posix() for path in current] != [item["path"] for item in listed]:
            raise ReceiptError(f"{area} inventory changed")
        for path, stored in zip(current, listed, strict=True):
            if args.mode == "full":
                if _sha(path) != stored["sha256"]:
                    raise ReceiptError(f"asset content changed: {path}")
            else:
                current_stat = path.stat()
                if current_stat.st_size != stored["size"] or current_stat.st_mtime_ns != stored["mtime_ns"]:
                    raise ReceiptError(f"asset size/mtime changed: {path}")
    if args.require_gate:
        gates = receipt["gates"]
        for gate in args.require_gate:
            if gate not in GATES or gates.get(gate, {}).get("status") != "PASS":
                raise ReceiptError(f"required gate is not PASS: {gate}")
    return {"schema": SCHEMA, "status": "VERIFIED", "mode": args.mode,
            "cache_assets": len(receipt["asset_inventory"]["cache"]),
            "source_assets": len(receipt["asset_inventory"]["source"]),
            "warning": "stat-only trust in immutable storage, not cryptographic byte verification" if args.mode == "fast" else None}


def _write_new(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Never overwrite evidence or an already-issued receipt.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n")
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("draft", help="Hash evidence/data once; never grants Gate approval")
    p.add_argument("--cache-root", type=Path, required=True)
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--evidence-index", type=Path, required=True)
    p.add_argument("--corpus-digest", required=True)
    p.add_argument("--source-binding-digest", required=True)
    p.add_argument("--vae-sha256", required=True)
    p.add_argument("--runtime-commit", required=True)
    p.add_argument("--builder-commit", required=True)
    p.add_argument("--include-videos", action="store_true")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--output", required=True, type=Path)
    p = commands.add_parser("approve", help="Requires an exact reviewed decision and external secret")
    p.add_argument("--draft", required=True, type=Path)
    p.add_argument("--review-file", required=True, type=Path)
    p.add_argument("--key-file", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p = commands.add_parser("verify", help="Verify an approved receipt; fast needs immutable storage")
    p.add_argument("--receipt", required=True, type=Path)
    p.add_argument("--cache-root", required=True, type=Path)
    p.add_argument("--source-root", required=True, type=Path)
    p.add_argument("--key-file", required=True, type=Path)
    p.add_argument("--runtime-commit", required=True)
    p.add_argument("--vae-sha256", required=True)
    p.add_argument("--source-binding-digest", required=True)
    p.add_argument("--require-gate", action="append", default=[])
    p.add_argument("--mode", choices=("full", "fast"), default="full")
    p.add_argument("--trust-immutable-storage", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "draft":
            result = draft(args)
            _write_new(args.output, result)
            print(f"EVIDENCE_ONLY draft written: {args.output}")
        elif args.command == "approve":
            if args.draft.resolve() == args.output.resolve():
                raise ReceiptError("approve must never overwrite original draft")
            result = approve(args)
            _write_new(args.output, result)
            print(f"ACCEPTED receipt written: {args.output}")
        else:
            result = verify(args)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"RECEIPT_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
