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

- immediate prior live blob SHA: `44cad4148e22eef8120423ec9b2f99a919eeb531`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Materialization Execution Request Design REQUEST_CHANGES

Formal pair:
- root design SHA: `1eb08dea015c1c3c64d504d96a52f02de4665dbd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_design_v0.1.md:13)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_materialization_execution_request_design_1eb08de_93a89ba.md`

Canonical review commit:
`b59ceb27c1906662a3a4ed7fd986e8e22e0cfb89`

Current blockers: `2 HIGH`.

Required remediation:

1. **Do not insert an intermediate request-design Gate.** The approved real-adapter v0.1 contract froze a two-stage route: close the adapter, then immediately submit the exact one-shot execution request for `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`. Current §1 adds another review layer before that exact request and is not authorized by v0.1/D024. Submit the actual one-shot request with all concrete values instead; changing the route requires an explicit higher-authority refreeze/supersession.

2. **Bind source identity before any project import.** The proposed bootstrap adds the mutable worktree to `sys.path` and imports the adapter before the adapter preflight checks formal-tree source identity. The adapter/authority modules transitively import `immutable_source_collection.py` and `tools.g0.audit_r09_b_ttt_root_gitlink_authority.py`, neither of which is frozen by §2 before import. The exact one-shot bootstrap must use only stdlib before project import and execution-time prove the approved formal-root source identity for the full transitive import closure (or an equivalently strong exact controlled-worktree proof that rejects tracked/untracked/shadowing/mode/type drift). Add an adversarial witness where a transitive dependency drifts while the two currently-frozen modules remain unchanged and prove rejection before project code executes.

Formal root/Gitlink was independently verified; child commit is reachable. The closed `ad9e011...` CPU/static production pair itself is not reopened by this docs-only review.

Scope reminder: this verdict does not authorize materialization, real source/checkpoint I/O, candidate/ref/evidence mutation, collection/receipt, publication/root audit, child/runtime changes, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.