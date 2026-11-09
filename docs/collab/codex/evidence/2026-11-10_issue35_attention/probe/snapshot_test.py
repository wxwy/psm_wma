"""Probe correctness: native serialization must retain layout, alias and RNG."""

import torch
import pytest

from hooks.freeze_capture import save_torch, tensor_tree


@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16])
def test_roundtrip_preserves_views_aliases_rng_and_original_values(tmp_path, dtype):
    base = torch.arange(128, dtype=dtype).reshape(8, 16)
    payload = dict(
        base=base,
        view=base[1:7, 2:14:2],
        expanded=base[:1].expand(4, 16),
        scalar=base[0, 0],
    )
    rng = torch.get_rng_state().clone()
    old = tensor_tree(payload)
    path = tmp_path / "record.pt"
    save_torch(path, payload)
    loaded = torch.load(path, weights_only=False)
    assert old == tensor_tree(loaded)
    assert torch.equal(rng, torch.get_rng_state())
    loaded["view"][0, 0] += 1
    assert loaded["base"][1, 2] == base[1, 2] + 1
    assert payload["base"][1, 2] == 18


def test_native_generation_carrier_roundtrip(tmp_path):
    from cosmos_framework.data.generator.action.utils.action_processing import (
        ActionProcessingRecord,
    )
    from cosmos_framework.data.generator.sequence_packing.sequence import SequencePlan
    from cosmos_framework.model.generator.utils.data_and_condition import (
        GenerationDataClean,
    )

    x = torch.randn(1, 16, 2, 2, 2)
    payload = dict(
        batch=dict(
            video=[[x]],
            action_processing_record=[
                ActionProcessingRecord(raw_action_dim=15, action_normalizer=None)
            ],
        ),
        prepared=(
            [SequencePlan(has_text=True, has_vision=True, has_action=True)],
            GenerationDataClean(
                batch_size=1,
                is_image_batch=False,
                x0_tokens_vision=[x],
                x0_tokens_local_memory=[torch.randn(4, 32)],
            ),
        ),
    )
    path = tmp_path / "carrier.pt"
    save_torch(path, payload)
    loaded = torch.load(path, weights_only=False)
    assert tensor_tree(payload) == tensor_tree(loaded)
    assert loaded["batch"]["video"][0][0] is loaded["prepared"][1].x0_tokens_vision[0]
    assert loaded["prepared"][0][0].has_vision


def test_native_fast_record_and_prefix_roundtrip(tmp_path):
    from cosmos_framework.inference.local_memory_online import _Record
    from cosmos_framework.model.generator.mot.local_evidence import (
        ContinualTTTFastState,
    )

    state = ContinualTTTFastState(*(torch.randn(2, 3) for _ in range(4)))
    previous = _Record("episode", 16, state, torch.randn(4, 32), "previous", 1, 16)
    candidate = _Record("episode", 32, state, torch.randn(4, 32), "candidate", 1, 16)
    payload = dict(previous=previous, candidate=candidate, prefixes=[candidate.token])
    path = tmp_path / "records.pt"
    save_torch(path, payload)
    loaded = torch.load(path, weights_only=False)
    assert tensor_tree(payload) == tensor_tree(loaded)
    assert loaded["candidate"].state is loaded["previous"].state
    assert loaded["candidate"].token is loaded["prefixes"][0]
    assert loaded["candidate"].consumer_step == 32
