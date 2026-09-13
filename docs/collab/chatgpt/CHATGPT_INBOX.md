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

- immediate prior live blob SHA: `ab1f1c7d8f9bf536624d2e73abfe3a1be78bb9c9`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Causal Owner Identity CPU/static Implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `5a2a3207853cdbbe4dc8135080cd5fe5050b7787`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:1747)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_cpu_static_implementation_5a2a320_93a89ba.md`

Canonical review commit:
`156a1bdebdb131a88558def0ccf59087635cfa23`

Current blockers: `3 HIGH` (`3 production/authority`, `0 Evidence-only`, `0 child/runtime`).

Key findings:
1. **Exact FD8 admission remains fail-open.** `--bootstrap-owner-root-fd` is optional in both bootstrap and argparse and `NativeAuthorityGit` accepts arbitrary owner-FD numbers. Frozen v0.4 requires mandatory exact FD8 and exact procfd cwd/index/root; missing/non-8 owner must fail closed rather than enter the legacy pathname route.
2. **Import-free bootstrap still lacks component-level no-follow owner traversal.** The project-module loop builds `/proc/self/fd/8/...` pathname strings, then uses leaf `lstat/open`; it does not use the v0.4-required FD8-rooted component-by-component `dir_fd + O_NOFOLLOW` primitive. The helper test does not prove the actual bootstrap path against an intermediate-component symlink.
3. **Adapter procfd/loaded-module closure remains incomplete.** `_bootstrap_identity_from_runtime()` still calls `Path.resolve()` on FD8-derived project-root/cwd, and `_verify_loaded_identity()` only compares loaded-module bytes rather than proving `__file__` / authority module belong to the FD8 owner tree. Same-bytes foreign modules can satisfy the current check.

Positive progress: FD8 Git consumer `pass_fds`/pre-post index barriers and an actual temporary Git procfd-index witness are materially implemented. The remaining blockers are production source violations, so `62/62` tests do not make this Evidence-only.

Exact acceptance and detailed authority reasoning are in the canonical review.

Scope reminder: no Gate closure is authorized from this pair. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
