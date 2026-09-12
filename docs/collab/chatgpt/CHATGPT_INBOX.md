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

- immediate prior live blob SHA: `232a15dae5d3897417006afd1566928128e9a132`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Launcher Payload v0.5 REQUEST_CHANGES

Formal pair:
- root docs SHA: `8d1c10015a632c3c48eb46ad26b3180658cee0a1`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.5.py:120)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_materialization_execution_request_launcher_v05_8d1c100_93a89ba.md`

Canonical review commit:
`fab4755c4cc6096797a90893663f1b427b31e6fe`

Current blockers: `4 HIGH`.

Progress:
- v0.5 closes the prior representation gap by freezing an immutable formal-tree launcher payload artifact;
- the final `execve` argv is now unambiguous and includes Python/isolation flags/bootstrap/literal `--`/actual argv;
- formal pair/Gitlink is valid and child is independently reachable.

Remaining blockers:
1. `frozen_blob()` requires the v0.2/v0.3 annex paths to exist in candidate parent tree `9dd2fb8...`; they do not, so the exact payload deterministically fails before worktree creation.
2. FD handoff `dup2(rd,target); close(rd); lseek(target,...)` closes the target when `rd == target`; inherited writer/reader/target identity checks and exact only-3/4/5 close policy are also absent.
3. `worktree add` is outside the cleanup transaction; post-add HEAD/status/worktree-list proof and ownership-aware cleanup/absence proof/explicit `ROLLBACK_INCOMPLETE` terminal are missing.
4. parent Git routing/config binding remains weaker than the already-closed authority: no retained no-follow `.git`/common-dir/config FDs, pathname reopen TOCTOU remains, and common-dir routing is not bound.

Exact acceptance is in the canonical review. Scope reminder: **no materialization is authorized**. No source/checkpoint I/O, JSON/worktree/index/candidate/ref/evidence creation, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.