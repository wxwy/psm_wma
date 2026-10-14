"""CPU-only integration fixtures with the *actual* public GA2 event signature."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from types import SimpleNamespace
import pytest

from v3_gateb1_native_driver import (
    NativeBridgeBlocked, NativeTwoWindowDriver, member_coordinates, expected_native_calls,
)


@dataclass(frozen=True)
class Identity:
    slot_id: int
    episode_id: str = "episode_0"
    source_digest: str = "source"
    segment_id: int = 0
    cursor: int = 0


@dataclass(frozen=True)
class Request:
    identity: Identity
    binding_epoch: int = 1
    valid_count: int = 16


class Model:
    def training_step(self, batch, iteration, **kwargs):
        return {"loss": iteration}, 0.5


class Capture:
    def __init__(self):
        self.before = 0
        self.after = 0

    def before_optimizer_step(self):
        self.before += 1

    def after_optimizer_step(self):
        self.after += 1
        return {"fqn": self.before, "after": self.after}


class FakeTrainer:
    def __init__(self, leg, partial=False):
        self.leg = leg
        self._pending_grouped_resume = {"rank": 0, "iteration": 1300}
        self._resume_required = True
        self._grouped_planner = SimpleNamespace(rank=0, world_size=8, b_stream=8, active_ga=2,
                                                catalog=SimpleNamespace(ttt_tbptt_steps=16))
        self._grouped_completed_iteration = 0
        self._grouped_window = None
        self.partial = partial
        self.events = []

    def _plan(self):
        requests = tuple(Request(Identity(i), valid_count=16 if not self.partial or i < 3 else 8)
                         for i in range(8))
        return SimpleNamespace(members=(requests, requests))

    def _observe_grouped(self, phase, **kwargs):
        self.events.append((phase, kwargs.get("index"), kwargs.get("packed_positions")))

    def _zero_grad(self, *args, **kwargs):
        self.events.append(("zero_grad", None, None))

    def training_step(self, model, optimizer, scheduler, grad_scaler, data, *, iteration, grad_accum_iter):
        if grad_accum_iter == 0:
            self._grouped_window = SimpleNamespace(plan=self._plan(), _member_index=0)
            self._pending_grouped_resume = None
        self._grouped_window._member_index = grad_accum_iter
        plan = self._grouped_window.plan
        for index in range(expected_native_calls(plan, grad_accum_iter, self.leg)):
            coords = member_coordinates(plan, grad_accum_iter, self.leg, index)
            prefixes = tuple(None if c.absolute_step == 0 else object() for c in coords)
            model.training_step({}, iteration, _local_memory_prefixes=prefixes)
            self._observe_grouped("native_forward", member=grad_accum_iter,
                                  index=coords[0].local_t if self.leg == "index8" else None,
                                  packed_positions=tuple((c.slot_id, c.local_t) for c in coords)
                                  if self.leg == "packed128" else None)
        if grad_accum_iter == 0:
            return {}, 0.5, 1
        self._observe_grouped("pre_optimizer", member=1)
        self._grouped_completed_iteration = iteration + 1
        self._zero_grad(model, optimizer, iteration)
        return {}, 0.5, 0


@contextmanager
def scope_noop():
    yield


def make_driver(leg, partial=False):
    trainer, model = FakeTrainer(leg, partial), Model()
    batch_calls = []
    def noise_scope(coords, iteration):
        @contextmanager
        def cm():
            batch_calls.append(tuple((x.slot_id, x.local_t, x.absolute_step) for x in coords))
            yield
        return cm()
    driver = NativeTwoWindowDriver(trainer=trainer, model=model, optimizer=object(), scheduler=object(),
                                   grad_scaler=object(), leg=leg, rank=0, noise_scope=noise_scope,
                                   producer_scope=scope_noop, capture_factory=Capture,
                                   local_snapshot=lambda it: {"local_iteration": it})
    return driver, trainer, model, batch_calls


@pytest.mark.parametrize("leg,partial,ncalls", [
    ("index8", False, 64), ("packed128", False, 4),
    ("index8", True, 64), ("packed128", True, 4),
])
def test_native_two_step_events_leg_real_shape(leg, partial, ncalls):
    driver, trainer, model, batches = make_driver(leg, partial)
    before_training_step = model.training_step.__func__
    result = driver.run()
    assert len(result) == 2
    assert [r.completed_iteration for r in result] == [1301, 1302]
    assert all(r.optimizer_snapshot == {"fqn": 1, "after": 1} for r in result)
    assert len(batches) == ncalls
    assert trainer._grouped_completed_iteration == 1302
    assert len([e for e in trainer.events if e[0] == "zero_grad"]) == 2
    assert model.training_step.__func__ is before_training_step
    assert "training_step" not in vars(model)
    if partial and leg == "packed128":
        assert len(batches[0]) == 3 * 16 + 5 * 8
        assert batches[0][0] == (0, 0, 0)
        assert batches[0][-1] == (7, 7, 7)


def test_model_methods_restored_on_failed_native_event():
    driver, trainer, model, _ = make_driver("packed128")
    old = model.training_step.__func__
    def broken(*args, **kwargs):
        raise ValueError("forced native failure")
    model.training_step = broken
    with pytest.raises(ValueError, match="forced native"):
        driver.run()
    assert model.training_step is broken  # preexisting instance override preserved
    del model.training_step
    assert model.training_step.__func__ is old


def test_missing_original_local_state_fails_before_running():
    driver, trainer, model, calls = make_driver("packed128")
    trainer._pending_grouped_resume = None
    with pytest.raises(NativeBridgeBlocked, match="Local DCP restore"):
        NativeTwoWindowDriver(trainer=trainer, model=model, optimizer=object(), scheduler=object(),
                              grad_scaler=object(), leg="packed128", rank=0,
                              noise_scope=lambda coords, iteration: scope_noop(), producer_scope=scope_noop,
                              capture_factory=Capture, local_snapshot=lambda it: it)
    assert not calls


def test_duplicate_and_wrong_native_index_fails():
    plan = SimpleNamespace(members=(tuple(Request(Identity(0)) for _ in range(8)),) * 2)
    with pytest.raises(NativeBridgeBlocked, match="duplicate"):
        member_coordinates(plan, 0, "packed128", 0)
    clean = FakeTrainer("index8")._plan()
    with pytest.raises(NativeBridgeBlocked, match="exceeded"):
        member_coordinates(clean, 0, "index8", 16)
    with pytest.raises(NativeBridgeBlocked, match="exactly once"):
        member_coordinates(clean, 0, "packed128", 1)


def test_no_provider_missing_and_wrong_frozen_world_size_rejected():
    _, trainer, model, _ = make_driver("index8")
    trainer._grouped_planner.world_size = 7
    with pytest.raises(NativeBridgeBlocked, match="frozen FSDP8"):
        make_broken = NativeTwoWindowDriver(trainer=trainer, model=model, optimizer=object(),
                                            scheduler=object(), grad_scaler=object(),
                                            leg="index8", rank=0, noise_scope=lambda x, it: scope_noop(),
                                            producer_scope=scope_noop, capture_factory=Capture,
                                            local_snapshot=lambda it: it)
        make_broken.run()
