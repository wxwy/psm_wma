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

- immediate prior live blob SHA: `b7dfdffce4727fa2c9ca42f4b33a8e1feb6bec87`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Launcher Payload v0.6 REQUEST_CHANGES

Formal pair:
- root docs SHA: `80132197c29bd139e3e05ce6deb3cbcf8f525de6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.6.py:131)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_materialization_execution_request_launcher_v06_8013219_93a89ba.md`

Canonical review commit:
`5cfbb337ce4db74f29cc8c08d63489ccc3347cf2`

Current blockers: `4 HIGH` (`3 launcher semantics + 1 Evidence-only`).

Progress:
- prior v0.5 HIGH-1 is CLOSED: selection/config/actual-argv authority is embedded and no longer falsely requires historical annex paths under `9dd2fb8...`;
- same-FD handoff and post-add checks are materially improved;
- formal pair/Gitlink is valid, child reachable, and child/runtime remains unchanged.

Remaining blockers:
1. `worktree add` can mutate and then fail/nonzero or fail the immediate post-route check before `owned` is assigned; the outer handler skips cleanup and can return ordinary failure instead of verified rollback/`ROLLBACK_INCOMPLETE`.
2. ordinary parent `.git` routing still never rejects/binds `.git/commondir`; common-dir authority can therefore change outside the retained `.git/config` snapshot.
3. FD handoff still lacks final backing pathname identity and exact `0600` mode proof; a same-bytes pathname replacement after reader-open is not rejected.
4. annex v0.6 requires causal witnesses for extra inherited FD, route/config replacement, post-add drift, foreign clean-root replacement, cleanup failure and successful cleanup; current pair supplies only same/different-FD temporary handoff plus static checks.

Exact acceptance is in the canonical review.

Scope reminder: **no materialization is authorized**. No source/checkpoint I/O, JSON/worktree/index/candidate/ref/evidence creation, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
