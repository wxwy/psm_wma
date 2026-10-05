# V3 Corrected Phase6 Encode1 observational parity — threshold freeze review

- 日期：2026-10-05
- Gate：`PHASE6-ENCODE1-OBSERVATIONAL-PARITY`
- production root before threshold freeze：`6c273fd45696ba1cd3b368b50963796a328903c8`
- production child/Gitlink（unchanged）：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- Phase6A scratch authority：`8c3800565f66cfbce2929264f1c2a7854137482e`
- Phase6 design：`docs/build/PSM-WMA_V3_phase6_online_inference_eval_design_v1.1_2026-10-05.md`
- ds Evidence：`/tmp/psm_wma_v3_phase6_encode1_ds_evidence_r1/`
- fixed probe SHA256：`a07e7fd1cbc96d855785708e0e9c6ecc7ec89240f0fae045ed9bbd34942a3fcb`

## Verdict

`ACCEPT_PHASE6_ENCODE1_OBSERVATIONAL_PARITY_FOR_THRESHOLD_FREEZE`

`PHASE6_ENCODE1_THRESHOLD_FROZEN_MAX_ABS_0_0_AND_EXACT_EQUAL`

`APPROVE_TO_RUN_PHASE6_ENCODE1_THRESHOLDED_VALIDATION_ONLY`

`PHASE6_SERVER_GPU_SIM_NOT_AUTHORIZED`

`PHASE3P5_PRODUCTION_THRESHOLDED_PARITY_REMAINS_OPEN`

## Evidence reviewed

Frozen bounded witness:
- strict cache: `target_atomic_closefridge_left_wrist_snapshot10`
- task: CloseFridge
- episode: 26
- starts: 0 / 128 / 257
- source: matching flat LeRobot v3
- VAE: local Wan2.2 VAE
- image_size: 256
- device: cuda:0
- video backend: pyav
- threshold in observational run: none
- self-declared pass: none

Three-way definition:
- A = cache exact-window actual `Z_t[0]`
- B = corrected independent single-frame Encode1(current composite)
- C = repeated-current Policy visual tokenizer encode first latent

For every selected window:
- shared single-frame preprocessing vs episode-level Phase3.5 preprocessing slice: exact_equal=true, max_abs=0
- padded z0: A/B, B/C, A/C all exact_equal=true, max_abs=0, mean_abs=0, RMSE=0
- native post-crop z0: all three pairwise exact_equal=true, max_abs=0, mean_abs=0, RMSE=0
- visual96: all three pairwise exact_equal=true, max_abs=0, mean_abs=0, RMSE=0
- Phase4 visual96 helper/formula witnesses: exact_equal=true, max_abs=0
- all compared tensors finite fp32 with expected geometry

The first ds attempt failed only inside the temporary probe's crop guard (wrong ndim check); raw failure evidence was preserved. The fixed second attempt changed only that probe guard, did not modify repository/cache/source, returned RC=0, and produced the reviewed JSON.

## Frozen numerical acceptance contract

Because the observational run measured exact equality on all frozen pairwise witnesses, the next bounded validation threshold is frozen as:

- require `exact_equal == true`
- require `max_abs <= 0.0`
- therefore mean_abs and RMSE must also be 0
- require finite tensors and exact expected geometry
- require identical selection/task/episode/starts, scratch SHA and probe SHA
- require shared preprocessing identity to remain exact

This threshold is frozen **after** observational measurement and must be tested on a fresh rerun; the observational JSON itself is not retroactively promoted to thresholded PASS.

## Next authorized execution

ds may create a fresh evidence root and rerun the same fixed probe on the same bounded witness. After the probe writes its observational JSON, a separate validator may mark PASS only if all frozen conditions above hold.

No repository production code changes are authorized for this validation.

Still prohibited:
- Policy DCP/server GPU smoke
- simulator
- 48/128-step soak
- 18-task screening/SR
- production child/Gitlink promotion
- formal training

This Phase6 bounded parity Gate is independent from Phase3.5 production parity and does not satisfy its >=3 task classes / >=9 exact windows requirement.
