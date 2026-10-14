"""CPU-only P0/P1 witness tests; never enter real FSDP/native model."""

from __future__ import annotations

import random
import sys
from pathlib import Path
from dataclasses import replace

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v3_gateb1_stochastic as stochastic  # noqa: E402
from v3_packed128_gateb_compare import ConsumerKey  # noqa: E402


def key(slot=0, t=2, rank=0):
    return ConsumerKey("source-fingerprint", rank, 1300, 0, slot, "episode_0003", "src-ep", 1, 42, 0, t)


def contract(profile="P1_MATCHED_STOCHASTIC", **changes):
    return replace(stochastic.SamplingContract(profile, "waver", 5.0, "none", False, cfg_dropout_rate=0.1), **changes)


def test_p0_sigma_half_and_shared_action():
    c = contract(profile="P0_FIXED")
    assert float(stochastic.sigma(key(), c)) == 0.5
    assert stochastic.sigma(key(), c, modality="action").item() == 0.5


def test_p1_matches_manual_production_waver_formula_on_same_seed():
    k, c = key(), contract()
    s = stochastic.sigma(k, c)
    gen = stochastic._generator(k, site="sigma", modality="vision")
    u = torch.rand((), generator=gen, dtype=torch.float32)
    value = 1 - u - 1.29 * (torch.cos(torch.pi / 2 * u).square() - 1 + u)
    shifted = 5.0 * value / (1 + (5.0 - 1) * value)
    torch.testing.assert_close(s, shifted, rtol=0, atol=0)
    assert 0 <= s.item() <= 1


def test_p1_video_sigma_shared_with_action_when_independent_schedule_false():
    c = contract()
    torch.testing.assert_close(stochastic.sigma(key(), c), stochastic.sigma(key(), c, modality="action"),
                               rtol=0, atol=0)


def test_keyed_noise_is_reproducible_order_independent_and_domain_separated():
    a, b, c = key(slot=0), key(slot=1), contract()
    state = random.getstate()
    first = stochastic.witness(a, c, vision_shape=(2, 3, 4, 4), action_shape=(16, 64))
    second = stochastic.witness(b, c, vision_shape=(2, 3, 4, 4), action_shape=(16, 64))
    reversed_order = stochastic.witness(a, c, vision_shape=(2, 3, 4, 4), action_shape=(16, 64))
    assert first == reversed_order
    assert first["vision_epsilon_sha256"] != second["vision_epsilon_sha256"]
    assert first["vision_epsilon_sha256"] != first["action_epsilon_sha256"]
    assert random.getstate() == state


def test_sigma_changes_with_frame_in_diffusion_forcing():
    c = contract(causal_training_strategy="diffusion_forcing")
    assert stochastic.sigma(key(), c, frame_index=0).item() != stochastic.sigma(key(), c, frame_index=1).item()
    with pytest.raises(stochastic.StochasticBlocked, match="per-frame"):
        stochastic.witness(key(), c, vision_shape=(2, 3), action_shape=(16, 64))


def test_independent_action_requires_distribution_and_actual_shift():
    with pytest.raises(stochastic.StochasticBlocked, match="distribution"):
        contract(independent_action_schedule=True)
    with pytest.raises(stochastic.StochasticBlocked, match="shift"):
        contract(independent_action_schedule=True, action_distribution="logitnormal")
    c = contract(independent_action_schedule=True, action_distribution="logitnormal", action_shift=3.0)
    assert stochastic.sigma(key(), c, modality="vision").item() != stochastic.sigma(key(), c, modality="action").item()


@pytest.mark.parametrize("value", ["ltx2", "invalid", "", "none"])
def test_unverified_distribution_is_rejected(value):
    with pytest.raises(stochastic.StochasticBlocked):
        contract(vision_distribution=value)


def test_unknown_causal_strategy_rejected():
    with pytest.raises(stochastic.StochasticBlocked, match="causal"):
        contract(causal_training_strategy="unknown")


def test_missing_epsilon_geometry_rejected():
    with pytest.raises(stochastic.StochasticBlocked):
        stochastic.epsilon(key(), (0, 64), modality="action")
    with pytest.raises(stochastic.StochasticBlocked):
        stochastic.epsilon(key(), (2, 4), modality="sound")


def test_p0_and_p1_epsilon_share_keyed_noise_and_never_touch_global_rng():
    before = torch.get_rng_state()
    a = stochastic.epsilon(key(), (4, 5), modality="vision")
    b = stochastic.epsilon(key(), (4, 5), modality="vision")
    torch.testing.assert_close(a, b, rtol=0, atol=0)
    assert torch.equal(before, torch.get_rng_state())


def test_caption_cfg_is_different_from_condition_mask_and_tracks_cfg_probability():
    c = contract(cfg_dropout_rate=1.0)
    assert stochastic.caption_cfg_drop(key(), c)
    c = contract(cfg_dropout_rate=0.0)
    assert not stochastic.caption_cfg_drop(key(), c)


def test_unverified_sigma_identity_rejected():
    with pytest.raises(stochastic.StochasticBlocked):
        stochastic.sigma(key(), contract(), modality="sound")
    with pytest.raises(stochastic.StochasticBlocked):
        stochastic.sigma(key(), contract(), frame_index=-1)
