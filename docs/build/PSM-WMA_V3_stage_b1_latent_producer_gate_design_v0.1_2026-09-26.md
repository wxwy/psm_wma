# PSM-WMA V3 Stage B1-Latent Producer Gate Design v0.1

- Date: 2026-09-26
- Gate: `V3-STAGE-B1-LATENT-PRODUCER`
- Owner: user; design/review: ChatGPT; implementation: cx; execution/data/evidence: ds.
- Baseline formal pair: root `ddca6b239697ac83a9c09157de060dbe9e91ac59` / child `4fa4f35c102433bb007d2a3fd4a9fc7fe0b5149f`.
- Status: DESIGN_FROZEN_FOR_IMPLEMENTATION.
- This Gate does not authorize training, GPU model execution, policy cached-latent input, or Local-TTT trainer wiring.

## 1. Goal and scope

Stage B1 only bridges the existing RoboCasa RGB Wan2.2 latent cache into the already frozen B0 Local-TTT evidence ABI.

Frozen B0 remains unchanged:
- `visual96 + executed_action15 -> evidence256`;
- `T=16, K_local=4, local_dim=32, ttt_dim=64, fast_hidden=256, inner_lr=0.1`;
- S0 has no evidence; for consumer `t>0`, evidence source step is exactly `t-1`;
- policy remains chunk=32 with 33-frame consumer contract;
- main Cosmos policy forward continues Stage-A native RGB -> online VAE path.

B1 must not route cached latent into the main policy forward.
## 2. Cache contract

Expected episode cache authority:
- one episode per H5;
- visual latent shape `[N,48,16,16]`, fp16;
- temporal compression factor 4;
- endpoint source frame indices `0,4,8,...`;
- `source_frame_to_latent_policy = causal_endpoint`.

Reader must fail closed on missing/wrong metadata, non-finite latent, wrong dtype/shape, non-monotone endpoint indices, endpoint outside episode frame range, or cache/episode identity mismatch.

Do not silently recompute VAE online in this Gate. A missing/invalid cache is an error, not fallback.

## 3. Strict causal mapping

For consumer step `t`:
- `t=0`: no memory evidence, exactly as B0.
- `t>0`: B0 evidence source step is `s=t-1`.
- choose the latest cached visual endpoint not later than `s`:
  `latent_endpoint(s) = max {e in endpoint_indices | e <= s}`.

For the frozen `0,4,8,...` cache:
`latent_endpoint(t) = 4 * floor((t-1)/4)` for `t>0`.

Examples:
- consumer 1..4 -> visual endpoint 0;
- consumer 5..8 -> endpoint 4;
- consumer 9..12 -> endpoint 8;
- consumer 13..16 -> endpoint 12.

Nearest, round-to-nearest and ceil mapping are forbidden because they can use future RGB frames.

Executed action remains exact `raw15[t-1]`; it is not temporally snapped to the visual endpoint.
## 4. Frozen latent -> visual96 baseline

Input for one selected endpoint: `z in R^[48,16,16]`.

B1 visual summary is parameter-free:
1. compute channel-wise spatial mean: `mu = mean(z, H,W)` -> 48D;
2. compute channel-wise spatial RMS: `rms = sqrt(mean(z^2,H,W) + eps)` -> 48D;
3. concatenate `visual96 = concat(mu, rms)` -> 96D.

Rules:
- compute accumulation in fp32 even when cache is fp16;
- `eps=1e-6`;
- output is finite fp32 `[96]`;
- no learned projection, random matrix, PCA fit, extra CNN, temporal averaging, interpolation, or future endpoint mixing in B1.

Rationale: producer remains deterministic/auditable and introduces zero new trainable state; B0 already owns the trainable 96->256 visual projection. Alternative spatial/learned pooling is a later ablation, not part of this Gate.

## 5. Episode / slot / cursor producer

Add a RoboCasa cached-latent producer that materializes one B0 `SegmentBatch` per stable slot request.

Identity authority:
- `slot_id`;
- `episode_id`;
- `cursor`;
- `segment_id` / provenance digests.

Segment semantics:
- segment start consumer = `cursor * 16`;
- non-terminal segment has exactly 16 consecutive consumers;
- terminal remainder may contain 1..16 valid consumers and tail PAD only;
- policy chunk stays 32; producer must not reinterpret TTT T=16 as policy horizon;
- `consumer_step` is episode-frame consumer index, not latent index and not policy-chunk index.
For every valid consumer t:
- `consumer_visual_summary[t]` is the visual96 summary of current consumer RGB state if that field is required by the carrier; it must never be used as the previous-evidence authority.
- `evidence_source_step[t]=t-1` for t>0 and -1 for t=0.
- `evidence_visual_summary_prev[t]` uses `latent_endpoint(t-1)` by Section 3.
- `evidence_executed_action_prev[t]=raw15[t-1]` exactly.
- `evidence_valid = consumer_valid & (consumer_step>0)`.
- PAD rows have no payload/evidence and must satisfy existing B0 validation exactly.

Producer may attach immutable diagnostic metadata such as `latent_endpoint_step` to payload/provenance, but must not add a second authority for `evidence_source_step`.

## 6. Minimal child implementation scope

Preferred new child files:
- `cosmos_framework/model/generator/mot/robocasa_latent_evidence.py`
- `cosmos_framework/model/generator/mot/robocasa_latent_evidence_test.py`
- `cosmos_framework/model/generator/mot/robocasa_segment_producer.py`
- `cosmos_framework/model/generator/mot/robocasa_segment_producer_test.py`

Existing B0 production files should remain unchanged unless a tiny import/type-only seam is unavoidable. Any semantic edit to `local_evidence.py`, `local_memory_segment.py`, or `local_memory_segment_adapter.py` requires explicit justification in the implementation record.

Do not cherry-pick the V2 producer patch. V2 may be read only as semantic reference.

## 7. Acceptance evidence

CPU/static tests must directly prove:
- exact endpoint mapping around boundaries: s={0,1,3,4,5,7,8,15,16};
- no selected endpoint > requested source step;
- synthetic future-sensitive cache: changing future latent endpoints leaves earlier visual96 unchanged;
- `[48,16,16] -> [96]` exact formula, fp16 input / fp32 output, finite checks;
- malformed metadata/shape/index ordering/episode mismatch fail closed;
- segment cursor 0/1 and terminal remainder produce exact consecutive consumer steps;
- S0 has no evidence; all t>0 use exact `evidence_source_step=t-1`;
- previous executed action is exact raw15[t-1];
- B0 `SegmentBatch.validate(16)` passes for produced segments;
- policy chunk/horizon is never changed or redefined by producer.

No GPU, no checkpoint, no VAE execution, no trainer, no policy forward in B1 acceptance.

## 8. ds data/evidence gate after implementation

After cx produces a fresh formal pair, ds must validate against real RoboCasa cache samples:
- at least 3 tasks and >=2 episodes/task;
- record cache path, H5 keys/metadata, latent shape/dtype, endpoint prefix/suffix;
- verify source video/action length consistency;
- materialize producer segments at episode start, an interior cursor, a compression boundary, and terminal remainder;
- emit a compact JSON evidence artifact containing consumer_step, evidence_source_step, selected latent endpoint, action source step, masks and shapes.

Any future-frame selection, episode identity mismatch, or source/action length mismatch is a hard failure.

## 9. Gate boundary

Passing B1 means only:
`RoboCasa cached RGB latent -> causal visual96 -> B0 SegmentBatch` is correct.

It does NOT approve:
- cached latent as main Cosmos policy input;
- trainer/grouped-driver integration;
- outer-loss production backward;
- DCP/resume;
- GPU training/eval;
- performance/SR claims.

Next Gate after B1 is producer-to-training integration; cached-latent policy parity remains a separate acceleration Gate.
