# V3 Stage B1-Latent Producer closure review

- Date: 2026-09-27
- Gate: `V3-STAGE-B1-LATENT-PRODUCER`
- formal implementation root: `93db96df841a14c4c3ef73bf6b4488142adcf567`
- formal child/Gitlink: `1ecebf1ab2fa64bc1d5906959c4cb1fe1d1edc5a`
- design authority: `65271367978537c5d7b5bae5fa50b1ee8056f356`
- predecessor rejected pair: `bedef75b6bc76cb167f2e27aeaecfe303865f9ab / 5f9c39464761665843b0f08c5e1d578f72114b33`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B1_LATENT_PRODUCER`

## Fresh-review basis

This is a fresh review of the new formal pair. Root diff from the v0.2 design authority contains only the child Gitlink update plus the B1 remediation record. Child diff from the rejected pair modifies only the four authorized B1 files:
- `robocasa_latent_evidence.py`
- `robocasa_latent_evidence_test.py`
- `robocasa_segment_producer.py`
- `robocasa_segment_producer_test.py`.

B0 production files remain unchanged.

Independent exact-pair CPU rerun:
- **132/132 PASS**
- zero skips
- runtime 7.25 s.

## Previous blockers

### HIGH-1 — real H5 frame-count ABI: CLOSED

Rejected implementation read nonexistent `source_video_frames`.

Current reader binds the real cache root `frame_count` attr and preserves exact cache/loader frame-count equality. ds production-API evidence constructed the reader successfully for 9/9 real H5 episodes across CloseFridge, NavigateKitchen and OpenDrawer.

### HIGH-2 — terminal endpoint contract: CLOSED

Current reader builds the exact frozen endpoint vector:
`range(0,F,4)` plus `F-1` when needed.

Standalone causal lookup now requires strict monotonicity rather than an invalid pure-4-grid assumption. Real evidence covers aligned and terminal-appended episodes, including tails such as `[248,252,256,257]`, `[120,124,128,129]` and `[324,328,332,333]`.

Across all sampled producer rows:
- future endpoint violations: **0**
- `evidence_source_step != consumer_step-1`: **0**
- S0 with evidence: **0**
- PAD contamination: **0**.

### HIGH-3 — camera authority: CLOSED

Reader production API no longer accepts caller-selected camera keys. It binds exactly Stage-A `left_wrist`:
- `observation.images.robot0_agentview_left`
- `observation.images.robot0_eye_in_hand`.

Both endpoint arrays must exactly match the canonical vector and each selected-camera valid mask must be bool/all-true. The right camera is outside B1 evidence authority.

Selected left+wrist latents are converted to fp32, concatenated on latent width `[48,16,32]`, then summarized by mean48 + RMS48 into visual96. ds independently recomputed this formula on real cache data; production output matched within atol 1e-5 and differed materially from left-only summaries, proving both selected views participate.
## Raw15 / producer contract

The producer still requires CPU `[F,15]` finite raw15 and cannot consume H5 `robot/action` because that source is native `[F,12]`.

Real ds evidence built raw15 from the V3 RoboCasa loader with:
- `use_base_action=True`
- `base_encoding="raw"`
- `camera_set="left_wrist"`
- `chunk_length=32`
- `use_state=True`
- `action_normalization=None`.

The loader action rows are 15D; H5 action rows are 12D and numerically/semantically distinct. No H5 12D action path enters B1.

Policy/TTT geometry remains unchanged:
- policy chunk = 32
- consumer observation window = 33 frames
- TTT segment = 16 consecutive consumers
- terminal remainder is tail-PAD only.

## Real-data Evidence

ds validation directly called production `RoboCasaLatentReader` and `RoboCasaSegmentProducer` on **3 tasks × 3 episodes = 9 real episodes**.

Covered per episode:
- episode start
- compression boundary
- interior cursor
- terminal remainder.

Observed hard-fail counts:
- future endpoint: 0
- left/wrist endpoint mismatch: 0
- invalid selected latent: 0
- cache/loader identity mismatch: 0
- cache/loader length mismatch: 0
- raw15 non-15D / non-loader-derived: 0
- policy-chunk/T16 reinterpretation: 0.

Observed output contract:
- `consumer_visual_summary (1,16,96) fp32`
- `evidence_visual_summary_prev (1,16,96) fp32`
- `evidence_executed_action_prev (1,16,15) fp32`
- masks `(1,16) bool`
- source/consumer steps `(1,16) int64`.

The terminal-appended cache endpoint itself is not selected by valid policy consumers in the sampled episodes, but it is correctly retained and validated in cache identity.

## Scope boundary

`APPROVE_TO_CLOSE_V3_STAGE_B1_LATENT_PRODUCER`

This closes only:
`real RoboCasa cached RGB latent -> causal left+wrist visual96 -> B0 SegmentBatch`.

It does **not** authorize:
- cached latent as the main Cosmos policy input;
- trainer/grouped-driver integration;
- production outer backward;
- checkpoint/resume;
- GPU training/evaluation;
- task-performance or SR claims;
- any later Stage B Gate.

