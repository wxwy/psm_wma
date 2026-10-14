"""CPU mock contracts for isolated no-full-data-rescan preflight."""
from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType

import pytest

from v3_gateb1_no_rescan import NoRescanBlocked, trusted_frozen_preflight, _logical_source_path


class Index:
    def __init__(self, path, receipt, rows):
        self.path, self.receipt, self.rows = path, receipt, rows

    @classmethod
    def open(cls, *args, **kwargs):
        raise RuntimeError("forbidden production full data verification")


class Catalog:
    def __init__(self):
        self._records = {"episode0": 1, "episode1": 2}

    def _audit_files(self):
        raise RuntimeError("forbidden production cache stat/glob")


class Reader:
    def _preflight_metadata(self):
        raise RuntimeError("forbidden production meta rglob")


def schema(tmp_path):
    path = tmp_path / "accepted_index"
    path.mkdir()
    receipt = {
        "schema": "accepted_index_v1", "bindings": ["identity"],
        "files": {"cache_payload": [], "source_data": [], "source_meta": []},
        "absolute_row_count": 4,
        "cache_manifest_sha256": "a" * 64, "cache_corpus_digest": "b" * 64,
        "source_binding_digest": "c" * 64, "row_mapping_sha256": "d" * 64,
    }
    (path / "receipt.json").write_text(json.dumps(receipt))
    return path, receipt


def modules():
    iv = ModuleType("verified")
    iv.RECEIPT, iv.ROWS, iv.SCHEMA = "receipt.json", "rows.npy", "accepted_index_v1"
    iv.VerifiedExactWindowIndex = Index
    cv = ModuleType("cache")
    cv.RoboCasaExactWindowCacheCatalog = Catalog
    sv = ModuleType("source")
    sv.RoboCasaExactWindowSourceReader = Reader
    sv._local_path = lambda *a: (_ for _ in ()).throw(RuntimeError("forbidden selected path resolve/stat"))
    return iv, cv, sv


def test_accepted_receipt_constructs_native_type_without_all_dataset_calls(tmp_path):
    path, receipt = schema(tmp_path)
    iv, cv, sv = modules()
    original_open = Index.open.__func__
    old_local = sv._local_path
    with trusted_frozen_preflight(verified_module=iv, cache_module=cv, source_module=sv):
        index = Index.open(path, cache_root=tmp_path / "cache", source_root=tmp_path / "source")
        assert isinstance(index, Index) and index.receipt == receipt
        assert index.rows == path / "rows.npy"  # not read/hashed at startup
        assert Catalog()._audit_files() == ([], [], 2)
        Reader()._preflight_metadata()
        assert sv._local_path(tmp_path, Path("data/chunk-0.parquet"), "selected") == tmp_path / "data/chunk-0.parquet"
    assert Index.open.__func__ is original_open
    assert sv._local_path is old_local
    with pytest.raises(RuntimeError, match="forbidden production"):
        Index.open(path, cache_root=tmp_path, source_root=tmp_path)
    with pytest.raises(RuntimeError, match="forbidden production"):
        Catalog()._audit_files()
    with pytest.raises(RuntimeError, match="forbidden production"):
        Reader()._preflight_metadata()


@pytest.mark.parametrize("field,value", [
    ("schema", "wrong"), ("bindings", []), ("files", {"cache_payload": []}),
    ("absolute_row_count", 0), ("cache_corpus_digest", "garbage"),
])
def test_untrusted_receipt_shape_fails_before_using_index(tmp_path, field, value):
    path, receipt = schema(tmp_path)
    receipt[field] = value
    (path / "receipt.json").write_text(json.dumps(receipt))
    iv, cv, sv = modules()
    with trusted_frozen_preflight(verified_module=iv, cache_module=cv, source_module=sv):
        with pytest.raises(NoRescanBlocked, match="schema"):
            Index.open(path, cache_root=tmp_path, source_root=tmp_path)


@pytest.mark.parametrize("path", [Path("../secret"), Path("/etc/passwd"), Path("data/../../secret")])
def test_logical_data_path_traversal_rejected_without_stat(path, tmp_path):
    with pytest.raises(NoRescanBlocked, match="non-canonical"):
        _logical_source_path(tmp_path, path, "selected")


def test_method_replacement_restores_if_validation_crashes(tmp_path):
    path, receipt = schema(tmp_path)
    receipt["schema"] = "tampered"
    (path / "receipt.json").write_text(json.dumps(receipt))
    iv, cv, sv = modules()
    with pytest.raises(NoRescanBlocked):
        with trusted_frozen_preflight(verified_module=iv, cache_module=cv, source_module=sv):
            Index.open(path, cache_root=tmp_path, source_root=tmp_path)
    with pytest.raises(RuntimeError, match="forbidden production"):
        Catalog()._audit_files()
