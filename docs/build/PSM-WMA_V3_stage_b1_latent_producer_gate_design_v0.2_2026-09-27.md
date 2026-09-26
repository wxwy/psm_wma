# PSM-WMA V3 Stage B1-Latent Producer Gate Design v0.2

- Date: 2026-09-27
- Gate: `V3-STAGE-B1-LATENT-PRODUCER`
- Supersedes: v0.1 at root `f0d020dd8c06ab734bd6d8b8d915c937fd57b94a`.
- Remediation target: formal implementation pair `bedef75b6bc76cb167f2e27aeaecfe303865f9ab / 5f9c39464761665843b0f08c5e1d578f72114b33`, reviewed as `REQUEST_CHANGES`.
- Scope remains B1 only: cached RGB latent -> causal visual96 -> B0 SegmentBatch. No trainer/GPU/policy-cached-latent wiring.

Everything from v0.1 remains frozen except the real-cache physical ABI, endpoint-vector rule and camera authority below.

## 1. Canonical real-cache physical ABI

For this Gate, metadata authority is the H5 root group `/`.

Required root attrs:
- `episode_id`
- `frame_count` (positive integer)
- `temporal_compression_factor == 4`
- `source_frame_to_latent_policy == "causal_endpoint"`.

Do not require or synthesize `source_video_frames`; the existing cache does not use that attr.

Canonical Stage-A-matched camera set is exactly:
- left: `observation.images.robot0_agentview_left`
- wrist: `observation.images.robot0_eye_in_hand`.

Required datasets for each selected camera `cam`:
- `latents/{cam}`: fp16 `[N,48,16,16]`
- `indices/latent_source_frame_indices/{cam}`: integer `[N]`
- `valid/{cam}`: bool `[N]`, all entries true for an accepted episode.

The right camera is not B1 evidence authority because Stage A is frozen to `camera_set="left_wrist"`.

The reader API must not accept arbitrary caller-selected camera keys in the production path.
## 2. Exact endpoint-vector contract

Let `F = frame_count`.

Canonical endpoint vector:
1. start with `0,4,8,... < F`;
2. if the last endpoint is not `F-1`, append terminal endpoint `F-1`.

Equivalent construction:

```text
E = list(range(0, F, 4))
if E[-1] != F - 1:
    E.append(F - 1)
```

Examples:
- F=313 -> `...,304,308,312`
- F=299 -> `...,292,296,298`
- F=280 -> `...,272,276,279`.

Both selected cameras must have endpoint arrays exactly equal to this vector and therefore exactly equal to each other.

Causal lookup remains:
`selected_endpoint(s) = max {e in E | e <= s}`.

The terminal irregular endpoint does not authorize nearest/ceil lookup. No selected endpoint may exceed the requested source step.

Standalone lookup may assume an already validated strictly increasing endpoint tuple; full 4-grid-plus-terminal validation belongs to the episode reader.

## 3. Canonical left+wrist visual96 fusion

For a selected causal endpoint, load:
- `z_left`: fp16 `[48,16,16]`
- `z_wrist`: fp16 `[48,16,16]`.

Convert both to fp32 and concatenate on latent width:

```text
z_lw = cat([z_left, z_wrist], dim=-1)   # [48,16,32]
mu   = mean(z_lw, H, W)                 # 48
rms  = sqrt(mean(z_lw^2, H, W) + 1e-6) # 48
visual96 = concat(mu, rms)               # 96
```

Rules:
- parameter-free;
- fp32 accumulation/output;
- finite-only;
- no learned projection/PCA/CNN;
- no temporal interpolation or averaging;
- no right-camera contribution.

This preserves the 96D B0 ABI while matching the two visual views consumed by the Stage A policy.
## 4. Producer causality remains unchanged

For consumer step `t`:
- t=0: no previous evidence;
- t>0: `evidence_source_step=t-1`;
- previous visual96 uses the left+wrist summaries at `max(E <= t-1)`;
- previous executed action is exact **V3-loader converted raw15[t-1]**, not H5 `robot/action`.

The real H5 `robot/action` is native 12D and is not an allowed source for B1 executed-action evidence. Shape validation must continue rejecting it.

Current consumer visual summary may use `max(E <= t)`; it never replaces previous-evidence authority.

Policy chunk remains 32 / consumer 33 frames. TTT T remains 16 consecutive consumers.

## 5. Remediation implementation scope

Modify only the existing B1 files unless tests require a narrow import/type adjustment:
- `robocasa_latent_evidence.py`
- `robocasa_latent_evidence_test.py`
- `robocasa_segment_producer.py`
- `robocasa_segment_producer_test.py`.

B0 three files remain unchanged.
No V2 cherry-pick.
No trainer/config/optimizer/checkpoint/server/eval/GPU changes.

The production reader should bind the canonical left+wrist H5 schema directly. A general-purpose arbitrary-camera reader is out of scope for B1.
## 6. CPU/static acceptance additions

In addition to all v0.1/B0 tests, directly prove:

1. real-schema fixture uses root `frame_count`, not `source_video_frames`;
2. exact endpoint vectors for aligned and terminal-appended examples (at least F=313,299,280);
3. causal lookup around the terminal irregular endpoint never selects future;
4. left and wrist endpoint mismatch rejects;
5. either selected view having invalid mask=false rejects;
6. selected latent wrong shape/dtype/nonfinite rejects;
7. exact left+wrist fused mean/RMS formula yields fp32 [96];
8. modifying right-camera cache does not change B1 visual96;
9. changing a future left/wrist endpoint does not alter earlier visual96;
10. arbitrary camera-key choice is no longer an accepted production control surface;
11. H5 native 12D action cannot enter producer raw15;
12. B0 32 tests remain PASS.

## 7. Real-data evidence required for closure

ds must rerun on the fresh remediation pair using >=3 tasks and >=2 episodes/task.

For each sampled episode record:
- H5 path and episode_id;
- frame_count;
- left/wrist latent shapes/dtypes;
- endpoint head/tail and terminal rule;
- selected valid masks;
- loader-produced raw15 shape/source;
- segment cases: episode start, interior, compression boundary, terminal remainder;
- consumer_step, evidence_source_step, selected endpoint, action source step, masks and output shapes.

Hard fail on:
- future endpoint;
- left/wrist endpoint mismatch;
- invalid selected latent;
- cache/loader episode or length mismatch;
- raw15 not 15D or not loader-derived;
- any policy chunk/T16 reinterpretation.

Passing v0.2 still does not authorize cached latent as policy input or training integration.

