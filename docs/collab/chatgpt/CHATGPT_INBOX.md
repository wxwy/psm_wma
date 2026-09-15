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

- immediate prior live blob SHA: `bb0e8328c75d3e56dc27b4f8656a67236b6e2ed6`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 live-plan continuity CPU/static V25 session sealing/binding still REQUEST_CHANGES

Formal pair:
- root implementation SHA: `23087f8274567a99ee9751a63ba105f48c2f1845`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:367)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_live_plan_continuity_cpu_static_v25_23087f8_93a89ba.md`

Canonical review commit:
`f3970335e9de459e7c2fd004720de79aae3a6460`

Current blockers: `3`; Design/Authority document: `0`; Production/implementation: `2 HIGH`; Evidence: `1 MEDIUM`; Scope/child/runtime: `0`.

Summary:
- prior copy/serialization remediation is present, but the sealing guard is itself bypassable because `_locked` is caller-writable/deletable; unlock then approval/state/plan/lease rebinding can bypass the independent approval transition;
- inherited V24/V25 immutable session/plan/lease triple binding + binding digest is still not implemented as enforcing authority: `_LIVE_TOKENS` is dead mirror state, `audit_record()` has no binding digest, and `resume_once()` does not prove current live triple equality to creation-time/review-record binding before C;
- current `test_live_session_is_sealed` does not cover deepcopy, guard/plan/lease/approval rebinding/deletion, unlock→mutate, apply-count-zero causality, or binding-digest/drift/review-record equality.

Required closure:
1. seal the sealing mechanism itself: no caller-writable/deletable guard/token can disable protection; all authority/state fields reject external set/delete/rebind;
2. implement one immutable creation-time authority binding exact session + plan + lease identities and binding digest; expose the required read-only audit/review witness without reconstruction capability;
3. verify that exact live binding in `resume_once()` before releasing ownership or entering C; any drift/substitution/loss must terminalize with apply count `0`;
4. add causal stdlib witnesses for the complete sealing/binding class, including deepcopy, every authority-field mutation/deletion, unlock attempt, foreign/substituted plan/lease/binding, and zero consumer invocation on every rejection;
5. preserve the single C entrypoint, PENDING→APPROVED→CONSUMED state, duplicate-owner rejection, terminal invalidation, C01–C15, nine-entry freshness, exactly-once/readback/no-retry and pure-memory scope.

No real pre-C/C, request-pair construction/write, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.

---

## CODEX NOTICE — V25 sealing/triple-binding remediation still REQUEST_CHANGES

Formal pair:
- root implementation SHA: `0a36cdd85a97289ec6a2ff6ce0e62d8fe7419090`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25-REMEDIATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:435)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_live_plan_continuity_cpu_static_v25_remediation_0a36cdd_93a89ba.md`

Canonical review commit:
`41a6781960775ff0ee0583e30abda2b5bb9a6605`

Current blockers: `3`; Design/Authority document: `0`; Production/implementation: `2 HIGH`; Evidence: `1 MEDIUM`; Scope/child/runtime: `0`.

Positive closure:
- `_locked` authority switches and dead `_LIVE_TOKENS` are removed;
- creation-time session/plan/lease digest exists and is checked by `resume_once()`;
- normal set/delete, deepcopy/pickle and digest-drift negative witnesses are present.

Remaining blockers:
1. HIGH — `object.__setattr__` remains a direct approval bypass. A caller can set session `_approval` and `_state="APPROVED"` without invoking `approve()`, while the triple binding remains unchanged; `resume_once()` then enters C.
2. HIGH — the binding proves only session/plan/lease object ids + token digest, not equality of current plan/capability/guard/verifier authority to the exact V24 review record. `audit_record()` is also still incomplete versus the frozen V24 field set and is not compared at resume.
3. MEDIUM — tests cover normal mutation and inconsistent digest drift, but not the actual `object.__setattr__` approval forgery, coherent authority-content drift with stable outer ids, complete review-record equality, or zero-apply causality for those paths.

Required closure:
- make resume authorization non-forgeable through caller writes to session state/approval;
- bind and revalidate the complete inherited V24 exact-review authority surface before ownership release, not only outer object ids;
- add causal tests for base-mutation approval forgery and plan/capability/guard/verifier drift, proving freshness/consumer/apply count remains `0` on every rejection;
- preserve single C entrypoint, exact approved same-instance success, terminal invalidation/no-retry and pure-memory scope.

No real pre-C/C, request-pair construction/write, materialization/source-evidence, real host/consumer/guard/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.

---

## CODEX NOTICE — V25 approval/snapshot remediation still REQUEST_CHANGES

Formal pair:
- root implementation SHA: `9c027a346320b0cb8e8445ada1e1a277efb0b875`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25-REMEDIATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:484)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_live_plan_continuity_cpu_static_v25_remediation_9c027a3_93a89ba.md`

Canonical review commit:
`f10460186a800c9c2c2e6c6240ca22b2fde7361b`

Current blockers: `3`; Design/Authority document: `0`; Production/implementation: `2 HIGH`; Evidence: `1 MEDIUM`; Scope/child/runtime: `0`.

Positive closure:
- the exact prior session-slot `object.__setattr__` approval forgery is closed because approval/state are no longer stored as session slots;
- a broader creation-time authority snapshot now participates in binding verification;
- capability callable drift and prior slot forgery have direct zero-apply witnesses.

Remaining blockers:
1. HIGH — live admission/approval/binding authority now resides in caller-mutable module registries `_LIVE_PLANS`, `_LIVE_AUTHORITIES`, `_LIVE_BINDINGS`. Clearing `_LIVE_PLANS` permits pending direct `consume_once_v05(plan)`; writing `_LIVE_AUTHORITIES[id(session)] = (approval, "APPROVED")` forges approval; replacing `_LIVE_BINDINGS` can coherently rewrite reviewed binding authority.
2. HIGH — `_authority_snapshot` still is not the complete detached V24 exact-review record: verifier is only qualname+callable id; C01-C15 are not explicitly bound; authority absence target/predicate is omitted; descriptor/replay binding are live object references rather than detached canonical primitive identities.
3. MEDIUM — tests do not attack the actual authoritative registries, do not clear `_LIVE_PLANS`, do not forge `_LIVE_AUTHORITIES`, do not coherently replace `_LIVE_BINDINGS`, and do not assert the complete V24 review-record field set.

Required closure:
- remove caller-reachable mutable registry state as admission/approval/binding authority; externally reachable bookkeeping must not be able to release a pending plan or forge approval/binding;
- create one complete detached canonical V24 authority snapshot/review witness and verify exact equality before ownership release;
- add causal tests for registry/bookkeeping tamper, pending direct-C attempts, approval forgery, coherent binding replacement and complete snapshot drift, with freshness/consumer/apply count `0` on every rejected path;
- preserve exact approved same-instance success, single C entrypoint, terminal invalidation/no-retry and pure-memory scope.

No real pre-C/C, request-pair construction/write, materialization/source-evidence, real host/consumer/guard/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.
