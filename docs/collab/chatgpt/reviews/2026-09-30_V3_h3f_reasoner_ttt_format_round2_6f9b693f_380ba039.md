# PSM-WMA V3 — H3-F Reasoner+Local-TTT formatter round2 remediation

- Date: 2026-09-30
- Formal root: `6f9b693fe51882b02d4ac2a55bdfeeba9644d861`
- Formal child/Gitlink: `380ba039ea19f314dd1c7cd9e6b94fc01f131f59`
- Status: **BLOCKED_PENDING_REASONER_TTT_READINESS**

Previous pair evidence:

- 34 pytest PASS;
- Ruff check PASS;
- diff check PASS;
- clean worktrees;
- prior facade bash-n PASS;
- sole blocker: `ruff format --check`.

This commit changes only the `forbidden_host` set-comprehension formatting in
`examples/psm_wma_robocasa_h3f.py` to the Ruff-stable multiline form verified by ds.

No runtime, optimizer, Reasoner+Local-TTT selection, gradient witness, owner-env, scheduler,
checkpoint, readiness, or resume behavior changed.

Re-run the complete CPU/static gate on this exact pair. If green, continue directly with the
already-authorized owner preflight → Reasoner+Local-TTT readiness10 → fail-closed matrix.
