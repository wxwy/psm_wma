"""Instance-scoped B1 model RNG injections. No global torch.randn monkeypatch.

P0/P1 exact ConsumerKey values are installed at the real OmniMoTModel
training_step *call boundary*. The scoped TorchDispatchMode intercepts native
aten.randn.generator ONLY while the original _add_noise_to_input executes.
Unknown random operations, modalities and mismatched geometry fail closed.
Requires source/target runtime audit and separate Owner GPU authorization.
"""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
from types import MethodType
from typing import Any, Callable, Iterator

import torch
from torch.utils._python_dispatch import TorchDispatchMode


class SiteBlocked(RuntimeError):
    """Unknown native model/producer stochastic site or mismatched Consumer order."""


@dataclass(frozen=True)
class SiteCount:
    vision_sigma: int
    action_sigma: int
    epsilon_calls: int
    epsilon_expected: int
    noising_calls: int


def _sha_tensor(tensor: torch.Tensor) -> str:
    """Small cryptographic witness: dtype+shape+all bytes, independent of batch order."""
    value = tensor.detach().to(device="cpu").contiguous()
    meta = json.dumps({"dtype": str(value.dtype), "shape": list(value.shape)}, sort_keys=True).encode()
    return hashlib.sha256(len(meta).to_bytes(8, "big") + meta
                          + value.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest()


class _NativeRandnQueue(TorchDispatchMode):
    """Thread-local dispatch-mode replacement, limited to original noising call."""

    def __init__(self, entries: list[tuple[str, torch.Tensor]]):
        super().__init__()
        self.entries = entries
        self.consumed: list[str] = []

    def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        kwargs = kwargs or {}
        if func in (torch.ops.aten.randn.default, torch.ops.aten.randn.generator):
            if not self.entries:
                raise SiteBlocked("unexpected extra native randn site")
            name, cpu = self.entries.pop(0)
            shape = tuple(int(d) for d in args[0])
            if cpu.device.type != "cpu" or not cpu.is_contiguous() or shape != tuple(cpu.shape):
                raise SiteBlocked(f"{name}: mismatch native epsilon tensor shape/device")
            target_dtype = kwargs.get("dtype") or torch.float32
            target_device = kwargs.get("device") or torch.device("cpu")
            self.consumed.append(name)
            return cpu.to(device=target_device, dtype=target_dtype)
        if str(func).startswith(("aten.rand.", "aten.randn_like.", "aten.bernoulli.", "aten.normal.")):
            raise SiteBlocked(f"unregistered native noising random site {func}")
        return func(*args, **kwargs)


@contextmanager
def _replace_instance_methods(obj: Any, replacements: dict[str, Callable[..., Any]]) -> Iterator[None]:
    initial = {name: (name in vars(obj), vars(obj).get(name)) for name in replacements}
    try:
        for name, fn in replacements.items():
            if not callable(getattr(obj, name, None)):
                raise SiteBlocked(f"production model method absent: {name}")
            setattr(obj, name, MethodType(fn, obj))
        yield
    finally:
        for name, (existed, value) in initial.items():
            if existed:
                setattr(obj, name, value)
            else:
                vars(obj).pop(name, None)


class NativeOmniMoTNoiseSites:
    """Bind the *actual* OmniMoTModel vision sigma and epsilon call sites.

    These are method-scoped to one model instance, not global monkeypatches.
    `keys` is the canonical ConsumerKey tuple, source Index8 or Packed128
    slot-major, assembled by the native GA2 bridge in exact forward order.
    `sigma_fn`, `epsilon_fn` use the B1 CPU source-equivalent samplers.
    """

    def __init__(self, model: Any, keys: tuple[Any, ...], contract: Any,
                 sigma_fn: Callable[..., torch.Tensor], epsilon_fn: Callable[..., torch.Tensor]):
        if not keys or not callable(sigma_fn) or not callable(epsilon_fn):
            raise SiteBlocked("missing ConsumerKey/sigma/epsilon witness")
        self.model, self.keys, self.contract = model, keys, contract
        self.sigma_fn, self.epsilon_fn = sigma_fn, epsilon_fn
        self.vision_calls = 0
        self.action_calls = 0
        self.noising_calls = 0
        self.epsilon_seen: list[str] = []
        self._scope = None
        self.vision_sigmas_cpu: torch.Tensor | None = None
        self.action_sigmas_cpu: torch.Tensor | None = None
        self.vision_eps_hashes: list[str] = []
        self.action_eps_hashes: list[str] = []
        self.action_mask_hashes: list[str] = []
        self.vision_mask_hashes: list[str] = []
        self.all_actions_conditioned = False

    def __enter__(self):
        orig_noiser = self.model._add_noise_to_input
        instance = self

        def vision(_model: Any, *args: Any, **kwargs: Any):
            if args or instance.vision_calls != 0:
                raise SiteBlocked("unexpected vision sigma signature/reentry")
            n = kwargs.get("batch_size")
            lengths = kwargs.get("num_vision_latent_frames")
            if n != len(instance.keys) or len(lengths or ()) != n:
                raise SiteBlocked("vision sigma batch/latent-frame geometry differs from Consumers")
            if kwargs.get("is_image_batch") is not False:
                raise SiteBlocked("B1 RoboCasa requires video-native schedule")
            if kwargs.get("iteration") != instance.keys[0].completed_iteration:
                raise SiteBlocked("sigma original iteration does not match ConsumerKey")
            native_dist = instance.contract.causal_training_strategy
            if native_dist != _model.config.causal_training_strategy:
                raise SiteBlocked("resolved causal schedule differs from witness")
            rf_cfg = getattr(_model.config, "rectified_flow_training_config", None)
            if rf_cfg is None or rf_cfg.independent_action_schedule != instance.contract.independent_action_schedule:
                raise SiteBlocked("native independent Action Sigma config is not witnessed")
            if rf_cfg.train_time_video_distribution != instance.contract.vision_distribution:
                raise SiteBlocked("native P1 video distribution differs from resolved config")
            resolutions = kwargs.get("resolutions")
            if isinstance(resolutions, str):
                resolutions = [resolutions] * n
            if not isinstance(resolutions, (tuple, list)) or len(resolutions) != n:
                raise SiteBlocked("per-consumer resolved vision resolution is missing")
            for resolution in resolutions:
                shift_cfg = rf_cfg.shift
                shift = shift_cfg[resolution] if isinstance(shift_cfg, Mapping) else shift_cfg
                if float(shift) != float(instance.contract.vision_shift):
                    raise SiteBlocked("native per-consumer RF shift differs from P1 contract")
            temporal = max(lengths) if native_dist == "diffusion_forcing" else 1
            sampled = torch.stack([
                torch.stack([instance.sigma_fn(key, instance.contract, modality="vision", frame_index=t)
                             for t in range(temporal)]) for key in instance.keys
            ]).to(device="cpu", dtype=torch.float32)
            instance.vision_sigmas_cpu = sampled.clone()
            sigmas = sampled.to(**_model.tensor_kwargs_fp32)
            flow = _model.rectified_flow_video
            instance.vision_calls += 1
            return sigmas * flow.noise_scheduler.config.num_train_timesteps, sigmas

        def action(_model: Any, *args: Any, **kwargs: Any):
            if args or not instance.contract.independent_action_schedule or instance.action_calls != 0:
                raise SiteBlocked("unexpected independent-action schedule call")
            if kwargs.get("batch_size") != len(instance.keys):
                raise SiteBlocked("action sigma must be sampled in original full-batch order")
            sampled = torch.stack([
                instance.sigma_fn(key, instance.contract, modality="action") for key in instance.keys
            ]).reshape(-1, 1).to(device="cpu", dtype=torch.float32)
            instance.action_sigmas_cpu = sampled.clone()
            sigmas = sampled.to(**_model.tensor_kwargs_fp32)
            instance.action_calls += 1
            return sigmas * _model.rectified_flow_action.noise_scheduler.config.num_train_timesteps, sigmas

        def noiser(_model: Any, *args: Any, **kwargs: Any):
            if len(args) < 2 or instance.noising_calls:
                raise SiteBlocked("unexpected native noiser args/reentry")
            if kwargs.get("iteration") != instance.keys[0].completed_iteration:
                raise SiteBlocked("native epsilon iteration differs from ConsumerKey")
            clean, packed = args[0], args[1]
            if getattr(_model.config, "sound_gen", False):
                raise SiteBlocked("unregistered sound noising not allowed for RoboCasa")
            for modality in ("lidar", "radar", "sound"):
                tensors = getattr(clean, f"x0_tokens_{modality}", None)
                if tensors is not None and len(tensors):
                    raise SiteBlocked(f"unregistered {modality} epsilon site")
            vision_items = clean.x0_tokens_vision
            actions = clean.x0_tokens_action
            v_pack = getattr(packed, "vision", None)
            vision_masks = getattr(v_pack, "condition_mask", None)
            if vision_masks is None or len(vision_masks) != len(instance.keys):
                raise SiteBlocked("RoboCasa vision condition mask witness missing")
            instance.vision_mask_hashes = [_sha_tensor(mask) for mask in vision_masks]
            if (len(vision_items) != len(instance.keys) or actions is None
                    or len(actions) != len(instance.keys)):
                raise SiteBlocked("RoboCasa native vision/action item count differs from Consumers")
            a_pack = getattr(packed, "action", None)
            masks = getattr(a_pack, "condition_mask", None)
            if masks is None or len(masks) != len(actions):
                raise SiteBlocked("action condition mask geometry unknown")
            all_cond = all(torch.all(mask == 1).item() for mask in masks)
            instance.all_actions_conditioned = all_cond
            instance.action_mask_hashes = [_sha_tensor(mask) for mask in masks]
            entries: list[tuple[str, torch.Tensor]] = []
            for index, (key, value) in enumerate(zip(instance.keys, vision_items, strict=True)):
                eps = instance.epsilon_fn(key, tuple(value.shape), modality="vision")
                instance.vision_eps_hashes.append(_sha_tensor(eps))
                entries.append((f"vision:{index}", eps))
            if not all_cond:
                for index, (key, value) in enumerate(zip(instance.keys, actions, strict=True)):
                    eps = instance.epsilon_fn(key, tuple(value.shape), modality="action")
                    instance.action_eps_hashes.append(_sha_tensor(eps))
                    entries.append((f"action:{index}", eps))
            hook = _NativeRandnQueue(entries)
            expected = len(entries)
            instance.noising_calls += 1
            with hook:
                output = orig_noiser(*args, **kwargs)
            if hook.entries or len(hook.consumed) != expected:
                raise SiteBlocked(f"epsilon native site coverage incomplete: {len(hook.consumed)}/{expected}")
            instance.epsilon_seen.extend(hook.consumed)
            return output

        self._scope = _replace_instance_methods(self.model, {
            "_get_train_noise_level_vision": vision,
            "_get_train_noise_level_action": action,
            "_add_noise_to_input": noiser,
        })
        self._scope.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None and (self.vision_calls != 1 or self.noising_calls != 1
                                     or self.action_calls != int(self.contract.independent_action_schedule)):
                raise SiteBlocked("missing original native sigma/noiser stochastic site")
        finally:
            assert self._scope is not None
            self._scope.__exit__(exc_type, exc, tb)
        return False

    def witness_records(self) -> tuple[dict[str, Any], ...]:
        """One recorded site-value digest for each actual Native Consumer."""
        size = len(self.keys)
        if (self.noising_calls != 1 or self.vision_calls != 1 or self.vision_sigmas_cpu is None
                or len(self.vision_eps_hashes) != size or len(self.action_mask_hashes) != size
                or len(self.vision_mask_hashes) != size
                or (not self.all_actions_conditioned and len(self.action_eps_hashes) != size)):
            raise SiteBlocked("incomplete B1 native per-consumer stochastic witness")
        vision = self.vision_sigmas_cpu
        action = self.action_sigmas_cpu if self.action_sigmas_cpu is not None else vision
        if tuple(vision.shape)[0] != size or tuple(action.shape)[0] != size:
            raise SiteBlocked("native sigma sample row count mismatch")
        return tuple({
            "consumer": key.as_dict() if hasattr(key, "as_dict") else dict(vars(key)),
            "vision_sigma_sha256": _sha_tensor(vision[i]),
            "action_sigma_sha256": _sha_tensor(action[i]),
            "vision_epsilon_sha256": self.vision_eps_hashes[i],
            "action_epsilon_sha256": "ALL_ACTION_CONDITIONING" if self.all_actions_conditioned else self.action_eps_hashes[i],
            "action_condition_mask_sha256": self.action_mask_hashes[i],
            "vision_condition_mask_sha256": self.vision_mask_hashes[i],
        } for i, key in enumerate(self.keys))

    @property
    def counts(self) -> SiteCount:
        return SiteCount(self.vision_calls, self.action_calls, len(self.epsilon_seen),
                         len(self.epsilon_seen), self.noising_calls)


@contextmanager
def b0_native_noise_scope(model: Any, coords: tuple[Any, ...], iteration: int, *,
                          checkpoint_fp: str, rank: int, contract: Any):
    """Real B0 canonical ConsumerKey → original model-callsite sigma/epsilon."""
    from v3_packed128_gateb_compare import ConsumerKey
    from v3_gateb1_stochastic import sigma, epsilon

    if not checkpoint_fp or type(rank) is not int or not 0 <= rank < 8:
        raise SiteBlocked("original B0 checkpoint fingerprint/rank required")
    keys = tuple(ConsumerKey(
        checkpoint_fp, rank, iteration, c.ga_member, c.slot_id,
        c.identity.episode_id, c.identity.source_digest, c.binding_epoch,
        c.identity.segment_id, c.identity.cursor, c.absolute_step,
    ) for c in coords)
    if len(set((k.ga_member, k.slot_id, k.absolute_step) for k in keys)) != len(keys):
        raise SiteBlocked("duplicate B0 consumer key in native batch")
    with NativeOmniMoTNoiseSites(model, keys, contract, sigma, epsilon) as sites:
        yield sites
