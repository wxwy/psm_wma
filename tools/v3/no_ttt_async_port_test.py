"""Receiver integration checks for the No-TTT async/lazy port, CPU only."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cosmos-framework"))

from cosmos_framework.model.generator.mot.robocasa_exact_window_local import (
    ExactWindowRankPlanner,
)  # noqa: E402
from cosmos_framework.trainer import matched_no_ttt as module  # noqa: E402
from cosmos_framework.trainer.no_ttt_async_loader import NoTTTAsyncLoader  # noqa: E402
from cosmos_framework.trainer.no_ttt_async_recipe import AsyncRecipe  # noqa: E402
from cosmos_framework.trainer.no_ttt_async_test_support import (  # noqa: E402
    SyntheticAsyncRecipe,
    build_synthetic_producer,
)
from cosmos_framework.trainer.no_ttt_cpu_loader import (
    RawRecipe,
    _require_same_rng,
    _rng_snapshot,
)  # noqa: E402
from cosmos_framework.utils.no_ttt_loader_profile import LoaderProfile  # noqa: E402


def _trainer(planner, producer, profile):
    trainer = object.__new__(module.MatchedNoTTTTrainer)
    trainer.config = SimpleNamespace(trainer=SimpleNamespace(grad_accum_iter=4))
    trainer.callbacks = SimpleNamespace(_callbacks=[])
    trainer.bind_grouped_stream(
        planner, producer, config_digest=producer.config_digest, loader_profile=profile
    )
    return trainer


@pytest.mark.parametrize("workers", [0, 1, 2, 4, 8])
def test_actual_trainer_uses_async_for_positive_workers_and_preserves_training_binding(
    monkeypatch, workers
):
    assert module.NoTTTAsyncLoader is NoTTTAsyncLoader
    assert Path(module.__file__).resolve().is_relative_to(ROOT / "cosmos-framework")
    producer = build_synthetic_producer(count=64, t=16, world=4)
    planner = ExactWindowRankPlanner(
        producer.catalog, rank=0, world_size=4, b_stream=8, active_ga=4, seed=83
    )
    metadata_calls = []

    def recipe(cls, selected, profile):
        assert selected is producer and profile.workers == workers
        metadata_calls.append(profile.workers)
        return SyntheticAsyncRecipe(count=64, t=16, world=4)

    def raw_forbidden(*args):
        pytest.fail("positive workers still bind the old RAW pipeline")

    # Only metadata is synthetic. Do not replace the actual trainer binding or
    # async loader class; this detects unused copied recipe/source modules.
    monkeypatch.setattr(AsyncRecipe, "from_producer", classmethod(recipe))
    monkeypatch.setattr(RawRecipe, "from_producer", classmethod(raw_forbidden))
    baseline = _trainer(planner, producer, LoaderProfile())
    before = _rng_snapshot()
    profile = LoaderProfile(workers, 1, True, 120) if workers else LoaderProfile()
    trainer = _trainer(planner, producer, profile)
    loader = trainer._no_ttt_loader
    try:
        assert module._binding(trainer) == module._binding(baseline)
        assert len(trainer.callbacks._callbacks) == 1
        assert trainer.callbacks._callbacks[0].checkpoint_component == "dataloader"
        if workers:
            assert type(loader) is NoTTTAsyncLoader
            assert loader.planner is planner and loader.profile is profile
            assert loader.iterator is None and loader.pending is None
            assert (
                loader.context.processes == []
            )  # Spawn only at the original lazy begin.
            assert metadata_calls == [workers]
        else:
            assert loader is None and metadata_calls == []
        _require_same_rng(before)
    finally:
        if loader is not None:
            loader.close()
            assert loader.closed and loader.context.processes == []


@pytest.mark.parametrize("workers", [1, 8])
def test_async_runtime_ownership_is_explicit_without_mutating_legacy_identity(workers):
    profile = LoaderProfile(workers, 1, True, 120)
    before = profile.identity()
    runtime = profile.async_identity()
    assert runtime["source_reader"] == "worker_offline_verified_source"
    assert runtime["transform"] == "worker_conditioned_parent_ordered_cfg_selection"
    assert runtime["max_prepared_windows"] == 2
    assert runtime["max_inflight_packets"] == workers
    assert profile.identity() == before
    assert before["schema"] == "nottt_cpu_raw_dataloader_v1"
    assert module.FORMAT == "psm_v3_matched_no_ttt_frontier_v1"
