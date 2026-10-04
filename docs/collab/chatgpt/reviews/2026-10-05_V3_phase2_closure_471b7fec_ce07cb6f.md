# V3 Phase 2 raw15/state15 + H_pred16 — GPT closure review

- 日期：2026-10-05
- Gate：V3-CORRECTED-PHASE2-IMPLEMENTATION
- formal root：471b7fec4f50296efb3a328735dc2611b900995f
- formal child/Gitlink：ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0
- design authority：docs/build/PSM-WMA_V3_phase2_raw15_state15_hpred16_design_v1.1_2026-10-05.md
- execution authorization：docs/collab/chatgpt/reviews/2026-10-05_V3_phase2_source_review_r3_471b7fec_ce07cb6f.md
- ds Evidence：/tmp/psm_wma_v3_phase2_ds_evidence_r1/

## Verdict

APPROVE_PHASE2_POLICY_CONTRACT_ONLY

Phase2 正式关闭。

该 verdict 只确认 synthetic/local CPU/static 下：
- official raw12→raw15
- official state16→state15
- [state15;16×raw15] 17-row clean/no-loss semantics
- ActionProcessor pad64/no-normalization
- Corrected H_pred16/obs17/R<=16 contract
- manifest-driven VAE contract + immutable authority
- legacy chunk32/[33] fail-closed

不批准 Phase3+、真实训练资产、GPU、训练、推理、仿真或 SR。

## Independent Evidence

A. exact pair/scope:
- formal root object exists
- formal gitlink = ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0
- child HEAD/origin = same
- child relative Phase1B parent 21e60d6e... scope exactly 2 Phase2 files

B. target pytest:
- Phase1A + Phase1B + Phase2
- 137 passed in 80.87s
- 0 failed/error

C. static:
- Ruff check PASS
- Ruff format --check PASS
- formal diff --check PASS
- repeated scope identical

D. immutable-authority independent probe:
- constructed manifest authority:
  compute_dtype=bfloat16
  exact=[17,61]
  chunk={256:68}
- public copy deliberately mutated to:
  compute_dtype=float32
  exact=[33]
  chunk={480:24}
- resolved runtime remains:
  exact=[17,61]
  chunk[256]=68
- validate resolved PASS
- validate exact=[33] => ValueError
- PROBE_RESULT=PASS

Evidence-bound Phase2 SHA256:
- policy module: a2236e0c96fa9cbdac372bd2ebaa92f4c1d5db98f4432942f21968a163bdde45
- policy tests: 9308ed2a6801468d2d0b319a8315a8fa261eea56c029123d2a8b7b603a51d227

Phase1A/1B tested parent hashes match prior closure Evidence.

## Frozen Phase2 result

1. Phase1B raw source window is converted by official RoboCasa private action/state helpers; no copied rotation implementation.
2. source raw12 layout and simulator env12 layout remain explicitly distinct.
3. policy action target is raw15:
   base_motion4 + control_mode1 + eef_pos3 + official rot6d6 + gripper1.
4. state token is state15:
   zeros5 + official current EEF state10.
5. action stream is exact [17,15]:
   row0=current state15; rows1..16=raw15 actions.
6. official WAM Case-B marks row0 clean; packer excludes it from noisy/mse indexes; flow loss excludes it.
7. max_action_dim64 padding preserves first15 channels and zero-fills tail; action_normalization=None.
8. all new Corrected V3 modules default H_pred/chunk=16, obs frames17; R contract 1..16, default16.
9. VAE exact-duration list comes from the full cache manifest, not guessed legacy defaults.
10. fixed Edge tokenizer is capability authority; caller runtime tokenizer non-contract fields are preserved.
11. manifest VAE authority is protected by immutable runtime snapshot; later public nested mutations cannot alter resolver/validator behavior.
12. old Nano/Edge/H100 chunk32/[33] route remains legacy/incompatible and is not silently turned into Corrected training.

## Explicit remaining boundary

Phase2 does NOT prove or implement:
- cache latent transport through ActionSFT pipeline
- cached-latent model consumption / OmniMoT cache-hit
- Policy + Local current-z_t sharing in the corrected training sample
- Local visual96 V2 pooling
- grouped B_stream/T/GA refactor
- Local inner/outer training path on corrected cached sample
- checkpoint/resume after corrected integration
- online inference/server/eval
- real training-server cache/source parity
- GPU/training/simulation/behavior

## Next allowed phase

Phase3 only:
cache-driven ActionSFT-compatible sample + video_latent transport + minimal OmniMoT training cache-hit seam.

Phase3 requires a new GPT design authority before cx production edits.
