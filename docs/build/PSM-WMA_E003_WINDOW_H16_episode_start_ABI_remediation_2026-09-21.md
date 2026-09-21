# PSM-WMA E003 WINDOW-H16 Smoke Failure Round 2 — Episode-Start ABI Remediation

- Date: 2026-09-21
- Status: IMPLEMENTED / STATIC-REVIEWED / RUNTIME-SMOKE-RETEST-PENDING
- Root baseline before remediation: `85e6ad28041cceadd46eb9dd9c60ccfbf082ce89`
- Child baseline before remediation: `d5de2b2f823a68bf7aab9b21d57f4610cd5a4429`
- Child remediation commit: `0ffbdebce5cdbf3b0a4ab2ded9ecaeed51f73af9`

## 1. Second smoke failure

The second FSDP8 WINDOW-H16 5-step smoke again failed on all 8 ranks at iteration 0 with:

```text
ValueError: Each cached vision item must contain exactly one latent tensor.
```

No checkpoint was produced.

The first remediation correctly fixed mid-episode H=16 samples, but the mixed-batch episode-start boundary remained inconsistent.

## 2. Real-data diagnosis

Runtime diagnosis confirmed:

- mid-episode WINDOW sample:
  - `video`: 17-item list
  - `video_latent`: 17 singleton cached-latent items
- episode-start WINDOW sample:
  - history length = 0
  - transform skipped the structure-normalization body because it was gated by `num_history_actions > 0`
  - the main video / cached latent therefore remained on the ordinary bare-tensor shape

When these samples coexisted in one training batch, the model correctly detected that the batch contains multi-vision samples because at least one sample has 17 items. The episode-start bare tensor then violated the per-sample multi-vision ABI and ultimately reached the cached-latent singleton assertion.

The current dataset already supplies an explicit empty WINDOW payload at episode start:

```text
window_history_video_latent = []
history_action = empty
window_history_frame_indices = empty
```

Therefore no dataset change is required. The missing normalization was solely in the transform.

## 3. Selected remediation

Use the minimal transform-side solution.

For every WINDOW sample, including zero-history episode start:

```text
video        = [main_video]
video_latent = [[main_latent]]
image_size   = [main_image_size]
```

For a sample with H completed history steps:

```text
video =
  [history_placeholder_0, ..., history_placeholder_(H-1), main_video]

video_latent =
  [[history_latent_0], ..., [history_latent_(H-1)], [main_latent]]
```

Thus a mixed batch has explicit per-sample item counts such as:

```text
[1, 17]
```

instead of accidentally interpreting a bare video's channel dimension as an item count.

## 4. Code change

File:

`cosmos-framework/cosmos_framework/data/generator/action/utils/transforms.py`

The common WINDOW ABI normalization was moved outside the `num_history_actions > 0` branch.

The history-specific content remains conditional only through the length of the history arrays.

For both H=0 and H>0:

- `video` is a list of vision-item tensors
- each `video_latent` vision item is a singleton `[latent]`
- `image_size` is a list aligned 1:1 with vision items
- `action_start_frame_offset=1`
- `vision_item_source_frame_offsets=range(H+1)`

No change to `omni_mot_model.py` or the dataset.

## 5. Added tests

Updated:

`cosmos-framework/cosmos_framework/data/generator/action/utils/transforms_test.py`

New coverage:

1. episode-start WINDOW sample:
   - history length 0
   - `video=[main_video]`
   - `video_latent=[[main_latent]]`
   - one aligned `image_size`
   - offsets `[0]`

2. mixed episode-start / H16 structural contract:
   - per-sample vision item counts `[1,17]`
   - per-sample latent item counts `[1,17]`
   - every cached item is exactly one singleton latent container

The existing H16 17-item contract test remains.

## 6. Research semantics unchanged

The formal WINDOW-H16 semantics remain:

```text
z[-16] ... z[-1] | z0 z1 z2 z3 z4
clean history      current/future WAM
```

At episode start there simply is no completed history yet:

```text
z0 z1 z2 z3 z4
```

The ABI wrapper does not add synthetic historical content.

No change to:

- H=16
- history action semantics
- clean/noised masks
- optimizer
- FSDP
- GA
- effective batch
- checkpoint cadence
- Local / GRU / TTT routes

## 7. Required retest

Before the next FSDP8 smoke:

1. sync the new root/child pair
2. run `transforms_test.py`
3. run the current Phase-0 targeted suite
4. run the same FSDP8 5-step smoke from iteration 0 with `DISABLE_AUTO_RESUME=1`

There is still no checkpoint to resume.

If another production ABI/runtime failure occurs, stop and report before modifying additional code.
