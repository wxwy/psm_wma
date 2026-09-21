# PSM-WMA E003 WINDOW-H16 Smoke Failure — Cached Multi-Vision ABI Remediation

- Date: 2026-09-21
- Status: IMPLEMENTED / STATIC-REVIEWED / RUNTIME-SMOKE-RETEST-PENDING
- Root baseline before remediation: `6791b92172009741f8267b339fb6302cdb0a2795`
- Child baseline before remediation: `db8ee13c19a524809f4356f34e7dbe71c5d0ec2d`
- Child remediation commit: `d5de2b2f823a68bf7aab9b21d57f4610cd5a4429`

## 1. Failure

The first FSDP8 WINDOW-H16 smoke reached the first `training_step` and all 8 ranks failed at data preparation with:

```text
ValueError: Each cached vision item must contain exactly one latent tensor.
```

Location:

`cosmos_framework/model/generator/omni_mot_model.py`

No optimizer iteration completed and no checkpoint was produced.

This is a WINDOW multi-vision cached-latent ABI integration failure. It is unrelated to EGL/MuJoCo.

## 2. Root cause

WINDOW transform created H history vision items plus the main WAM item.

For H=16:

```text
video:
  [history_pixel_0, ..., history_pixel_15, main_video]

video_latent before fix:
  [history_latent_0, ..., history_latent_15, main_latent]
```

The model's multi-vision preparation first flattens vision items across samples. Its cached-latent consumer then requires every flattened vision item to carry exactly one latent as:

```text
[latent]
```

Thus the required per-sample cached-latent shape is:

```text
[
  [history_latent_0],
  ...,
  [history_latent_15],
  [main_latent],
]
```

The old WINDOW transform emitted bare latent tensors at the item level and violated this ABI.

## 3. Exact remediation

File:

`cosmos-framework/cosmos_framework/data/generator/action/utils/transforms.py`

WINDOW now emits:

```python
data_dict["video_latent"] = [
    [latent] for latent in [*window_history_latents, main_latent]
]
```

Pixel placeholders intentionally remain bare tensors:

```text
[history_pixel_0, ..., history_pixel_15, main_video]
```

Do **not** singleton-wrap each pixel placeholder. The model's multi-vision media flatten path calls `item.unsqueeze(0)`, so wrapping pixels would create a new type mismatch.

## 4. Test coverage

Updated:

`cosmos_framework/data/generator/action/utils/transforms_test.py`

Coverage now asserts:

- normal WINDOW multi-vision latent items are singleton containers
- pixel placeholders remain tensors
- H=16 produces exactly 17 vision items
- 16 history items each carry one-frame latent
- final WAM item carries the 5-frame latent
- source-frame offsets remain `0..16`
- action start offset remains 1

## 5. Semantics unchanged

This remediation does not change the WINDOW-H16 research semantics:

```text
z[-16] ... z[-1] | z0 z1 z2 z3 z4
clean history      current/future WAM
```

It only repairs the container ABI between transform/dataloader/model preparation.

No change to:

- H=16
- full-spatial history latents
- clean historical actions
- loss semantics
- rank count
- grad accumulation
- optimizer
- checkpoint cadence
- Local/GRU/TTT routes

## 6. Required next step

Rerun the gated WINDOW-H16 smoke from iteration 0.

Before FSDP8 launch:

1. sync root/child to the new locked pair
2. run the targeted WINDOW transform test
3. run the existing Phase-0 targeted suite
4. start the same 8-GPU 5-step smoke with `DISABLE_AUTO_RESUME=1`

Because the failed run produced no checkpoint, there is nothing to resume.

If the next failure exposes another ABI mismatch, stop and report before modifying additional production code.
