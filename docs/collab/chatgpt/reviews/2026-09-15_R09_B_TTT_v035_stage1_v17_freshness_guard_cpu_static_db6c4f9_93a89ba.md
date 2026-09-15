# ChatGPT formal review — Stage-1 v1.7 freshness-guard CPU/static remediation

Formal pair:
- root: `db6c4f93473e7ef58a294cff3fb8c692b100badd`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-FRESHNESS-GUARD-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:243)`

Blockers:
- Design/Authority: 0
- Production/implementation: 0
- Evidence/Scope: 1 HIGH
- child/runtime: 0

## Positive closure

The previous production blocker is closed. `rehearse_v05()` now creates a deterministic nine-entry freshness lease domain: git identity, config, local V2, both output absences, and all four designated absences. Absence entries carry ordered synthetic name plus exact path, predicate, byte length and SHA-256; the injected `FreshnessLeaseV1._domain` must equal the computed tuple exactly, so missing/extra/reordered/foreign domain entries fail pre-C. The C ABI remains `consume_once_v05(plan)` with no external `ClosureV1`; guard STALE/UNKNOWN still terminates before apply; one-write/readback/hard-stop and terminal no-retry remain intact. Formal root tree binds `cosmos-framework` mode 160000 exactly to the declared child.

## HIGH 1 — direct causal evidence for absence drift is still missing

Location: `tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:243` (`test_output_and_designated_absence_identity_are_in_guard_domain`).

Root cause:
- the test proves the six absence identities are present in `plan.freshness_identities`;
- it then creates a separate fixture with `freshness="STALE"`, whose fake guard returns the constant configured outcome independently of any output/designated-absence drift;
- no output-absence or designated-absence live state/lease comparison is actually changed after pre-C and causally mapped to STALE;
- after the STALE failure the test does not perform a second `consume_once_v05(stale_plan)` and assert `already_consumed`.

Contract/evidence violation:
V21 and the prior ChatGPT acceptance require direct CPU/static evidence that mutable-local absence drift is detected by the sealed freshness mechanism before `apply_opaque_v1`, with consumer call count zero and terminal/no-retry behavior. Membership of an identity in the domain plus an unrelated constant-STALE fixture is not that behavioral witness.

Acceptance criterion:
1. Build a fake freshness guard/live-state seam that derives `FRESH` vs `STALE` from the sealed lease/domain comparison, not from a free constant.
2. For at least one output absence and one designated absence (preferably sweep all six), mutate the simulated current absence identity after rehearsal while keeping the sealed plan unchanged.
3. Invoke public `consume_once_v05(plan)` and prove it raises freshness before apply, with consumer call count exactly 0.
4. Invoke `consume_once_v05(plan)` again and prove `already_consumed`.
5. Preserve the current nine-entry exact domain, no-external-Closure ABI, remote-pre-C-only rule, pure-memory hard scope, and all existing terminal result/readback tests.

No real pre-C/C, request pair, materialization, source-evidence, real I/O, child mutation, GPU or training is authorized for this pair.
