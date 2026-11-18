"""One authoritative source scan per independent published-Episode admission."""

import pytest

from g2.io import digest
from g2.latent_cache import sealed_source
from g2.latent_cache.batch_engine import BatchEngine
from g2.latent_cache.contract import CacheError
from g2.tests.test_batch_engine import init, sample


def test_discover_registers_with_one_authoritative_offer_scan(tmp_path, monkeypatch):
    root, _ = sample(tmp_path)
    before = {
        str(p.relative_to(root)): digest(p) for p in root.rglob("*") if p.is_file()
    }
    spool, spec = init(tmp_path)
    expected = sealed_source.scan_source
    calls = []

    def scanned(*args, **kwargs):
        calls.append(str(args[0]))
        return expected(*args, **kwargs)

    monkeypatch.setattr(sealed_source, "scan_source", scanned)
    engine = BatchEngine(
        spool, spec, mode="independent", dataset_root=tmp_path / "dataset"
    )
    try:
        engine._discover()
        assert calls == [str(root)]
        with spool._db() as db:
            row = db.execute("SELECT target,source_ready FROM jobs").fetchone()
            assert row is not None and row["target"] == str(root)
            assert row["source_ready"] is not None
        assert not (root / "vae_cache/COMPLETE.json").exists()
        assert all(digest(root / name) == sha for name, sha in before.items())
    finally:
        engine._shutdown()


def test_interrupted_authoritative_offer_remains_durably_recoverable(
    tmp_path, monkeypatch
):
    root, _ = sample(tmp_path)
    spool, spec = init(tmp_path)
    real = sealed_source.scan_source

    def interrupted(*_args, **_kwargs):
        raise CacheError("injected CPU-only independent offer failure")

    monkeypatch.setattr(sealed_source, "scan_source", interrupted)
    engine = BatchEngine(
        spool, spec, mode="independent", dataset_root=tmp_path / "dataset"
    )
    try:
        with pytest.raises(CacheError, match="injected CPU-only"):
            engine._discover()
        with spool._db() as db:
            row = db.execute("SELECT target,source_ready FROM jobs").fetchone()
            assert row is not None and row["target"] == str(root)
            assert row["source_ready"] is None
        assert not (root / "vae_cache/COMPLETE.json").exists()
        monkeypatch.setattr(sealed_source, "scan_source", real)
        engine._recover()
        with spool._db() as db:
            assert db.execute("SELECT source_ready FROM jobs").fetchone()[0] is not None
    finally:
        engine._shutdown()
