# ChatGPT Review — Authority Root Real Adapter / Execution Request Design v0.5

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

## Exact formal pair

- root design SHA: `066de7052310dc889074632981cc3cdec880ab41`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `be833f807e50a9a1d433c8fdf7f341e7ad3544f6`; the child is unchanged.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. That child commit is reachable in `wxwy/cosmos-framework`.

Latest repository coordination for this exact pair says MM has entered review and Kimi has received the request but had no exact-pair final at the captured snapshot. Those are coordination signals only and are not inherited as ChatGPT's technical conclusion.

## Review basis

Reviewed against:

- approved authority-root materialization/binding v0.1 + ABI v0.2;
- the closed synthetic authority-root implementation and actual `publish_candidate()` / `_rollback()` control flow;
- real-adapter design v0.1-v0.4;
- prior ChatGPT exact-pair review for `be833f8... / 93a89ba...`, which left two HIGH blockers;
- current v0.5 addendum, especially the cross-module commit protocol and rollback reachability matrix.

## Prior blocker closure

### Prior HIGH-2 — rollback reachability did not match production: CLOSED

v0.5 cleanly separates `rollback.entered` from `rollback.required`, defines `required` as owned-endpoint deletion only, adds legitimate `pre_publication` and `local_cas` no-ownership fail-stop states, retains fresh final observations, and tightens `post_publication` to require all six local/remote create/succeeded/owned bits. This now matches the current production `publish_candidate()` / `_rollback()` control flow closely enough for implementation.

### Prior HIGH-1 — authority-side post-commit capability ambiguity: substantially closed, but one post-commit callback branch remains unspecified

v0.5 materially improves the design by authority-issuing both `PublicationWitness` and `EvidenceCommit` before the callback, pre-validating their identity/epoch/binding, sealing the commit while the guard is still present, and making `commit.consume_by_unlink()` the one-shot linearization transition. It also correctly states that committed state must preserve refs and that post-commit violations sit outside the rollback boundary.

However, the exact callback exception path after the unlink commit is still not fully frozen, and the return-value contract is internally inconsistent.

## Current blocker

### HIGH-1 — a finalizer can still raise after `consume_by_unlink()` commits, while the design only freezes normal-return dispatch and gives contradictory return-value semantics

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.5.md:22`

**Root cause**

v0.5 makes `commit.consume_by_unlink()` the exact PASS linearization point. That is directionally correct. But this method is called *inside arbitrary finalizer code*. After it returns successfully, Python control returns to the finalizer, which can still execute code and raise an exception before returning to `publish_candidate()`.

The design currently freezes only the normal-return branch:

- item 5 says that **after the finalizer returns**, authority performs a total non-throwing state dispatch and preserves refs if the exact issued commit is already committed;
- item 6 defines several post-commit report/wrapper violations as preserve-refs fail-stop outside rollback.

It does not explicitly freeze the equally reachable branch:

1. `consume_by_unlink()` succeeds, so guard is absent, PASS is verifier-visible, and the commit capability is committed;
2. finalizer then raises an arbitrary exception instead of returning;
3. the call unwinds directly into the authority-side exception path.

Unless the implementation is explicitly required to catch **all callback outcomes** first and dispatch on committed state before deciding rollback, the inherited broad `publish_candidate()` `try/except` can still roll refs back after accepted PASS is visible — the same split-brain class this design is intended to eliminate.

There is also a direct specification contradiction in the same paragraph set:

- item 5 says the finalizer **may return any object**, and that the return value is not a commit capability and is not validated;
- item 6 and the required tests classify an **ordinary return value** as a possible `POST_COMMIT_CAPABILITY_VIOLATION`.

Both cannot be the exact contract. The implementation stage must not invent whether an ordinary return is success or a fail-stop.

**Violated frozen contract**

The accepted invariant is:

`accepted PASS visible <=> guard unlink succeeded <=> exact EvidenceCommit consumed <=> exact candidate refs preserved`.

Once guard unlink succeeds, no callback outcome may re-enter ownership rollback. Conversely, before that point, all rejection paths must remain rollback-capable and accepted PASS must remain invisible.

**Exact acceptance**

Keep remediation in the same design Gate and retain the v0.5 capability architecture, but freeze a single outcome-dispatch contract:

1. authority must wrap the finalizer call so **both normal return and exception** become an outcome object/result that is inspected only through the authority-owned `EvidenceCommit` state;
2. if `commit` is not committed, any callback return/exception is pre-commit and may enter the existing rollback path;
3. if `commit` is committed, **any** callback return or exception is post-commit: exact candidate refs and accepted PASS are preserved, and no rollback call is permitted;
4. choose one return-value rule and make it single-valued:
   - either finalizer return values are always ignored after commit, in which case ordinary return is not a violation; or
   - an exact post-commit return contract is required, but any mismatch is explicitly preserve-refs fail-stop and never rollback.
   Do not simultaneously allow arbitrary returns and classify ordinary returns as violations;
5. add direct CPU/static tests for at least:
   - `consume_by_unlink()` succeeds, then finalizer raises;
   - `consume_by_unlink()` succeeds, then finalizer returns an ordinary object;
   - pre-commit finalizer exception;
   - replay/wrong/unsealed commit before commit;
   and prove no accepted-PASS case ever calls `_rollback`.

## Non-blocking findings

- v0.5 closes the previous rollback reachability blocker.
- v0.2 corrected exact raw-byte/native Git OID binding remains intact.
- v0.2 per-fixed-ref exact-old lease-CAS remains intact.
- The four-file implementation allowlist remains justified.
- The user-requested next stage remains CPU/static only; no real materialization or source I/O is authorized here.

## Blocker summary

- production/design blockers: `1 HIGH`
- Evidence-only blockers: `0`
- total blockers: `1`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.5.md:22)`

This verdict binds only the exact formal pair `066de7052310dc889074632981cc3cdec880ab41` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation stays in this same real-adapter/execution-request design Gate. This verdict does **not** authorize implementation yet and does not authorize real selection/config JSON creation, candidate/ref/origin mutation, source read, collection/receipt/source-evidence/publication, child/runtime modification, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
