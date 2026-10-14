"""CPU-only scoped *actual model-method* RNG injection fixtures."""
from __future__ import annotations

from types import SimpleNamespace
import pytest
import torch

from v3_gateb1_model_sites import NativeOmniMoTNoiseSites, SiteBlocked


class Model:
    def __init__(self, causal="none"):
        self.config = SimpleNamespace(
            causal_training_strategy=causal, sound_gen=False,
            rectified_flow_training_config=SimpleNamespace(
                independent_action_schedule=False, train_time_video_distribution="waver",
                shift={"480": 5},
            ),
        )
        self.tensor_kwargs_fp32 = {"device": torch.device("cpu"), "dtype": torch.float32}
        flow = SimpleNamespace(noise_scheduler=SimpleNamespace(config=SimpleNamespace(num_train_timesteps=1000)))
        self.rectified_flow_video = flow
        self.rectified_flow_action = flow

    def _get_train_noise_level_vision(self, **kwargs):
        raise AssertionError("unkeyed production vision sampler should not run")

    def _get_train_noise_level_action(self, **kwargs):
        raise AssertionError("unkeyed production action sampler should not run")

    def _add_noise_to_input(self, clean, packed, sigmas, iteration=None):
        gen = torch.Generator().manual_seed(99)
        # Exact native ordering: vision samples, then action samples.
        a = [torch.randn(x.size(), generator=gen, **self.tensor_kwargs_fp32)
             for x in clean.x0_tokens_vision]
        if all(torch.all(mask == 1).item() for mask in packed.action.condition_mask):
            b = [torch.zeros_like(x) for x in clean.x0_tokens_action]
        else:
            b = [torch.randn(x.size(), generator=gen, **self.tensor_kwargs_fp32)
                 for x in clean.x0_tokens_action]
        return a, b


class Key:
    def __init__(self, position, iteration=1300):
        self.position = position
        self.completed_iteration = iteration
        self.absolute_step = position


class Contract:
    causal_training_strategy = "none"
    independent_action_schedule = False
    vision_distribution = "waver"
    vision_shift = 5.0


def sigma(key, contract, *, modality, frame_index=0):
    return torch.tensor(0.2 + 0.1 * key.absolute_step + 0.01 * frame_index, dtype=torch.float32)


def epsilon(key, shape, *, modality):
    offset = 1 if modality == "vision" else 10
    return torch.full(shape, float(key.position + offset), dtype=torch.float32)


def inputs(*, all_conditioned=False):
    clean = SimpleNamespace(x0_tokens_vision=[torch.ones((3, 2, 4, 4)) for _ in range(2)],
                            x0_tokens_action=[torch.ones((16, 64)) for _ in range(2)],
                            x0_tokens_lidar=[], x0_tokens_radar=[], x0_tokens_sound=[])
    mask = torch.ones((16, 1)) if all_conditioned else torch.zeros((16, 1))
    packed = SimpleNamespace(action=SimpleNamespace(condition_mask=[mask, mask]))
    return clean, packed


def call(model, *, all_conditioned=False):
    clean, packed = inputs(all_conditioned=all_conditioned)
    t, sigmas = model._get_train_noise_level_vision(batch_size=2, is_image_batch=False,
        num_vision_latent_frames=[2, 2], iteration=1300, resolutions=["480", "480"])
    return t, sigmas, model._add_noise_to_input(clean, packed, sigmas, iteration=1300)


def test_original_native_sigma_and_epsilon_method_sites_are_scoped_and_restored():
    model, keys, c = Model(), (Key(0), Key(1)), Contract()
    prev_vision = model._get_train_noise_level_vision.__func__
    prev_noise = model._add_noise_to_input.__func__
    with NativeOmniMoTNoiseSites(model, keys, c, sigma, epsilon) as hook:
        time, levels, (v, a) = call(model)
        assert time.shape == levels.shape == (2, 1)
        torch.testing.assert_close(levels.squeeze(-1), torch.tensor([0.2, 0.3]), rtol=0, atol=1e-7)
        assert (v[0] == 1).all() and (v[1] == 2).all()
        assert (a[0] == 10).all() and (a[1] == 11).all()
        assert len(hook.epsilon_seen) == 4
    assert model._get_train_noise_level_vision.__func__ is prev_vision
    assert model._add_noise_to_input.__func__ is prev_noise
    assert "_add_noise_to_input" not in vars(model)


def test_conditioned_action_not_noised_and_vision_still_aligned():
    model = Model()
    with NativeOmniMoTNoiseSites(model, (Key(0), Key(1)), Contract(), sigma, epsilon) as hook:
        _, _, (v, a) = call(model, all_conditioned=True)
        assert len(hook.epsilon_seen) == 2
        assert all((x == 0).all() for x in a)
        assert (v[0] == 1).all()


def test_missing_native_sigma_site_fails_after_context_and_restores():
    model = Model()
    with pytest.raises(SiteBlocked, match="missing original"):
        with NativeOmniMoTNoiseSites(model, (Key(0),), Contract(), sigma, epsilon):
            pass
    assert "_add_noise_to_input" not in vars(model)


def test_missing_native_epsilon_call_fails_after_context_and_restores():
    model = Model()
    with pytest.raises(SiteBlocked, match="missing original"):
        with NativeOmniMoTNoiseSites(model, (Key(0), Key(1)), Contract(), sigma, epsilon):
            model._get_train_noise_level_vision(batch_size=2, is_image_batch=False,
                num_vision_latent_frames=[2, 2], iteration=1300, resolutions=["480", "480"])
    assert "_get_train_noise_level_vision" not in vars(model)


def test_extra_unregistered_randn_site_fails_closed():
    m = Model()
    old = m._add_noise_to_input
    def broken(clean, packed, sigmas, iteration):
        v, a = old(clean, packed, sigmas, iteration)
        torch.randn((1,), dtype=torch.float32)
        return v, a
    m._add_noise_to_input = broken
    with pytest.raises(SiteBlocked, match="extra"):
        with NativeOmniMoTNoiseSites(m, (Key(0), Key(1)), Contract(), sigma, epsilon):
            call(m)
    assert m._add_noise_to_input is broken


def test_unknown_sensor_modality_blocks_before_randn():
    m = Model()
    clean, packed = inputs()
    clean.x0_tokens_lidar = [torch.ones((1, 1, 1, 1))]
    with pytest.raises(SiteBlocked, match="lidar"):
        with NativeOmniMoTNoiseSites(m, (Key(0), Key(1)), Contract(), sigma, epsilon):
            m._add_noise_to_input(clean, packed, torch.ones(2, 1), iteration=1300)


def test_native_batch_mismatch_blocks_before_randomness():
    m = Model()
    with pytest.raises(SiteBlocked, match="batch/latent"):
        with NativeOmniMoTNoiseSites(m, (Key(0), Key(1)), Contract(), sigma, epsilon):
            m._get_train_noise_level_vision(batch_size=1, is_image_batch=False,
                num_vision_latent_frames=[2], iteration=1300, resolutions=["480"])


def test_diffusion_forcing_sigma_geometry_respects_native_tmax():
    m = Model(causal="diffusion_forcing")
    c = Contract()
    c.causal_training_strategy = "diffusion_forcing"
    with NativeOmniMoTNoiseSites(m, (Key(0), Key(1)), c, sigma, epsilon) as hook:
        time, levels = m._get_train_noise_level_vision(batch_size=2, is_image_batch=False,
            num_vision_latent_frames=[3, 2], iteration=1300, resolutions=["480", "480"])
        assert levels.shape == (2, 3)
        assert time.shape == (2, 3)
        clean, packed = inputs()
        v, a = m._add_noise_to_input(clean, packed, levels, iteration=1300)
        assert len(v) == len(a) == 2
        assert hook.vision_calls == 1


def test_sigma_distribution_mismatch_is_fail_closed():
    m = Model()
    m.config.rectified_flow_training_config.train_time_video_distribution = "logitnormal"
    with pytest.raises(SiteBlocked, match="distribution"):
        with NativeOmniMoTNoiseSites(m, (Key(0), Key(1)), Contract(), sigma, epsilon):
            call(m)


def test_sigma_shift_mismatch_is_fail_closed():
    m = Model()
    m.config.rectified_flow_training_config.shift = {"480": 3}
    with pytest.raises(SiteBlocked, match="shift"):
        with NativeOmniMoTNoiseSites(m, (Key(0), Key(1)), Contract(), sigma, epsilon):
            call(m)
