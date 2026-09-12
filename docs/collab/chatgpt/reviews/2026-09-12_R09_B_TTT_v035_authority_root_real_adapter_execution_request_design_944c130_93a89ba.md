# ChatGPT Review — Authority Root Real Adapter / Execution Request Design v0.6

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

## Exact formal pair

- root design SHA: `944c1305bcaef818e178c781b5cf2ce8aebbc9a8`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `066de7052310dc889074632981cc3cdec880ab41`; the child is unchanged.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is reachable in `wxwy/cosmos-framework`.

Latest repository coordination for this exact pair reports both MM and Kimi have now produced the same exact-pair final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC`. Those are coordination signals only; ChatGPT's conclusion below is independently derived.

## Review basis

Reviewed against:

- approved authority-root materialization/binding v0.1 + ABI v0.2;
- the closed synthetic authority-root implementation and actual `publish_candidate()` / `_rollback()` control flow;
- real-adapter design v0.1-v0.5;
- prior ChatGPT exact-pair review for `066de705... / 93a89ba...`, which left one HIGH blocker;
- current v0.6 addendum, specifically the authority-owned callback outcome capture, post-commit dispatch, return-value semantics, and CPU/static acceptance matrix.

## Prior blocker closure

### Prior HIGH — post-commit callback exception could still re-enter rollback: CLOSED

v0.6 directly closes the remaining split-brain branch.

The prior problem was that `consume_by_unlink()` could commit PASS inside arbitrary finalizer code, after which the finalizer could still raise before normal return; the inherited outer `publish_candidate()` exception boundary could then roll refs back even though accepted PASS was already visible. v0.6 now requires the authority module to capture the **entire** callback invocation as `returned(value)` or `raised(exception)` before deciding whether rollback is legal.

The mandatory dispatch order is now explicit:

1. perform pre-commit publication work and issue/pre-validate the exact witness/commit pair;
2. invoke the finalizer under an inner `BaseException` outcome capture;
3. inspect the authority-owned exact `EvidenceCommit.state` **before** deciding rollback;
4. if `committed`, leave the rollback boundary normally and preserve exact candidate refs regardless of whether the callback returned or raised;
5. only after leaving that rollback boundary may a raised callback outcome be re-emitted as `PostCommitFinalizerError`, preserving the original exception as cause;
6. if not committed, both callback return and callback exception remain pre-commit and enter the already-frozen ownership-aware rollback path.

This makes the previously required invariant mechanically single-valued:

`guard unlink succeeded <=> EvidenceCommit committed <=> accepted PASS visible <=> exact candidate refs preserved <=> callback outcome bypasses _rollback`.

The ordinary-return contradiction is also closed. v0.6 explicitly chooses one rule: a normal finalizer return value never carries capability semantics and is ignored; after commit it returns the exact `PublicationWitness`, while before commit a normal return without commit is the stable pre-commit failure `FINALIZER_DID_NOT_COMMIT`.

The required CPU/static matrix directly covers the previously missing branches: post-unlink ordinary exception, `KeyboardInterrupt`, custom `BaseException`, arbitrary normal-return objects, pre-commit callback exception, no-consume return, replay/wrong/unsealed commit, and direct `_rollback` spying. That is sufficient for the implementation Gate to prove the outcome boundary rather than infer it.

## Regression review

No regression was found in the previously closed contracts:

- v0.5 rollback reachability remains inherited unchanged, including `rollback.entered` versus ownership-based `required`, no-ownership `pre_publication` / `local_cas` final-proof outcomes, and strict `post_publication` double-owned chronology;
- v0.4 primary/rollback failure separation remains binding;
- v0.3 exact nested evidence ABI, opaque witness/commit capability model, and four-file implementation allowlist remain binding;
- v0.2 exact raw-byte/native Git blob OID binding and per-fixed-ref exact-old remote lease-CAS remain binding;
- the implementation authorization remains CPU/static and temporary-only.

The formal commit itself is docs-only for this Gate: `SESSION.md`, `TODO.md`, and the v0.6 design file. The child/Gitlink is unchanged.

## Blocker summary

- production/design blockers: `0`
- Evidence-only blockers: `0`
- total blockers: `0`

## Final verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC`

This verdict binds only the exact formal pair `944c1305bcaef818e178c781b5cf2ce8aebbc9a8` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Scope of approval is exactly the frozen four root files from v0.3/v0.6 and temporary-directory / local bare-remote CPU/static tests. It does **not** authorize real selection/config JSON creation, real candidate/ref/origin mutation, real source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1. A later real materialization execution request remains separately gated.