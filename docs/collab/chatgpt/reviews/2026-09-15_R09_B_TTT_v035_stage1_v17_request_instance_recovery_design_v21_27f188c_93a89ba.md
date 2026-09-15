# ChatGPT Formal Review — Stage-1 v1.7 request-instance recovery design V21

Formal pair:
- root: `27f188c6cd13db2e257dc2951b0b744b2ff3dd64`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V21`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_FRESHNESS_GUARD_CPU_STATIC`

Blockers: `0`.

## Findings

V21 closes the V20 C-time freshness atomicity blocker without widening execution authority.

- `rehearse_v05()` remains the only provenance/query/discovery phase.
- A single host-owned, non-copyable/non-serializable `FreshnessGuardV1` plus opaque `FreshnessLeaseV1` is frozen pre-C with exact provider/module/path/blob/callable/ABI/transport identity.
- Immutable ContractV05 facts remain sealed-only; mutable local `.git`/config/local-V2 and designated/output absences are represented by pre-C-bound lease handles/predicates/identities; remote V2 and authority-ref queries are explicitly pre-C-only; post-write pair paths/bytes are sealed before C.
- The future production ABI removes arbitrary `current_closure` input and permits only `consume_once_v05(plan)`.
- C is frozen as guard check -> exactly one opaque consumer call -> exact byte readback -> hard stop. `STALE`/`UNKNOWN`/guard exception are terminal before consumer; all call/post-call failures remain terminal and no-retry.
- Planned CPU/static direct evidence is sufficient for the next implementation Gate: lease/domain/capability drift pre-consumer fail-close, old ABI rejection, no C-time query/reconstruction, remote-query non-use in C, exactly-once success and terminal failure behavior.

Formal root tree binds `cosmos-framework` mode `160000` exactly to the declared child, and the child resolves.

## Scope

This approval authorizes only the root CPU/static freshness-guard implementation and stdlib evidence described by V21. It does not authorize real freshness guard I/O, real pre-C/C, request-pair construction, materialization, source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
