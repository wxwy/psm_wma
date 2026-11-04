# G2 RGB-only follow-up — read-only source audit

Date: 2026-11-04 (Asia/Shanghai). Formal implementation stays
`a9ffd313770c5344195f415425124a5075e62b2b` /
Child-Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`.
This is an author source audit and evidence handoff, not a new Code Gate or
server experiment. No production changes or additional tests were performed.

## New formal evidence consumed

Exact-pair GPT Code APPROVE in commit
`3054d6ac5e36fc9fe3fcf331152a8cc305d5d821` and independent server report
`799199e94c86715abf30b6ab5bb3cd413691d4f5` were read from Git objects. The
isolated candidate advanced from59fb20ec to799199e9 by clean fast-forward;
the four added files contain only reviews/Inbox. Official V3 was separately
fetched/advertised as083b36ac27ad43b6f5127d9a58aed4fac02eaaa7.

Per that server report, all six geometry comparisons PASS with128 matched
rays each and0.880–4.423mm maximum errors. Eligible coverage is37549–61932
pixels of65536. Geometry work for this narrow fix is complete; it is not a
full-map accuracy claim. Cached/fresh depth, K/Pose and runtime checks PASS.

Five of six original RGB comparisons still exceed MAE5. New and old G3
constructor kwargs produce identical RGB in the same current OSMesa process;
RGB/RGB-D and segmentation-before/after also agree exactly. Gate B remains
`PHYSICAL_REPLAY_NOT_ACCEPTED`. These are reported server measurements,
not author cloud execution. Historical failed outputs remain immutable.

## Source facts and limits

- Replay reads uint8 RGB and flips vertically once; no channel swap, brightness,
  gamma, resize or color correction is applied. `rgb_metrics()` converts to
  float64 before differences, excluding uint8 subtraction overflow.
- Official RoboCasa LeRobot video writing uses H.264/yuv420p/CRF23. Equal
  imageio/OpenCV frames exclude decoder disagreement, not every possible shared
  color-metadata issue. However, video encoding cannot alone explain two
  different **raw** render outputs. First establish that saved G3 RGB is raw,
  rather than a decoded reference or postprocessed image.
- MuJoCo3.3.1 `src/render/render_gl3.c` uses `scene.SHADOW` and `con.shadowFBO`
  in lighting (around1131/1165), and chooses different shadow polygon offsets
  according to `GL_ARB_clip_control` (around1227). Therefore matching XML,
  geometry and camera matrices do not establish matching photometry.
- `src/render/render_context.c` allocates the offscreen color buffer as
  `GL_RGBA8` (around1120–1123); inspected texture paths use GL_RGB/GL_RGBA.
  These paths do not establish an explicit sRGB transform. Brighter images
  are insufficient to diagnose gamma, a color-range error or EGL.
- Current per-frame fingerprints omit some texture/material parameters,
  headlight, actual scene lights and GL/shadow-buffer identity. Missing fields
  are evidence gaps, not evidence that those properties actually changed.

Public source references:
[render_gl3.c, MuJoCo3.3.1](https://github.com/google-deepmind/mujoco/blob/3.3.1/src/render/render_gl3.c),
[render_context.c, MuJoCo3.3.1](https://github.com/google-deepmind/mujoco/blob/3.3.1/src/render/render_context.c).

## Decision and current blocker

No justified production color fix is established. Do not change Depth,
geometry, state index, rendering kwargs or thresholds. Do not repeat107 CPU
tests or the six-frame replay merely to recover already known facts.

Next is existing-evidence, server-local RGB provenance inspection, specified in
`docs/collab/codex/requests/2026-11-04_G2_RGB_Readonly_Provenance_Handoff.md`.
The author cloud has no callable remote execution tool, so no server files,
scripts or arrays were accessed/transferred. Old actual GL identity and raw
artifact provenance cannot be inferred here. Mark unavailable historical
information UNKNOWN. Any later controlled rendering experiment needs its
factor, environment and execution scope reviewed first. No Gate C/N100,
GPU/EGL, V3 merge, training or old-output changes are authorized here.
