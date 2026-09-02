# R09-B2 P4-v4 Execution-Preflight v0.3 design review

## Request / design

- Request commit: `17a8454835f45194541e02e25021660ff79615c9`
- Design commit: `d03b8ddea378a3b9ade0ad37180f64440b2463a7`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Upstream P4 provenance design: `f362b824735807278b74ccc553fc8f556598a8d2`
- Upstream P4 static implementation: `3d990e6fb65c192f12e3c2b58ae49356d3eba1e7`
- Upstream ChatGPT review: `4088920d96bfb63cb64e06fe4315e74f7fbe67aa`
- P5 evidence-authority implementation / closure: `3e3a853c61dd32888932041e6afbfac466818e09` / `507a343154cb14239f25480927827a5fb05c9c30`

## Verdict

`REQUEST_CHANGES`

`APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_STATIC_TOOLS` is not authorized.

## Findings

### HIGH — candidate byte grammar is still incompatible with the final P5 evidence grammar

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_preflight_design_v0.3_2026-09-02.md:13-16` requires `attempt_id` and `run_token` to appear in every PASS candidate file and assigns the candidate files `schema_version="r09_b2_p4_v4_candidate_v1"`. `:22-24` then says record/refreeze will submit the three P4 JSON files to the fixed P5 evidence paths.

The already-closed P5 consumer is fail-closed on the P4-v4 request/result/verification exact top-level key sets. Its request schema does not admit top-level `attempt_id` or `run_token`; `run_token` is already bound inside `p4_run`. The result and verification schemas likewise do not admit arbitrary candidate-only fields. Therefore there is no currently defined byte-preserving path from the proposed PASS candidate files to the final six authorized evidence blobs.

Two bad outcomes are possible:

1. record/refreeze copies the PASS files verbatim: P5 rejects the extra candidate metadata / incompatible schema;
2. record/refreeze strips or rewrites candidate fields: the candidate request/result/verification SHA chain no longer binds the exact bytes later committed and frozen by `AUTHORIZED_P4_V4_EVIDENCE`.

Required fix: freeze one deterministic byte contract. Preferably, the PASS candidate's three P4 evidence files are already **byte-for-byte final P5-consumable request/result/verification files**; attempt identity lives in the candidate directory plus verifier-owned linkage to the existing nested `p4_run.run_token`, not as new top-level evidence fields. Record/refreeze must publish those exact bytes without reserialization. If a wrapper design is preferred instead, define exact wrapper key sets plus an exact embedded final-evidence payload and prove that record/refreeze publishes the embedded payload bytes unchanged, with both candidate verification and final authority binding those same bytes.

Add permanent CPU negatives for extra candidate-only top-level keys and for any record/refreeze transformation that changes even one byte of the final request/result/verification payload.

### MEDIUM — two-backend publication atomicity is not frozen

The final P5 authority freezes six blobs in one exact evidence commit, but `docs/build/PSM-WMA_R09_B2_P4_v4_execution_preflight_design_v0.3_2026-09-02.md:13-24` specifies only a single-backend candidate state machine. It does not state the exact pair-level admission rule for selecting recurrent + `ttt_fast_weight` PASS candidates or require all six files to be published in one atomic evidence commit.

Required fix: record/refreeze must consume the exact backend set `["recurrent","ttt_fast_weight"]`, require one canonical PASS candidate per backend, independently revalidate both, enforce the intended shared-source/cross-backend invariants, and publish all six fixed files in one commit-or-none operation. A FAIL/missing backend must prohibit partial evidence publication and authority freezing.

## Positive observations

- The previously invalid P4 provenance anchor is corrected: `f362b824...`, `3d990e6...`, and `4088920...` are all real and mutually consistent with the frozen Gitlink.
- The P5 evidence-authority prerequisite is now actually closed by `3e3a853...` / `507a343...`.
- Post-commit publication identity is now non-circular: the P4 files do not self-report their containing commit; a later reviewed P5 verifier revision freezes the exact commit/tree/Gitlink/six blob digests out-of-band.
- One-shot failure poison/no cleanup/no retry semantics are preserved and materially improved over v0.2.
- Scope remains design/static tooling only; no runtime execution is authorized.

## Gate decision

Revise the candidate-to-final byte grammar and pair-level publication contract, then resubmit the P4-v4 preflight static design. Until then, no P4-v4 tooling implementation, staging, candidate execution, record/refreeze, evidence publication, P5 export/compose, GPU, training, evaluation, inference, B2-T, or Local Memory training is authorized.
