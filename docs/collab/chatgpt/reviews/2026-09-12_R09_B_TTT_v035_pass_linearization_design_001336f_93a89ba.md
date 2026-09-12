# ChatGPT Review — Authority Root PASS Linearization Design v0.10

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`

## Exact formal pair

- root design SHA: `001336fa5d785d8c77a2685ac1c754c096b4fb06`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.10.md`

The formal root is reachable (`docs: clarify authority pass observation boundary`). Its exact tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Fresh incremental review against:

- approved authority-root design chain v0.3-v0.6;
- PASS-linearization design chain v0.7-v0.9;
- prior ChatGPT v0.9 review `a98e82714940d7bed1969cafb2ef32100c287d59 / 93a89ba...`, whose only remaining HIGH was the contradiction between observation-only ref-witness semantics and a CPU/static requirement demanding rollback for unobservable post-observation/pre-swap drift;
- exact v0.10 text.

## Prior blocker closure

### v0.9 HIGH-1 — observation-only ref semantics contradicted the pre-swap drift test matrix: CLOSED

v0.10 explicitly selects the recommended Option A and makes the observation boundary exact:

- the only ref fact bound to acceptance is the final explicit local/remote `== candidate` observation before the terminal-state pointer swap;
- there is no further ref I/O, namespace lock, or hidden validation after that observation;
- any external drift after that observation, including drift occurring before the pointer swap, does not retroactively invalidate the historical witness or cancel the prepared terminal transition;
- if a later explicit ref check detects mismatch, the result is external-corruption fail-stop/recovery; it does not silently claim current refs are exact, does not auto-repair them, and does not roll back an already ACCEPTED terminal state;
- only drift occurring before the declared final observation and observed by that validation can cause ordinary pre-state rejection/rollback.

The CPU/static matrix now matches the stated observation-only semantics. Implementation is no longer required to detect an event that the design simultaneously defined as outside the observed authority fact.

## Retained design contracts

The previously accepted v0.9 contracts remain intact:

- one authority-owned terminal-state cell is the sole semantic acceptance state; `accepted`, rollback permission, preserve-refs, and witness-return eligibility are derived from that one cell;
- guard transition is the final fallible pre-state action;
- crash windows A/B/C are explicit; guard-absent B/C restart states are fail-stop and cannot be distinguished or authorized from pathname/evidence alone;
- public API remains v0.8/v0.6-compatible: successful `publish_candidate(...)` returns the exact `PublicationWitness`; private `AcceptedPass` does not escape authority dispatch;
- pathname/evidence verification remains observation/audit only and cannot manufacture acceptance authority;
- exact-old CAS remains ownership evidence for the activation and is not misrepresented as a global namespace lock.

## Non-blocking implementation evidence requirements

The implementation Gate should directly prove the frozen semantics rather than reintroducing stronger claims:

1. post-final-observation local/remote drift, including drift before the terminal pointer swap, may still lead to ACCEPTED from the historical witness;
2. a later ref check must surface mismatch as external corruption/fail-stop and must never report the current namespace as exact;
3. pre-final-observation drift observed by the final validation remains a pre-state failure and follows existing ownership-aware rollback rules;
4. crash-window A must not infer activation ownership merely from a candidate-valued ref after process loss; existing expected-zero/exact-old lease rules must remain fail-closed;
5. no independent mutable accepted/committed/consumed/preserve flag may be reintroduced outside the single terminal-state cell.

These are implementation acceptance details, not new design blockers.

## Blocker summary

- design/contract blockers: `0`
- total blockers: `0`

## Final verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC`

This approval binds only the exact formal pair `001336fa5d785d8c77a2685ac1c754c096b4fb06 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Authorization is limited to the already frozen four root tooling/test files and temporary directory/local bare-remote CPU/static implementation/tests. It does **not** authorize real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
