# PSM-WMA E003 WINDOW-H16 — Current Training Status Record

- Date: 2026-09-21
- Status: TRAINING PATH UNBLOCKED / FORMAL RUNTIME STATUS PARTIALLY OBSERVED
- Root baseline at record creation: `f002680b9be76245dbd47089159ec7c4693426b9`
- Child baseline at record creation: `3fe91004471c74a728df960c05b5eb43ac120510`
- Method: native sliding-window history, H=16
- Checkpoint cadence: `save_iter=100` for formal training; smoke remains `save_iter=1`

## 1. Current method semantics

WINDOW-H16 directly exposes bounded recent visual/action history to the Cosmos backbone without a learned Local compressor:

```text
z[-16] ... z[-1] | z0 z1 z2 z3 z4
clean history      current / future WAM
```

The last H=16 completed observations are represented as full-spatial single-frame cached VAE latents and their executed actions are clean action conditions.

No GRU, Local 1x32 token, or TTT fast-weight state is used.

## 2. Training configuration

Current formal configuration:

- `PSM_HISTORY_MODE=window`
- history horizon: H=16
- FSDP: 8 ranks
- native-forward sample cap: 16 samples/rank
- grad accumulation: GA=16
- effective consumers/update: `16 × 8 × 16 = 2048`
- formal ceiling: `max_iter=5000`
- checkpoint cadence: `save_iter=100`
- logging: every iteration

The current WINDOW path intentionally reduces native-forward samples from the baseline 128 to 16 because H16 carries full-spatial history vision items.

## 3. Integration history

### Round 1 — cached multi-vision latent ABI failure

First FSDP8 smoke failed at iteration 0 before any checkpoint.

Failure:

```text
ValueError: Each cached vision item must contain exactly one latent tensor.
```

Cause:

WINDOW transform emitted per-sample cached latents as a flat list:

```text
[z[-16], ..., z[-1], main_latent]
```

while the model cached multi-vision ABI requires one singleton latent container per vision item:

```text
[[z[-16]], ..., [z[-1]], [main_latent]]
```

Remediation:

- child commit `d5de2b2f823a68bf7aab9b21d57f4610cd5a4429`
- each cached vision item is now exactly one `[latent]`
- pixel placeholders remain tensors because the model media flatten path calls `unsqueeze(0)`

### Round 2 — episode-start mixed-batch ABI failure

The second FSDP8 smoke again failed at iteration 0 with the same model-side assertion.

Real-data diagnosis showed:

- mid-episode H16 sample: correct 17-item multi-vision structure
- episode-start H0 sample: still bare `video` / bare `video_latent`

When these coexist in one batch, the model's batch-level multi-vision probe enters multi-vision mode and misinterprets the bare video's channel dimension as item count.

Observed bad item-count pattern:

```text
[3, 17]
```

Remediation:

- production child commit `0ffbdebce5cdbf3b0a4ab2ded9ecaeed51f73af9`
- every WINDOW sample now uses the same outer multi-vision ABI
- episode start:
  - `video=[main_video]`
  - `video_latent=[[main_latent]]`
  - `image_size=[main_image_size]`
- H16 sample:
  - 16 history items + one main WAM item

Real-data diagnosis after this fix reported correct per-sample counts:

```text
[1, 17]
```

with zero cached-latent ABI failures on the diagnosed path.

### Round 3 — test-only resize assertion bug

The production ABI remediation was validated, but one new unit test failed because it compared the transformed episode-start pixel tensor against the original `256×512` input.

The standard action transform legitimately resolves `resolution=None` to the model tier and resizes:

```text
[3,17,256,512] -> [3,17,192,320]
```

This is existing transform behavior and unrelated to WINDOW semantics.

Test-only closure:

- child commit `3fe91004471c74a728df960c05b5eb43ac120510`
- production code unchanged from `0ffbdebc`
- test now checks structural ABI rather than pixel identity

## 4. Current runtime observation

Latest owner-side observation during WINDOW-H16 training:

```text
GPU memory ~= 25 GB per GPU
```

on the 8-GPU job.

This is substantially below the 80 GB device capacity and indicates that H=16 does not currently present a memory-capacity problem under the existing `16 samples/rank` configuration.

Important qualification:

- this record does not infer a formal smoke PASS, optimizer-step count, loss value, checkpoint existence, or final peak memory unless explicitly reported by the runtime executor
- `nvidia-smi` process memory is not the same as `torch.cuda.max_memory_allocated/reserved`
- a formal peak report should still include full forward/backward/optimizer-step peak

## 5. Current interpretation of memory headroom

The H16 representation increases per-sample vision context substantially:

```text
H0:
  z0 z1 z2 z3 z4

H16:
  z[-16] ... z[-1] z0 z1 z2 z3 z4
```

However the training route compensates by reducing per-rank native-forward samples to 16.

With current observed usage of about 25 GB/GPU, there appears to be significant memory headroom.

If another concurrent training job is considered, the primary risk is likely to shift from raw VRAM capacity toward:

- compute contention
- FSDP/NCCL communication overlap
- step-time inflation
- dataloader / host-resource contention

rather than immediate OOM.

## 6. Remaining formal runtime fields to close

When ds_pro reports again, append:

- exact current root/child SHA
- smoke PASS/FAIL
- completed optimizer iterations
- finite total/vision/action losses
- `torch.cuda.max_memory_allocated`
- `torch.cuda.max_memory_reserved`
- per-step wall time
- checkpoint path(s)
- reload + closed-loop smoke status
- formal-training auto-resume status

Until those are reported, preserve the distinction:

```text
production ABI path fixed and real-data validated
!=
formal training gate fully closed
```

## 7. Experiment role

WINDOW-H16 is the key matched control for the Local Memory study:

```text
Off       : no explicit history
WINDOW-H16: raw recent history
Init      : learned W0 + dynamic retrieval, no online write
Required  : learned W0 + dynamic retrieval + online fast-weight write
```

The final comparison should therefore be:

```text
Required / Init / WINDOW-H16 / Off
```

to separate raw history access, learned retrieval/compression, and episode-specific online persistent writing.
