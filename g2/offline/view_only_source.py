"""Lossless, bounded working-source compression for View-first Stage A.

VAE-enabled jobs keep the existing full-source/ACK/retirement protocol unchanged.
View-only jobs keep every source byte reversibly, allowing a separate future
VAE ingestion stage without accumulating 30 MiB JSON per episode.
"""

from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
import os
from functools import lru_cache
from pathlib import Path

from g2.io import digest, parse_json, read_json
from g2.latent_cache.contract import CacheError, contained, fingerprint
from g2.latent_cache.storage import atomic_json

FULL = "spatial_source.json"
PACKED = "spatial_source.json.gz"
RECEIPT = "SPATIAL_SOURCE_GZIP.json"
CLAIM = ".g2_view_only_claim.json"
SOURCE_SCHEMA = "g2_view_only_source_gzip_v1"
CLAIM_SCHEMA = "g2_view_only_output_claim_v1"
MAX_RAW_BYTES = 1024 * 1024**2
MAX_PACKED_BYTES = 256 * 1024**2
VAE_SOURCE_SCHEMA = "g2_view_first_working_source_v1"
RAW_SCHEMA = "g2_working_source_json_v1"


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


def _decode_gzip_bounded(z, expected_bytes):
    """Decode one immutable compressed byte string; never trust its filename."""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(z)) as reader:
            raw = reader.read(expected_bytes + 1)
            if len(raw) > expected_bytes:
                raise CacheError("unbounded compressed source")
    except (OSError, EOFError) as exc:
        raise CacheError("working source gzip corrupted") from exc
    try:
        source = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise CacheError("working source is not valid JSON") from exc
    if not isinstance(source, dict) or source.get("source_id") is None:
        raise CacheError("working source identity missing")
    return (
        raw,
        source,
        _sha(raw),
        fingerprint({k: v for k, v in source.items() if k != "source_id"}),
    )


@lru_cache(maxsize=1)
def _cached_decode_gzip(z, expected_bytes):
    """Only exact compressed *bytes* are cached, not paths, stat or mtimes.

    Source bytes are always re-read and SHA-verified against the signed gzip
    receipt; a changed byte string never hits this cache. A defensive copy of
    the cached JSON tree is returned to callers, preventing cross-call mutation.
    Limit eligible raw and compressed sizes and hold at most one Episode.
    """
    return _decode_gzip_bounded(z, expected_bytes)


MAX_CACHED_RAW_BYTES = 64 * 1024**2
MAX_CACHED_GZIP_BYTES = 16 * 1024**2


def working_source_info(root, *, include_raw=False):
    """Verified working bytes/transport identity; never materialize a JSON copy.

    A typed gzip receipt is the explicit declaration used by existing PR66
    outputs. The profile and original readiness bind its logical raw identity.
    A final capsule is deliberately not a full working source.
    """
    root = Path(root).absolute()
    manifest = read_json(contained(root, "episode_manifest.json"))
    if manifest.get("schema") != "g2_spatial_profile_episode_v1":
        raise CacheError("working source requires an explicit working profile schema")
    full = contained(root, FULL, allow_missing=True)
    zipped = contained(root, PACKED, allow_missing=True)
    receipt = contained(root, RECEIPT, allow_missing=True)
    packed_mode = receipt.exists()
    if not packed_mode:
        if zipped.exists() or receipt.exists() or not full.is_file():
            raise CacheError("ambiguous working-source compression state")
        if full.stat().st_size > MAX_RAW_BYTES:
            raise CacheError("working source exceeds finite bound")
        raw = full.read_bytes()
    else:
        if full.exists() or manifest["output_profile"]["view_vae"]:
            raise CacheError("gzip source requires an unambiguous View-first profile")
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
        if (
            type(doc["raw_bytes"]) is not int
            or not 0 < doc["raw_bytes"] <= MAX_RAW_BYTES
            or type(doc["gzip_bytes"]) is not int
            or not 0 < doc["gzip_bytes"] <= MAX_PACKED_BYTES
        ):
            raise CacheError("declared compressed source sizes exceed finite bounds")
        cached = (
            doc["raw_bytes"] <= MAX_CACHED_RAW_BYTES and len(z) <= MAX_CACHED_GZIP_BYTES
        )
        raw, decoded_source, decoded_sha, source_fingerprint = (
            _cached_decode_gzip(z, doc["raw_bytes"])
            if cached
            else _decode_gzip_bounded(z, doc["raw_bytes"])
        )
        if (
            len(raw) > MAX_RAW_BYTES
            or doc["raw_sha256"] != decoded_sha
            or doc["raw_bytes"] != len(raw)
        ):
            raise CacheError("decompressed working source identity differs")
        source = copy.deepcopy(decoded_source) if cached else decoded_source
    if not packed_mode:
        try:
            source = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise CacheError("working source is not valid JSON") from exc
        if not isinstance(source, dict) or source.get("source_id") is None:
            raise CacheError("working source identity missing")
        source_fingerprint = fingerprint(
            {k: v for k, v in source.items() if k != "source_id"}
        )
        decoded_sha = _sha(raw)
    if packed_mode and doc["source_id"] != source["source_id"]:
        raise CacheError("View-only compression source ID differs")
    ready = read_json(contained(root, "SPATIAL_SOURCE_READY.json"))
    if (
        source.get("schema") != "g2_sealed_spatial_source_v1"
        or ready.get("schema") != "g2_sealed_spatial_source_v1"
        or source["source_id"] != source_fingerprint
        or source["source_id"] != manifest["source_id"]
        or ready.get("source_id") != source["source_id"]
        or ready.get("source_manifest_sha256") != decoded_sha
        or ready.get("complete_spatial_source") is not True
        or ready.get("profile_complete") is not False
    ):
        raise CacheError("working bytes differ from original source readiness")
    identity = PACKED if packed_mode else FULL
    names = (
        (identity, "SPATIAL_SOURCE_READY.json", RECEIPT)
        if packed_mode
        else (identity, "SPATIAL_SOURCE_READY.json")
    )
    files = {name: digest(contained(root, name)) for name in names}
    if files[identity] != _sha(z if packed_mode else raw):
        raise CacheError("working source changed during verified reading")
    return dict(
        source=source,
        raw_sha256=decoded_sha,
        raw_bytes=len(raw),
        format_schema=SOURCE_SCHEMA if packed_mode else RAW_SCHEMA,
        identity_manifest=identity,
        files=files,
        **(dict(raw=raw) if include_raw else {}),
    )


def load_working_source(root):
    """Backward-compatible tuple API for verified full working data only."""
    info = working_source_info(root)
    return info["source"], info["raw_sha256"]


def view_first_binding(root, info=None):
    info = working_source_info(root) if info is None else info
    return dict(
        schema=VAE_SOURCE_SCHEMA,
        source_id=info["source"]["source_id"],
        manifest_sha256=info["files"][info["identity_manifest"]],
        complete_sha256=info["files"]["SPATIAL_SOURCE_READY.json"],
        identity_manifest=info["identity_manifest"],
        readiness_marker="SPATIAL_SOURCE_READY.json",
        raw_source_sha256=info["raw_sha256"],
        working_storage=dict(schema=info["format_schema"], files=info["files"]),
        validation_scope="VERIFIED_PUBLISHED_VIEW_FIRST_AND_EXACT_WORKING_BYTES",
    )


def verify_published_working_binding(root, source):
    """Recheck the exact files of a previously verified, SHA-pinned cache source."""
    root = Path(root).absolute()
    manifest = read_json(contained(root, "episode_manifest.json"))
    identity = source.get("identity_manifest")
    if identity not in {FULL, PACKED}:
        raise CacheError("unknown pinned working source format")
    packed = identity == PACKED
    file_path = contained(root, identity)
    ready_name = "SPATIAL_SOURCE_READY.json"
    storage = source.get("working_storage", {})
    names = {identity, ready_name, RECEIPT} if packed else {identity, ready_name}
    if (
        manifest.get("schema") != "g2_spatial_profile_episode_v1"
        or manifest.get("source_id") != source.get("source_id")
        or storage.get("schema") != (SOURCE_SCHEMA if packed else RAW_SCHEMA)
        or set(storage.get("files", {})) != names
        or file_path.stat().st_size > (MAX_PACKED_BYTES if packed else MAX_RAW_BYTES)
        or contained(root, FULL if packed else PACKED, allow_missing=True).exists()
        or (packed and manifest["output_profile"]["view_vae"])
        or (not packed and contained(root, RECEIPT, allow_missing=True).exists())
    ):
        raise CacheError("pinned View-first working-source profile differs")
    files = {identity: digest(file_path)}
    if files[identity] != storage["files"][identity]:
        raise CacheError("pinned working source bytes changed")

    def read_proof(name):
        with contained(root, name).open("rb") as stream:
            data = stream.read(1024 * 1024 + 1)
        files[name] = _sha(data)
        if len(data) > 1024 * 1024 or files[name] != storage["files"][name]:
            raise CacheError("pinned working source receipt changed")
        return parse_json(data)

    ready = read_proof(ready_name)
    raw_sha = ready.get("source_manifest_sha256")
    if (
        ready.get("schema") != "g2_sealed_spatial_source_v1"
        or ready.get("source_id") != source["source_id"]
        or ready.get("complete_spatial_source") is not True
        or ready.get("profile_complete") is not False
        or raw_sha != source.get("raw_source_sha256")
    ):
        raise CacheError("pinned working source readiness differs")
    if packed:
        proof = read_proof(RECEIPT)
        if (
            proof.get("schema") != SOURCE_SCHEMA
            or proof.get("source_id") != source["source_id"]
            or proof.get("raw_sha256") != raw_sha
            or proof.get("gzip_sha256") != files[identity]
            or proof.get("gzip_bytes") != file_path.stat().st_size
            or type(proof.get("raw_bytes")) is not int
            or not 0 < proof["raw_bytes"] <= MAX_RAW_BYTES
            or proof.get("receipt_id")
            != fingerprint({k: v for k, v in proof.items() if k != "receipt_id"})
        ):
            raise CacheError("pinned gzip source receipt differs")
    elif raw_sha != files[identity]:
        raise CacheError("pinned raw source bytes differ from readiness")
    return view_first_binding(
        root,
        dict(
            source={"source_id": ready["source_id"]},
            files=files,
            identity_manifest=identity,
            format_schema=storage["schema"],
            raw_sha256=raw_sha,
        ),
    )


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
    if (
        not isinstance(source_selection_sha256, str)
        or len(source_selection_sha256) != 64
    ):
        raise CacheError("source selection fingerprint required")
    root.mkdir(parents=True, exist_ok=True)
    marker = contained(root, CLAIM, allow_missing=True)
    expected = _claim_contents(root, profile, source_selection_sha256)
    if marker.exists():
        if read_json(marker) != expected:
            raise CacheError(
                "View-only output root belongs to a different source/profile"
            )
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
            "schema",
            "output_root",
            "profile_id",
            "source_selection_sha256",
            "source_format",
            "vae_disabled",
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
