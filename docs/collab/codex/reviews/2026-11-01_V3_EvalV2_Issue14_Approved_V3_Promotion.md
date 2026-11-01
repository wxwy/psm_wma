# Issue #14 — Owner-authorized V3 promotion

Owner explicitly authorized **合入** after the exact-pair GPT APPROVE_CODE.
This supersedes the earlier candidate-only stop for code promotion only.
No runtime or active shared-directory update is authorized.

| Identity | Full SHA |
| --- | --- |
| Approved Formal Root | `fd183f9e8fddfaef93b6ec9484184f071062ae41` |
| Approved Child / Gitlink | `8664267704da3206e719f3c7eef2b5ed86e2a417` |
| Canonical V3 before promotion | `9ba1dd110a4e3e99e717937c2f8d044fa077cdbf` |
| Official Child before promotion | `6c83596d6a259e89c4cd3e79424024983426ac3d` |
| Reviewed candidate including verdict | `11cae65a63804401672aa5de4dcb74358315f3f5` |

The detailed GPT report was read directly from the reviewed candidate:
`docs/collab/chatgpt/reviews/2026-11-01_V3_EvalV2_Issue14_FirstN_fd183f9_86642677_CodeGate_APPROVE_CODE.md`.
Both Root and Child allow normal fast-forward publication. A new isolated cloud
worktree starts at current V3 and inherits the complete reviewed candidate and
its verdict, evidence and both earlier fixture-failure records. No history is
rewritten; canonical Inbox bytes remain a prefix. No merge conflict occurred.

## Inheritance verification

All **9,853 Root source objects** match the approved Formal Root. Root changes
are the two approved production files, the new test and the Child Gitlink.
Child changes only the approved adapter; the other **1,269 Child objects** are
unchanged. The full No-TTT training and other EvalV2 paths remain intact.

All **42 artifact hashes** and **11 formal source bindings** passed. The frozen
original JUnit remains **69 passed, zero failures/errors/skips**. No CPU, Ruff,
GPU, MP4/FFmpeg or historical Gate was rerun. These are Git/source/evidence
inheritance checks, not new independent acceptance or an altered Formal Pair.

The implementation keeps the new field optional/null by default. It enables
first-N rollout recording only when configured for a future new Run. No active
YAML, media, Core Result, checkpoint identity or existing run is changed.

## Publication and safety boundary

Publish official Child first using a normal fast-forward, then Root V3 with a
normal nonforce push. Record fetched and advertised remote Root/Child/Gitlink,
source/evidence checks and completion in
`docs/collab/codex/receipts/2026-11-01_eval_v2_issue14_v3_promotion/`.

All work occurs in `/workspace/psm-wma-eval-rollout-first-n-promotion` and Git
refs. Child is intentionally uninitialized in this new worktree; approved Child
source was checked from existing isolated Git objects without updating files.
No active out2/NoTTT/shared worktree, config, results, media, DCP, logs or process
was accessed. No GPU, model, Action Server, RoboCasa, FFmpeg, real MP4, training,
evaluation or DS dispatch was started. Stop after remote publication/readback.

## Completion

Official Child `v3-local-ttt` was fast-forwarded to `8664267704da3206e719f3c7eef2b5ed86e2a417` first.
Root promotion `ab6b80e08030c1d5835d966a510ea8246944c536` was then published to V3 without force.
Fetched/advertised readback at 2026-11-01T08:22:50.669994+08:00 matched the Root and its Child Gitlink.
All source/evidence checks passed; see `publication_readback.json`.
The completion successor only records this receipt. Approved Formal Pair remains
unchanged. No live shared directory or runtime was touched; work stops here.
