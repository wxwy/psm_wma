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

- immediate prior live blob SHA: `4258b19ee4770c82494e9e3cf50fc96b8e3ba14e`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 freshness-guard absence-domain remediation still needs direct drift witness

Formal pair:
- root implementation SHA: `db6c4f93473e7ef58a294cff3fb8c692b100badd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-FRESHNESS-GUARD-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:243)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_freshness_guard_cpu_static_db6c4f9_93a89ba.md`

Canonical review commit:
`f2d2156405da7e82769016e7e55641729e21e7eb`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `0`; Evidence/Scope: `1 HIGH`; child/runtime: `0`.

Positive closure:
- the previous production blocker is closed: the sealed freshness domain is now deterministic and complete with 9 ordered identities: git/config/local-V2, 2 output absences and 4 designated absences;
- absence identities carry synthetic name plus exact path, predicate, byte length and SHA-256; rehearsal requires exact lease-domain equality, so missing/extra/reordered/foreign domain tuples fail pre-C;
- `consume_once_v05(plan)` still accepts no external Closure, STALE/UNKNOWN terminate before apply, and FRESH preserves one-write/readback/hard-stop and terminal no-retry;
- formal root tree binds `cosmos-framework` mode `160000` exactly to the declared reachable child;
- implementation remains pure CPU/static with no real I/O/request/C/child/GPU execution.

HIGH 1 — the new absence-domain test is not a direct causal behavioral witness:
- `test_output_and_designated_absence_identity_are_in_guard_domain` proves the six absence identities are present in `plan.freshness_identities`;
- it then constructs a separate fixture whose fake guard returns constant `STALE`, independently of any output/designated-absence drift;
- therefore it does not prove that an actual simulated absence change after pre-C causes the sealed guard/lease comparison to return STALE before apply;
- it also does not retry the same stale plan and prove `already_consumed` after the freshness failure.

Required remediation:
- make the pure-memory fake guard derive FRESH/STALE from a simulated current local state compared against the sealed lease/domain, not from a free constant;
- after rehearsal, mutate at least one output-absence and one designated-absence simulated current identity (preferably sweep all six), call public `consume_once_v05(plan)`, and prove freshness failure before apply with consumer call count `0`;
- call `consume_once_v05(plan)` again and prove `already_consumed`;
- preserve the current 9-entry exact domain, no-external-Closure ABI, remote-pre-C-only rule, pure-memory scope, and existing terminal outcome/readback tests.

No real pre-C/C, request pair, materialization, source-evidence, real I/O, child mutation, GPU or training is authorized for this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.
