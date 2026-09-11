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

- immediate prior live blob SHA: `e334e09013c637564ac6c7e24adb9ec94b4f4794`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Publication Freeze Design two-phase remediation APPROVED

Formal pair:
- root design SHA: `c6be81ef0b9b9937987c53bb84524131019b5d9a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-ROOT-PUBLICATION-FREEZE-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_ROOT_PUBLICATION_FREEZE`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_root_publication_freeze_design_c6be81e_93a89ba.md`

Canonical review commit:
`e83fc8c88e3823fd2b2df3a4b89cfde0b0edc079`

Current blockers: `0`.

Closure:
- the prior Section 6 unconditional zero-mutation HIGH is closed;
- Section 6 now binds Section 3's exact two-phase failure semantics: pre-live zero mutation; post-live snapshot rollback plus restoration verification for ordinary failure; incomplete/uncertain rollback is `ROLLBACK_INCOMPLETE`, preserves evidence, blocks authority/audit/runtime progression and automatic retry, and does not claim zero mutation;
- no failure may create accepted publication authority or proceed to read-only source audit;
- formal root resolves exactly to the requested reachable child/Gitlink, and child is unchanged.

Authorized next action only: the next independent docs-only source-evidence producer/closure design in the frozen Gate sequence.

Still not authorized: publication creation/write/materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
