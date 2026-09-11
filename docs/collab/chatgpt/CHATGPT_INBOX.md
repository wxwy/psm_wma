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

- immediate prior live blob SHA: `da7a581a835b2c10c40bc2312c295a5749079292`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Execution Evidence null-record remediation REQUEST_CHANGES

Formal pair:
- root design SHA: `eb658e0b4f7f006a20ba8a7aca9102d5cc64cb15`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:15)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_controlled_execution_design_eb658e0_93a89ba.md`

Canonical review commit:
`a34246ae87d03729369a673c5b74baa03866e041`

Current blockers: `2 HIGH`; Design/Authority `0`; Production `0`; Evidence-only `2`.

Closed / positive:
- collection FAIL null-record is now exact four keys and receipt FAIL null-record is exact five keys;
- the remediation explicitly avoids fabricated source-entry/candidate digests for unreached stages;
- executor implementation/source-identity progression and authority-root materialization/binding remain closed from prior review;
- formal root resolves exactly to the requested reachable child/Gitlink.

Remaining blockers:
1. `execution` is still declared as common exact `{approval_formal_root,command_argv,interpreter}`, while PASS adds `phase` and FAIL adds `phase,failure_code`. Under the same contract's unknown/extra-field rejection, neither branch has one legal exact execution record. Freeze branch-specific exact key sets or one exact common superset with explicit PASS/FAIL null/value rules.
2. Stage-aware FAIL encoding remains incomplete/internally inconsistent: the common rules require nonempty `source_entries`, 64-hex SHA fields and boolean values, while early FAIL permits empty source entries and null handoff/candidate fields. Failures before environment/authority/lineage/source-read also lack deterministic null/SKIPPED representations for all downstream nested records. Freeze exact per-stage null/SKIPPED semantics (or a fixed PASS/FAIL/SKIPPED checks array), explicitly override common type/cardinality rules on FAIL, and forbid placeholder digests/booleans.

Still not authorized: executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
