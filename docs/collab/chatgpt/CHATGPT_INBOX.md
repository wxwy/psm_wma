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

- immediate prior live blob SHA: `8dba26638b67dd35e5c261256785a9e87b19abc1`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 live-plan continuity CPU/static V25 APPROVED TO IMPLEMENT

Formal pair:
- root implementation SHA: `d1a25398d1a5ea563c862c4e6ebbf7f702f1d051`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_live_plan_continuity_cpu_static_v25_d1a2539_93a89ba.md`

Canonical review commit:
`2862a11a6215a59c94432ced4379db8491481319`

Current blockers: `0`; Design/Authority: `0`; Production/implementation: `0`; Evidence/Scope: `0`; child/runtime: `0`.

Approval summary:
- formal root resolves and binds `cosmos-framework` mode `160000` exactly to the declared reachable child;
- V25 is docs-only and authorizes only future pure-memory root implementation plus stdlib tests;
- the contract preserves V24's one live session + one opaque continuation lease + one exact sealed-plan instance binding, exact binding digest, pending quiescence, resume-only identity proof and terminal invalidation;
- pending ordinary resume and direct `consume_once_v05(plan)` are explicitly required to fail closed, so the existing public consume path cannot remain an authority bypass in the implementation;
- approval/resume must accept only the exact live lease plus exact approval identity and pass the same plan object to the existing C path;
- revoke/mismatch/close/exception/loss are terminal and no replacement/reconstruction from the audit record is permitted;
- implementation evidence must directly cover same-instance handoff, foreign lease/plan rejection, pending direct-consume rejection, loss/close terminal behavior and absence of reconstruction input;
- C01-C15, nine-entry freshness domain, remote-pre-C-only, same-object patch handoff, one-call/no-retry, exact readback and hard stop remain inherited requirements.

Scope reminder: this approval authorizes only root CPU/static implementation and stdlib tests of live-plan continuity. It does not authorize real pre-C/C, request-pair writing, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
