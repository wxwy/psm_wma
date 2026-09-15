# ChatGPT independent review — Stage-1 v1.7 live-plan continuity CPU/static V25

Formal pair:
- root: `d1a25398d1a5ea563c862c4e6ebbf7f702f1d051`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC`

Blockers: `0`.

## Independent findings

- The formal root resolves and its tree binds `cosmos-framework` as mode `160000`, type `commit`, exactly to the declared child SHA; the child commit is independently resolvable.
- The root change is docs-only. It does not execute or authorize real pre-C/C, request-pair writing, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
- V25 correctly narrows the future implementation to the existing pure-memory pre-C module and stdlib tests.
- Its minimum contract carries forward V24's same-instance continuity model: one `LivePlanSessionV1`, one opaque continuation lease, one live sealed plan, immutable token/binding digest, pending quiescence, resume-only exact-identity verification, terminal invalidation on revoke/mismatch/close/exception, and no reconstruction from the audit record.
- Crucially, pending-state direct `consume_once_v05(plan)` / ordinary resume is required to fail closed, so the future implementation cannot leave the already-public direct-consume path as an authority bypass.
- The requested tests cover same-instance handoff, foreign lease/plan rejection, pending direct-consume rejection, loss/close terminal behavior, and absence of reconstruction inputs.

## Implementation-review acceptance focus

The next implementation review must verify behavior, not only the presence of new types:
1. a session-owned pending plan cannot reach `consume_once_v05` through the existing public path;
2. approval/resume accepts only the exact live lease plus exact approval identity and hands the same plan object to C;
3. foreign/replaced plan or lease, copy/serialize/rebind, close/revoke/loss, or binding mismatch permanently invalidates the session with no replacement/reconstruction path;
4. the pure-memory implementation introduces no real host capability or real I/O and does not weaken C01-C15, the nine-entry freshness domain, remote-pre-C-only, same-object patch handoff, one-call/no-retry, exact readback, or hard stop.

Scope reminder: this approval authorizes only root CPU/static implementation and stdlib tests for live-plan continuity. It does not authorize real pre-C/C or any downstream execution.
