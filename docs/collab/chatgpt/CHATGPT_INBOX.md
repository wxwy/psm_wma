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

- immediate prior live blob SHA: `3ae708ae9cde6efc960e2332fec8330ab593feff`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Launcher v0.8 Static Witness Closure REQUEST_CHANGES

Formal pair:
- root docs SHA: `5ff4df58cc8e17644aab945de3de6d74b8b2967c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py:90)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_execution_witness_closure_v08_5ff4df5_93a89ba.md`

Canonical review commit:
`913f73bc297974b30607d9aa85e548da97a972a2`

Current blockers: `1 HIGH`.

Progress:
- v0.7 FD enumeration blocker is CLOSED: v0.8 derives durable FDs by post-listing `fstat` and directly witnesses `close_to_keep({3,4,5})` in a forked child with an injected extra FD;
- the v0.7 Gate/Evidence mismatch is largely CLOSED: v0.8 now explicitly requests only `APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_WITNESS_CLOSURE`, not materialization, and adds direct temporary native-Git/payload witnesses;
- Gitlink is exact and child/runtime is unchanged.

Remaining HIGH:
- after a successful native `worktree add`, `capture_owned()` still binds whatever directory occupies `CLEAN` at its first observation; the code has no identity causally anchored to the inode actually created by the Git mutation. A replacement in the add→capture gap can therefore become the provisional owner, and a sufficiently Git-valid foreign replacement can satisfy later HEAD/status/worktree-list checks. This does not meet the prior exact acceptance that post-add replacement must never become accepted owner authority.
- current witnesses cover missing CLEAN, foreign replacement after ownership capture, nonzero add and post-add `commondir` drift, but not successful add followed by foreign CLEAN replacement before the first ownership bind.

Acceptance: causally anchor accepted CLEAN ownership to the exact add-created object (or fail `ROLLBACK_INCOMPLETE` if continuity cannot be proved), and add a direct temporary native-Git witness that injects a sufficiently Git-valid CLEAN replacement in the successful-add→capture interval and proves it is never accepted or force-removed.

Scope reminder: **this is static-witness/PREPARE closure only; no materialization is authorized**. No source/checkpoint I/O, worktree/backing/index/candidate/ref/evidence creation on project paths, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.