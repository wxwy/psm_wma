# G2 RGB provenance — minimum server-local evidence handoff

Date: 2026-11-04 (Asia/Shanghai). For the execution/validation role; no production
code edits. Formal implementation remains Root
`a9ffd313770c5344195f415425124a5075e62b2b` /
Child-Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`.

The reviewed task is RGB-only. Geometry6/6 PASS from report799199e9 stands;
Gate B still FAIL because original RGB MAE<=5 holds only1/6. This handoff
prepares the next read-only investigation; it does not assert anyone executed
these steps or authorize a new rendering/GPU experiment.

## P0 — inspect existing evidence; no new GL context or replay

1. On the server, establish how `/tmp/g3_full.py` produced RGB saved under
   `/tmp/g3_out/`: raw `sim.render` or reference video, original frame indices,
   dtype/shape, channel order, vertical flip, any encode/decode or postprocessing.
   Bind the retained script/hash to its output provenance if possible. A hash
   of the file **now** is not proof it was identical when old G3 ran. Return a
   producer summary and hashes, never the script or image/array contents.
2. Look for already retained **actual historical** backend evidence associated
   with that run: Python/import/library identities, GL context implementation,
   GL_VENDOR/GL_RENDERER/GL_VERSION/GLSL. Only inspect known experiment logs or
   an independently identified, still-alive original process. Script defaults,
   current shell MUJOCO_GL, current packages, `glxinfo` in a different process
   or file mtime cannot prove the old context. Missing evidence is UNKNOWN.
   Do not enumerate unrelated processes or dump environments/shell history.
3. Read current six-camera `rgb_render_diagnostics` from the existing report
   `/tmp/g2_gpt_gateb_r2_20261104_0630/physical_report_r2.json` and compare any
   available old provenance: render/geom/site flags, MSAA, material/light hashes.
   Missing fields should be listed, not manufactured by reconstructing an old
   context. Fields needed for a future controlled capture are actual GL identity,
   loaded GL/OSMesa/EGL/MuJoCo library versions, clip-control capability,
   shadow flag/FBO/size, headlight and live scene lights, material texture IDs,
   specular/emission/shininess/reflectance and texture content/shape hashes.
4. If relevant, inspect only existing video metadata:
   pix_fmt/color_range/color_space/color_transfer/color_primaries. A bounded
   local numeric comparison of existing old/current/reference RGB may return
   MAE, per-channel signed bias and a few luminance-bin error summaries. Do not
   fit or apply a correction, re-encode frames, emit pixels/histograms sufficient
   to reconstruct images, or reinterpret lower corrected MAE as a Gate pass.

Use a fresh external text-evidence directory. Preserve all earlier reports,
caches, source scripts and `/tmp/g3_out`. Do not pull/update active worktrees.
Read the server GitHub fetch skill before any separately needed isolated fetch.
No data/script/image/video/NPY/NPZ or reversible payload may leave the server;
only necessary non-sensitive aggregate text/status/hashes can be handed back.

## Minimal return and decision

Return one concise table for old G3 versus current OSMesa: raw producer identity;
actual historical GL identity and supporting artifact; available light/material/
texture/framebuffer provenance; explicit UNKNOWN fields. State whether the raw
render-to-render difference is established independently of video decoding.
Provide the server-local evidence path and factual findings, not a guessed fix.

- If provenance establishes a concrete mismatch, propose the single smallest
  code or environment correction, with causal evidence and unchanged raw MAE5.
- If the old context is unrecoverable, STOP with that fact. Propose **one**
  controlled experiment for separate review; do not sweep backends/settings.
  A useful contrast is wrist frame214 (large mismatch) and frame0 (small
  mismatch), fixing all inputs/assets and varying one specifically justified
  factor. Preserve RGB and geometry metrics; changing backend to EGL or using
  GPU is not authorized by this handoff.
- Arbitrary brightness/gamma correction, replacing original RGB references,
  changing state indices/thresholds, re-opening Depth/geometry work, Gate C,
  N100 export, V3 merge and training remain outside scope.
