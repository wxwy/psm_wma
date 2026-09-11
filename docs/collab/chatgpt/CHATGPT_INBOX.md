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

- immediate prior live blob SHA: `0f7e0ca7e0af204fc23e5b4a764c710b3d18a3c5`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Publication Freeze Design REQUEST_CHANGES

Formal pair:
- root design SHA: `dc11da59495f41cea58ccf17225469fcf6183452`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-ROOT-PUBLICATION-FREEZE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_root_publication_freeze_design_v0.1.md:23)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_root_publication_freeze_design_dc11da5_93a89ba.md`

Canonical review commit:
`25ae9c28be23adac2f8607e3c46c79d5134632bf`

Current blockers: `3 HIGH`: Design/Authority `3`; Production `0`; Evidence-only `0`.

Positive findings:
- formal root resolves exactly to the requested reachable child/Gitlink and remains docs-only for this Gate;
- unique publication path and inherited v0.3 three-key publication / nested config/source schemas are retained;
- the design correctly separates publication writing from later formal-root source audit and keeps real checkpoint/data/cache I/O, GPU and training out of scope.

Required remediation:
1. Freeze an exact machine-readable publication-input witness contract and authority provenance. The design currently says the input package has only two nested objects but also compares against `expected_witness` without freezing its schema, digest relationships, immutable source-evidence binding or anti-caller-selection rule. Add the independent source-evidence producer/closure Gate explicitly before real materialization.
2. Do not pass or record an expected child revision as authoritative future audit invocation input. Any pre-commit index Gitlink observation is only a non-authoritative mutation guard; the post-commit audit must derive child revision solely from the locked formal root tree Gitlink, using child-git-dir only as object transport.
3. Resolve the transaction contradiction between staging/writing then validating the index blob and the stated zero target/index mutation on every pre-commit validation failure. Freeze isolated temporary-state validation before live mutation, or an exact snapshot/rollback/post-failure equivalence protocol with explicit mutation boundary.

Still not authorized: publication creation/write, real root source-audit execution, production `root_gitlink_authority_v1` creation/consumption, runtime integration, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
