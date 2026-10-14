"""Read-only native FSDP/optimizer tensor capture seam for Gate B1.

Call before optimizer.step only AFTER both native GA2 backwards and reviewed
unscale/clipping callbacks; call after the real optimizer step BEFORE zero_grad.
This module does not perform model/DCP load, mutate runtime state, or invoke GPU.
Its snapshots are detached CPU copies and cannot independently close Gate B1.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

import torch
from torch import nn
from torch.distributed.tensor import DTensor

from v3_gateb1_metrics import FQNSnapshot, FAMILIES


class CaptureBlocked(RuntimeError):
    """Live optimizer state is not yet safe/complete for FSDP8 parity capture."""


ACTION_FRAGMENTS = ("action2llm", "llm2action", "action_modality_embed")


def classify(name: str) -> str:
    if "local_memory" in name:
        return "local"
    if any(fragment in name for fragment in ACTION_FRAGMENTS):
        return "action"
    return "generation"


def _cpu_local(tensor: torch.Tensor | None, *, name: str) -> torch.Tensor:
    if tensor is None or not isinstance(tensor, torch.Tensor):
        raise CaptureBlocked(f"{name}: required runtime tensor missing")
    try:
        local = tensor.detach().to_local() if isinstance(tensor, DTensor) else tensor.detach()
    except Exception as exc:
        raise CaptureBlocked(f"{name}: DTensor local shard unavailable") from exc
    if local.is_sparse or not torch.isfinite(local).all().item():
        raise CaptureBlocked(f"{name}: nonfinite or sparse tensor")
    return local.to(device="cpu", copy=True).contiguous().clone()


def _shard_identity(param: nn.Parameter, *, rank: int) -> str:
    # Must include rank + mesh + placements to prevent accidental cross-shard pairing.
    value = param.detach()
    base = {"rank": rank, "dtype": str(value.dtype), "local_shape": tuple(value.shape)}
    if isinstance(value, DTensor):
        base.update(
            global_shape=tuple(value.shape),
            shard_shape=tuple(value.to_local().shape),
            placements=[str(p) for p in value.placements],
            mesh_shape=tuple(value.device_mesh.mesh.shape),
            mesh_dims=tuple(value.device_mesh.mesh_dim_names or ()),
        )
    return json.dumps(base, sort_keys=True, separators=(",", ":"))


def _step(group: Mapping[str, Any], *, label: str) -> int:
    value = group.get("step")
    if isinstance(value, torch.Tensor):
        if value.numel() != 1 or value.dtype not in (torch.int32, torch.int64):
            raise CaptureBlocked(f"{label}: optimizer group step must be an integer scalar")
        value = value.item()
    if type(value) is not int or value < 1:
        raise CaptureBlocked(f"{label}: optimizer step missing or invalid")
    return value


@dataclass(frozen=True)
class _Point:
    family: str
    shard_key: str
    gradient: torch.Tensor
    master: torch.Tensor
    m1: torch.Tensor
    m2: torch.Tensor


class NativeOptimizerCapture:
    """Read-only snapshot coordinator for actual fused Adam state after iter1300.

    Supports OptimizersContainer and direct inner optimizer. Requires every
    selected optimizer FQN to have a loaded moment state and non-None gradient.
    The optimizer parameter itself is authoritative FP32 unless master_weights
    is enabled and a separate, verified FP32 master exists.
    """

    def __init__(self, model: nn.Module, optimizer: Any, *, rank: int, expected_fqns: set[str] | None = None):
        if type(rank) is not int or not 0 <= rank < 8:
            raise CaptureBlocked("rank must match frozen FSDP8 mesh")
        self.rank = rank
        self.optimizers = tuple(getattr(optimizer, "optimizers", (optimizer,)))
        if not self.optimizers:
            raise CaptureBlocked("no inner optimizers")
        names_by_id: dict[int, str] = {}
        for name, param in model.named_parameters():
            if id(param) in names_by_id:
                raise CaptureBlocked(f"tied/duplicate FQN binding: {name}")
            names_by_id[id(param)] = name
        self.records: dict[str, tuple[Any, int, int, nn.Parameter]] = {}
        for oi, opt in enumerate(self.optimizers):
            if not hasattr(opt, "param_groups") or not hasattr(opt, "state"):
                raise CaptureBlocked("optimizer missing state/param_groups")
            for gi, group in enumerate(opt.param_groups):
                for pi, param in enumerate(group["params"]):
                    name = names_by_id.get(id(param))
                    if name is None or name in self.records:
                        raise CaptureBlocked("optimizer-selected FQN unknown or duplicated")
                    self.records[name] = (opt, gi, pi, param)
        if not self.records or (expected_fqns is not None and set(self.records) != expected_fqns):
            raise CaptureBlocked("optimizer-selected FQN coverage mismatch")
        if FAMILIES - {classify(name) for name in self.records}:
            raise CaptureBlocked("missing selected generation/action/local FQN family")
        self._pre: dict[str, _Point] | None = None
        self._before_steps: dict[tuple[int, int], int] | None = None

    def _point(self, name: str) -> _Point:
        opt, gi, pi, param = self.records[name]
        state = opt.state.get(param, {})
        if "exp_avg" not in state or "exp_avg_sq" not in state:
            raise CaptureBlocked(f"{name}: missing restored Adam moments")
        group = opt.param_groups[gi]
        _ = _step(group, label=f"{name}")
        if getattr(opt, "master_weights", False):
            masters = getattr(opt, "param_groups_master", None)
            if masters is None or gi >= len(masters) or pi >= len(masters[gi]["params"]):
                raise CaptureBlocked(f"{name}: true FP32 optimizer master unavailable")
            param_master = masters[gi]["params"][pi]
        else:
            param_master = param
        if param_master is None or param_master.dtype != torch.float32:
            raise CaptureBlocked(f"{name}: cannot prove FP32 optimizer parameter authority")
        if state["exp_avg"].dtype != torch.float32 or state["exp_avg_sq"].dtype != torch.float32:
            raise CaptureBlocked(f"{name}: Adam moments must be FP32")
        return _Point(
            family=classify(name), shard_key=_shard_identity(param, rank=self.rank),
            gradient=_cpu_local(param.grad, name=f"{name}.grad"),
            master=_cpu_local(param_master, name=f"{name}.master"),
            m1=_cpu_local(state["exp_avg"], name=f"{name}.exp_avg"),
            m2=_cpu_local(state["exp_avg_sq"], name=f"{name}.exp_avg_sq"),
        )

    def before_optimizer_step(self) -> None:
        if self._pre is not None:
            raise CaptureBlocked("already captured before optimizer step")
        self._pre = {name: self._point(name) for name in sorted(self.records)}
        self._before_steps = {
            (oi, gi): _step(group, label=f"optimizer[{oi}].group[{gi}]")
            for oi, opt in enumerate(self.optimizers) for gi, group in enumerate(opt.param_groups)
            if group["params"]
        }

    def after_optimizer_step(self) -> dict[str, FQNSnapshot]:
        if self._pre is None or self._before_steps is None:
            raise CaptureBlocked("must first capture after GA2, before optimizer")
        for (oi, gi), before in self._before_steps.items():
            after = _step(self.optimizers[oi].param_groups[gi], label=f"optimizer[{oi}].group[{gi}]")
            if after != before + 1:
                raise CaptureBlocked("missing/multiple optimizer step or GradScaler skip")
        out = {}
        for name, before in self._pre.items():
            after = self._point(name)
            if before.family != after.family or before.shard_key != after.shard_key:
                raise CaptureBlocked(f"{name}: parameter/family/shard altered during optimizer")
            out[name] = FQNSnapshot(
                before.family, before.shard_key, before.gradient,
                before.master, after.master, before.m1, after.m1, before.m2, after.m2,
            )
        self._pre = None
        self._before_steps = None
        return out
