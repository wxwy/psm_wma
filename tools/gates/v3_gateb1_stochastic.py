"""CPU-only per-Consumer matched stochastic inputs for proposed V3 B1 profiles.

This producer is NOT yet injected into the native Cosmos/FSDP training sites.
P1 uses explicit resolved distribution/shift (no silent defaults); it must be
bound to the true runtime configuration before a separate GPU authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import random
from typing import Any

import torch

from v3_packed128_gateb_compare import ConsumerKey, stable_seed


class StochasticBlocked(ValueError):
    """Unsupported or unverified stochastic call site/configuration."""


@dataclass(frozen=True)
class SamplingContract:
    profile: str                         # P0_FIXED | P1_MATCHED_STOCHASTIC
    vision_distribution: str            # Actual resolved value, e.g. waver
    vision_shift: float                  # Actual per-consumer resolved shift
    causal_training_strategy: str       # none | teacher_forcing | diffusion_forcing
    independent_action_schedule: bool
    action_distribution: str | None = None
    action_shift: float | None = None
    cfg_dropout_rate: float = 0.1

    def __post_init__(self) -> None:
        if self.profile not in {"P0_FIXED", "P1_MATCHED_STOCHASTIC"}:
            raise StochasticBlocked("unapproved stochastic profile")
        if self.vision_distribution not in {"waver", "uniform", "logitnormal"}:
            raise StochasticBlocked("unsupported unresolved P1 vision distribution")
        if self.causal_training_strategy not in {"none", "teacher_forcing", "diffusion_forcing"}:
            raise StochasticBlocked("unknown causal strategy")
        if not math.isfinite(self.vision_shift) or self.vision_shift <= 0:
            raise StochasticBlocked("invalid resolved vision shift")
        if not math.isfinite(self.cfg_dropout_rate) or not 0 <= self.cfg_dropout_rate <= 1:
            raise StochasticBlocked("invalid text CFG dropout rate")
        if self.independent_action_schedule:
            if self.action_distribution not in {"waver", "uniform", "logitnormal"}:
                raise StochasticBlocked("independent action schedule distribution unverified")
            if self.action_shift is None or not math.isfinite(self.action_shift) or self.action_shift <= 0:
                raise StochasticBlocked("independent action shift is missing")
        elif self.action_distribution is not None or self.action_shift is not None:
            raise StochasticBlocked("shared action sigma must not trigger its own P1 random draws")


def _generator(key: ConsumerKey, *, site: str, modality: str, item_index: int = 0,
               subindex: int = 0) -> torch.Generator:
    g = torch.Generator(device="cpu")
    # Use the original B0 length-prefixed and domain-separated seed schema.
    g.manual_seed(stable_seed(key.scoped(site, modality, item_index, subindex), domain=f"B1:{site}:{modality}"))
    return g


def _unshifted_sample(distribution: str, generator: torch.Generator) -> torch.Tensor:
    if distribution == "uniform":
        return torch.rand((), generator=generator, dtype=torch.float32)
    if distribution == "logitnormal":
        return torch.sigmoid(torch.randn((), generator=generator, dtype=torch.float32))
    if distribution == "waver":
        u = torch.rand((), generator=generator, dtype=torch.float32)
        return 1.0 - u - 1.29 * (torch.cos(torch.pi / 2.0 * u).square() - 1 + u)
    raise StochasticBlocked(f"unverified sigma distribution {distribution}")


def sigma(key: ConsumerKey, contract: SamplingContract, *, modality: str = "vision",
          item_index: int = 0, frame_index: int = 0) -> torch.Tensor:
    """One per-consumer scalar sigma matching the selected production distribution.

    For diffusion_forcing the caller must request a separate frame_index key
    for each VAE latent frame and explicitly validate actual frame count/masks.
    """
    if item_index < 0 or frame_index < 0 or modality not in ("vision", "action"):
        raise StochasticBlocked("invalid sigma identity/site")
    if modality == "action" and not contract.independent_action_schedule:
        # Actual Cosmos3 Edge default action schedule reuses vision sigma.
        return sigma(key, contract, modality="vision", item_index=item_index, frame_index=frame_index)
    if contract.profile == "P0_FIXED":
        return torch.tensor(0.5, dtype=torch.float32)
    distribution = contract.vision_distribution if modality == "vision" else contract.action_distribution
    shift = contract.vision_shift if modality == "vision" else contract.action_shift
    if distribution is None or shift is None:
        raise StochasticBlocked("resolved sigma distribution or shift absent")
    frame = frame_index if contract.causal_training_strategy == "diffusion_forcing" else 0
    generator = _generator(key, site="sigma", modality=modality, item_index=item_index, subindex=frame)
    x = _unshifted_sample(distribution, generator)
    # Production RectifiedFlow.TrainTimeSampler uses this exact non-ltx2 warp.
    return (shift * x / (1 + (shift - 1) * x)).to(torch.float32)


def epsilon(key: ConsumerKey, shape: tuple[int, ...], *, modality: str,
            item_index: int = 0, subindex: int = 0) -> torch.Tensor:
    """Individual native vision/action item with explicit dimension identity."""
    if modality not in {"vision", "action"} or not shape or any(type(x) is not int or x <= 0 for x in shape):
        raise StochasticBlocked("epsilon shape/modality contract missing")
    if item_index < 0 or subindex < 0:
        raise StochasticBlocked("invalid epsilon consumer subindex")
    return torch.randn(shape, generator=_generator(key, site="epsilon", modality=modality,
                                                  item_index=item_index, subindex=subindex), dtype=torch.float32)


def caption_cfg_drop(key: ConsumerKey, contract: SamplingContract) -> bool:
    """Text-tokenizer caption dropout decision, NOT a vision/action condition mask."""
    state = key.scoped("cfg_dropout", "caption")
    seed = stable_seed(state, domain="python_cfg")
    return random.Random(seed).random() < contract.cfg_dropout_rate


def tensor_fingerprint(value: torch.Tensor) -> str:
    if value.device.type != "cpu" or not value.is_contiguous():
        raise StochasticBlocked("witness fingerprint requires contiguous CPU tensor")
    meta = f"{value.dtype}:{tuple(value.shape)}".encode()
    return hashlib.sha256(len(meta).to_bytes(8, "big") + meta + value.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest()


def witness(key: ConsumerKey, contract: SamplingContract, *, vision_shape: tuple[int, ...],
            action_shape: tuple[int, ...]) -> dict[str, Any]:
    """Frozen per-Consumer identity only; not a replacement for model-site hooks."""
    if contract.causal_training_strategy == "diffusion_forcing":
        raise StochasticBlocked("per-frame sigma needs an explicit native frame-count plan")
    vision_sigma = sigma(key, contract, modality="vision")
    action_sigma = sigma(key, contract, modality="action")
    eps_vision = epsilon(key, vision_shape, modality="vision")
    eps_action = epsilon(key, action_shape, modality="action")
    return {
        "key": key.as_dict(),
        "profile": contract.profile,
        "vision_sigma": float(vision_sigma),
        "action_sigma": float(action_sigma),
        "vision_sigma_sha256": tensor_fingerprint(vision_sigma),
        "action_sigma_sha256": tensor_fingerprint(action_sigma),
        "vision_epsilon_sha256": tensor_fingerprint(eps_vision),
        "action_epsilon_sha256": tensor_fingerprint(eps_action),
        "cfg_caption_dropped": caption_cfg_drop(key, contract),
    }
