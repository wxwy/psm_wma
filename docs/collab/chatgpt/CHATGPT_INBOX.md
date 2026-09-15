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

- immediate prior live blob SHA: `d50e3d1a0951622746c12e229cec1c0abf41d615`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 freshness-guard CPU/static Gate APPROVED TO CLOSE

Formal pair:
- root implementation SHA: `37eca204a2144d9e191c4f995d881749a9a9d218`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-FRESHNESS-GUARD-CPU-STATIC`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_FRESHNESS_GUARD_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_freshness_guard_cpu_static_37eca20_93a89ba.md`

Canonical review commit:
`57711e3cc5991fc279dda82cb27c7653d4019a8a`

Current blockers: `0`; Design/Authority: `0`; Production/implementation: `0`; Evidence/Scope: `0`; child/runtime: `0`.

Closure summary:
- the previously accepted production implementation remains intact: the sealed freshness lease domain deterministically contains git/config/local-V2, two output absences and four designated absences, and C accepts no external reconstructed `ClosureV1`;
- the prior evidence blocker is closed: the fake guard now derives `FRESH`/`STALE` from a simulated live domain compared directly with the sealed identities and lease domain;
- the direct public-path test sweeps both output absences and all four designated absences, mutates each simulated live identity after rehearsal, proves `freshness` failure before consumer apply with apply count zero, then proves the same plan is terminal via `already_consumed` on the second call;
- formal root tree binds `cosmos-framework` mode `160000` exactly to the declared reachable child;
- this exact pair changes only CPU/static test evidence and stays within the authorized pure-memory scope.

Scope reminder: this closes only the root CPU/static freshness-guard Gate. It does not authorize a real freshness guard, real pre-C/C, request-pair construction, materialization, source-evidence, real Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
