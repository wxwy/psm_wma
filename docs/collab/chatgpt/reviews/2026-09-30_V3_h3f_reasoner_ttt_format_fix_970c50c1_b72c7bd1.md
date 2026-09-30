# PSM-WMA V3 — H3-F Reasoner+Local-TTT formatter remediation

- Date: 2026-09-30
- New formal root: `970c50c1d8cd1975c822f672afa823f2a8ea7573`
- New formal child/Gitlink: `b72c7bd1c53e3767d69dd10c2223fa5057259738`
- Status: **BLOCKED_PENDING_REASONER_TTT_READINESS**

ds validated the previous pair with:

- 34/34 pytest PASS;
- Ruff check PASS;
- bash -n PASS;
- git diff --check PASS;
- root/child clean.

The only blocker was `ruff format --check` for two set-comprehensions in
`examples/psm_wma_robocasa_h3f.py`.

This pair applies only the formatter-requested folding of those two expressions. No runtime,
optimizer, Reasoner+Local-TTT inventory, gradient witness, owner-env, scheduler, checkpoint, or
resume semantics changed.

Re-run full CPU/static on this exact pair. If green, continue directly with owner-env preflight,
Reasoner+Local-TTT readiness10, and the previously authorized fail-closed matrix.
