"""Stage-A/A2 boundary only; this is not a background VAE consumer implementation.

Both eventual consumers must use the existing encoding/storage APIs. Events
carry copied final bytes; final source ownership is sealed independently, before
VAE completion. No legacy COMPLETE marker is synthesized to break that cycle.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .contract import CacheError, fingerprint, safe_relative
from .storage import atomic_json


@dataclass(frozen=True)
class ConsumerLimits:
    max_events: int = 32
    max_spool_bytes: int = 256 * 1024 * 1024

    def __post_init__(self):
        if any(
            type(x) is not int or x < 1 for x in (self.max_events, self.max_spool_bytes)
        ):
            raise CacheError("consumer limits must be positive; no unbounded mode")


@dataclass(frozen=True)
class FinalPixelEvent:
    event_id: str
    episode_key: str
    view_id: str
    canonical_view_id: str
    variant: str
    rgb_sha256: str
    final_pixel_phase: str
    png_bytes: bytes
    source_fingerprint: str
    profile_id: str
    pixel_record_key: str

    def descriptor(self):
        return {k: v for k, v in self.__dict__.items() if k != "png_bytes"}


def final_pixel_event(
    path,
    *,
    episode_key,
    view_id,
    canonical_view_id,
    variant,
    source_fingerprint,
    profile_id,
):
    safe_relative(view_id)
    safe_relative(canonical_view_id)
    if variant not in ("clean", "w_rbs"):
        raise CacheError("unknown finalized pixel variant")
    data = Path(path).read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise CacheError("final event must contain a real PNG")
    sha = hashlib.sha256(data).hexdigest()
    identity = dict(
        episode_key=episode_key,
        view_id=view_id,
        rgb_sha256=sha,
        source_fingerprint=source_fingerprint,
        profile_id=profile_id,
    )
    return FinalPixelEvent(
        fingerprint(identity),
        episode_key,
        view_id,
        canonical_view_id,
        variant,
        sha,
        "FINAL_MARKER_PIXELS" if variant == "w_rbs" else "FINAL_CLEAN_PIXELS",
        bytes(data),
        source_fingerprint,
        profile_id,
        # Numeric reuse is pixel+View+recipe based, separate from publication
        # scope. Language/template changes must not require new VAE math.
        fingerprint(dict(view_id=view_id, rgb_sha256=sha)),
    )


def seal_source(root, inventory):
    """Source readiness precedes VAE; queue admission is not profile completion."""
    from g2.offline.output_profile import SOURCE_SCHEMA

    if inventory.get("schema") != SOURCE_SCHEMA:
        raise CacheError("explicit new source inventory schema is required")
    body = dict(inventory)
    body["source_id"] = fingerprint(inventory)
    root = Path(root)
    atomic_json(root / "spatial_source.json", body)
    atomic_json(
        root / "SPATIAL_SOURCE_READY.json",
        dict(
            schema=SOURCE_SCHEMA,
            source_id=body["source_id"],
            source_manifest_sha256=hashlib.sha256(
                (root / "spatial_source.json").read_bytes()
            ).hexdigest(),
            complete_spatial_source=True,
            profile_complete=False,
        ),
    )
    return body["source_id"]
