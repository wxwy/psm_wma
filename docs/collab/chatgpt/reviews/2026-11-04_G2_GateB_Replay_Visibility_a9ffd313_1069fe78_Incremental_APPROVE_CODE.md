# GPT Incremental Code Gate — G2 Gate B Replay Visibility

Date: 2026-11-04. **Verdict: APPROVE_CODE (isolated Gate B diagnostic rerun only).**

Formal Root: `a9ffd313770c5344195f415425124a5075e62b2b`
Formal Child/Gitlink: `1069fe78841228cadbbfbe6afbd767eaed6225da`
Prior Formal Root: `b67bc4ca9a2afb1ff26fac0846f8ee7042a589ab`
Implementation parent: `992cfc2adb3150c573d19206e176bd8a52574949`
Candidate branch: `v3-g2-gateb-replay-fix-20261104`.

This review is **docs-only** and does not change the source Formal Pair. V3 remains unmerged. The prior server Gate B remains **PHYSICAL_REPLAY_NOT_ACCEPTED** until a new independent real-host replay passes unchanged requirements.

## Scope/source review

- Confirmed parent992cfc2..FormalRoot a9ffd313 is **one implementation commit** changing six root files; one production source file `tools/g2/rgbd_pose/replay.py`, added `tools/g2/test_replay_render_visibility.py`, minor adaptation of existing tests and runbook/SESSION/TODO.
- No Child change; no training, Cosmos model, encoder, action path, source/frame mapping, codec/cache publisher, or verifier thresholds altered.
- Reviewed `replay.py:30–78,199–399` and `docs/build/PSM-WMA_G2_GateB_Replay_Visibility_Followup_2026-11-04.md`, plus the author handoff and structured test evidence.
- Author `gate.json` and two separate JUnit suites verify **83 legacy + 24 native CPU OSMesa = 107 distinct PASS / 0 fail/skip/error**. The frozen 20 on original source were **RED9 / PASS11**, while corrected source had GREEN20. Ruff/format/source hashes are author attestations, not independent GPT re-execution. Native Mesa synthetic geoms were exercised, not real RoboCasa.
- Production never uses cached depth magnitude/error to decide sample eligibility, and retains `>=16` matching-geometry samples and absolute optical-Z error `<=0.01 m`. The smooth-interior selection is deliberately conservative to avoid MSAA/segmentation/transparent/backface non-equivalence. A zero/low coverage or unsupported visibility setting is **INCONCLUSIVE**, not PASS. RGB original-video MAE `<=5` remains a separate hard gate.

## Review findings

**No code blocker for a diagnostic Gate B rerun.** The new front-face mesh Möller–Trumbore path, near-plane-origin conversion, opaque scene eligibility, per-render visibility/segmentation checks, and same-ID interior filtering have positive native CPU evidence and negative tests that reject bad cached depth/pose and one bad eligible ray. These are relevant to the old ray checker’s reproducible false positives. Do not infer this repairs all former RoboCasa geometry failures or RGB mismatch.

**Nonblocking watch points / hard checks in next real-host report:**
1. `replay.py:272–318`: smooth/opaque eligible coverage is selective; record eligible/fresh pixels, matching samples, selection rules and failures for **all six** frame-camera pairs. Do not generalize a pass of smooth surfaces into full depth-map accuracy; meaningful coverage is important.
2. `replay.py:334–362`: native geom identity + mesh front-face replacement must be checked on real RoboCasa complicated meshes; report number of front-face corrected rays, mismatches, actual max error and wall time. Synthetic geometry alone cannot close physical acceptance.
3. `replay.py:217–264`: RGB diagnostics show renderer mode differences and context fingerprint changes only. They **do not repair** original RGB MAE failures (previously 5/6 above 5) and must not mask those failures. Keep original RGB comparison unchanged.
4. Real env interoperability: `scene.geoms`, `geom.transparent`, segmentation and flags may differ in the real installed robosuite/MuJoCo stack. Unsupported semantics must yield INCONCLUSIVE (never forced PASS).

## Next action authorized by this Code Gate

Allow **one isolated Gate B replay diagnostic** on DS server after checkout of exact Formal Root/Child with clean source. Follow `docs/build/PSM-WMA_G2_GateB_Replay_Visibility_Followup_2026-11-04.md` and previous frozen runbook: `CloseFridge` local0/global502, frames0/214/428, cameras left+eye_in_hand; fresh cache and report namespace. Use existing CPU OSMesa software backend, no GPU/EGL fallback or training resource modification. Preserve old failed caches/logs.

- Required: nonvisual alignment and source identity PASS; native RGB versus original video `MAE<=5` all six; K/poses, saved/fresh valid mask and metric depth consistency; corrected backprojection `<=1e-7` pixel; independent geometry `>=16` matched, `max optical-Z error<=0.01m` all six; report `PHYSICAL_REPLAY_PASS` exit0. Do **not** weaken thresholds, alter samples post-error, or re-label inconclusive as pass.
- If any item fails, **STOP**, retain new text-only report and prior artifacts, present isolated cause(s), and request the smallest new source change after evidence; no automatic repeated Gate B loops.
- RGB/Depth/MP4/NPY/NPZ/video, local probes and reversible encoded payloads stay on the DS host. Cross-session only non-sensitive aggregate text status/metadata/hashes.

**Not authorized:** Gate C, N=100 batch, V3 merge, nav_sg, training, checkpoint, production GPU, modifications to frozen results, or any change outside this diagnostic rerun.

This is approval of an incremental checker/diagnostic implementation, **not** proof that the downstream real-data Gate is satisfied.
