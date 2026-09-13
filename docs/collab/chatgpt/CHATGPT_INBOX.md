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

- immediate prior live blob SHA: `05818ae26c4540d6499e4e597e2f518ff00ac0cf`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Causal Owner Identity CPU/static Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `c8aafca005ff061788114281e47fd1a4e2b6a843`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:1614)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_cpu_static_remediation_c8aafca_93a89ba.md`

Canonical review commit:
`5070757d1fddd581121f73f86905caa840b38210`

Current blockers: `2 HIGH` (`2 production/authority`, `0 Evidence-only`, `0 child/runtime`).

Prior blocker disposition:
- prior HIGH-2 (bootstrap project modules lacked FD8 component-level no-follow closure): **CLOSED**;
- prior HIGH-3 (procfd resolve/content-only loaded-module identity): **CLOSED**;
- prior HIGH-1 (exact FD8 admission): **materially improved but still blocking**.

Remaining blockers:
1. **Production `NativeAuthorityGit` still admits `owner_fd=None`.** The exact `production && owner_fd==8` check remains nested inside `if owner_fd is not None`, so `NativeAuthorityGit(..., production=True, owner_fd=None)` creates a second legacy pathname authority route with no owner barrier or FD8 `pass_fds`. Move the production FD8 requirement outside the optional branch and directly witness `None`, non-8, mismatched cwd, and mismatched index rejection before Git/config/module consumption.
2. **Import-free bootstrap `grun()` lacks the frozen per-consumer owner/index barrier.** It now uses exact `close_fds=True, pass_fds=(8,)`, but still does only `routecheck()` → Git subprocess → `routecheck()`. v0.4 §3.2 requires live FD8 owner identity plus FD8-relative no-follow `.authority-root.index` / required-path identity revalidation before and after every bootstrap Git consumer. Add that barrier and a direct bootstrap changed-index/owner-drift witness.

Positive remediation: exact parser/bootstrap FD8 argv is now mandatory, bootstrap project-module closure uses FD8-started component-by-component no-follow traversal, `_bootstrap_identity_from_runtime()` no longer resolves owner procfd fields, and loaded adapter/authority objects are checked against FD8-relative `(dev, ino)` identity.

Scope reminder: no Gate closure is authorized from this pair. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
