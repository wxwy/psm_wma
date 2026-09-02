# ChatGPT independent review — R09-B2 P4-v4 execution request `backends` v0.1

- Design commit: `90b4cf9b9c9c99b1363bccc8614d680e1e304ba4`
- Request/ledger commit: `937542e8df8c30271e233169d286dd04f2119dd7`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Previous ChatGPT anchor: `1b58fd9f3680054f5434e7006c8db503997329b8`
- Scope: design only; no execution/materialization/P5/GPU/training authority.

## Verdict

`REQUEST_CHANGES`

The proposed split is directionally sound: `backends` should carry a small verifier-owned P3 backend contract rather than inspect optimizer/module names itself. However the v0.1 contract is not yet machine-satisfiable under its own restrictions.

## Blocking findings

### HIGH — `p3_contract` cannot be canonical-equal to P5 v0.9 as currently schematized

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_backends_design_v0.1_2026-09-02.md:5`

P4 v0.1 defines:

```text
p3_contract={artifact_sha256,verifier_sha256,backend_contract,identity_sha256}
```

but the frozen P5 v0.9 provenance contract is exactly the three-field core:

```text
p3_contract={artifact_sha256,verifier_sha256,backend_contract}
```

(`docs/build/PSM-WMA_R09_B2_P5_full_config_diff_design_v0.9_2026-09-02.md`, and current `verify_r09_b2_p5_full_config_diff.py::_p3_provenance()`). Therefore the statement that the whole P4 `p3_contract` must be canonical-equal to P5 v0.9 is impossible while P4 adds a self-digest field.

Freeze the distinction explicitly, e.g.:

```text
p3_core={artifact_sha256,verifier_sha256,backend_contract}
p3_contract={**p3_core,identity_sha256}
identity_sha256=canonical_sha256(p3_core)
```

and require `p3_core` (not the four-field wrapper) exact-equal to the verifier-owned P5 v0.9 core.

### HIGH — verifier-owned optimizer membership is not obtainable under the declared static implementation boundary

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_backends_design_v0.1_2026-09-02.md:5-7`

P5 v0.9 does not expose literal per-backend `optimizer_membership_sha256` constants. Its verifier derives them by:

1. binding fixed `P3_ARTIFACT_SHA256` / `P3_VERIFIER_SHA256`;
2. reading the frozen P3 inventory via `_load_frozen_inputs(evidence_root)`;
3. computing `_p3_contract(inventory, backend)` from the verified model-parameter membership.

See `tools/g0/verify_r09_b2_p5_full_config_diff.py::_p3_contracts()` and `tools/g0/verify_r09_b2_p4_d005.py::_p3_contract()`.

The proposed P4 design simultaneously says the root validator must not trust self-report **and** must not read the P3 artifact/verifier or call the P5 verifier/exporter. With no exact expected backend-contract snapshot frozen in the design, `optimizer_membership_sha256` has no admissible authority source and can only be format-checked/self-reported.

Choose and freeze one authority model before implementation:

- **Snapshot model (preferred for this static section):** freeze the exact recurrent and `ttt_fast_weight` three-field `p3_core` values (including exact selector list and membership SHA), plus the exact P3 artifact/verifier SHA constants and the reviewed P5-v0.9 authority identity from which the snapshot was derived; validator compares only to these constants and never reads P3 evidence.
- **Read-only recomputation model:** explicitly permit a fixed, reviewed read-only P3 authority path and exact tool identity, then recompute the two cores from the frozen bytes. This changes the stated no-artifact-read boundary and must include the same no-follow/single-authority discipline used elsewhere.

Do not introduce a second semantic optimizer/member allowlist; the P4 contract must be a byte-exact mirror of the already reviewed P5/P3 verifier-owned result.

### MEDIUM — “frozen P5 v0.9” needs an exact machine identity

The design names “P5 v0.9” but does not bind the authority to an exact approved implementation/tool blob or an exact frozen contract snapshot. A prose version label is insufficient for a static validator because the source files can evolve while retaining the same document name.

Whichever authority model is chosen above, freeze either:

- exact approved P5/P3 verifier revision + relevant Git blob SHA(s), or
- exact per-backend contract snapshot values whose provenance is bound to that reviewed revision.

## What is already acceptable

- Exact outer and per-backend key sets.
- Backend byte-exact labels and exact two-backend roster.
- Cross-side artifact/verifier equality requirement.
- Stable ordered selector-list grammar and 64-lowercase-hex digest grammar.
- Rejection of swap/third-backend/identity reuse.
- Static-only implementation boundary and no execution/materialization authority.

## Gate state

`backends` remains design-pending. Closed sections remain 7/8 (87.5%). No real preflight, candidate/run/staging creation, final request execution, P5 export/compose, GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized by this review.
