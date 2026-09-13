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

- immediate prior live blob SHA: `3c216e4273fa4de1c133cb744a7affb027035b6d`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Causal Owner Identity Execution Design v0.3 REQUEST_CHANGES

Formal pair:
- root docs SHA: `781824f4ed2682b1347126a58f645ef0702117bd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.3.md:71)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_execution_design_v03_781824f_93a89ba.md`

Canonical review commit:
`8cec96a99b820d4dd7ee8088eca98e8a1ab3e487`

Current blockers: `2 HIGH` (`2 design/authority`, `0 child/runtime`).

Progress:
- prior FD-collision blocker is CLOSED: v0.3 reserves FD3--9, fixes `clean_owner_fd=9`, freezes source-open→rebind→fstat→source-close chronology, and keeps FD9 stable across backing/Git/bootstrap operations;
- v0.3 correctly refreezes final child `--cwd`, `--index`, `--bootstrap-project-root`, and `--bootstrap-owner-root-fd` to FD8/procfd bytes and explicitly places root adapter changes in the next implementation scope;
- exact Gitlink is valid and child/runtime remains unchanged.

Remaining blockers:
1. **FD8 descendant inheritance is not frozen through the actual Git consumer.** `NativeAuthorityGit` uses `GIT_INDEX_FILE=/proc/self/fd/8/.authority-root.index` but current Git subprocess calls have no `pass_fds` contract; bootstrap Git probes likewise have no descendant FD8 contract. Freeze exact post-exec subprocess inheritance/identity checks so every consumer of an FD8-derived path retains FD8, without leaking backing FDs, and witness an actual Git operation after global CLEAN replacement.
2. **The existing bootstrap/adapter route checks still canonicalize procfd paths to global paths.** Current bootstrap payload contains `realpath(path)==path` guards that reject FD8-rooted module paths, while `_verify_loaded_identity()` and `NativeAuthorityGit` configuration checks use `Path.resolve()`. Freeze procfd-safe replacements that preserve anti-symlink/module/route/config identity without global CLEAN reconstruction, and add direct rename/replacement witnesses.

Exact acceptance and prior-blocker disposition are in the canonical review.

Scope reminder: **no CPU/static implementation is authorized from this pair**. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
