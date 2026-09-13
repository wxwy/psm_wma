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

- immediate prior live blob SHA: `a334f66a268870032207a5df69a5504c1fc7f2d9`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Causal Owner Identity CPU/static Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `e88a9a9dd989e6a00e74d51ee9848b8ad241caa1`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:341)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_cpu_static_remediation_e88a9a9_93a89ba.md`

Canonical review commit:
`091d7261cda3e4115cf34cdcf21adde6bc9ab07b`

Current blockers: `1 HIGH` (`1 production/authority`, `0 Evidence-only`, `0 child/runtime`).

Prior blocker disposition:
- prior production `NativeAuthorityGit(owner_fd=None)` route: **CLOSED**;
- prior bootstrap per-`grun()` owner/index pre/post identity ordering: **CLOSED**.

Remaining blocker:
1. **Bootstrap index type authority is weaker than frozen v0.4 §3.2.** `bootstrap_payload()` opens `.authority-root.index`, captures `(dev, ino)`, and rechecks identity, but never proves the opened entry is a regular file. On Linux the current `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` open can succeed for a directory, so a non-regular index can pass the barrier and reach the first `grun()` Git consumer. Add a regular-file type proof at initial FD8-relative index admission (and preserve equivalent type safety across rechecks) plus a direct temporary CPU witness proving a directory/non-regular index is rejected before any `grun()` Git consumer launches.

Positive remediation: production FD8 constructor admission is now exact; exact procfd cwd/index rejection witnesses exist; bootstrap now has owner/index pre/post barriers around each `grun()`; same-bytes foreign loaded-module identity remains rejected.

Scope reminder: no Gate closure is authorized from this pair. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
