# V3 Gate B1 — CPU implementation milestone (not GPU readiness)

**Author:** GPT, 2026-10-14  
**Scope:** isolated root branch v3-gateb1-numeric-implementation-20261014, baseline B0 diagnostic ec9d162b926c4f197f5cfb692499b4dbda888686. Frozen production Index8 and Packed128 implementations unchanged. No GPU authorization.

## Implemented now

- v3_gateb1_metrics.py: CPU FP64 metric computation from captured real FSDP tensor copies; per-optimizer-selected FQN comparisons (generation, action, local), loss-component scalar comparisons, all four Local Fast State tensors, FP32 master DeltaParameter and Adam DeltaM1/DeltaM2 vs whole-weight false pass, FSDP rank-shard descriptors, discrete witness equality, fail-closed missing/shape/dtype/nonfinite/no-family situations. Output is only **candidate threshold** evidence, not B1 approval.
- v3_gateb1_stochastic.py: CPU per-Consumer site-keyed RNG provider reusing B0 ConsumerKey/stable_seed, P0 sigma=0.5, P1 production-shaped waver/uniform/logitnormal sampler+shift, separate keyed vision/action epsilon, keyed text caption CFG dropout (not condition_mask), Action shares Vision sigma when independent_action_schedule=False, reject unresolved distribution or diffusion-forcing missing frame geometry.
- v3_gateb1_fsdp_capture.py: read-only before-optimizer and after-real-step native capture seam. Enumerates all optimizer-selected model FQNs and generation/action/local families; captures actual FP32 master-or-parameter and restored Adam moments, gradient CPU shard copies; validates shard/rank and exactly one optimizer group step (no synthetic moment zero-filling). Does NOT initiate model load/optimizer or GPU activity.
- test_v3_gateb1_metrics.py, test_v3_gateb1_stochastic.py and test_v3_gateb1_fsdp_capture.py: 68 local CPU-only tests passed with torch 2.10.0+cpu / pytest 9.0.2. For local stochastic tests, B0 ConsumerKey/stable_seed shim was copied verbatim from ec9d162b (B0 full module is already present on the GitHub branch); all four pushed Git blobs were checked against local git hash-object. py_compile passed. **Ruff was not installed locally; executor verification needed.**

- v3_gateb1_dcp_transient.py: strict original iter1300 4-component official DCP read seam, with exactly one native rank-local dataloader callback, temporary digest-only target state translation using the already-closed B0 helper, before/after source fingerprint guard, and mandatory finally restoration; never invokes save or Trainer.train. Unit-tested using a CPU fake official checkpointer, NOT yet exercised on genuine FSDP8 GPU.
- test_v3_gateb1_dcp_transient.py: adds 10 CPU mock integration/negative tests (total 68).

## Explicit limitations (not complete FSDP8 Comparator)

- No genuine 8-rank model/DCP load has been executed. The strict DCP seam invokes the official read-only loader only when given real initialized objects after separate Owner GPU authorization or initializes 8-rank FSDP2, injects RNG at all native training call-sites, gathers gradients or runs optimizer steps. B0 paired-run remains deliberately blocked.
- P1 numerical distribution must be confirmed from actual Corrected Phase5 resolved config, and every native stochastic site must be registered; a CPU source-equivalent formula is **not site-injection parity**.
- The proposed FP32/BF16 gradient, Fast State and update/moment thresholds remain UNFROZEN. CPU negative tests establish the checker is non-vacuous; Owner ratification and independent review are required before GPU.
- DS_PRO CPU test only; no 451GB dataset validation, no new offline acceptance, no GPU/torchrun, no checkpoint migration, no formal resume.

## Immediate next implementation work

B1 native transient runtime adapter under this independent branch: official 4-component DCP strict read without persistent writes; in-memory Local Sidecar digest translation; real two-step GA2 native callback discipline and full FQN, moment, Fast State tensor capture; verified per-Consumer Sigma/Epsilon/CFG callsite hooks; Full/Terminal × P0/P1 evidence. Separate Owner GPU authorization only after full code review.

Owner requested V3 full repository audit be deferred to the end. The old B0 CPU gate is CLOSED and must not be repeated.


## 2026-10-14 — Native two-window GA2 and model callsite scope added

- **Exact implementation code SHA:** `5aa79a73a4c6f1a424fa0a9476e1ce52ae9e9361` (parent `738873693920f14e6f45f9f1cd2046108143e234`), isolated B1 root branch; six new files in `tools/gates/`.
- **NativeTwoWindowDriver** invokes the *original* production `GroupedLocalMemoryTrainer.training_step()`, GA=0 then GA=1, for completed source iterations 1300 and 1301 (resulting 1301 and 1302), with snapshot at the real pre-optimizer and post-optimizer/pre-zero-grad boundaries. Per-consumer coordinates computed from actual frozen planner; Index8 index-major calls vs Packed128 single slot-major call; S0 Local Prefix binding checked.
- **NativeOmniMoTNoiseSites** temporarily intercepts only this model instance’s `_get_train_noise_level_vision`, `_get_train_noise_level_action`, and `_add_noise_to_input`. Vision RF distribution and per-consumer shift checked against resolved runtime config; the noiser uses a scoped `TorchDispatchMode` for actual `aten.randn` epsilon draws with exact expected geometry/count and fail-closed extra RNG ops. **Not a global torch.randn monkeypatch**. Runtime site coverage outside noising still requires real code audit.
- **ScopedNativeProducerCFG** keys actual corrected Phase5 text-Transform dropout to B0 canonical ConsumerKey, requires `num_workers=0`, restores both producer and transform instance bindings on errors.
- **build_loaded_native_bridge()** sketches the official FSDP model-to-CUDA → `on_train_start` → optimizer/scheduler/scaler init → strict transient original iter1300 DCP read → direct GA2 driver setup, restricted to isolated /tmp logs. It is an executable seam when supplied with real configured objects but **NOT a finished standalone 8-rank launcher**; it has not loaded a 4B model or DCP in CUDA. External accepted-dataset no-rescan loader for the frozen old Child pair and separate GPU authorization are required before running.
- **Local author verification:** precisely these six new implementation/test files were locally run with Python 3.13, torch 2.10+cpu, pytest 9: **23 passed** and all six py_compile passed. Six GitHub blobs matched `git hash-object` from local files. Ruff missing locally, DS independent CPU Gate pending; no GPU, torchrun, real DCP load or dataset scan performed.
- **DS_PRO one-batch CPU request:** `docs/collab/chatgpt/requests/2026-10-14_DS_PRO_V3_GateB1_native_GA2_modelsite_CFG_CPU_one_batch.md` bound to implementation SHA `5aa79a73...`. This is an incremental Gate, not repeated B0 or a whole V3 audit.
- **Remaining HOLD:** exact frozen 8-rank runtime/load, no-scan accepted-index reader under frozen pair, complete full-model stochastic site coverage and run-to-run proof, numeric threshold Owner ratification, four Full/Terminal×P0/P1 GPU cases, Gate M, Formal30k iter1301. No code here grants GPU execution authority.
