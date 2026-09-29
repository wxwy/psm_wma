# PSM-WMA V3 — Stage 3E preflight format remediation + H3-F 30k formal budget freeze

- Date: 2026-09-29
- Formal root: `db08117786a2483ca5cc7f4b58a0c3518e78bccc`
- Formal child/Gitlink: `b43097c74982f13e67c071ece729c7b6929cad52`
- Parent Stage-3E pair: `3649033a9e8db0abd5c18af65da497e8e2931b2e` / `5d6ed4a22d4c84d8b850d008aa46b551dff37a50`
- Stage 3E status: **REVALIDATION REQUIRED**
- H3-F formal training budget: **max_iter = 30000**

## Stage 3E remediation

ds validated the previous Stage-3E pair with:

- 10/10 pytest PASS;
- ruff check PASS;
- git diff --check PASS;
- clean child worktree.

The only blocker was `ruff format --check`, which reported exactly two formatting hunks:

1. collapse the Stage-A authority digest mismatch message into the formatter-preferred f-string;
2. collapse the test's small `segments` tuple comprehension.

Child `b43097c74982f13e67c071ece729c7b6929cad52` applies exactly those style corrections.

No H100 authority path, Stage-A digest, catalog rule, manifest digest, grouped binder path,
trainer behavior, B1 cache, or Stage-A asset is changed by the formatting remediation.

## H3-F formal budget decision

The active RoboCasa H100 route now freezes:

- `H3F_FORMAL_MAX_ITER = 30000`
- checkpoint/evaluation schedule:
  `1000, 2000, 4000, 8000, 12000, 16000, 20000, 24000, 30000`

This replaces the **future RoboCasa H3-F planning budget** only.

It does **not** rewrite historical LIBERO 5000-step evidence and does not change H3-E smoke
semantics. H3-E remains:

- fresh: one optimizer iteration;
- same-job resume: continue to iteration two.

The repository does not yet contain a standalone H3-F long-run launcher, so the 30k value is
frozen now as the V3 formal budget authority and must be consumed when that launcher is created.
It is deliberately not implemented by turning the H3-E smoke harness into a 30k runner.

## Required revalidation

Before Stage 3E can close, ds must re-run on this exact pair:

1. `examples/psm_wma_robocasa_h100_test.py` — now expected 11 PASS;
2. ruff check — PASS;
3. ruff format --check — PASS;
4. git diff --check — PASS;
5. real H100-authority preflight:
   - Stage-A config/model metadata SHA256 exact;
   - 9036 catalog;
   - frozen manifest digest exact;
   - rank0 production grouped planner/binder path materializes 8 unique train episodes;
   - native batch shapes `[33,64]` and raw `[33,15]`;
6. negative pair-lock and authority-digest probes.

No 8×H100 training is authorized by this review.
