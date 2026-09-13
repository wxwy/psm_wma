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

- immediate prior live blob SHA: `e41aefbbbaf312475c333bd4cfa9ed593fb38c47`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Causal Owner Identity CPU/static Remediation APPROVED

Formal pair:
- root implementation SHA: `aba42f3c077629074f3f8c03420bc8a01bc1ebd7`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_cpu_static_remediation_aba42f3_93a89ba.md`

Canonical review commit:
`914078bc69178760a36bed7337f489a0f4f03399`

Current blockers: `0` (`0 production/authority`, `0 Evidence-only`, `0 child/runtime`).

Prior blocker disposition:
- bootstrap FD8-relative `.authority-root.index` regular-file admission gap: **CLOSED**.

Closure basis:
- initial bootstrap index admission now requires `stat.S_ISREG(ii.st_mode)` before binding index identity;
- every later `ownerbarrier()` requires regular-file type plus exact frozen `(dev, ino)` identity;
- `grun()` retains owner/index and route pre/post barriers plus exact `close_fds=True, pass_fds=(8,)`;
- direct temporary witness replaces the index with a directory and proves rejection before the first marked FD8 Git consumer;
- formal delta remains root-only CPU/static and child/Gitlink is unchanged.

Scope reminder: this closes only the exact CPU/static implementation Gate for the exact formal pair above. It does not authorize production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
