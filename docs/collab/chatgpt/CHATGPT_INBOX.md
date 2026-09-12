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

- immediate prior live blob SHA: `da5f8eb9d52a29f74c1a19c768945cc188585471`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Launcher Payload v0.7 Static Closure REQUEST_CHANGES

Formal pair:
- root docs SHA: `bf852c233b2c2e31eb33dc859188a9a4b41c50df`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.7.py:152)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_materialization_execution_request_launcher_v07_bf852c2_93a89ba.md`

Canonical review commit:
`9a7873339da5184deb5a0855bcd17e42c5c7b4aa`

Current blockers: `3 HIGH` (`2 launcher/execution-request production + 1 Gate/Evidence`).

Progress:
- prior `.git/commondir` authority blocker is CLOSED: v0.7 rejects and revalidates `commondir`/`config.worktree` absence;
- prior backing pathname/mode blocker is CLOSED: v0.7 revalidates pathname/reader/target identity and exact `0600` mode;
- child/runtime remains unchanged and the exact Gitlink is valid.

Remaining blockers:
1. exact FD close-set check is wrong: the second `os.listdir('/proc/self/fd')` includes the enumeration directory FD itself, so the raw name-set comparison can reject even when the durable open set is exactly `{3,4,5}`; current helper-only FD witness does not exercise this production seam.
2. after successful `worktree add`, `owned=os.lstat(CLEAN)` is still outside the mutation-boundary protection; if CLEAN disappears/lookup fails before `owned` is assigned, the outer handler skips cleanup and returns an ordinary post-mutation exception instead of verified rollback/`ROLLBACK_INCOMPLETE`.
3. formal request itself says approval is not requested until the full temporary native-Git witness matrix is complete, and annex says those witnesses are mandatory before any materialization verdict. Current 6/6 suite is still helper/classifier-heavy and lacks the required partial/nonzero add, post-route drift, route/config replacement, foreign CLEAN replacement, exact FD enumeration, and real cleanup failure/success causal seams. If this is only a static-closure Gate, freeze a dedicated non-materialization verdict/request; otherwise complete the matrix and submit a new pair explicitly eligible for `APPROVE_TO_MATERIALIZE`.

Exact acceptance is in the canonical review.

Scope reminder: **no materialization is authorized**. No source/checkpoint I/O, JSON/worktree/index/candidate/ref/evidence creation on the real project, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
