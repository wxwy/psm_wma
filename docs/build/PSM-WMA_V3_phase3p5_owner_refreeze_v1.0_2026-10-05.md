# PSM-WMA V3 Corrected — Phase3.5 Owner Refreeze v1.0

日期：2026-10-05  
Authority：Owner explicit decision in chat, recorded by GPT reviewer.

## Decision

The previously frozen Phase3.5 final production thresholded parity requirement:

- at least 3 distinct underlying RoboCasa task classes;
- at least 9 exact windows total;

is **refrozen** as follows:

1. It is **no longer a blocker for production promotion** of the already reviewed Corrected V3 Phase4/5/6 candidate.
2. It is **deferred to a pre-formal-training supplemental evidence Gate**.
3. This decision does **not** invalidate the original Phase3.5 design or historical evidence; it changes only the sequencing / blocking role of the 3-task coverage clause.

## Evidence accepted in place of the old promotion blocker

The Owner accepts the following combined evidence as sufficient to unblock production promotion:

### A. Exact-window real Wan parity on current strict snapshot

- strict CloseFridge exact-window cache/source binding;
- current Wan2.2 full encode;
- starts 0 / 128 / 257;
- offline cache vs online exact-window encode:
  - exact equality;
  - global max_abs = 0.0.

### B. Phase6 Encode1 three-way parity

For the same real pixels:

- A = cache exact-window current latent Z_t[0];
- B = independent single-frame Encode1(current composite);
- C = repeated-current Policy visual tokenizer first latent.

Across selected real windows:

- padded z0: A/B, B/C, A/C exact;
- native post-crop z0: exact;
- visual96: exact;
- max_abs = mean_abs = RMSE = 0;
- frozen exact threshold revalidated and CLOSED.

### C. Real no-policy Online Local smoke

Fresh clean r2:

- real composite RGB;
- real Wan Encode1;
- real canonical completed raw15 evidence;
- 20 chronological steps;
- model-owned Local scan;
- N>T path exactly 16 + 4;
- candidate unpublished before commit;
- exact replay performs 0 Encode1 / 0 scan / 0 re-adaptation;
- changed same-frontier evidence fails closed;
- reset/session isolation passes;
- Local slow parameters bit-exact unchanged;
- no retained Wan causal state;
- 24/24 checks PASS.

## Promotion consequence

The production promotion blocker:

`PRODUCTION_PROMOTION_STILL_BLOCKED_BY_PHASE3P5_THRESHOLDED_REAL_PARITY`

is superseded for the current reviewed candidate by:

`PHASE3P5_3TASK_COVERAGE_DEFERRED_TO_PRE_FORMAL_TRAINING`

and:

`PRODUCTION_PROMOTION_UNBLOCKED_FOR_EXACT_REVIEWED_CANDIDATE`

The exact candidate source authorized for promotion preparation is:

`8c3800565f66cfbce2929264f1c2a7854137482e`

Remote candidate ref:

`wxwy/cosmos-framework:v3-corrected-promotion-candidate-20261005`

The candidate must remain byte/tree-identical to that SHA.

## What remains gated

This refreeze does **not** authorize:

- skipping fresh production-pair review after Gitlink changes;
- bypassing production promotion review;
- directly starting formal long training;
- claiming 18-task SR;
- deleting the deferred 3-task parity obligation.

After production promotion is reviewed and closed, GPU readiness must still proceed through bounded readiness gates before formal training.

Before formal training, the deferred supplemental parity must be satisfied unless the Owner issues another explicit refreeze.
