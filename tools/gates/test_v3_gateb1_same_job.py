"""CPU-only precise DCP same-job adapter tests; no original checkpoint files."""
from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from v3_gateb1_same_job import SameJobBlocked, REQUIRED, exact_readonly_same_job_source


@dataclass(frozen=True)
class Source:
    path: str
    warm_start: bool
    backend_key: str | None = None


class Checkpointer:
    def __init__(self):
        self.config_checkpoint = SimpleNamespace(
            strict_resume=True, load_training_state=True, load_ema_to_reg=False)
        self.load_training_state = True
        self.save_to_object_store = False
        self.original_calls = 0
        self.save_calls = 0

    def _same_job_load_source(self, path):
        return Source(path=path, warm_start=False)

    def keys_to_resume_during_load(self):
        self.original_calls += 1
        # A direct load_path without latest is a warm start in original code.
        return {"model"}, Source("/original_warm_start", True)

    def save(self, *args):
        self.save_calls += 1


@pytest.fixture
def f(tmp_path):
    checkpoint = tmp_path / "iter_000001300"
    for k in REQUIRED:
        (checkpoint / k).mkdir(parents=True)
    return Checkpointer(), checkpoint


def test_explicit_original_path_is_scoped_as_full_native_same_job_without_latest_pointer(f):
    cp, ckpt = f
    original = cp.keys_to_resume_during_load.__func__
    with exact_readonly_same_job_source(cp, ckpt) as evidence:
        keys, source = cp.keys_to_resume_during_load()
        assert keys == REQUIRED and source.path == str(ckpt)
        assert source.warm_start is False and source.backend_key is None
        assert evidence["source_kind"] == "same-job-transient"
        assert cp.original_calls == 0
        assert not (ckpt.parent / "latest_checkpoint.txt").exists()
        with pytest.raises(SameJobBlocked, match="SAVE forbidden"):
            cp.save()
    assert cp.keys_to_resume_during_load.__func__ is original
    assert "keys_to_resume_during_load" not in vars(cp)
    assert "save" not in vars(cp)
    assert cp.original_calls == 0 and cp.save_calls == 0


def test_methods_restored_on_exception(f):
    cp, ckpt = f
    with pytest.raises(ValueError, match="DCP injected failure"):
        with exact_readonly_same_job_source(cp, ckpt):
            raise ValueError("DCP injected failure")
    assert cp.keys_to_resume_during_load()[1].warm_start is True
    cp.save()
    assert cp.save_calls == 1


def test_existing_instance_override_preserved(f):
    cp, ckpt = f
    existing = lambda: ({"model"}, Source("/old", True))
    cp.keys_to_resume_during_load = existing
    with exact_readonly_same_job_source(cp, ckpt):
        assert cp.keys_to_resume_during_load()[1].warm_start is False
    assert cp.keys_to_resume_during_load is existing


def test_incomplete_state_and_warm_config_fail_before_overrides(f):
    cp, ckpt = f
    cp.config_checkpoint.strict_resume = False
    with pytest.raises(SameJobBlocked, match="strict"):
        with exact_readonly_same_job_source(cp, ckpt):
            pass
    cp.config_checkpoint.strict_resume = True
    cp.config_checkpoint.load_training_state = False
    with pytest.raises(SameJobBlocked, match="strict"):
        with exact_readonly_same_job_source(cp, ckpt):
            pass
    assert "keys_to_resume_during_load" not in vars(cp)


def test_unapproved_ema_copypath_rejected(f):
    cp, ckpt = f
    cp.config_checkpoint.load_ema_to_reg = True
    with pytest.raises(SameJobBlocked, match="EMA"):
        with exact_readonly_same_job_source(cp, ckpt):
            pass


def test_missing_component_rejected(f):
    cp, ckpt = f
    (ckpt / "trainer").rmdir()
    with pytest.raises(SameJobBlocked, match="missing component trainer"):
        with exact_readonly_same_job_source(cp, ckpt):
            pass


def test_only_exact_iter1300_allowed(f):
    cp, ckpt = f
    with pytest.raises(SameJobBlocked, match="iter1300"):
        with exact_readonly_same_job_source(cp, ckpt.parent):
            pass


def test_no_object_store_source(f):
    cp, ckpt = f
    cp.save_to_object_store = True
    with pytest.raises(SameJobBlocked, match="local"):
        with exact_readonly_same_job_source(cp, ckpt):
            pass


def test_malformed_official_source_rejected(f):
    cp, ckpt = f
    cp._same_job_load_source = lambda path: Source(path, True)
    with pytest.raises(SameJobBlocked, match="not exact"):
        with exact_readonly_same_job_source(cp, ckpt):
            pass
