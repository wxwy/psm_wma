# Codex G2 depth codec implementation — issue #19

This is a **kickoff marker only**, not an implemented fix.

- Source issue and full acceptance contract: https://github.com/wxwy/psm_wma/issues/19
- Base branch: `v3-g2-spatial-policy-20261104`
- This isolated Codex implementation branch: `v3-g2-codex-depth-zero-sentinel-20261105`
- Owner-approved specification: https://github.com/wxwy/psm_wma/blob/9568723fd19d008be180c7b3e4126e1176c07d26/docs/collab/chatgpt/reviews/2026-11-05_G2_Uint16_Depth_ZeroSentinel_No_Stored_Valid_Owner_Decision.md

**Status:** Awaiting Codex implementation and tests. Do not merge this placeholder or consider it an implementation.

Required: exactly depth/K/GL-CV pose/frame_indices in NPZ; `uint16_mm` zero sentinel for renderer-invalid and out-of-range pixels, no persisted valid array, range-exclusion metrics, strict versioned verification and safe 7-episode legacy transition plan.

Must not touch `V3`/`V2`, historical formal evidence, production Depth cache, nav_sg or training. Native GPU4-6 export/resume only after separate review and authorization.
