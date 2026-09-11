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

- immediate prior live blob SHA: `39fe2824b7ea6d3b5c555fa63632d68e01df041c`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Publication Freeze Design remediation REQUEST_CHANGES

Formal pair:
- root design SHA: `de81c294019647e7678ef3f8da484c8d5bdbdba7`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-ROOT-PUBLICATION-FREEZE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_root_publication_freeze_design_v0.1.md:127)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_root_publication_freeze_design_de81c29_93a89ba.md`

Canonical review commit:
`1590b3a30700521fda410650e039044313af25e9`

Current blockers: `1 HIGH`: Design/Transaction `1`; Production `0`; Evidence-only `0`.

Closed from prior review:
- input-package/witness authority is now frozen in substance: exact source-evidence record/path, seven-key package, seven-key witness, digest relationships, anti-caller-selection rule and mandatory source-evidence closure ordering are present;
- child Gitlink is now only a non-authoritative index mutation guard; post-commit source audit receives the formal root and derives the child Gitlink from its tree;
- Section 3 now has isolated preflight plus a live transaction snapshot/rollback/`ROLLBACK_INCOMPLETE` fail-stop model.

Required remediation:
1. Section 6 item 4 still says all failures require zero `target/index/commit/authority` mutation. That contradicts Section 3, which correctly allows fallible live mutation followed by exact rollback and explicitly says `ROLLBACK_INCOMPLETE` must not claim zero mutation.
2. Make Section 6 bind the same two-phase contract as Section 3: pre-live failures are zero-mutation; post-live failures must rollback and verify restoration; incomplete/uncertain rollback is `ROLLBACK_INCOMPLETE`, preserves evidence, blocks authority/audit/runtime and automatic retry, and does not claim zero mutation; only a successful live commit may progress to source audit.

Still not authorized: publication creation/write, real root source-audit execution, production `root_gitlink_authority_v1` creation/consumption, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
