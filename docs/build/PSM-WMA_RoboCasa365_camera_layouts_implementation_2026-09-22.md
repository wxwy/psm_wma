# PSM-WMA RoboCasa365 — Configurable Camera Layout Implementation

Date: 2026-09-22

## Implemented camera sets

The RoboCasa data path now supports three explicit pre-VAE compositions:

### 1. left_wrist (default)

```text
agentview_left | wrist
256x256       | 256x256
-> 256x512
-> VideoResize(resolution=None)
-> 192x320 at current tier-256 policy
-> expected Wan2.2 exact-window latent [5,48,12,20]
```

This is the first-stage default because it matches the LIBERO concat-view geometry most closely.

### 2. wrist_lr

```text
      wrist 256x256
-----------------------
left 128x128 | right 128x128
-> 384x256
-> VideoResize(resolution=None)
-> 320x192
-> expected latent [5,48,20,12]
```

This preserves the previous PSM-WMA RoboCasa three-camera layout. The legacy name
`wrist_top_agentview_lr_bottom` is accepted as an alias for `wrist_lr`.

### 3. left_wrist_right

```text
left | wrist | right
256  | 256   | 256
-> 256x768
-> VideoResize(resolution=None)
-> 192x320 under the current tier-256 policy
-> expected latent [5,48,12,20]
```

This keeps all three source cameras at full resolution before the common Cosmos resize.
A future higher-resolution experiment can reuse the same layout without changing the cache schema.

## Dataset changes

Child implementation adds:

- `camera_set` with values `left_wrist`, `wrist_lr`, `left_wrist_right`
- layout-specific camera decoding (two-view mode does not decode the unused right camera)
- layout-specific composition and prompt description
- layout-specific cached-path pixel placeholder geometry
- cache manifest validation against the selected camera set
- backward alias for the old three-view camera-mode name
- L0 tests for source composition and expected Cosmos canvas sizes

## Cache-builder changes

`tools/g0/build_cosmos_robocasa_latent_dataset.py` now accepts:

```text
--camera-set left_wrist
--camera-set wrist_lr
--camera-set left_wrist_right
```

The builder no longer hardcodes the three-view latent geometry. It records observed:

- camera set and exact camera keys
- composed output size
- actual post-VideoResize VAE canvas size
- actual encoded latent shape

An existing episode cache is reused only when its camera layout matches the requested layout, preventing silent reuse across camera-set experiments.

## Scope boundary

This commit implements the camera-layout family only.

The previously reviewed RoboCasa v2.1 readiness items remain separate until implemented:

- v2.1 meta episodes/tasks loading compatibility
- episode-index-aware v2.1 video path
- canonical RoboCasa domain registration
- deterministic episode-limit subset selection

Therefore the layout code is ready for its unit tests, but a full N=10 cache build must still pass the remaining v2.1 compatibility gate first.
