"""B1 native two-step GA2 seam. Never calls Trainer.train or saves DCP.

Requires actual production GroupedLocalMemoryTrainer and FSDP model already
prepared and strictly restored from original iter1300. Run is GPU-authorized
ONLY after a separate Owner sign-off; this module itself stays CPU-testable.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from types import MethodType
from typing import Any, Callable, ContextManager, Iterator

import torch


class NativeBridgeBlocked(RuntimeError):
    """Missing real native event, consumer witness or optimizer boundary."""


@dataclass(frozen=True)
class ConsumerCoordinate:
    ga_member: int
    slot_id: int
    local_t: int
    absolute_step: int
    identity: Any
    binding_epoch: int


@dataclass(frozen=True)
class CompletedNativeWindow:
    completed_iteration: int
    rank: int
    native_calls: tuple[tuple[int, tuple[ConsumerCoordinate, ...]], ...]
    optimizer_snapshot: Any
    local_snapshot: Any
    weighted_losses: dict[str, Any] | None = None
    stochastic_witnesses: tuple[dict[str, Any], ...] = ()
    cfg_witnesses: tuple[dict[str, Any], ...] = ()


def member_coordinates(plan: Any, ga_member: int, leg: str, native_call: int) -> tuple[ConsumerCoordinate, ...]:
    """Freeze actual Consumer order for each original Native forward."""
    if leg not in {"index8", "packed128"} or ga_member not in (0, 1) or native_call < 0:
        raise NativeBridgeBlocked("invalid native leg/member/index")
    requests = plan.members[ga_member]
    if len(requests) != 8:
        raise NativeBridgeBlocked("frozen B_stream=8 is required")
    if leg == "packed128":
        if native_call != 0:
            raise NativeBridgeBlocked("Packed128 must call Native exactly once per member")
        pairs = [(req, t) for req in requests for t in range(req.valid_count)]
    else:
        active = [t for t in range(16) if any(t < req.valid_count for req in requests)]
        if native_call >= len(active):
            raise NativeBridgeBlocked("Index8 native index exceeded active temporal range")
        pairs = [(req, active[native_call]) for req in requests if active[native_call] < req.valid_count]
    coords = tuple(ConsumerCoordinate(
        ga_member=ga_member, slot_id=req.identity.slot_id, local_t=t,
        absolute_step=req.identity.cursor * 16 + t,
        identity=req.identity, binding_epoch=req.binding_epoch,
    ) for req, t in pairs)
    if not coords or len(set((c.slot_id, c.local_t) for c in coords)) != len(coords):
        raise NativeBridgeBlocked("empty/duplicate native Consumer coordinates")
    return coords


def expected_native_calls(plan: Any, ga_member: int, leg: str) -> int:
    if leg == "packed128":
        return 1
    return max(req.valid_count for req in plan.members[ga_member])


@contextmanager
def _patch_methods(obj: Any, replacements: dict[str, Callable[..., Any]]) -> Iterator[None]:
    """Instance-local method replacement, restoring even after FSDP/NCCL errors."""
    before = {name: (name in vars(obj), vars(obj).get(name)) for name in replacements}
    try:
        for name, func in replacements.items():
            if not callable(getattr(obj, name, None)):
                raise NativeBridgeBlocked(f"missing native method: {name}")
            setattr(obj, name, MethodType(func, obj))
        yield
    finally:
        for name, (was_set, value) in before.items():
            if was_set:
                setattr(obj, name, value)
            else:
                vars(obj).pop(name, None)


class NativeTwoWindowDriver:
    """Call ONLY the real GroupedLocalMemoryTrainer.training_step 2×GA2.

    `noise_scope` must be a reviewed, *actual model-callsite* Consumer-keyed
    sigma/epsilon context manager. `producer_scope` must key the original
    native Transform's text-CFG dropout. Neither may be omitted or no-op.
    `capture_factory` returns a NativeOptimizerCapture; `local_snapshot` calls
    native snapshot_grouped_local_state AFTER the successful real commit.
    """

    def __init__(self, *, trainer: Any, model: Any, optimizer: Any, scheduler: Any,
                 grad_scaler: Any, leg: str, rank: int, noise_scope: Callable[[tuple[ConsumerCoordinate, ...], int], ContextManager[Any]],
                 producer_scope: Callable[[], ContextManager[Any]], capture_factory: Callable[[], Any],
                 local_snapshot: Callable[[int], Any]):
        planner = getattr(trainer, "_grouped_planner", None)
        if (leg not in ("index8", "packed128") or type(rank) is not int or not 0 <= rank < 8
                or planner is None or planner.rank != rank or planner.world_size != 8
                or planner.b_stream != 8 or planner.active_ga != 2
                or planner.catalog.ttt_tbptt_steps != 16):
            raise NativeBridgeBlocked("B1 requires actual frozen FSDP8 B8 T16 GA2 planner")
        if (getattr(trainer, "_pending_grouped_resume", None) is None
                or getattr(trainer, "_resume_required", None) is not True):
            raise NativeBridgeBlocked("original iter1300 Local DCP restore must be pending and required")
        if getattr(trainer, "_grouped_window", None) is not None:
            raise NativeBridgeBlocked("unexpected live window before native restore")
        if any(x is None or not callable(x) for x in (noise_scope, producer_scope, capture_factory, local_snapshot)):
            raise NativeBridgeBlocked("real noise/CFG/optimizer/Local witness hooks mandatory")
        self.trainer, self.model, self.optimizer = trainer, model, optimizer
        self.scheduler, self.grad_scaler = scheduler, grad_scaler
        self.leg, self.rank = leg, rank
        self.noise_scope, self.producer_scope = noise_scope, producer_scope
        self.capture_factory, self.local_snapshot = capture_factory, local_snapshot

    def run(self) -> tuple[CompletedNativeWindow, CompletedNativeWindow]:
        tr, model = self.trainer, self.model
        original_step = model.training_step
        original_observe = tr._observe_grouped
        original_zero = tr._zero_grad
        window_events: list[CompletedNativeWindow] = []
        active_calls: dict[int, int] = {}
        calls: list[tuple[int, tuple[ConsumerCoordinate, ...]]] = []
        weighted_losses: dict[str, Any] = {}
        site_records: list[dict[str, Any]] = []
        cfg_start = 0
        producer_records: Any = None
        active_capture = None
        completed: Any = None
        current_iter = 1300

        def model_step(_self: Any, batch: Any, iteration: int, **kwargs: Any) -> Any:
            if iteration != current_iter:
                raise NativeBridgeBlocked("native model iteration mismatch")
            window = getattr(tr, "_grouped_window", None)
            if window is None or window.plan is None:
                raise NativeBridgeBlocked("model forward outside real grouped window")
            ga = window._member_index
            counter = active_calls.get(ga, 0)
            coords = member_coordinates(window.plan, ga, self.leg, counter)
            prefixes = kwargs.get("_local_memory_prefixes")
            if not isinstance(prefixes, tuple) or len(prefixes) != len(coords):
                raise NativeBridgeBlocked("Native Local prefix/Consumer count mismatch")
            if any((p is None) != (c.absolute_step == 0) for p, c in zip(prefixes, coords, strict=True)):
                raise NativeBridgeBlocked("S0 Local prefix witness mismatch")
            active_calls[ga] = counter + 1
            with self.noise_scope(coords, iteration) as site:
                output = original_step(batch, iteration, **kwargs)
            if site is not None:
                if not callable(getattr(site, "witness_records", None)):
                    raise NativeBridgeBlocked("B1 model stochastic scope lacks value witnesses")
                witnessed = site.witness_records()
                if len(witnessed) != len(coords):
                    raise NativeBridgeBlocked("model stochastic witness Consumer count mismatch")
                site_records.extend(witnessed)
            if not isinstance(output, tuple) or len(output) != 2 or not isinstance(output[0], dict):
                raise NativeBridgeBlocked("native model must return (metrics_dict, loss)")
            # The native window multiplies the mean loss for this call by
            # count / n_window; capture *that same* weighted value here.
            # Otherwise comparing Index8 micro-loss to Packed128 batch loss
            # is a false objective parity test.
            components = {"weighted_outer": output[1]}
            components.update({k: v for k, v in output[0].items() if "loss" in k and torch.is_tensor(v) and v.ndim == 0})
            factor = len(coords) / window.plan.n_window
            for name, raw in components.items():
                if not isinstance(raw, (float, int, torch.Tensor)):
                    raise NativeBridgeBlocked(f"native scalar loss {name} invalid")
                value = torch.as_tensor(raw).detach()
                if value.numel() != 1 or not bool(torch.isfinite(value).all()):
                    raise NativeBridgeBlocked(f"native scalar loss {name} nonfinite/non-scalar")
                detached = value.to(device="cpu", dtype=torch.float64) * factor
                weighted_losses[name] = weighted_losses.get(name, torch.zeros_like(detached)) + detached
            calls.append((ga, coords))
            return output

        def observe(_self: Any, phase: str, **kw: Any) -> Any:
            nonlocal active_capture
            if phase == "native_forward":
                ga = kw.get("member")
                c = active_calls.get(ga, 0) - 1
                if c < 0:
                    raise NativeBridgeBlocked("Native forward event without model call")
                coords = member_coordinates(tr._grouped_window.plan, ga, self.leg, c)
                # Frozen source GroupedLocalMemoryTrainer.native_loss reports
                # _observe_grouped("native_forward", index=None), even though
                # the source window iterates each index. Index identity is
                # proven by counter/member_coordinates at the model callsite.
                # Some synthetic tracers additionally annotate the index;
                # validate only when a concrete annotation is provided.
                if self.leg == "index8" and kw.get("index") not in (None, coords[0].local_t):
                    raise NativeBridgeBlocked("Index8 Native index event mismatch")
                if self.leg == "packed128" and tuple(kw.get("packed_positions") or ()) != tuple(
                        (x.slot_id, x.local_t) for x in coords):
                    raise NativeBridgeBlocked("Packed128 native slot-major positions mismatch")
            if phase == "pre_optimizer":
                if active_capture is not None or active_calls.get(0, 0) != expected_native_calls(
                        tr._grouped_window.plan, 0, self.leg) or active_calls.get(1, 0) != expected_native_calls(
                        tr._grouped_window.plan, 1, self.leg):
                    raise NativeBridgeBlocked("Optimizer reached before complete GA2 native calls")
                active_capture = self.capture_factory()
                active_capture.before_optimizer_step()
            return original_observe(phase, **kw)

        def zero_grad(_self: Any, *args: Any, **kwargs: Any) -> Any:
            nonlocal active_capture, completed, cfg_start
            if active_capture is None or completed is not None:
                raise NativeBridgeBlocked("zero_grad without exactly one real optimizer commit")
            snapshots = active_capture.after_optimizer_step()
            local = self.local_snapshot(current_iter + 1)
            cfg_current = tuple(producer_records[cfg_start:]) if producer_records is not None else ()
            cfg_start = len(producer_records) if producer_records is not None else 0
            completed = CompletedNativeWindow(
                current_iter + 1, self.rank, tuple(calls), snapshots, local,
                {k: v.to(torch.float32) for k, v in weighted_losses.items()},
                tuple(site_records), cfg_current,
            )
            active_capture = None
            return original_zero(*args, **kwargs)

        with (_patch_methods(model, {"training_step": model_step}),
              _patch_methods(tr, {"_observe_grouped": observe, "_zero_grad": zero_grad}),
              self.producer_scope() as cfg_evidence):
            producer_records = cfg_evidence
            for completed_before in (1300, 1301):
                current_iter = completed_before
                active_calls.clear()
                calls.clear()
                weighted_losses.clear()
                site_records.clear()
                completed = None
                for ga in (0, 1):
                    _, _, next_ga = tr.training_step(
                        model, self.optimizer, self.scheduler, self.grad_scaler, {},
                        iteration=current_iter, grad_accum_iter=ga,
                    )
                    if next_ga != (ga + 1 if ga == 0 else 0):
                        raise NativeBridgeBlocked("GA2 did not reach required next microstep")
                if completed is None or getattr(tr, "_grouped_completed_iteration", None) != current_iter + 1:
                    raise NativeBridgeBlocked("native optimizer/Local commit incomplete")
                window_events.append(completed)
            if len(window_events) != 2:
                raise NativeBridgeBlocked("exactly two consecutive native windows required")
        return tuple(window_events)  # type: ignore[return-value]


def build_loaded_native_bridge(*, config: Any, model: Any, planner: Any, producer: Any,
                               trainer: Any, checkpoint_path: Any, leg: str, rank: int,
                               checkpoint_fp: str, sampling_contract: Any, target_digest: str | None = None):
    """Faithfully reproduce the official model+optimizer setup, without Trainer.train.

    Caller is responsible for an Owner-authorized CUDA FSDP8 initialization and
    a previously accepted no-scan dataset catalog. Native Trainer construction
    may write config snapshots: the caller must isolate config.job.path_local
    under /tmp. No checkpoint save or generation of training job namespaces.
    """
    from pathlib import Path
    import torch

    out = Path(config.job.path_local).resolve()
    ckpt = Path(checkpoint_path).resolve(strict=True)
    if not out.is_relative_to(Path("/tmp").resolve()) or out == Path("/tmp") or ckpt.is_relative_to(out):
        raise NativeBridgeBlocked("B1 native trainer config/log output must be isolated in /tmp")
    if not torch.cuda.is_available() or not torch.distributed.is_initialized():
        raise NativeBridgeBlocked("actual torchrun FSDP8 not initialized; no CPU/GPU claim")
    if torch.distributed.get_world_size() != 8 or torch.distributed.get_rank() != rank:
        raise NativeBridgeBlocked("native FSDP8 distributed rank topology mismatch")
    if (getattr(trainer, "_grouped_planner", None) is not planner
            or getattr(trainer, "_grouped_producer", None) is not producer
            or not getattr(trainer, "_grouped_config_digest", None)):
        raise NativeBridgeBlocked("native corrected trainer must already bind exact planner/producer/digest")
    if getattr(trainer, "_grouped_num_workers", None) != 0:
        raise NativeBridgeBlocked("real Transform CFG witness requires num_workers=0")
    from v3_gateb1_dcp_transient import strict_transient_load
    from v3_gateb1_fsdp_capture import NativeOptimizerCapture
    from v3_gateb1_model_sites import b0_native_noise_scope
    from v3_gateb1_producer_cfg import b0_consumer_cfg_scope
    from cosmos_framework.trainer.local_memory_grouped_resume import (
        require_dcp_grouped_resume_component, snapshot_grouped_local_state,
    )

    # The following sequence matches ImaginaireTrainer.train initialization,
    # but intentionally NEVER invokes that save-capable training loop.
    model = model.to("cuda", memory_format=config.trainer.memory_format)
    model.on_train_start(config.trainer.memory_format)
    trainer.callbacks.on_optimizer_init_start()
    optimizer, scheduler = model.init_optimizer_scheduler(config.optimizer, config.scheduler)
    grad_scaler = torch.amp.GradScaler("cuda", **config.trainer.grad_scaler_args)
    trainer.callbacks.on_optimizer_init_end()
    trainer._resume_required = require_dcp_grouped_resume_component(trainer.checkpointer)
    if not trainer._resume_required:
        raise NativeBridgeBlocked("strict native same-job dataloader restore not selected")
    evidence = strict_transient_load(checkpointer=trainer.checkpointer, trainer=trainer,
                                     model=model, optimizer=optimizer, scheduler=scheduler,
                                     grad_scaler=grad_scaler, checkpoint_path=ckpt,
                                     leg=leg, rank=rank, target_digest=target_digest)
    trainer.callbacks.on_train_start(model, iteration=1300)
    model.train()
    bridge = NativeTwoWindowDriver(
        trainer=trainer, model=model, optimizer=optimizer, scheduler=scheduler, grad_scaler=grad_scaler,
        leg=leg, rank=rank,
        noise_scope=lambda coords, iteration: b0_native_noise_scope(
            model, coords, iteration, checkpoint_fp=checkpoint_fp, rank=rank, contract=sampling_contract),
        producer_scope=lambda: b0_consumer_cfg_scope(trainer, producer, rank=rank, checkpoint_fp=checkpoint_fp),
        capture_factory=lambda: NativeOptimizerCapture(model, optimizer, rank=rank),
        local_snapshot=lambda completed: snapshot_grouped_local_state(
            trainer._grouped_window, iteration=completed, config_digest=trainer._grouped_config_digest,
        ),
    )
    return bridge, evidence
