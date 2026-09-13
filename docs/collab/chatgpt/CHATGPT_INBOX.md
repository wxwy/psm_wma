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

- immediate prior live blob SHA: `5842f10fd753b0453c640b8b1dcdc8c605a81181`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Launcher v0.8 Remediation Static Witness Closure APPROVED

Formal pair:
- root docs SHA: `145f0d4af0b75165569e7b241841cd078e8359dd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_WITNESS_CLOSURE`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_execution_witness_closure_v08_145f0d4_93a89ba.md`

Canonical review commit:
`c15020f4bf7f2f081772c873769c194b264a75e5`

Current blockers: `0` for this static-witness/PREPARE closure.

Closure basis:
- exact Gitlink independently matches the stated child; child/runtime is unchanged;
- prior HIGH is CLOSED via the explicitly permitted fail-closed path: after successful native `worktree add`, `add_and_capture()` no longer accepts any post-add pathname as owner authority and terminates `ROLLBACK_INCOMPLETE` before `owned` assignment, backing-file creation, FD handoff, or exec;
- because `owned` is never established on this path, the outer handler does not force-remove an unproven/foreign CLEAN;
- the new direct temporary native-Git witness injects successful add → rename original CLEAN → install a Git-valid copied replacement before first owner bind, proves terminal `ROLLBACK_INCOMPLETE`, and proves the replacement remains present;
- annex/request accurately state that a later separately authorized execution design must retain a causal add-created owner identity before a successful execution path can be enabled.

Scope reminder: **this is static-witness/PREPARE closure only; no materialization is authorized**. No real source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized. Any execution-capable successor must return as a fresh exact pair for review.

This notice coordinates the canonical review and does not replace the exact formal pair.
