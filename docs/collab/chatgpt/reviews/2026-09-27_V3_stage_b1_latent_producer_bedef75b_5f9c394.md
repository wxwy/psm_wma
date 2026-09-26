# V3 Stage B1-Latent Producer fresh review

- Date: 2026-09-27
- Gate: `V3-STAGE-B1-LATENT-PRODUCER`
- formal root: `bedef75b6bc76cb167f2e27aeaecfe303865f9ab`
- formal child/Gitlink: `5f9c39464761665843b0f08c5e1d578f72114b33`
- design authority reviewed: `f0d020dd8c06ab734bd6d8b8d915c937fd57b94a`
- verdict: `REQUEST_CHANGES`

## Review basis

Fresh review was performed against the exact pair, not cx's report. Child diff from B0 contains only four new B1 files; B0 production files are unchanged. Independent CPU rerun on the exact child: **98/98 PASS in 6.83s**.

The synthetic CPU behavior is internally coherent, but real RoboCasa cache inspection exposes production-contract mismatches that synthetic fixtures do not represent.

## HIGH-1 — real H5 frame-count ABI is wrong

**Location:** `cosmos_framework/model/generator/mot/robocasa_latent_evidence.py:70-78`

The reader requires metadata attr `source_video_frames`. The real cache root attrs use **`frame_count`**, and do not contain `source_video_frames`. A real episode therefore fails with KeyError before any producer segment can be materialized.

Observed real-cache root attrs include:
- `episode_id`
- `frame_count`
- `temporal_compression_factor=4`
- `source_frame_to_latent_policy=causal_endpoint`.

**Acceptance fix:** bind to the actual cache ABI (`frame_count`) and add fixtures matching the physical H5 schema. Do not silently alias arbitrary metadata names.

## HIGH-2 — legal terminal endpoint is rejected

**Location:** `robocasa_latent_evidence.py:16-24,96-98`

Current code requires every endpoint to equal `index*4` and requires the full vector to equal `range(0,F,4)`. Real cache generation appends terminal `F-1` when it is not already on the 4-frame grid.

Examples observed:
- F=299: tail `...,292,296,298`
- F=319: tail `...,312,316,318`
- F=280: tail `...,272,276,279`.

Independent audit across 100 sampled H5 episodes matched exactly:
`0,4,8,...` plus terminal `F-1` iff not already present.

Current reader rejects these valid episodes even though causal selection for B1 remains `max(endpoint <= source_step)`.

**Acceptance fix:** freeze and validate the actual endpoint vector; standalone causal lookup must accept the legal terminal endpoint while still requiring strict monotonicity and never selecting future frames. Add boundary fixtures for aligned and non-aligned terminal frames.
## HIGH-3 — camera authority is not frozen

**Location:** `robocasa_latent_evidence.py:49-57,89-102`

The real cache contains three independent camera latent datasets:
- `observation.images.robot0_agentview_left`
- `observation.images.robot0_agentview_right`
- `observation.images.robot0_eye_in_hand`.

The current reader accepts an arbitrary caller-provided `latent_key` and therefore allows the same episode to produce different visual96 evidence without changing any frozen experiment identity.

Stage A's formal policy observation contract is **`camera_set="left_wrist"`**: `agentview_left + eye_in_hand`. Stage B1 must not let callers choose right/left/wrist ad hoc.

**Acceptance fix:** freeze B1 visual authority to the same `left_wrist` camera set. Read exactly left + wrist latent/endpoints/valid masks; require the two endpoint arrays to be identical and selected validity true. Ignore right camera for this Gate.

To retain visual96 with zero new trainable state, fuse the two selected `[48,16,16]` endpoint latents at latent-statistic level: concatenate left+wrist on latent width to `[48,16,32]`, then compute channel mean48 + RMS48 in fp32.

## Non-blocking findings

- `raw15` cannot be accidentally sourced from H5 `robot/action` because the real H5 action is 12D and the producer rejects non-15D input. Real ds evidence must nevertheless show that the supplied raw15 comes from the V3 loader/conversion path.
- Policy chunk=32 / 33-frame consumer geometry and TTT T=16 remain correctly separated.
- B0 SegmentBatch causality `evidence_source_step=t-1` is preserved.
- No main-policy cached-latent wiring, trainer wiring, GPU or VAE fallback was introduced.

## Verdict

`REQUEST_CHANGES`

All three HIGH findings are production blockers for the real-cache Gate. The synthetic 98/98 PASS result does not close them.

This verdict is limited to Stage B1-Latent Producer and does not alter the already-closed Stage A or B0 CPU core conclusions.

