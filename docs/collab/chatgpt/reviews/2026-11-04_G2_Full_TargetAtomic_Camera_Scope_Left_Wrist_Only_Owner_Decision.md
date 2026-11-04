# G2 Stage-1 — Owner Camera Scope Decision: Left + Wrist only

Date: 2026-11-04. Authority: the Owner explicitly decided to postpone the Right camera for this production round.

**Decision:** Full RoboCasa365 v3 target-atomic batched Depth/Pose recovery must process **exactly two cameras**, specified explicitly at the export CLI:

```bash
--cameras robot0_agentview_left,robot0_eye_in_hand
```

- `robot0_agentview_left` (Left): **IN SCOPE**.
- `robot0_eye_in_hand` (Wrist): **IN SCOPE**.
- `robot0_agentview_right` (Right): **OUT OF SCOPE** for this round, not a mandatory input or production blocker. Keep the existing script capability to select it for a separately approved future expansion.

The existing G2 exporter already parses the comma-separated `--cameras` list and validates camera names; **no production source modification is required**. The choice should be specified explicitly in future run commands instead of relying on defaults. Do not silently add Right to the frozen 92 batches or the first-batch plan.

**Output:** Keep the Gate C-approved per-camera `uint16_mm` Depth, valid mask, K, `T_world_camera_cv`, `T_world_camera_gl`, frame indices, 32-frame compressed NPZ chunks and the per-episode `frames.jsonl` provenance/manifest/COMPLETE records. Existing original RGB videos remain references; no duplicate RGB or per-frame NPY exports are required by this decision.

**Frozen data scale:** the full-source two-camera batch partition remains 9,126 episodes / 2,231,347 source frames, split into 92 deterministic batches of at most 100 total episodes each. No partition/refreeze or two-to-three-camera budget change is needed.

**Separate unresolved decision:** exact durable production output directory, full-coverage disk quota, retention policy, and a separate batch execution authorization have **not** been approved by this camera-scope decision. A suitable lightweight offline reader for nav_sg may consume the current NPZ Depth + K/Pose and original RGB by frame ID; offline adapter integration remains separate.

Gate C remains PASS for the previously checked two cameras. This is a docs-only scope decision; it neither starts rendering nor modifies G2 code, V3, nav_sg, original source or existing caches.
