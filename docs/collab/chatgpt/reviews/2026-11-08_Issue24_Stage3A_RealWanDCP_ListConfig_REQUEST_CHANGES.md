# Issue24 / Issue23 Stage3A — GPT 独立真实 H100 Wan/DCP Gate: REQUEST_CHANGES

**Formal verdict for new REAL-MODEL functional Gate: `REQUEST_CHANGES`**.

**Scope note: previous Stage3A `APPROVE_CODE` applies to frozen CPU/static Code Gate and is NOT retroactively replaced.** This is the **next distinct real-Wan/DCP functional Gate**, which has been executed and is blocked by a newly uncovered actual-model configuration compatibility defect. No complete B/C numerical parity, native server/simulator latency or SR result exists for this attempt.

- Date: 2026-11-08, Owner issued “继续” after CPU approval; only bounded real DCP/Wan B1 parity preflight, **not** 18×2/900EP, large SR, training or merge.
- Exact formal pair remains **Root `ef82fe02ee73e3c804b83ffbd68c5123c1377fa2` / Child+Root Gitlink `6842b329f71fff8b9813b2d00b83edfc61e3e505`**. Root PR #25 later docs commits do not change target. Child Draft PR #7 unchanged. No new code review of the unchanged pair was performed.
- Frozen input: actual RoboCasa Local-TTT DCP checkpoint `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019/checkpoints/iter_000015000`, same path `config.yaml`, original target-atomic left+wrist recorded RGB. Actual H100 GPU6 (Policy), planned independent GPU4 Worker. GPU4–7 idle at preflight, GPU0–3 unrelated training untouched.

## Finding H1 — HIGH, PRODUCTION BLOCKER: actual Hydra/OmegaConf ListConfig cannot be hashed into C-mode Loaded VAE Identity

- **Location** Child `cosmos_framework/inference/robocasa_vae_daemon.py:47–66`, specifically `config["encode_exact_durations"] = tokenizer.encode_exact_durations` (around line 58) passed unmodified into `canonical_json(config)` at line 66. Call chain `loaded_vae_identity():97` and Child `cosmos_framework/scripts/action_policy_server_robocasa.py:1064–1088` in real `sim_shared_vae` C initialization.
- **Actual independent witness**: a frozen-source H1006 process **successfully loaded the real iter15000 DCP and reached `loaded_vae_identity(model.tokenizer_vision_gen)`**, but raised `TypeError: Object of type ListConfig is not JSON serializable` rethrown as `cosmos_framework.inference.robocasa_vae_protocol.ProtocolError: invalid canonical JSON`. GPU policy process exited with nonzero, no worker/Sim or Action path was launched, GPU4–7 return 0MiB. The actual model exposes OmegaConf `ListConfig` as an effective tokenizer setting; the production identity helper assumes native JSON types.
- **Independent zero-GPU reproduction** on the exact same frozen Child: `types.SimpleNamespace` with `encode_exact_durations=OmegaConf.create([17,61,73])`, all other supported fields primitive; calling **real** `worker_constructor_config` raises **same `ProtocolError`**. This excludes GPU OOM, weight corruption, resource ownership, task behavior or a genuine B/C VAE numeric mismatch as the cause.
- **Frozen contract violated**: Stage3 design requires C Worker + Policy compare immutable identity computed from **actually loaded** Wan weights/config/scale and enable B1 `sim_shared_vae` with actual DCP checkpoint, before any Action feature admission. An inability to serialize legitimate effective runtime Hydra config makes the C profile fail at startup. Existing synthetic CPU fixtures used normal Python list, missing realistic model container type.
- **Remediation acceptance** (narrow): At the original actual-loaded-model identity seam, normalize only supported OmegaConf `ListConfig` / `DictConfig` values to ordinary canonical primitive Python list/dict **without changing order, lengths, field names or model/encoder math**. Validate integer semantics/bounded shape and reject unsupported/ambiguous objects; `None` behavior stays explicit. Ensure the same frozen constructor configuration is used for both Policy and Worker and the resulting loaded-state hashes remain authoritative; do not disable identity check, truncate ignored fields, replace with a supplied string/model name, serialize via `str`, or quietly rewrite a cache/Resume contract. Add focused **real OmegaConf ListConfig fixture** at `worker_constructor_config` and `loaded_vae_identity` entrance; test equality against equivalent primitive list, changed values/config mismatch fails closed, and Root/Child C CLI bootstrap test reaches identity construction without training/GPU. Retain all existing Stage3A author and legacy A/B regressions.
- **New formal pair required**: Codex must implement and submit new Child SHA & Root Gitlink SHA even if the change is one line/test only; no inheritance of previous CPU approval. Provide focused independent repeatable CPU evidence, diff and formal pair, then request fresh GPT Code Gate **before** another real H100 execution.

## Evidence provenance / state

Isolated reviewer evidence-only scripts, no project source modified, stored on authorized `data`:

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_stage3a_real_gpu_b1_parity_20261108/`

- `policy_features.log` — real DCP load, actual exception `ListConfig`.
- `policy_features.json` — `status=FAILED`, actual phase `policy_features`, no B/C numerical results.
- `omegaconf_ListConfig_CPU_repro.json` — isolated exact-branch actual helper reproduction, no GPU.
- `b1_wan_dcp_cross_gpu_probe.py` — isolated reviewer H100 test protocol. **Only `policy_features` phase was attempted**; planned `worker_features` / `policy_compare` NOT RUN due to hard fail at identity check.
- Real reviewer checkout Root `ef82fe02...`, Child `6842b329...` unchanged/clean; all GPU4–7 0MiB post-exit; no training, no real Sim, no checkpoint write, no V3 merge.

## Next Gate after Codex fix

1. Re-review **new exact pair** CPU/static before any GPU.
2. Re-run same true H100 single Policy DCP iter15000 on GPU6, true independent Wan Worker on GPU4, compare actual Loaded VAE identity; complete B1 current-policy pre-crop Visual96 and corresponding Worker non-boundary Visual96; measure strict B1 same-source numeric.
3. On same L weight, compare T16 vs16×T1 FastState, Prefix and native Action for 2 fixed real RGB history chunks. Report maxabs/meanabs, exact equality, prior stochastic repeat control separately. Nonzero means **numerical Gate must be reviewed**, not silently accepted.
4. Only if real B1 fixed-input Gate passes can Owner-authorized 1 Policy Server×1 Sim C real EGL/actual poststep functional smoke be considered. P0 A/B/C SR/cost benefit is a distinct Gate. B8 Action remains prohibited.

**Final: `REQUEST_CHANGES` for Issue24 Stage3A H100 real model startup, Finding H1 HIGH.** This is not a request to redesign Stage3A or undo previous CPU APPROVE_CODE. Formal review document + canonical Inbox append required for persistence.
