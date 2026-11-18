"""CPU genuine-batch call/contract probes; no real Wan or GPU evidence."""

import copy
from pathlib import Path

import numpy as np
import pytest
import torch

from g2.latent_cache.batch_contract import make_batch_recipe
from g2.latent_cache.batch_encoding import WanBatchEncoder
from g2.latent_cache.contract import (
    CacheError,
    make_recipe,
    preprocessing_recipe,
    validate_recipe,
)
from g2.tests.test_view_vae_encoding import FakeWan

CHILD = Path(__file__).resolve().parents[2] / "cosmos-framework"


class NativeBatchProbe(FakeWan):
    def encode(self, pixels):
        assert pixels.ndim == 5 and pixels.shape[1:] == (3, 1, 256, 256)
        assert pixels.dtype == torch.float32 and not torch.is_grad_enabled()
        self.calls.append(pixels.clone())
        values = pixels.mean((1, 2, 3, 4))
        out = values[:, None, None, None, None].expand(-1, 48, 1, 16, 16).clone()
        if self.failure == "nan":
            out[0, 0, 0, 0, 0] = float("nan")
        if self.failure == "dtype":
            out = out.to(torch.bfloat16)
        if self.failure == "time":
            out = out.repeat(1, 1, 2, 1, 1)
        if self.failure == "batch":
            out = out[:1]
        if self.failure == "truncated":
            out = out[:, :, :, :1]
        if self.failure == "retained":
            self.model.model._enc_cache[0] = torch.ones(1)
        return out


def fake_encoder(tmp_path):
    weights = tmp_path / "TEST_ONLY_weights.pth"
    weights.write_bytes(b"FAKE_CPU_NOT_WAN")
    made = []

    def factory(**kwargs):
        obj = NativeBatchProbe(**kwargs)
        made.append(obj)
        return obj

    return WanBatchEncoder(
        weights, cosmos_root=CHILD, device="cpu", _tokenizer_factory=factory
    ), made


@pytest.mark.parametrize("count", [1, 8, 16, 32])
def test_one_actual_native_batch_call_preserves_T1_full_grid_and_member_independence(
    tmp_path, count
):
    encoder, made = fake_encoder(tmp_path)
    images = [np.full((19, 31, 3), n, np.uint8) for n in range(count)]
    results = encoder.encode_batch(images, preprocessing_recipe())
    assert len(made) == 1 and len(made[0].calls) == 1
    assert tuple(made[0].calls[0].shape) == (count, 3, 1, 256, 256)
    assert len(results) == count
    for i, (latent, prep) in enumerate(results):
        assert latent.shape == (48, 16, 16) and latent.dtype == torch.float32
        assert latent.untyped_storage().nbytes() == latent.numel() * 4
        assert prep["batch_position"] == i and prep["vae_input_shape"] == [
            count,
            3,
            1,
            256,
            256,
        ]
        assert prep["original_hw"] == [19, 31] and prep["storage_conversion"]["exact"]
    if count > 1:
        assert not torch.equal(results[0][0], results[-1][0])
    with pytest.raises(CacheError, match="no silent B1"):
        encoder.encode(images[0], preprocessing_recipe())


@pytest.mark.parametrize(
    "failure", ["nan", "dtype", "time", "batch", "truncated", "retained"]
)
def test_native_bad_batch_never_yields_a_valid_partial_result(tmp_path, failure):
    encoder, made = fake_encoder(tmp_path)
    encoder.encode_batch([np.zeros((8, 8, 3), np.uint8)], preprocessing_recipe())
    made[0].failure = failure
    with pytest.raises((CacheError, RuntimeError)):
        encoder.encode_batch(
            [np.zeros((8, 8, 3), np.uint8)] * 2, preprocessing_recipe()
        )


def test_batch_recipe_is_separate_and_legacyB1_rejects_batch_relabel(tmp_path):
    encoder, _ = fake_encoder(tmp_path)
    legacy = make_recipe(encoder.base.descriptor())
    batch = make_batch_recipe(encoder.descriptor())
    assert legacy["recipe_id"] != batch["recipe_id"]
    assert validate_recipe(batch) == batch and validate_recipe(legacy) == legacy
    assert batch["record_shape"] == [48, 16, 16]
    assert batch["actual_batch_range"] == [1, 32]
    with pytest.raises(CacheError):
        make_recipe(encoder.base.descriptor(), batch_size=32)
    changed = copy.deepcopy(batch)
    changed["batch_size"] = 8
    with pytest.raises(CacheError):
        validate_recipe(changed)


@pytest.mark.parametrize("count", [0, 33])
def test_empty_or_oversized_call_is_rejected_before_model_load(tmp_path, count):
    encoder, made = fake_encoder(tmp_path)
    with pytest.raises(CacheError):
        encoder.encode_batch(
            [np.zeros((8, 8, 3), np.uint8)] * count, preprocessing_recipe()
        )
    assert not made


def test_shape_and_storage_recipe_limits_do_not_guess_a_new_model_bucket(tmp_path):
    encoder, made = fake_encoder(tmp_path)
    with pytest.raises(CacheError):
        make_batch_recipe(encoder.descriptor(), preprocessing_recipe(1024, 1024))
    with pytest.raises(CacheError):
        make_batch_recipe(encoder.descriptor(), storage_dtype="bfloat16")
    with pytest.raises(CacheError):
        encoder.encode_batch(
            [np.zeros((8, 8, 3), np.uint8)], preprocessing_recipe(1024, 1024)
        )
    assert not made
