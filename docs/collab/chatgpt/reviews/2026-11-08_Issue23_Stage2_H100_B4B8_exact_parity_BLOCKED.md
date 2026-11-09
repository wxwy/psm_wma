# Issue23 Stage2 — Independent Real-Wan H100 Batch Numerical Gate

**Verdict: `BLOCKED_NUMERICAL_PARITY`** — required exact=0 VAE latent/Visual96 equivalence fails for **B4 and B8**. This is a **new GPU numerical Gate** only; it does **not** revoke previously validated Stage1 standalone CPU `APPROVE_CODE` and does not imply a code defect has been localized.

- Owner authorization: Stage2 real Wan2.2 BF16 B1/B4/B8 numerical, shared Sim-GPU/EGL contention experiment; **not** Stage3/production/900EP.
- Frozen isolated source: Root `3ab4578475d8df5ce93b7bde6c4f2073a46f777e` / Child+Gitlink `0a2119782fb5078fee3359f9ef7383d788744458`. Exact repos clean before and after.
- Real model: `Wan2.2_VAE.pth`, SHA256 `20eb789667fa5e60e7516bf509512f6cb61f01b0aa0695eadaea930c13892b36`; Wan 704,688,668 params, frozen BF16, eager (B1-AOT not installed/used). GPU4 H100.
- Input: 8 distinct actual RoboCasa365 v3 target-atomic recorded `robot0_agentview_left` + `robot0_eye_in_hand` composite RGB images, 256×512 HWC uint8, frame indices 0,8,...,56; original policy preprocessing equals standalone helper **exactly** (source/padded/size). Input SHA per frame in raw JSON.
- B1 reference: official Child policy-independent `encode_current_composite_visual96(tokenizer,prepare_robocasa_composite_frame(image))`; candidate Stage1 `LoadedWanEncode1` run on exactly the same frozen tokenizer and same images. Latent is full **pre-crop** [8,48,12,20], not model's postcrop latent. `torch.cuda.Event` used for timing, explicit wait between batch results, no other GPU4–7 process while testing.

| Actual test | Full pre-crop latent max/mean absolute diff | Visual96 max/mean absolute diff | Exact hash |
|---|---|---|---|
| B1, eight independent T1 | 0 / 0 | 0 / 0 | ✅ both |
| B4, two batches | **0.03125 / 0.00161667005** | **0.00650634617 / 0.00078859966** | ❌ |
| B8, one batch | **0.0234375 / 0.00165186205** | **0.00713452697 / 0.00083547598** | ❌ |

The observed BF16 multi-batch shape change produces nonzero values in both latent and downstream Visual96. Cause has not been narrowed to cuDNN/GEMM dispatch vs other numerical effects, and no behavioral effect on Local-TTT FastState/Prefix/Action/SR was measured. **Do not call it a proven algorithm bug or harmless drift**.

Single-frame B1 **does** preserve exact source numerical equivalence. Stage0's gate contract had frozen **zero difference** for B>1, with any proposed tolerance required to be approved *before* using future evaluation data. No tolerance existed; therefore **B4/B8 numerics are blocked**. Do not retrospectively choose a threshold just above measured 0.007135. A new proposal may evaluate distinct holdout samples + downstream action/SR sensitivity with independent review, or stay with Sim-side shared B1 (no wait, preserves numerical source) and reap *pipeline overlap* without GPU multi-batch.

**Performance not established**: only eight inputs, first ever B4/B8 calls include potential first-run backend/kernel effects. Reported initial total CUDA elapsed: independent reference B1 35.49ms; new adapter B1 63.33ms, B4 76.87ms, B8 71.28ms. These are **not warmed throughput benchmarks** and do not support a definitive speed conclusion. The 16Sim EGL+Worker contention study was **NOT RUN**, deliberately held behind the numerical Gate; full Policy/TTT and SR also **NOT RUN**. These restrictions are important for the performance objective.

## Evidence and controls

All artifacts under `data:/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/v3_issue23_stage2_resource_gate_20261108/`:

- `stage2_real_wan_microbatch.py` (isolated test harness, SHA256 `bece0660d2ce4fbff4efb04dd0a9ba67273550f72d09a9ce508e2a63b21812b4`).
- `stage2_real_wan_microbatch.log`, `stage2_real_wan_microbatch.json` (SHA256 `42d611738c738a3ea085c01356cdd04f02db2c247c90d254830b2d738342a4f`), `stage2_real_wan_microbatch.exit`.
- `stage2_numerical_gate_result.json` with `result=BLOCKED_NUMERICAL_PARITY`; explicit `egl_16sim_contention=NOT_RUN_BLOCKED_BY_NUMERICAL_GATE`.
- GPU4–7 post-test: all 0 MiB, GPU 0–3 unrelated train untouched.
- Note: harness shell exit0 means test ran/computed and **properly recorded a FAILED NUMERICAL GATE**, not approval. Machine-readable `status` is the authority.

Resource precondition was initially blocked by owner-controlled `gpu_load_sim.py` stress, then user explicitly authorized stopping only that exact tmux `gpu` process; post-stop GPU4–7 were clean, and model test ran after clean exclusive preflight.

## Decision and stop

**Stage2 full acceptance OPEN/BLOCKED; Stage3 prohibited**. Codex may prepare a docs-only constrained diagnostic/alternate proposal. Do not modify Child production math, waive numerical tolerance silently, merge PR6/PR4, update official Root V3 Gitlink, or launch 16Sim/EGL/paired SR as if B4/B8 were validated. Owner needs to choose which branch to advance:

- Strict zero: **Sim shared Worker B1/wait0**, use cross-GPU overlap rather than per-call microbatch to seek throughput; submit a scope-adjusted Stage2 B1-only EGL/perf Gate.
- New B4/B8 tolerance proposal: independently justify numeric differences with controlled kernel diagnostics and new holdout, preregister tolerances and prove downstream FastState/Prefix/Action and SR acceptability. No automatic passage from this observed result.

GitHub Issue23 evidence link: https://github.com/wxwy/psm_wma/issues/23#issuecomment-6715545305
