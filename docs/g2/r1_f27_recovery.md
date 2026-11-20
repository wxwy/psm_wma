# R1 Iter 5000 F27 recovery

The stopped 900-episode Run has manifest `513ae651c38cc6d7b069ec7efced5c84bddef735dfd103f68c4b897313d8f654`. It contains 93 verified Core results, including 31 successes and 62 failures. The native Store yields 93 `skip_valid_core` and 807 `execute` dispositions. The retained Core list in Task order hashes to `02663c7cd0f753436347ea24319127edfd2cccdc9439118150f65207705fdfe1` with EvalV2 `digest`. The partial SR is 31/93. [Incident report](https://github.com/wxwy/psm_wma/pull/93#issuecomment-7040238798)

## Renderer repair

The first failure occurred in the Frame 0 `+Y` static translucent pass for TurnOffStove EP6. The material painter received Geom 0 without a matching registry entry. The shader now writes an explicit completion value and one-based triangle codes. The reader verifies completion, hit/miss consistency, Geom/triangle identity and finite hit data before resolving the original faces. The renderer reprojects a rejected readback from the same mesh, crop and axis using the existing CPU implementation. The affected layer's evidence records the recovery backend and error. Valid submitted Geom 0 has the same meaning as other Geom IDs.

Original Root `511698256f81267abb4fcf6748b9166ab9ca1b6f`, V3 base `5659b3898b94b302288669d03092fb9b5a5d4023`, tested repair `7d78aa0df6b1154473273b1f653134a896f892e3`. Child/Gitlink `5a6585a1308782f52d4601be03771c977a15bf9c`. The native scene check used nav_sg `c7997241b2b0f1e6f7d44f851f8cea62de2144ad`. [Draft PR #94](https://github.com/wxwy/psm_wma/pull/94)

## Offline and live comparison

The offline production log records 9,126 completed episodes. All 500 offline TurnOffStove episodes have completion markers. Of those, 29 use the same Layout 1 and Style 1 as the incident. All 29 published a `+Y` Frame 0 image at 599 × 326 and 1 cm per pixel, the incident crop. Their raw episode metadata differs from the incident metadata. This comparison verifies coverage of the direction and image dimensions.

The archived offline launch references `f3eff3e5c836d13f947c1b17eaaa051bad375b1a`. Its compute shader and surface painter Git blobs match the stopped evaluation Root. Both routes use direct material F27 and lazy texture decoding. Offline renders recorded XML and state rows in dedicated F27 subprocesses with the existing MuJoCo 3.3.7 overlay and eight workers per GPU on four GPUs. EvalV2 renders live resets from MuJoCo 3.3.1 with sixteen Actor slots per render GPU on two GPUs. The live F27 call also restores the Actor's camera context. The recorded launch differences leave the original hardware trigger unresolved.

The controlled comparison used the same new TurnOffStove model, Frame 0 state, nav_sg snapshot, Geom list and projection in both F27 call sites. Injecting Geom 0 into the `+Y` readback caused `KeyError(0)` in both baseline routes. Applying the shared fix recovered both, each with 193,752 valid color pixels and the same PNG SHA256 `02551f8e75ad70497088877c33319bc69ac2935faa3740708cdc83eddfff3aee`. The four Geoms in the submitted static translucent group excluded Geom 0.

Re-running the related renderer suite with the existing offline MuJoCo 3.3.7 overlay gave 131 passes and one optional real-asset skip. This includes the four `colorspace` cases that failed with the MuJoCo 3.3.1 XML parser.

## Author checks

The 17 focused tests passed using the existing PSM interpreter. The software EGL check attested Mesa llvmpipe and verified nine GLSL raster cases covering the nearest hit, K8 and K32. The hit masks, Geom IDs, face IDs and flags exactly matched the CPU reference. Depth and barycentric weights matched to `1e-13` absolute tolerance.

The expanded candidate run returned 375 passes, six failures and one skip. The six failing test identities also failed on V3 `5659b389` in the same environment. Four texture cases require the `colorspace` MJCF attribute missing in the installed MuJoCo 3.3.1 parser. The stalled-encoder cleanup and actor-transport cases also failed on the baseline. The skip is the optional `G2_F27_REAL_SOURCE_MJCF` fixture. The notes below describe the separately executed fresh-scene check.

A fresh TurnOffStove sample with MuJoCo 3.3.1 produced a source-bound native nav_sg snapshot with one Room and 48 entities. In the actual `+Y` static translucent pass, an injected unregistered Geom 0 triggered CPU recovery. The View had 193,752 valid color pixels and the RGB image matched the clean Mesa render exactly. Frame 0 F27 time was 10.745 s clean and 10.739 s with the injected fault in this one software-rendered sample.

The historical EP6 replay used the original environment seed and replayed 750 saved actions from EP3 before the second reset. EP3 initial metadata matched. The second reset differed in the compiled model, physics state and three metadata fields. The old Frame 0 snapshot was left bound to its original model and state. The precise NVIDIA driver trigger and a GPU canary remain open.

On `data`, the isolated `.g2_f27_r1_cpu_371db771_20261120.RHAAPr` directory contains `focused_final.log`, `focused_final.xml`, `candidate.log`, `candidate.xml`, `baseline.log`, `baseline.xml`, `software_gl_receipt.json`, `turnoff_ep6_history_receipt.json`, `turnoff_new_scene_receipt.json`, `offline_online_same_source_receipt.json`, `offline_overlay_f27.xml` and the scene probes. It also contains `original_native_dry_run.json` from the original Root's CLI. That preview yielded 93 `skip_valid` and 807 `execute_missing` with zero models loaded and zero environments created. The evaluator and its original data remained in place. CPU verification used the following test command from the detached candidate checkout with the existing PSM interpreter as `PSM_PY`.

```bash
export CUDA_VISIBLE_DEVICES='' COSMOS_TRAINING=1 COSMOS_INTERNAL=0 COSMOS_DEVICE=cpu
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD:$PWD/cosmos-framework:$PWD/scripts"
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl EGL_PLATFORM=surfaceless
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=2
export __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json
export MESA_GL_VERSION_OVERRIDE=4.6 MESA_GLSL_VERSION_OVERRIDE=460
"$PSM_PY" -m pytest -o addopts='' -q --noconftest --import-mode=importlib \
  g2/tests/test_f27_raster_readback.py \
  tools/v3/eval_v2_production_tests/runtime_evidence_test.py -k f27
"$PSM_PY" -m pytest -o addopts='' -q --noconftest --import-mode=importlib \
  g2/tests/test_f27*.py g2/tests/test_surface*.py g2/tests/test_static_surface_cache.py \
  g2/tests/test_visual_mesh_zbuffer.py g2/tests/test_lazy_surface_view.py \
  g2/tests/test_shared_f27.py g2/tests/test_online*.py tools/v3/eval_v2_production_tests/*_test.py
```

## Native Resume after review

The approved checkout must use the original Run's attested source path and interpreter search path because the vendor runtime identity includes `PYTHONPATH`. Use the original evaluation config, checkpoint, dataset, G2 recipe, nav_sg identity, M16/B8 placement, 120 ms batch window and 2 GiB Policy GPU cache. The saved `resume_exact_config.yaml` in the isolated evidence directory resolves to every value in the original invocation. Its SHA256 is `24cf4a80f56b7a3747ca49291c76cd2f7ab6a6641e6e5a3ccef5ff85f38e6520`. It comes from the archived plan with the original output directory and vendor-lock paths restored.

The Owner supplies an approval file for the independently reviewed deployed pair. `to_root` is the exact checked-out Root SHA. The existing Run digest, frozen Root and Child must match the following fields. Supply the actual Owner decision and independent review references.

```json
{
  "schema": "psm_eval_v2_f27_resume_approval_v1",
  "approved_by": "Owner",
  "owner_decision_ref": "<explicit Owner decision>",
  "review_ref": "<independent review of the deployed repair>",
  "manifest_digest": "513ae651c38cc6d7b069ec7efced5c84bddef735dfd103f68c4b897313d8f654",
  "from_root": "511698256f81267abb4fcf6748b9166ab9ca1b6f",
  "to_root": "<reviewed deployed Root SHA>",
  "child_sha": "5a6585a1308782f52d4601be03771c977a15bf9c"
}
```

Run the read-only preview first. It must show 93 `skip_valid` and 807 `execute_missing`, including TurnOffStove EP6 in the latter group. Full Resume runs the production identity, checkpoint, model config, vendor, recipe and task checks before startup. A mismatch stops execution. The invocation seals the real execution Root, the approval and hashes of Core records retained before that invocation. The original manifest and Core bytes serve as the recovery anchors.

```bash
bash scripts/run_robocasa_eval_v2.sh dry-run --config "$FROZEN_EVAL_CONFIG" \
  --output-dir "$STOPPED_RUN" --f27-resume-approval "$OWNER_APPROVAL"
```

The following is the Owner's manual command after the NVIDIA canary and approval. Use the attested launch interpreter and environment from the original Run. It was left unexecuted during author validation.

```bash
bash scripts/run_robocasa_eval_v2.sh resume --config "$FROZEN_EVAL_CONFIG" \
  --output-dir "$STOPPED_RUN" --f27-resume-approval "$OWNER_APPROVAL"
```
