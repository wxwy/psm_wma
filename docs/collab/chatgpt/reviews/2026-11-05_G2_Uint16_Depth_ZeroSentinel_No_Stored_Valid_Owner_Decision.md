# G2 Stage-1 — Owner final depth encoding decision: uint16 millimeters with zero sentinel; no stored per-pixel valid mask

Date: 2026-11-05 (Asia/Shanghai). Scope: future G2 full RoboCasa365 target-atomic Left + Wrist Depth/Pose production.

## Decision

The Owner explicitly rejected keeping a separate per-pixel `valid` array in the production NPZ. **Store only the `uint16_mm` depth array; encoded depth `0` means there is no usable encoded depth at this pixel.** A Boolean mask may be calculated transiently during validation or in-memory readers (`valid = depth > 0`), but must not be duplicated in the persisted chunk.

- In-bounds, renderer-valid metric depth in `[0.001,65.535]` metres: round to nearest millimetre and encode as `uint16`.
- Renderer-invalid or finite, positive depth outside the representable interval: encode `0` as **not represented**. Do not clip/saturate to `65535`, wrap integers, or reinterpret zero as a real surface at the camera.
- Count/report out-of-range source pixels by frame/camera/episode as compact metadata, including whether the source value was below/above range. This is statistics, **not** another per-pixel mask.
- Preserve per-frame `K`, `T_world_camera_cv`, `T_world_camera_gl`, `frame_indices`, source RGB video reference and provenance. Keep existing compressed NPZ chunks (32 frames per camera), no duplicate RGB.
- Cameras remain **only** `robot0_agentview_left` and `robot0_eye_in_hand`. Keep the same fixed owner-approved output root `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-depth` and deterministic 92-batch/full-9,126-member source selection.
- `nav_sg` zero-value semantics and unit scaling are deferred to the integration stage, as the Owner requested; the future offline reader must explicitly skip zero, not convert it into a fake near-plane obstacle or point.

## Implementation boundary / cache transition

**This is a design decision, not a claim that code or existing cache files were already modified.** The formally validated G2 `psm_wma_robocasa_rgbd_pose_v1` schema currently requires a `valid` array in `cache.py` and an invalid-pixel mask convention in `geometry.py`; the exporter, verifier and schema documentation need a coordinated code/contract change. Internal code may still use transient masks.

The initial GPU4/5/6 production run stopped after **7 completed, independently verified episodes** (2,353 frames), with a far-range wrist floor pixel triggering the existing uint16 overflow check on CloseFridge global episode736 frame73. All seven committed chunks use the **previous** `depth+valid` schema; their manifests, root `cache_manifest.json`, and checksums are immutable. Do not mix new no-valid chunks into that original contract, change files in place, delete the 7 episodes or erase the preserved failed/staging evidence.

When implementing, design an explicit versioned cache upgrade or verified migration/re-encode of those 7 episodes, with safe backups/atomicity and a coherent root contract for the Owner-approved output location. Verify bitwise `valid == (depth > 0)` for legacy chunks before any mechanical migration, and preserve original provenance/lineage. Native checks must verify zero-sentinel representation, far-floor episode736 frame73/74, source-frame alignment and the absence of near-field phantom points. Do not silently change historical Gate C acceptance; new schema needs a new validation receipt.

**No Depth exporter, validator, V3, nav_sg, original data, cache, run or GPU was modified by this documentation-only decision.** The first batch is still stopped; do not automatically restart the 100-episode producer.

Previous suggestion to retain `valid` for convenience is superseded by the Owner's explicitly chosen minimal storage format. The measured compression cost of legacy `valid` was small, but the format decision is about avoiding redundant persisted data and keeping the consumer interface simple.
