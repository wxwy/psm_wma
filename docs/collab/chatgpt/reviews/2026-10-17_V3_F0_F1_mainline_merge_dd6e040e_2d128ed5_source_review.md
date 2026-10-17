# V3 F0/F1 Packed128 Source Merge — Independent Git-tree verification

**Date:** 2026-10-17
**Action:** Owner explicitly authorized promotion of already CPU-gated F0/F1 isolated implementation to Root branch V3.
**Formal merged Root implementation SHA:** dd6e040ea8229fc3ce81259952444f82dd9897b2
**Formal merged Child/Gitlink SHA:** 2d128ed5a07601cdd424974f99b67832eafeeb41
**Prior V3 parent:** 53f0b9b8942c2f38613a7ee3d5b541aae91f4371
**Incoming F1 docs-branch parent:** ccfd900bc35fcd39ca9953aa7aa55b85398300ad
**Resulting merge tree:** aececd5da25a4d1d7ed8e3116acb9c89516188c1
**Mechanism:** explicit two-parent merge commit. V3 ref updated with force=false, expected_sha matching old V3; success returned.
**Promotion structural verdict:** SOURCE_MERGE_VERIFIED; runtime Root-identity CPU preflight remains pending. No GPU authorization.

## Verified Git identity and preservation

1. Queried V3 remote after updating: head exactly dd6e040ea8229fc3ce81259952444f82dd9897b2. Two parent commits as noted. Gitlink is mode 160000, type commit, SHA 2d128ed5a07601cdd424974f99b67832eafeeb41.
2. The merge imported all **62 F1-only files**, including executable scripts/train_v3_packed128_staged.sh (mode 100755), F0/F1 frozen docs/build contracts, DS acceptance instructions, Codex reports and author CPU evidence, retaining identical F1 blob SHA.
3. Four overlapping paths were resolved deliberately. SESSION.md and TODO.md adopt F1's full append-only superset of previous V3 content. cosmos-framework Gitlink moves to the tested F1 Child. Canonical CODEX_INBOX_2026-10-15_CONTINUATION.md keeps previous V3 content unchanged and appends only three Codex historical branch entries missing on V3.
4. Recursive 11k-leaf Git-tree audit: all original V3 paths retained; only the exact four overlapping paths changed. All original F1 paths present with identical SHA, except purposefully combined Inbox. The eight latest V3-only GPT requests/reviews were preserved with exact SHA. There were no Local-TTT numerical, evaluation E1, old Index8 or legacy B1 code changes outside the already accepted F1 Child.
5. F1 formal Root 6ebf8998a7935f2ad690bb547c5db5e5a4322e6d is an ancestor of incoming history, but **current formal training Root is dd6e040ea8229fc3ce81259952444f82dd9897b2**. Previous world8 preflight digest 65ad8bce52aed0feaecbf399828667683f7a461487f870e0493dad8766abd01f binds old Root and cannot be used as the new Root's identity.
6. Child repository has no V3 branch; its approved commit 2d128ed5a07601cdd424974f99b67832eafeeb41 is available on v3-f1-checkpoint-rng-20261016. Do not move the historical v3-local-ttt branch; Root V3 now points directly at the correct Child commit.

## Minimal remaining Gate

- DS CPU-only clean detached Root dd6e040ea8229fc3ce81259952444f82dd9897b2 and Child 2d128ed5a07601cdd424974f99b67832eafeeb41 checkout; use the full environment for **read-only world8 corrected Phase5 preflight**, exact new expected-root and expected-child, and no Job namespace write. Record a new config_digest, exact Packed128/native/profile, 30000/500/100.
- F0/F1 CPU source bytes and prior independent results remain valid for their specific scope: do not rerun large F0/F1/B0/B1 suites solely because Root SHA changes. Any new Child or other implementation change needs a fresh scoped Gate.
- G0 GPU release remains BLOCKED pending distinct Owner authorization, target /mnt/data1 FS tiny safety probe and space threshold, 8-GPU Config.validate/NCCL and real DROID/Local diagnostics.

This source merge **does not** authorize CUDA, real DCP, G0 bounded3, Fresh100, Resume500, Formal30k, moving/deleting old iter1300 or 595GB B1 Evidence. Documentation commits after this merge are bookkeeping and must not be substituted for the implementation SHA.
