# ChatGPT Review — Authority Root Real Adapter / Execution Request Design v0.4

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

## Exact formal pair

- root design SHA: `be833f807e50a9a1d433c8fdf7f341e7ad3544f6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `c4133389f856f5ab7a5ad01923f71c0c3892ce09`; the child is unchanged.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is reachable in `wxwy/cosmos-framework`.

Latest repository coordination state for this exact pair reports MM=`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC`; Kimi was still reviewing and had no final at the captured snapshot. Those are coordination signals only and are not inherited as ChatGPT's technical conclusion.

## Review basis

Reviewed against:

- approved authority-root materialization/binding v0.1 + ABI v0.2;
- closed synthetic authority-root implementation and its actual `publish_candidate()` / `_rollback()` control flow;
- real-adapter design v0.1-v0.3;
- prior ChatGPT review for `c413338... / 93a89ba...`, which left two HIGH blockers;
- current v0.4 addendum, especially the PASS linearization, failure object and rollback reachability overrides.

## Prior blocker closure status

v0.4 makes real progress on both previous blockers:

1. **Prior HIGH — two incompatible writer commit points: substantially closed on the writer side.** All fallible write/fsync/re-read/validation work is now explicitly placed before guard unlink, and guard unlink is declared the sole writer-side PASS transition.
2. **Prior HIGH — generic rollback row erased primary failure and allowed null/unverified state: substantially closed.** v0.4 introduces separate primary/rollback failure fields and origin-specific rollback rows with concrete verified authority/candidate requirements.

However, two blocking inconsistencies remain when the addendum is checked against the inherited capability contract and the actual production rollback state machine.

## Current blockers

### HIGH-1 — guard unlink is declared committed before the authority side has safely accepted the returned `EvidenceCommit` capability

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.4.md:11`

**Root cause**

v0.4 correctly makes guard unlink the writer-side linearization point and forbids any fallible writer operation after it. But the inherited v0.3 capability contract still requires the authority module to distinguish a valid same-witness sealed `EvidenceCommit` from an ordinary value, a different-witness capability, or a replay. v0.4 itself also says the finalizer's only public success result is a same-witness sealed capability and that `publish_candidate()` returns normally only after receiving it.

That leaves an unresolved post-linearization decision on the authority side:

1. finalizer performs successful `unlink(guard)`, making PASS verifier-visible and, by v0.4, committing publication;
2. finalizer returns some object to `publish_candidate()`;
3. the authority module must still determine whether that object is the correct sealed capability for this witness/activation and whether it is unused;
4. if that check can reject and raise into the existing `try/except`, the code re-enters ref rollback after accepted PASS is already visible; if it cannot reject, the opaque capability / same-witness / anti-replay contract is no longer enforced.

The design therefore moved the ambiguity one boundary later but did not remove it. The invariant `accepted PASS visible <=> transaction committed <=> exact candidate refs preserved` is not mechanically guaranteed for invalid/different/replayed callback returns.

**Why this is blocking**

This is the same split-brain class as the prior HIGH: accepted evidence could coexist with rollback, or the authority module could weaken the capability contract to avoid rollback. The implementation stage is not allowed to invent which side wins.

**Exact acceptance**

Freeze a single authority-owned postcondition around guard unlink so no rejection path remains after the PASS transition. Any of these shapes is acceptable if fully specified and tested:

1. all capability type/token/witness-identity/replay validation occurs **before** guard unlink, and guard unlink consumes a prevalidated one-shot commit capability; after unlink, `publish_candidate()` has no branch that can fail into rollback; or
2. if an invalid callback result can still be detected after guard unlink, that condition is explicitly post-commit and must preserve exact candidate refs; it may fail-stop/report but may never enter ownership rollback.

The design must state which component creates/seals the `EvidenceCommit`, when same-witness identity is checked, and which exact operation consumes its one-shot state.

CPU/static acceptance must include at least: ordinary return value, different-witness capability, replayed capability, and wrong/unsealed capability. Each must either fail pre-commit with no accepted PASS + complete rollback, or be a frozen post-commit preserve-refs fail-stop; no case may expose accepted PASS and then execute ref rollback.

### HIGH-2 — rollback reachability still does not match the actual `publish_candidate()` state machine

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.4.md:50`

**Root cause**

v0.4 says every `ROLLBACK_INCOMPLETE` must originate from one of only four primary phases: `remote_cas`, `post_publication`, `binding_reverify`, or `evidence_write`, and every rollback-required record must already carry concrete verified authority/candidate and `both_absent=true` pre-observations.

The existing production state machine is broader. `publish_candidate()` wraps the **pre-publication observation and local CAS** in the same `try/except`, and `_rollback()` always performs fresh final local+remote observations even when no `*_created` ownership witness exists. Therefore legitimate fail-stop cases also exist before the four v0.4 rows:

- **`pre_publication`**: a concurrent/pre-existing foreign fixed ref or unreadable endpoint causes the initial observation to fail; `_rollback()` owns nothing and must not delete it, but final observation is non-absent/unprovable, so it returns `ROLLBACK_INCOMPLETE`.
- **`local_cas`**: the local expected-zero CAS can lose a race or become operationally ambiguous without creating a local ownership witness; `_rollback()` again must preserve foreign/unproved state, and fresh final observation can force `ROLLBACK_INCOMPLETE`.

v0.4 makes those terminal states unrepresentable because it says the four listed origins are exhaustive and couples rollback-required state to `both_absent=true` plus verified mutation-path provenance.

The `post_publication` row is also too permissive in the opposite direction: in the actual current algorithm `post_publication` is reached only **after remote CAS returned success and `remote_created=True`**, so local and remote create/succeeded/owned bits must all already be true. The row currently allows remote succeeded/owned to vary, admitting evidence states that cannot occur in production.

**Why this is blocking**

The evidence verifier is supposed to mechanically reproduce actual chronology. As written it would reject legitimate fail-stop records from the real adapter while accepting impossible `post_publication` ownership combinations.

**Exact acceptance**

1. Align the evidence state machine with the actual `publish_candidate()` `try/except` and `_rollback()` behavior rather than only mutation-owned paths.
2. Explicitly freeze `pre_publication` and `local_cas` terminal behavior, including the case where no endpoint is owned but fresh final observation is foreign/unreadable/non-absent and the only safe result is `ROLLBACK_INCOMPLETE`.
3. Define `rollback.required` unambiguously. If it means “the recovery/final-proof routine is entered,” it can be true even with no owned delete; if it means “at least one owned endpoint requires deletion,” then the schema needs a separate way to encode rollback/final-proof invocation and incomplete final observations. Do not overload the field implicitly.
4. Tighten `post_publication`: both local and remote create/succeeded/owned bits are necessarily true before this phase can occur under the current algorithm.
5. Add direct validator negatives/positives for:
   - pre-publication foreign ref -> preserved foreign + `ROLLBACK_INCOMPLETE`;
   - pre-publication observation error with unprovable final endpoint;
   - local-CAS race/ambiguous result without ownership witness;
   - impossible post-publication record with remote not owned;
   - all existing remote_cas / binding_reverify / evidence_write rollback rows.

If production is intentionally changed so those earlier rollback outcomes become impossible, that production change itself must be explicitly designed and reviewed; v0.4 currently does not request it.

## Non-blocking findings

- v0.2's corrected exact raw-byte / native blob OID binding remains intact.
- v0.2's per-fixed-ref exact-old remote lease-CAS remains intact.
- Expanding the implementation allowlist to four root files remains justified.
- Splitting primary and rollback failure fields is the right direction and should be retained.
- Using guard presence as fail-closed evidence visibility is acceptable provided the authority-side capability transition is made linear with it.

## Blocker summary

- production/design blockers: `2 HIGH`
- Evidence-only blockers: `0`
- total blockers: `2`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.4.md:11)`

This verdict binds only the exact formal pair `be833f807e50a9a1d433c8fdf7f341e7ad3544f6` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same real-adapter/execution-request design Gate. This verdict does **not** authorize implementation yet and does not authorize real selection/config JSON creation, candidate/ref/origin mutation, source read, collection/receipt/source-evidence/publication, child/runtime modification, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
