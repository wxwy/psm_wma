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

- immediate prior live blob SHA: `b632a2dac4aadd961679f3120de3204b36f85502`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Source-Evidence closure stage-split design refreeze v0.3 APPROVED

Formal pair:
- root design SHA: `5a668ad8871798a0c252ce9c05dbf167c36ba839`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN-REFREEZE`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT_MATERIALIZATION_REQUEST`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_source_evidence_closure_stage_split_design_refreeze_v03_5a668ad_93a89ba.md`

Canonical review commit:
`e7480c0eee3cc9012ca2a8ec38b7aa53015b1f5b`

Current blockers: `0`; Design/Authority blockers: `0`; production blockers: `0`; evidence-only blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The prior v0.9 HIGH on the unreviewed intermediate execution stage is closed at design level. v0.3 explicitly supersedes only v0.2 §3 activation granularity and freezes two independently reviewed stages: Stage 1 authority-root materialization, then Stage 2 source-evidence closure.
2. Stage 1 must hard-stop after producing the authority tuple. Its review/ledger commit cannot become candidate parent and cannot be treated as a Stage-2 receipt.
3. Stage 2 cannot be constructed until the Stage-1 tuple is independently bound and the missing producer/record/receipt/publication/root-audit production entrypoints are independently implemented/reviewed/closed.
4. Stage 2 retains v0.2 `collection -> producer -> receipt root -> root audit` ordering and hard-stop at independent receipt-root review.
5. The prior v0.9 exact-instance binding omission is now frozen as a Stage-1 design requirement: same-round selection/config raw+FD identity, complete outer launcher argv, sanitized environment, bootstrap contract/owner FD, tool closure, Git/Python identity, cwd/index/evidence identity, dual-end ref-absent observation, and canonical whole-request SHA.
6. Missing/stale/drifted fields or non-absent ref must yield `BLOCKED_AUTHORITY_NOT_CLOSED` with zero mutation.

Exact next allowed action: construct and independently review one fully fresh-bound Stage-1 authority-root materialization request satisfying v0.3 §2. This approval does **not** authorize its execution.

Scope reminder: no real materialization/source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/source-evidence/publication mutation, Stage-2 request construction/execution, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
