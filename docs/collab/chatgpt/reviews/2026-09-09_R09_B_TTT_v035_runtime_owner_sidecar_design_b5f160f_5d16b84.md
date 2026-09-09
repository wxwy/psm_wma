# ChatGPT 独立 runtime-owner / sidecar design v0.8 review

Formal reviewed pair:
- root design SHA: `b5f160f485097945516961336a41af696d28e487`
- child/Gitlink SHA: `5d16b84fe17a42f128065bf36361f6b1bb93a436`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh review of v0.8 relative to superseded v0.7. Child is unchanged. v0.8 correctly narrows the implementation whitelist, makes the exact `CanonicalSegmentWiring` an explicit owner-constructor authority, adds exact pending discard, removes caller-supplied snapshot boundary, and freezes committed-frontier snapshot checks. Review is based only on the Codex request, v0.8, inherited v0.6 contract, and formal child source.

## Closed design gaps

1. **CLOSED — exact wiring authority is now representable.** Owner receives one exact `CanonicalSegmentWiring`; `prepare()` delegates to that exact object and forbids per-call reconstruction, consistent with inherited v0.6 exact capability identity.
2. **CLOSED — snapshot is now tied to committed state rather than caller-declared boundary.** v0.8 requires `IDLE`, no transaction/pending/admitted residue, and cross-checks sidecar records against scheduler committed/stable identities.

## Current blocker

1. **HIGH — the frozen phase machine cannot execute a multi-member GA window or its retry suffix.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.md:52-82`.

   The only declared path is `IDLE -> ADMITTED -> OPEN -> PREPARED -> COMMITTED -> IDLE`, with `begin(plan)` allowed only from `ADMITTED` when there is no open transaction, while `finish_window(transaction)` is allowed only after **all** plan members have completed. For any `GAWindowPlan` with more than one member, after the first member commits the owner reaches `COMMITTED`, but there is no frozen transition that admits/prepares the next member while retaining the same open transaction. Returning to `IDLE` would still leave the transaction unfinished, contradicting the `begin()` precondition and the `finish_window()` precondition. Thus the frozen API cannot realize the existing multi-member `GAWindowPlan` contract.

   The retry route is likewise unreachable: `abort(..., RETRY)` moves the owner to `ABORTED`, while the text says the recovery suffix must enter through a new exact `begin()`. But `begin()` is frozen to require `ADMITTED`, and no `ABORTED -> ADMITTED` / retry-reset transition exists. Therefore the one allowed suffix retry cannot be started under the stated phase machine.

   **Acceptance:** freeze an explicit per-member/window state machine that preserves one exact transaction across all members and defines the post-commit transition for a nonterminal member, including when the next identity is admitted and when the prior forward/pending capability is cleared. Separately freeze the retry transition from an aborted attempt-0 transaction into the exact attempt-1 suffix transaction/plan, including which owner fields are cleared/retained and why the old transaction/forward can never regain authority. Add CPU/static acceptance for a real `GAWindowPlan` with at least two members and for attempt-0 transient abort -> attempt-1 suffix begin -> member execution -> finish, plus negative old-capability reuse.

## Scope boundary

No runtime-owner CPU/static implementation authority is granted for this pair. This remains docs-only. No production model/trainer/packer wiring, persistent sidecar/checkpoint I/O, config/default/registry changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1 is authorized.
