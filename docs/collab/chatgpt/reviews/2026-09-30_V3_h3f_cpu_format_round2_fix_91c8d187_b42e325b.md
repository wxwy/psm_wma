# PSM-WMA V3 — H3-F CPU readiness round2 formatter remediation

- Date: 2026-09-30
- New formal root: `91c8d187074c9f7262d539688708bf9ed06f9f97`
- New formal child/Gitlink: `b42e325be45a62b93c7c89d3d61af1045e4167a9`
- Status: **H3F_READINESS_CPU_ROUND2_FIX_PENDING_REVALIDATION**

ds reported the previous pair passed all 27 tests and Ruff check, but
`ruff format --check` requested two function signatures in
`examples/psm_wma_robocasa_h3f_test.py` be collapsed to one line.

This commit applies exactly those two formatter changes. No H3-F production logic or training
contract changed.

Re-run the complete CPU/static gate on the exact new pair. If green, continue directly with the
already-authorized read-only H3-F preflight, storage budget, and timing budget. The 30k GPU run
remains unauthorized.
