# RoboCasa365 G2 Stage-1 RGB-D/Pose cache

This is offline data preparation, with no Cosmos model/recipe changes and no
nav_sg integration. Original RGB videos are referenced, never re-encoded.

From the Root checkout:

```bash
python -m tools.g2.export_robocasa_rgbd_pose --help
python -m tools.g2.verify_robocasa_rgbd_pose --help
```

Use `--dry-run` to verify the episode mapping and nonvisual raw/Flat rows without
creating a renderer or writing the output directory. Real export requires the
RoboCasa/robosuite/MuJoCo environment, assets and original recordings on the server.
`--state-index-policy frame_index` is an explicit mapping declaration, not proof
of physical alignment. Gate B/C must establish that proof.

- [Input/output schema](rgbd_pose_schema.md)
- [Current spatial-v2 acceptance and bounded Gate C plan](../../docs/build/PSM-WMA_G2_Spatial_Acceptance_v2_and_GateC_Plan_2026-11-04.md)
- [Original implementation/recovery runbook (historical RGB hard gate)](../../docs/build/PSM-WMA_G2_Stage1_RGBD_Pose_Cache_r1_2026-11-04.md)

The spatial-v2 verifier preserves re-rendered RGB metrics as nonblocking
diagnostics. Automatic spatial PASS is separate from external human RGB/Depth
review; an `--owner-visual-review-ref` citation never automatically attests PASS.
Historical reports remain unchanged.

No default N/seed selection exists. Supply one explicit episode or the exact
existing training membership manifest. A completed cache is reusable only after
its identity, file checksums, arrays and frame references validate.
