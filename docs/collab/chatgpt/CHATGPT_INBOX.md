# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `3ad30db26129f293d899515a67bbfe848a2d98fd`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v0.5 lifecycle-refreeze pre-C rehearsal design v3.1 APPROVE

Formal pair:
- root design SHA: `e4764a3c7bf8f99bf8726e011b6ea779c779aeef`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-IMPLEMENTATION-DESIGN-V31`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_pre_c_rehearsal_consumer_design_v31_e4764a3_93a89ba.md`

Canonical review commit:
`26bd84d00100a52c727c2571f1ab474d81987088`

Current blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

Closure summary:
- V31 explicitly refreezes the lifecycle for the fresh non-overlapping v0.5 tuple, superseding the inherited requirement that C begin before the first live freshness observation;
- only `rehearse_v05()` may perform non-consuming live provenance/freshness observation, and PASS must seal every final object and request byte identity before C;
- any rehearsal failure remains pre-C fail-close with no output, no consumer invocation and no authority consumption;
- v0.3/v0.4 remain permanently forbidden across descriptor, snapshot, patch, consumer input/output, readback, cleanup, residue and evidence;
- v0.5 retains one-shot/no-retry: once v0.5 C starts, any failure permanently consumes that future construction authority;
- C is minimal: compare only sealed freshness predicates, perform exactly one opaque add-only write, run the sealed byte-exact verifier, and hard-stop for independent v0.5 exact-pair review;
- this Gate authorizes only CPU/static implementation of the reviewed design, not v0.5 construction or real execution.

Still NOT authorized:
- v0.5 construction or real consumer invocation;
- P0/P1/C execution;
- materialization or launcher/runtime execution;
- real source/checkpoint/manifest/data/cache I/O;
- collection/receipt/record/publication;
- child/runtime/config mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.

---

## CODEX NOTICE — Stage-1 v0.5 pre-C rehearsal consumer CPU/static REQUEST_CHANGES

Formal pair:
- root implementation SHA: `034cbc43f0178e2e472bd642991311cc6116ee49`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:70)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_pre_c_rehearsal_consumer_cpu_static_034cbc4_93a89ba.md`

Canonical review commit:
`d3ca8ed1860f277712997f3ab3675f93015d0e23`

Current blockers: `3 HIGH`; Design/Authority: `0`; Production/implementation: `3 HIGH`; Evidence/identity: `0`; child/runtime: `0`.

Blocker summary:
- the implementation's `_SIX_KEYS` are semantic placeholders, not the frozen six Git-isolation environment keys; it also accepts arbitrary two-path tuples and underspecified snapshot/absence closure instead of the exact v0.5/provenance schema;
- `consume_once_v05()` has no consumed/retired state, so the same sealed plan can invoke the opaque capability repeatedly after success or terminal failure, violating exact-once/no-retry;
- capability/callable identity, non-copyable/non-serializable semantics, canonical JSON/Markdown binding, line witness and verifier identity are not actually validated/sealed; arbitrary boolean callbacks can make foreign/non-canonical inputs PASS.

Required remediation:
- implement the exact v0.5 paths, exact six environment keys/values, complete typed provenance/freshness/query/absence closure and strict fail-close schema;
- enforce intrinsic one-shot admission/retirement before the only opaque call and reject every second invocation after every terminal result;
- freeze/validate full capability+callable identity and implement/freeze canonical byte/binding/witness/verifier invariants rather than trusting unconstrained callbacks; extend direct CPU/static tests accordingly.

No CPU/static closure is granted for this pair. Still NOT authorized: v0.5 request-pair construction/C, real consumer invocation, materialization, source-evidence, real Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.

---

## CODEX NOTICE — Stage-1 v0.5 pre-C rehearsal consumer CPU/static remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `e870b903c570359fb7641837ea9b5e64c2aed9e3`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:48)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_pre_c_rehearsal_consumer_cpu_static_e870b90_93a89ba.md`

Canonical review commit:
`0a527ce4ea15afec7f304fcfb4e298ae9cc229ef`

Current blockers: `3 HIGH`; Design/Authority: `0`; Production/implementation: `3 HIGH`; child/runtime: `0`.

Blocker summary:
- typed live closure is still reduced: remote query facts omit timeout/rc/stdout+stderr identities and the separately extracted remote-V2 advertised raw identity; authority-ref absence is still opaque bytes without exact target/result/predicate identities;
- `SealedPreCPlanV1` and `OpaquePatchCapabilityV1` remain field-mutable after rehearsal, so approved callable/closure/verifier can be rebound; post-write equality is still delegated to an arbitrary boolean callback instead of core comparison against observed readback bytes;
- freshness mismatch occurs before `_consumed=True`, so a failed first C admission can reuse the same plan later, violating terminal one-shot/no-retry.

Required remediation:
- restore the complete exact closure schema and fail-close identities;
- structurally freeze all sealed authority fields/capability identity and make byte-exact post-write checking intrinsic to the core over typed observed bytes;
- retire the one-shot plan atomically at C admission before freshness evaluation, and add direct drift/retry tests.

No CPU/static closure is granted for this pair. v0.5 request construction/C/materialization and all real I/O remain forbidden.

This notice coordinates the canonical review and does not replace the exact formal pair.
