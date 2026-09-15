# ChatGPT Formal Review — Stage-1 v1.7 exact-plan pre-C authority V23

Formal pair:
- root: `04fd92eea3506ffe1de0ef8cce12377f81e2e75f`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-EXACT-PLAN-PRE-C-AUTHORITY-V23`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_exact_plan_pre_c_authority_v2.3.md:26)`

Blockers: `1 HIGH`
- Design/Authority: `1 HIGH`
- Production/implementation: `0`
- Evidence/Scope: `0`
- child/runtime: `0`

## Positive closure

- The formal root resolves and its tree binds `cosmos-framework` mode `160000` exactly to the declared reachable child.
- V23 correctly chooses the two-stage remediation for the V22 capability-identity blocker: this Gate authorizes only one real non-consuming pre-C; the future C remains separately forbidden until an exact-plan review approves the actual consumer/guard/verifier identities and all sealed C inputs.
- The design preserves C01--C15, the nine-entry freshness domain, remote-pre-C-only facts, canonical bytes/paths, same-object patch handoff, terminal no-retry semantics, and the four-step future C.
- No real pre-C/C, request pair, materialization, source-evidence, child/runtime/config mutation, GPU or training is executed by this formal root.

## HIGH — exact-plan approval does not yet bind to the same live `SealedPreCPlanV1` instance that future C will consume

V23 says pre-C forms the sealed plan only in-process, forbids request/receipt/cache/sidecar/evidence writes, emits a read-only exact-plan review record, and then hard-stops for independent review. But the controlling production type `SealedPreCPlanV1` explicitly rejects copy, deepcopy, and serialization. V23 does not define any host-owned continuation/lease/session mechanism proving that the exact non-copyable plan instance created by pre-C remains alive across the independent review and is the sole object later passed to `consume_once_v05(plan)`.

Without that continuity contract, there are only two interpretations, both unsafe:
1. the pre-C process ends and future C reconstructs/re-resolves another plan from the review record; then the approved record is not proof that C consumes the same capability/guard/verifier objects and sealed bytes that were reviewed;
2. the process remains alive, but V23 does not freeze the resume-only handle/session identity, lifetime/failure semantics, or the rule that any process/plan/handle loss invalidates the authority instead of allowing reconstruction.

This is the same authority principle V23 is intended to enforce: independent approval must bind the *actual object graph that will perform the irreversible write*, not merely a textual identity record from an earlier plan.

## Acceptance criterion

Freeze one exact continuity model before authorizing real pre-C. The simplest acceptable model is:
- pre-C creates one non-copyable `SealedPreCPlanV1` plus one host-owned opaque continuation/lease handle in the same process/session;
- the exact-plan review record binds an unambiguous session/plan/lease identity and all already-required capability/guard/verifier literals and sealed bytes;
- while review is pending, that plan is quiescent and cannot call the consumer or mutate/rebind its object graph;
- exact-plan approval can resume **only that live plan instance** through a resume-only C entrypoint; C does not reconstruct, import, resolve, deserialize, or replace capability/guard/verifier/bytes/paths;
- process death, handle loss, plan replacement, identity drift, or inability to prove same-instance continuity invalidates the authority and requires a fresh pre-C + exact-plan review cycle; no retry/repair/reconstruction under the old approval.

An alternative design may use another mechanism, but it must prove the same property: the exact-plan record reviewed by the three reviewers is cryptographically/structurally bound to the same non-copyable sealed plan instance later consumed by C.

Scope reminder: this review does not reopen the closed CPU/static freshness-guard Gate. Real C/request-pair write, materialization, source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1 remain forbidden.
