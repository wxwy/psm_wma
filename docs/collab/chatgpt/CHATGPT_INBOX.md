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

- immediate prior live blob SHA: `aad85b8046d52f9d425df0158fefb1d04e401745`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Causal Owner Identity Execution Design v0.1 Remediation REQUEST_CHANGES

Formal pair:
- root docs SHA: `64b706b7b97451fd90cb6e9292100e512952f28a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md:27)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_execution_design_v01_64b706b_93a89ba.md`

Canonical review commit:
`68c0666cec3f407f87a86167fcfbc64f44256595`

Current blockers: `2 HIGH` (`2 design/authority`, `0 child/runtime`).

Progress:
- prior private-parent/frozen-path HIGH is CLOSED: the remediation now preserves frozen `ROOT=/disk/rl/psm_wma`, CLEAN `/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8`, and unchanged `--cwd` / `--index` / `--bootstrap-project-root` bytes;
- backing-file handoff is materially improved: create/open/readback is now intended to stay relative to retained `clean_fd`;
- exact Gitlink remains valid and child/runtime is unchanged.

Remaining blockers:
1. **Owner FD lifecycle is not a single frozen contract.** Step 1 establishes `root_fd`; step 2/4/cleanup revert to stale `parent_fd`; step 3 makes `root_fd` fixed FD 6; the matrix later says `root_fd=6` closes after Git while simultaneously requiring `root_fd` for every later handoff/exec admission. Freeze a long-lived root authority vs temporary FD-6 alias explicitly, exact duplication/inheritance/CLOEXEC/close chronology, clean-FD lifetime, and correct cleanup of the CLEAN child only. Project `ROOT` must never be treated as an empty disposable parent.
2. **Causal owner continuity still stops before the actual exec/bootstrap consumer.** Final exact `{3,4,5}` proof requires owner FDs to be closed, while inherited bootstrap continues to resolve the absolute CLEAN root/module path after `execve`. A replacement after the last pre-exec check can therefore redirect bootstrap. Refreeze an owner capability that survives into bootstrap (or an equivalent immutable handle), exact FD/argv/bootstrap contract and hashes, with no absolute-path fallback; add a temporary CPU/static causal witness that replaces CLEAN after the last pre-exec check but before bootstrap/module lookup and proves foreign code cannot be consumed.

Exact acceptance and blocker lifecycle are in the canonical review.

Scope reminder: **no CPU/static implementation is authorized from this pair**. No real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication/root audit, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
