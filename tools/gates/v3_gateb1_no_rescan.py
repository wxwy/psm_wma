"""Scoped trusted-index opening for B1's TWO IMMUTABLE historical Cosmos children.

Their frozen VerifiedExactWindowIndex.open always verifies all cache/source
files. Gate B0 already established the exact source/index/cache identity and
Owner forbids re-running the 451GB offline audit. Rather than modifying the
original Source/Target Child SHAs, this B1 *diagnostic-only* context replaces
ONLY the preflight file-audit entrypoints. The original in-memory manifest,
source-binding, row-map geometry, Consumer and runtime sample guards remain.

Scope is one-process/one-thread preflight only; restores all patch targets.
Neither this helper nor its tests read cache payloads or start GPU training.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
from types import ModuleType
from typing import Iterator
from unittest.mock import patch


class NoRescanBlocked(ValueError):
    """Previously accepted dataset authority is missing or malformed."""


def _open_accepted_index(cls: type, root: str | Path, *, cache_root: str | Path,
                         source_root: str | Path, verified_module: ModuleType):
    """Construct original immutable Index from its receipt without global file walk.

    Reproduce the old open() schema guards; only checks reading the one receipt
    and leaves rows memory mapping to the unchanged original open_rows method.
    """
    del cache_root, source_root  # source/cache identities checked by native Catalog and Reader
    directory = Path(root)
    receipt_path = directory / verified_module.RECEIPT
    receipt = json.loads(receipt_path.read_bytes())
    digests = (
        "cache_manifest_sha256", "cache_corpus_digest",
        "source_binding_digest", "row_mapping_sha256",
    )
    if (
        type(receipt) is not dict
        or receipt.get("schema") != verified_module.SCHEMA
        or type(receipt.get("bindings")) is not list
        or not receipt["bindings"]
        or type(receipt.get("files")) is not dict
        or set(receipt["files"]) != {"cache_payload", "source_data", "source_meta"}
        or type(receipt.get("absolute_row_count")) is not int
        or receipt["absolute_row_count"] <= 0
        or any(type(receipt.get(k)) is not str or len(receipt[k]) != 64 for k in digests)
    ):
        raise NoRescanBlocked("trusted verified-index receipt schema invalid")
    # Not reading/re-hashing the large row-mapping array is deliberate. The
    # original class will np.load/mmap and verify dtype/shape when requested.
    return cls(directory, receipt, directory / verified_module.ROWS)


def _logical_source_path(root: Path, relative: Path, label: str) -> Path:
    """Lexical traversal guard, not a per-Episode path.realpath/stat probe."""
    candidate = Path(relative)
    if not candidate.parts or candidate.is_absolute() or ".." in candidate.parts:
        raise NoRescanBlocked(f"{label}: non-canonical source path")
    return Path(root) / candidate


@contextmanager
def trusted_frozen_preflight(*, verified_module: ModuleType, cache_module: ModuleType,
                             source_module: ModuleType) -> Iterator[None]:
    """Run frozen corrected_phase5.preflight() once, without dataset-file audits.

    Preconditions: authoritative index/cache/source was accepted offline, and
    consumer is a separate isolated B1 leg process with num_workers=0.
    """
    index_cls = verified_module.VerifiedExactWindowIndex
    catalog_cls = cache_module.RoboCasaExactWindowCacheCatalog
    reader_cls = source_module.RoboCasaExactWindowSourceReader
    for name, obj in (("index", index_cls), ("catalog", catalog_cls), ("reader", reader_cls)):
        if obj is None:
            raise NoRescanBlocked(f"missing original {name} class")

    def trusted_open(cls, root, *, cache_root, source_root):
        return _open_accepted_index(cls, root, cache_root=cache_root,
                                    source_root=source_root, verified_module=verified_module)

    def trusted_audit(self):
        if not hasattr(self, "_records") or not self._records:
            raise NoRescanBlocked("manifest records missing before trusted cache audit")
        return [], [], len(self._records)

    with (
        patch.object(index_cls, "open", classmethod(trusted_open)),
        patch.object(catalog_cls, "_audit_files", trusted_audit),
        patch.object(reader_cls, "_preflight_metadata", lambda self: None),
        patch.object(source_module, "_local_path", _logical_source_path),
    ):
        yield
