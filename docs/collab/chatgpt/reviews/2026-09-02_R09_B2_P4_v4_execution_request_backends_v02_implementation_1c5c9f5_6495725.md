# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request `backends` v0.2 implementation

- Implementation: `1c5c9f51d2632ba38375cd958d877efb5287f604`
- Closure request / ledger HEAD: `6495725b21d2a0c7ee2de321adf63491810068bb`
- Approved design: `3721e77e1e0b8065f8b757df567f755d02c17e60`
- Prior design approval: `5a23517b0dc4ef4af81902953bc54bf1a95c5efe`
- Gitlink independently re-read at request HEAD: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

The implementation itself is consistent with the approved v0.2 contract: it freezes the approved P3 snapshot constants, validates the exact two-backend schema, computes `p3_contract.identity_sha256` over the three-field `p3_core`, exact-compares each backend core against the verifier-owned snapshot, rejects record identity reuse, enforces cross-side artifact/verifier equality, and introduces no artifact/P5/path/subprocess/ambient input channel.

Closure is blocked only by two permanent CPU-fixture gaps relative to the v0.2 design's explicit matrix.

## Blocking fixture gaps

1. **Selector stable-order negative case is not actually covered.**
   `BackendsAuthorityTest.test_backends_reject_core_grammar_swap_and_pair_binding_drift()` covers empty, duplicate and retyped selector lists, but does not mutate a valid snapshot by swapping two otherwise valid selector entries while preserving all values. The approved design explicitly requires `selector order/duplicate/type` coverage. Add a test that swaps two valid recurrent selector entries, recomputes wrapper/record/outer identities, and proves `validate_backends()` rejects it via the snapshot contract.

2. **The current `core swap` fixture does not exercise a backend-core swap.**
   Its mutation replaces the entire `recurrent` record with the TTT record. That fails earlier because `record["backend"] != "recurrent"`; it therefore does not prove the approved `swap` invariant at the P3 snapshot layer. Add a test that keeps each record's backend label byte-exact, swaps only the two `p3_contract` / `p3_core` payloads, recomputes all identities, and proves each side is rejected against `P3_CORE_SNAPSHOTS[backend]`.

These are tests-only remediation items; no redesign or validator semantic change is requested unless the new fixtures expose a real fail-open bug.

## Scope remains unchanged

Do not authorize or execute real P4 preflight, candidate/run/staging materialization, record/refreeze/evidence publication, P5 authority/export/compose, torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training.

`backends` remains open; Execution Request remains 7/8 closed (87.5%).
