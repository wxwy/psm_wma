"""Lossless, bounded working-source compression for View-first Stage A.

VAE-enabled jobs keep the existing full-source/ACK/retirement protocol unchanged.
View-only jobs keep every source byte reversibly, allowing a separate future
VAE ingestion stage without accumulating 30 MiB JSON per episode.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path

from g2.io import read_json

from g2.latent_cache.contract import CacheError, contained, fingerprint
from g2.latent_cache.storage import atomic_json

FULL = "spatial_source.json"
PACKED = "spatial_source.json.gz"
RECEIPT = "SPATIAL_SOURCE_GZIP.json"
CLAIM = ".g2_view_only_claim.json"
SOURCE_SCHEMA = "g2_view_only_source_gzip_v1"
CLAIM_SCHEMA = "g2_view_only_output_claim_v1"
MAX_RAW_BYTES = 128 * 1024**2
MAX_PACKED_BYTES = 32 * 1024**2


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _gzip_receipt(raw, zipped, source_id):
    fields = dict(
        schema=SOURCE_SCHEMA,
        raw_sha256=_sha(raw),
        gzip_sha256=_sha(zipped),
        raw_bytes=len(raw),
        gzip_bytes=len(zipped),
        source_id=source_id,
    )
    return dict(fields, receipt_id=fingerprint(fields))


def load_working_source(root):
    """Read a full working source or a verified lossless gzip, never both."""
    root = Path(root).absolute()
    full = contained(root, FULL, allow_missing=True)
    zipped = contained(root, PACKED, allow_missing=True)
    receipt = contained(root, RECEIPT, allow_missing=True)
    if full.exists():
        if zipped.exists() or receipt.exists() or not full.is_file():
            raise CacheError("ambiguous working-source compression state")
        if full.stat().st_size > MAX_RAW_BYTES:
            raise CacheError("working source exceeds finite bound")
        raw = full.read_bytes()
    else:
        if not zipped.is_file() or not receipt.is_file():
            raise CacheError("working source or signed gzip receipt missing")
        if zipped.stat().st_size > MAX_PACKED_BYTES:
            raise CacheError("compressed source exceeds finite bound")
        z = zipped.read_bytes()
        doc = read_json(receipt)
        if not isinstance(doc, dict) or doc.get("schema") != SOURCE_SCHEMA:
            raise CacheError("invalid View-only compression receipt")
        if set(doc) != {
            "schema",
            "raw_sha256",
            "gzip_sha256",
            "raw_bytes",
            "gzip_bytes",
            "source_id",
            "receipt_id",
        }:
            raise CacheError("unknown View-only compression receipt keys")
        expected = fingerprint({k: v for k, v in doc.items() if k != "receipt_id"})
        if doc["receipt_id"] != expected:
            raise CacheError("View-only compression receipt identity differs")
        if doc["gzip_sha256"] != _sha(z) or doc["gzip_bytes"] != len(z):
            raise CacheError("compressed source bytes changed")
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(z)) as reader:
                raw = reader.read(MAX_RAW_BYTES + 1)
                if reader.read(1):
                    raise CacheError("unbounded compressed source")
        except (OSError, EOFError) as exc:
            raise CacheError("working source gzip corrupted") from exc
        if (
            len(raw) > MAX_RAW_BYTES
            or doc["raw_sha256"] != _sha(raw)
            or doc["raw_bytes"] != len(raw)
        ):
            raise CacheError("decompressed working source identity differs")
    try:
        source = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise CacheError("working source is not valid JSON") from exc
    if not isinstance(source, dict) or source.get("source_id") is None:
        raise CacheError("working source identity missing")
    if not full.exists() and doc["source_id"] != source["source_id"]:
        raise CacheError("View-only compression source ID differs")
    return source, _sha(raw)


def compress_working_source(root):
    """Compress a not-yet-published View-only source before atomic episode rename."""
    root = Path(root).absolute()
    full = contained(root, FULL)
    zipped = contained(root, PACKED, allow_missing=True)
    receipt = contained(root, RECEIPT, allow_missing=True)
    if zipped.exists() or receipt.exists():
        raise CacheError("View-only source compression already exists")
    raw = full.read_bytes()
    if len(raw) > MAX_RAW_BYTES:
        raise CacheError("View-only source exceeds maximum size")
    source = json.loads(raw)
    z = gzip.compress(raw, compresslevel=1, mtime=0)
    if len(z) > MAX_PACKED_BYTES:
        raise CacheError("View-only gzip exceeds maximum size")
    temp = root / (".view-only-source-" + str(os.getpid()) + ".tmp")
    with temp.open("xb") as handle:
        handle.write(z)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, zipped)
    atomic_json(receipt, _gzip_receipt(raw, z, source["source_id"]))
    full.unlink()
    # Verify against the existing immutable source-readiness hash; no source ID changed.
    loaded, raw_sha = load_working_source(root)
    ready = read_json(contained(root, "SPATIAL_SOURCE_READY.json"))
    if loaded != source or ready.get("source_manifest_sha256") != raw_sha:
        raise CacheError("compressed source is not identical to source readiness")
    return receipt


def _claim_contents(root, profile, source_selection_sha256):
    return dict(
        schema=CLAIM_SCHEMA,
        output_root=str(Path(root).absolute()),
        profile_id=profile.to_dict()["profile_id"],
        source_selection_sha256=source_selection_sha256,
        source_format=SOURCE_SCHEMA,
        vae_disabled=True,
    )


def claim_view_only_root(root, profile, source_selection_sha256):
    """Claim only a fresh empty output root, or revalidate the exact same plan."""
    root = Path(root).absolute()
    if root.is_symlink() or any(p.is_symlink() for p in root.parents):
        raise CacheError("View-only output cannot contain symlinks")
    if profile.view_vae:
        raise CacheError("View-only claim cannot advertise a VAE profile")
    if not isinstance(source_selection_sha256, str) or len(source_selection_sha256) != 64:
        raise CacheError("source selection fingerprint required")
    root.mkdir(parents=True, exist_ok=True)
    marker = contained(root, CLAIM, allow_missing=True)
    expected = _claim_contents(root, profile, source_selection_sha256)
    if marker.exists():
        if read_json(marker) != expected:
            raise CacheError("View-only output root belongs to a different source/profile")
    else:
        if any(root.iterdir()):
            raise CacheError("legacy output path contains unowned data")
        atomic_json(marker, expected)
    return expected


def verify_view_only_claim(root, profile):
    """Worker-side verification without filesystem-owner or source upgrades."""
    root = Path(root).absolute()
    if profile.view_vae:
        raise CacheError("VAE jobs cannot use the View-only root claim")
    marker = read_json(contained(root, CLAIM))
    if (
        not isinstance(marker, dict)
        or set(marker)
        != {
            "schema", "output_root", "profile_id",
            "source_selection_sha256", "source_format", "vae_disabled",
        }
        or marker.get("schema") != CLAIM_SCHEMA
        or marker.get("output_root") != str(root)
        or marker.get("profile_id") != profile.to_dict()["profile_id"]
        or marker.get("source_format") != SOURCE_SCHEMA
        or marker.get("vae_disabled") is not True
        or type(marker.get("source_selection_sha256")) is not str
        or len(marker["source_selection_sha256"]) != 64
    ):
        raise CacheError("View-only output root not owned by this exact profile")
    return marker
