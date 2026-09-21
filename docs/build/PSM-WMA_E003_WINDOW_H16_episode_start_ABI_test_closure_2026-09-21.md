# PSM-WMA E003 WINDOW-H16 — Episode-Start ABI Test Assertion Closure

- Date: 2026-09-21
- Status: TEST-ONLY FIX / PRODUCTION ABI REMEDIATION UNCHANGED
- Root baseline: `19bbfda1264224a66d8b41ef7326aee61cb54e1a`
- Production child: `0ffbdebce5cdbf3b0a4ab2ded9ecaeed51f73af9`
- Test-only child closure: `3fe91004471c74a728df960c05b5eb43ac120510`

## 1. Context

After the episode-start ABI remediation, real-data diagnosis confirmed the production fix:

- episode-start sample is now an explicit one-item vision list
- H16 sample remains a 17-item vision list
- mixed per-sample vision-item counts are `[1,17]`
- every cached latent item is a singleton `[latent]`
- the prior `omni_mot_model.py` cached-latent singleton assertion no longer reproduces on the diagnosed real-data path

One new unit test still failed.

## 2. Test failure

Test:

`test_action_transform_pipeline_native_window_episode_start_uses_single_item_multi_vision_abi`

The test compared:

```python
result["video"][0] == main_video
```

pixel-for-pixel.

With `resolution=None`, the standard action transform resolves the model input resolution tier and resizes the input video. Therefore a `256x512` test input can legitimately become `192x320`.

The test was asserting an unrelated resize invariant, not the WINDOW ABI contract.

## 3. Fix

Only `transforms_test.py` changed.

The test now verifies the relevant structural contract:

- exactly one outer vision item
- item remains a tensor
- channel/time dimensions remain `[3,17]`
- dtype remains uint8
- cached latent remains exactly `[[main_latent]]`
- one image-size item
- source-frame offsets remain `[0]`
- action start offset remains 1

No production code changed from child `0ffbdebce5cdbf3b0a4ab2ded9ecaeed51f73af9`.

## 4. Execution decision

This test-only closure does not invalidate the real-data ABI evidence or require another design change.

ds_pro may continue:

1. sync root/child
2. rerun the targeted transform test / Phase 0
3. continue the fresh FSDP8 5-step smoke from iter0

If the FSDP8 runtime produces a new production failure, stop and report before changing additional code.
