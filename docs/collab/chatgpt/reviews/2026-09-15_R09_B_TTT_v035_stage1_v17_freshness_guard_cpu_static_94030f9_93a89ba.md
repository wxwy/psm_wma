# ChatGPT independent review — Stage-1 v1.7 freshness-guard CPU/static

Formal pair:
- root: `94030f90cc4de2d5b2c1dd60a412fb10768d71f9`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-FRESHNESS-GUARD-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:452)`

Blockers: `1 HIGH`.
- Design/Authority: 0
- Production/implementation: 1 HIGH
- Evidence/Scope: 0
- child/runtime: 0

## Positive closure

- Formal root resolves and binds `cosmos-framework` mode `160000` exactly to the declared child; child resolves independently.
- `FreshnessGuardV1` / `FreshnessLeaseV1` are sealed and non-copyable/non-serializable.
- `consume_once_v05(plan)` removes the prior externally reconstructed `ClosureV1` ABI.
- Guard `STALE`/`UNKNOWN` fail before consumer apply; FRESH retains exactly one opaque apply, byte-exact readback and terminal no-retry.
- Scope remains pure CPU/static; no real guard/consumer/Git/network/source/data/cache/child/GPU path is introduced.

## HIGH 1 — freshness lease comparison domain omits required local absence records

Controlling V21 design requires the pre-C-bound lease comparison domain to cover all mutable local records: `.git`/config/local-V2 **and designated local absence/output absence**. It explicitly requires the lease comparison domain to equal the C995 local mutable records, with omissions or extras failing pre-C.

The implementation at `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:452` constructs `local` from only:
- `closure.git_identity`
- `closure.config_raw`
- `closure.local_v2_raw`

`lease_domain` is derived only from those three raw facts. `closure.output_absences` and `closure.designated_absences` are not represented in the sealed freshness identities/lease domain. Therefore a local output/designated path can drift after pre-C without any identity for that drift reaching `guard_opaque_v1(...)`; the guard cannot prove the V21-required freshness boundary before apply.

The current 11/11 suite likewise proves STALE/UNKNOWN behavior only for the fake guard result and does not directly prove output/designated-absence drift is present in the lease comparison domain and rejected before apply.

### Acceptance

- Extend the sealed lease comparison domain to include exact typed identities for every V21 mutable-local class: `.git`/config/local-V2, exact output absences, and all designated local absences, with deterministic ordering and no extra/missing entries.
- Preserve paths/predicates plus raw identity needed to distinguish those absence observations; a bare `(name,length,SHA)` tuple is insufficient unless its name uniquely and exactly binds the frozen path/predicate semantics.
- Add direct CPU/static negative witnesses for output-absence and designated-absence drift after pre-C: guard must return/trigger STALE before `apply_opaque_v1`, consumer call count must remain zero, and the retired plan must remain terminal/no-retry.
- Preserve the no-external-Closure ABI, remote-pre-C-only rule, exact consumer/readback sequence, pure-memory scope and all already-closed ContractV05 constraints.

No real pre-C/C, request pair, materialization, source-evidence, real I/O, child mutation, GPU or training is authorized by this review.
