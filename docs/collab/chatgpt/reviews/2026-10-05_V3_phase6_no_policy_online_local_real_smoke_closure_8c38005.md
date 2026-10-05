# V3 Corrected Phase6 no-policy online Local real smoke closure — GPT review

- 日期：2026-10-05
- Gate：`PHASE6-NO-POLICY-ONLINE-LOCAL-REAL-SMOKE`
- production root before closure：`36d6a4198fa40947c399fc952d807d831f0358c3`
- production child/Gitlink（unchanged）：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- Phase6A scratch authority：`8c3800565f66cfbce2929264f1c2a7854137482e`
- parent Gate：`PHASE6-ENCODE1-THRESHOLDED-PARITY` CLOSED
- final clean Evidence root：`/tmp/psm_wma_v3_phase6_no_policy_online_local_ds_evidence_r2/`
- bounded task witness：CloseFridge / episode 26 / source steps 0..19

## Verdict

`PHASE6_NO_POLICY_ONLINE_LOCAL_REAL_SMOKE_CLOSED`

`PHASE6_FULL_POLICY_SERVER_GPU_SIM_NOT_AUTHORIZED`

`PRODUCTION_PROMOTION_STILL_BLOCKED_BY_PHASE3P5_THRESHOLDED_REAL_PARITY`

本 verdict 关闭的是 real Wan Encode1 + corrected Online Local runtime 的 no-policy bounded smoke。未加载完整 Policy DCP，未启动 HTTP server、simulator、SR 或训练；production child/Gitlink 未改变。

## Evidence

Final fresh r2 rerun:
- process exit code: 0
- smoke_gate_pass=true
- 24 / 24 behavioral checks PASS
- real Wan VAE + corrected composite RGB
- Local runtime geometry: evidence256 / local32 / ttt64 / fast_hidden256 / T16 / K4 / raw15
- peak allocated GPU memory ≈2698.4 MiB
- peak reserved GPU memory ≈2802.0 MiB

Completed-action / action-authority witnesses:
- canonical raw15 re-decodes to the exact submitted env12 within frozen decoder tolerance
- source action row matches dataset env12 witness
- composite PNG wire round-trip is bit-exact
- source steps are contiguous 0..19

Online Local transaction:
- cold S0: no prefix, no fast state, zero Encode1, zero scan
- 20 completed real evidence rows produce finite K4x32 prefix and finite fp32 fast state
- N>T path performs exactly two model-owned scans: T16 from fresh W0, then T4 with continuation state
- candidate state/frontier remains unpublished before commit
- commit advances live frontier from 0 to 20
- Local slow parameters are bit-exact unchanged

Replay / fail-closed / reset:
- exact lost-response replay uses zero Encode1, zero model scan and zero adaptation
- replay returns identical committed prefix/state and does not advance frontier
- same-frontier changed executed_action or composite bytes is rejected before Encode1/scan
- client exact-frontier acknowledgement remains valid after rejected replay mutation
- reset clears Local records/pending state and visual replay witness
- next session/episode returns to cold lazy state

Wan state boundedness:
- tokenizer use_streaming_encode=false
- keep_encoder_cache=false
- keep_decoder_cache=false
- actual causal host is WanVAE_
- encoder cache before/after: 26 slots, all None
- encoder stream shape before/after: None
- decoder cache before/after: 34 slots, all None
- encode_streaming calls=0
- decoder decode calls=0
- causal cache snapshot before/after is unchanged

## Probe provenance note

The first r1 execution exposed an Evidence-probe-only S24 issue. That directory was later reused, so its stdout/runclock and regenerated JSON did not form one clean provenance chain. The repository/scratch implementation was not changed.

GPT therefore required a fresh r2 directory. r2 used the corrected probe and produced one clean run with exit code 0 and all 24 checks PASS. The r1 mixed directory is retained only as historical diagnostic evidence and is not the closure authority.

## Scope / next Gate

CLOSED:
- Phase6A CPU/static scratch
- Phase6 Encode1 thresholded numerical parity
- Phase6 no-policy real Online Local smoke

Still blocked / unauthorized:
- full Policy DCP loading
- HTTP server GPU smoke
- simulator 48/128-step
- 18-task SR screening
- production child/Gitlink promotion
- formal training

The next production prerequisite remains the independent Phase3.5 thresholded parity Gate (>=3 task classes / >=9 exact windows), unless the Owner explicitly refreezes/waives that requirement. This Phase6 no-policy closure does not waive Phase3.5.
