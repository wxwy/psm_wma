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

- immediate prior live blob SHA: `40d65bfd181e1144f6306664283b649ad7ee96b3`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Causal Owner Identity Execution Design v0.2 REQUEST_CHANGES

Formal pair:
- root docs SHA: `de1d12f194030067a4afa656379378713b151734`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.2.md:36)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_execution_design_v02_de1d12f_93a89ba.md`

Canonical review commit:
`1529f8e6cf8f54001c97d267eb48b3bb3347ad64`

Current blockers: `2 HIGH` (`2 design/authority`, `0 child/runtime`).

Progress:
- v0.2 correctly separates long-lived `root_authority_fd=7` from Git-only `git_root_fd=6`, removes stale `parent_fd`, and constrains cleanup to the owned CLEAN entry;
- inheriting `bootstrap_clean_fd=8` and using `/proc/self/fd/8` as the bootstrap root is the correct direction and materially improves the prior exec/bootstrap continuity problem;
- exact Gitlink is valid and child/runtime is unchanged.

Remaining blockers:
1. **`clean_owner_fd` is still not collision-safe.** It is left as an unconstrained ordinary FD while the frozen backing ABI targets `3/4/5`, Git requires `dup2(7,6)`, and bootstrap requires `dup2(clean_owner_fd,8)`. A low-number allocation can therefore destroy or alias the only held CLEAN owner capability. Freeze a collision-free owner-FD allocation/rebind contract outside `{3,4,5,6,7,8}`, exact identity/CLOEXEC/close chronology, and direct low-FD/adversarial-FD witnesses.
2. **FD8 only anchors bootstrap loading; the existing adapter still consumes CLEAN-derived `--cwd` / `--index` after exec.** v0.2 explicitly supersedes the old bootstrap-project-root field but does not freeze child-visible procfd replacements for every affected path-bearing argv field, nor authorize/refreeze an adapter ABI change. The frozen adapter requires `--cwd`, `--index`, and `--bootstrap-project-root`, validates cwd/root identity, and constructs `NativeAuthorityGit` from those paths. Refreeze all CLEAN-derived post-exec fields to FD8/procfd semantics (or explicitly refreeze adapter source/ABI), freeze the complete child argv/digest, and extend the final-seam fixture through the actual bootstrap→adapter transaction boundary.

Exact acceptance and prior-blocker disposition are in the canonical review.

Scope reminder: **no CPU/static implementation is authorized from this pair**. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
