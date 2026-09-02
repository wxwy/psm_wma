# ChatGPT independent review — R09-B2 P4-v4 Execution Request `backends` v0.2 design

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_BACKENDS_STATIC_TOOLS`

## Reviewed identities

- design root: `3721e77e1e0b8065f8b757df567f755d02c17e60`
- request / ledger HEAD: `fb50f80ac52f43a52cadfb2b58568c4ab2592263`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- previous ChatGPT blocker review: `94e1988d35f467943e3388ad0ea3a496ce5f2df3`
- design: `docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_backends_design_v0.2_2026-09-02.md`

## Independent findings

The three blockers from v0.1 are closed.

1. **P4 wrapper vs P5 wire schema is now explicit.**
   - `p3_core={artifact_sha256,verifier_sha256,backend_contract}` is the exact three-field P5 v0.9 wire object.
   - P4 `p3_contract` adds only `identity_sha256`, defined as `canonical_sha256(p3_core)`.
   - Validation compares the projected three-field core, not the four-field wrapper, to the frozen snapshot. This removes the impossible whole-object canonical-equality requirement from v0.1.

2. **Optimizer membership is no longer request-self-reported authority.**
   - v0.2 freezes reviewed code constants `P3_CORE_SNAPSHOTS` and `P3_SNAPSHOT_AUTHORITY` and fixes the validator interface to `validate_backends(value: object) -> None`.
   - The validator has no path/root/artifact/request-authority input and no P3/P5 I/O or subprocess path; request values can only be accepted by exact comparison against reviewed constants.
   - Independent re-read of the frozen D005 records confirms the snapshot values:
     - recurrent selector list exactly `moe_gen,time_embedder,vae2llm,llm2vae,action2llm,llm2action,action_modality_embed,local_memory2llm,local_memory_modality_embed,local_history_runtime`
     - recurrent `optimizer_membership_sha256=31f5e455485b2c471c47da2d2c1819214372967ad1c76311e79bfe7865ec15fd`
     - TTT selector list exactly `local_history_runtime.encoder,local_memory2llm,local_memory_modality_embed`
     - TTT `optimizer_membership_sha256=379abd364d8a741adeafca441736c034fc3d93250d5ca8685630d18872867404`
     - P3 artifact SHA `5dd5253cabaa5efa54f3ddc8891f632e3b05e515bf91c8055108e037f69b684d`
     - P3 PASS-verifier artifact SHA `e9700cd63e9626ce88969b2d21682c186af7dfe0c7489f88795de1301d5b64f8`

3. **The authority identity is sufficiently frozen without making unfinished P5 runtime authority.**
   - v0.2 records the historical D005 revision, historical D005 verifier blob SHA, both frozen D005 raw-record SHAs, and the P3 artifact/PASS-verifier SHAs.
   - This satisfies the prior requirement for an exact reviewed snapshot while preserving the existing gate boundary: P5 v0.9 implementation is not executed or trusted as runtime authority here.

## Implementation requirements / closure checklist

Implementation approval is **static-only** and must remain within:

- `tools/g0/r09_b2_p4_v4_execution_preflight.py`
- its stdlib CPU test file

The implementation must materially enforce the frozen v0.2 contract:

- exact outer / record / `p3_contract` / `backend_contract` schemas;
- canonical outer, record and P3-wrapper identities;
- exact two backends and byte-exact backend labels;
- strict lowercase-64-hex grammar;
- exact projection to `p3_core` and exact comparison against the per-backend code snapshot;
- artifact/verifier cross-side equality;
- exact selector order/content/type and membership values;
- swap / third-backend / record-identity reuse rejection;
- ambient independence and no filesystem/subprocess/project execution side effects.

Permanent CPU fixtures must cover the design's stated mutation matrix, including each frozen selector/member field drift while recomputing non-target identities so the intended validation branch is reached.

## Authorization boundary

This approval does **not** authorize real P4 preflight, candidate/run/staging/materialization, record/refreeze/evidence publication, P5 authority/export/compose, torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training.

A separate implementation closure review is required before this final static section can be marked closed.
