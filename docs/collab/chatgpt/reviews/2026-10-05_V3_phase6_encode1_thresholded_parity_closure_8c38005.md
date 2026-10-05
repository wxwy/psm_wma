# V3 Corrected Phase6 Encode1 thresholded parity closure — GPT review

- 日期：2026-10-05
- Gate：`PHASE6-ENCODE1-THRESHOLDED-PARITY`
- production root before closure：`3f0d5e20a29922b40054c7d348eaba77675531f2`
- production child/Gitlink（unchanged）：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- Phase6A scratch authority：`8c3800565f66cfbce2929264f1c2a7854137482e`
- threshold-freeze review commit：`b6c42088ae41904c0667d1066983c2829ae61c36`
- threshold-freeze review：`docs/collab/chatgpt/reviews/2026-10-05_V3_phase6_encode1_observational_threshold_freeze_8c38005.md`
- final ds Evidence root：`/tmp/psm_wma_v3_phase6_encode1_ds_evidence_r3/`

## Verdict

`PHASE6_ENCODE1_THRESHOLDED_PARITY_CLOSED`

`APPROVE_TO_RUN_PHASE6_NO_POLICY_ONLINE_LOCAL_REAL_SMOKE_ONLY`

`PHASE6_POLICY_SERVER_GPU_SIM_NOT_AUTHORIZED`

`PRODUCTION_PROMOTION_STILL_BLOCKED_BY_PHASE3P5_THRESHOLDED_REAL_PARITY`

本 verdict 关闭 Phase6 的 bounded Encode1 numerical parity Gate。只授权下一步 Gate 2：real Wan + corrected Online Local core 的 no-policy bounded smoke。不得加载完整 Policy DCP/server，不得运行 simulator/SR，不得提升 production child/Gitlink。

## Frozen threshold

观测后冻结的验收标准：

- exact_equal 必须为 true
- max_abs <= 0.0
- mean_abs = 0.0
- RMSE = 0.0
- all tensors finite
- exact frozen geometry / shared preprocessing identity
- exact scratch/probe/review/child authority

该阈值不是事先假定，而是在 r1 observational exact equality 后冻结，并由 fresh r3 重跑验证。

## Final Evidence

Authority:
- corrected pairlock SHA256：`db2e52d2ead4281760caeaf08478045db8344d5a643833f45c55d34c3ec193fc`
- fixed probe SHA256：`a07e7fd1cbc96d855785708e0e9c6ecc7ec89240f0fae045ed9bbd34942a3fcb`
- scratch：`8c3800565f66cfbce2929264f1c2a7854137482e`
- review commit：`b6c42088ae41904c0667d1066983c2829ae61c36`
- current V3 bookkeeping head at run：`3f0d5e20a29922b40054c7d348eaba77675531f2`
- production child/Gitlink：`b673ceda5a9ff058abb31224b7006f2d87771ad2`

Fresh observational rerun:
- C0 SHA256：`dce68c34b82167a00ded963268f491d5ae0a62e0ec44391280ec7c1aaaddad90`
- CloseFridge / episode 26 / starts 0,128,257
- probe threshold=None / self-declared pass=None
- shared preprocessing exact
- A=cache Z_t[0], B=independent Encode1, C=repeated-current Policy first latent
- padded z0 / native post-crop z0 / visual96 的 A/B、B/C、A/C 全部 exact_equal=true，max_abs=mean_abs=RMSE=0

Independent numerical validator:
- validator SHA256：`6c615a93027684a78d1eef2d8358cda8e0a4f321edaac92b9dc2c852fb2e9a01`
- D1 SHA256：`7e0f8b0df7075309c1ea4c6af0582904c7ffbc4704ebc7c500311d68f74ad571`
- status=PASS
- threshold=0.0
- exact_required=true
- checks_total=435
- checks_failed=0

Final authority validator:
- finalizer SHA256：`fe492501f546444e0d8a0a469b5fe857504d517d883527a17f91ac5f51391356`
- E1 SHA256：`af80778d7937e86abd867b4ca5a332da4644cf35bc934d5a8adb6a06eaf278ae`
- status=PASS
- checks_total=33
- checks_failed=0
- independently binds scratch SHA / review commit / current V3 head / child Gitlink / actual probe SHA / D1 PASS

## Next authorized Gate

Only:
`PHASE6-NO-POLICY-ONLINE-LOCAL-REAL-SMOKE`

Required bounded proof:
- use real corrected composite RGB and real Wan Encode1
- use corrected model-owned Local scan with a Local runtime only; no full Policy DCP/generation
- use completed canonical raw15 sequence
- cold S0 has no prefix
- first completed sequence yields finite prefix / fast state / telemetry
- exercise N>T chronological chunking on real evidence
- candidate remains unpublished before commit
- exact replay performs zero Encode1 / zero Local re-adaptation and returns identical prefix/state
- changed same-frontier evidence fails closed
- reset clears session state / replay witness
- bounded memory / no retained causal VAE state

Still prohibited:
- full Policy DCP
- server GPU smoke
- simulator
- 48/128-step soak
- 18-task screening/SR
- production promotion
- formal training

Phase6 parity closure does not close or waive Phase3.5 >=3 task classes / >=9 windows production parity.
