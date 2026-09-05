# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.12

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `2309d69c3ac6f873d25815a529c3548bf633bf50`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `61f8461054191562b8476f3241e597d7d3cce698`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.12_2026-09-05.md`

## Prior blocker status

- v0.11 HIGH-1 (fixed record count can tail-truncate an episode while verifier required one terminal per group): **PARTIALLY CLOSED**. v0.12 correctly permits one certified zero-terminal tail group and defines single-pass end-of-stream disposal of its open Local transaction.
- v0.10 approved active-wiring scope remains unaffected.

## Blocking finding

### HIGH-1 — certified-tail `ordinal contiguous` rule is incompatible with the actual suite round-robin manifest layout

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.12_2026-09-05.md` §1.2-§1.3; `tools/g0/build_r09_b2_stream_manifest.py` current suite round-robin construction.

v0.12 certifies a zero-terminal tail group only when the group's ordinals form the suite's maximum suffix, parenthetically requiring the group's ordinals to be contiguous and include the suite maximum ordinal.

The actual builder assigns a suite per micro-batch by round-robin (`suite = SUITES[microbatch % len(SUITES)]`) and global `ordinal` increases across all suites. Therefore one episode of a given suite can legitimately span multiple appearances of that suite across different micro-batches, with records from the other suites interleaved between them. Its global ordinals are then not consecutive integers even though it is a perfectly valid contiguous suffix in that suite's own filtered record stream.

As frozen, a correct tail-truncated episode can therefore fail the verifier solely because other-suite records appear between two rows of the same suite tail group. This makes the certification rule inconsistent with the real manifest grammar.

**Frozen-contract violation:** v0.12 §1.2 certified-tail predicate versus the inherited fixed-count/suite-round-robin builder ordering.

**Acceptance:** define suffix/contiguity in the **suite-filtered `(suite, epoch)` record sequence**, not as consecutive global ordinal integers. For example, after filtering records to one `(suite, epoch)` in ascending global ordinal, the zero-terminal group must equal the final contiguous group of that filtered sequence, contain that filtered sequence's maximum global ordinal, have count `<` the dataset-recomputed valid-window count, and contain no terminal. Keep at most one such group per `(suite, epoch)`. Add a verifier fixture where one legitimate tail episode spans multiple suite round-robin micro-batches and has non-consecutive global ordinals; it must PASS, while a non-suffix group with the same counts must FAIL.

## Accepted / unchanged

- true terminal is never forged;
- fixed manifest record count is preserved;
- one certified zero-terminal tail group direction is acceptable;
- single-pass end-of-stream semantics (open tail transaction not commit/reset; process-local fast state discarded) are acceptable;
- v0.11 wrapper/model fail-closed terminal provenance direction and whitelist remain acceptable;
- no implementation/GPU/training authorization is granted by this verdict.

## Scope

Only v0.12 tail-policy design remediation is required. v0.10 previously approved CPU/static implementation scope remains valid; v0.11/v0.12 terminal-provenance whitelist expansion remains blocked until a remediated formal pair is approved.
