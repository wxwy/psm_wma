# Issue24 Stage3A — Actual H100 1 Policy Server × 1 RoboCasa Sim C-B1 End-to-End Functional Gate

**Formal verdict: PASS_REAL_C_B1_1SERVER_1SIM_FUNCTIONAL_LOOP_SUBGATE.**

**This is an engineering/integration functional PASS, not a robot task-success PASS, SR improvement, or an optimized-vs-legacy B speedup claim.** A single valid CloseFridge rollout reached the official 900-step horizon, produced 57 policy replans and 56 genuine Local-TTT adaptations, and cleanly ended. The robot failed to close the fridge (valid task outcome: failure, 0/1). This is not the previous invalid startup-failure category.

Reviewer/execution: GPT, 2026-11-08. User explicitly authorized resuming the previously reviewed single C-B1 hardware Gate.

## 1. Immutable implementation identity and exact run profile

| Field | Frozen value |
|---|---|
| Root implementation SHA | 8a17c3db6a2e571b67e6a149638f9d7922a704d5 |
| Child + Root Gitlink SHA | 00f30235da6ffb085a9304ef6501ede509203092 |
| Root / Child reviews | Root Draft PR #25 / Child Draft PR #7, both unmerged |
| Model | Actual RoboCasa Local-TTT L DCP iter_000015000, unchanged weight/config |
| Policy Server | exactly 1, physical H100 GPU6, Bpolicy1, wait0, 30-step UniPC |
| Simulator + shared Wan Worker | 1 real RoboCasa CloseFridge EGL Sim + 1 actual Wan2.2 BF16 eager Worker, same physical H100 GPU4 |
| VAE profile | sim_shared_vae, Bvae1, wait0, current Policy-owned boundary + 15 post-step Worker feature frames |
| Action format | canonical executed raw15; submitted MuJoCo env action 12-D; horizon16 / state15 |
| Seed / task | CloseFridge episode 0, seed 4603, official 900-step task horizon |
| Original C shutdown input | terminate_grace_s remains Python float 15.0 |
| Topology changes | no extra server or Sim, no training, no official V3 source promotion |

Independent detached Formal Pair Root/Child worktrees remained clean before and after the run. The config was derived from the previous source-locked, vendor-approved single C-B1 run, with only fresh output namespace, port and same-version Root vendor-lock path. Public dry-run PASS and strict vendor/code/asset-manifest runtime preflight PASS; only one fresh episode was launched.

## 2. Real hardware and source identity gate closure

Actual Policy on GPU6 and actual Wan Worker on GPU4 both loaded. Root private Worker FD accepted the original 15.0-second shutdown setting (H2 actual path). Worker READY attestation loaded the real Wan and successfully verified strict raw-PyTorch CUDA UUID -> expected GPU-prefixed UUID -> nvidia-smi actual index + PCI (H3 actual path).

Actual Child Actor accepted Root's **full18-source C witness set** via real imports and strict per-file path/SHA256 matching (H4 actual path). It proceeded into physical EGL initialization, actual RoboCasa env reset and real actions. There was no source identity bypass.

Actual EGL render_context proved context_verified=true and physical_identity_verified=true on GPU4: NVIDIA UUID GPU-545d3c6f-e60e-dad5-cb58-b0fd6aceb33b, PCI 0000:98:00.0, strict expected device equal actual device.

## 3. Original on-disk actual closed-loop source & memory evidence

Actual complete qualified run:
- **900 / 900** contiguous actual action source_steps 0..899.
- Every one of the 900 action records has evidence_completed=true, canonical_executed_raw15 length15 and submitted_env12 length12.
- **57** Replan records with strictly contiguous real source_steps 0,16,32,...,896; all match the Native transaction frontier, LocalMemory consumer_step and Policy-owned committed boundary header.source_step.
- Every Replan reports evidence_profile=sim_shared_vae_b1_t1; all57 report encoded_steps=0 for legacy history VAE inside Policy (no repeated server-side history encoding).
- Replan0: no prior completed history, adapted_steps0, prefix_present=false.
- Replans1..56: adapted_steps=16 and prefix_present=true for **all56**; nonzero FastState and fast update norms, positive inner_loss_mean, no replay masquerading as new updates.
- All57 Native batch sizes1, transaction protocol robocasa.session-transactions.b1.v1; all57 raw transaction traces complete, zero overflow/pending CUDA/incomplete spans; per trace feature_verify, boundary capture, Native transaction and Prefix injection are present.
- Actual slot lifecycle reaches SESSION_OPEN, EXECUTING, SESSION_CLOSING and CLEAN. LocalMemory reset_ok=true, rollout_error=null, cleanup_error=null. Media/transaction_fetch error arrays are empty and unquiesced=false. This is the actual C feature path in Policy Action execution, not merely offline Wan/TTT numerical parity.

**No separate downloadable per-frame signed Worker HMAC receipt bundle was exported in this Gate**; signed feature admission was validated by the actual production path and its complete feature_verify/transaction records. This is a limitation of the published evidence granularity, not evidence of an HMAC error.

## 4. Real single-server/single-sim timing

Each actual Policy Replan has its own latency_ms and transaction timing in the authoritative 57 per-Replan records:

| Metric | Actual value |
|---|---:|
| First action/replan | 12,868.486 ms |
| Second replan | 4,443.006 ms |
| Steady replan (exclude the first two), N=55, P50 | **1,517.911 ms** |
| Steady replan N=55 P95 | **1,540.513 ms** |
| Steady replan N=55 P99 | **1,545.243 ms** |
| Steady replan N=55 mean | 1,414.753 ms |
| Feature prepare across 57, P50 / P95 | 89.858 / 100.367 ms |
| Native generation across 57, P50 / P95 | 1,354.515 / 1,368.336 ms |
| Policy queue across 57, P50 / P95 | 0.109 / 0.122 ms |
| Episode actual elapsed | **144.256 s** |
| Formal fresh command | exit_code=0 |

All timing segments can overlap; their independent summary quantiles must not be arithmetically summed into a synthetic critical path. This is one real C-B1 Episode and cannot establish statistical p95 across tasks or a speedup relative to the old B path. A later same-checkpoint, matched same-seed B run would be required for that comparison; no 900EP rerun is needed for this single-server/single-sim workflow.

## 5. Task outcome, end and resource ledger

The official result record says:
- task instruction: Close the fridge door.
- completion: official_horizon, steps900, replans57, environment_success=false, outcome=failure.
- summary status=complete, expected1, valid1, success0, failure1, invalid0, interrupted0, pending0.
- results_qualified=true, clean_execution=true, process_errors=[], unresolved_process_errors=0.
- media diagnostics: errors=[], dropped0, cleanup failure=false, transaction_fetch errors=[], unquiesced=false.
- rollout MP4 exists (532,877 bytes). It was not used as a substitute for model or identity proof.

Process closure evidence: actual Worker GPU4 cleanly exits returncode0; final Actor and Policy Server are terminated as run-owned groups after episode completion; all three process groups have live_group=false and no remaining PIDs. Final GPU4,5,6,7 memory reported 0MiB. Existing training/other GPUs, model weights, official V3/PRs and checkpoints were not modified.

**An environment task failure in one valid run is neither a C pipeline defect nor a guarantee of behavioral parity with B.** It remains legitimate 0/1 task success data, with the normal statistical caveat of N=1.

## 6. Independent raw evidence and immutable identity

Data host evidence root:

/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_h4_8a17c3db_00f30235_C1S1_real_20261108/

Machine-asserted independent summary:

independent_C1S1_B1_real_e2e_evidence.json

Its SHA256:
**401397cb7057471e1ec62029fe9c0c4b53ad383f4ab6aee61da4d8a35955a7af**

Includes checks for the exact SHA/Gitlink, config identity, real EGL proof, Wan Worker READY attestation, all900 actual action source indices/canonical action/evidence_completed, all57 Native transaction frontiers, 56 T1 adaptations and Prefix, zero legacy history VAE, trace completeness, cleanup/MP4, and SHA256 of raw logs/results/predictions/actions/process exit artifacts. Original data and private source/capability material are retained only on the authorized data host.

The transcript also contains dry_run.log/exit, fresh.log/exit, the original sealed Run, per-episode JSONL, LocalMemory lifecycle, server metrics and Worker/source runtime proofs. No source patch, test shim, credential export, model rewrite or fake success was used to pass the Gate.

## 7. Scope and next Gate

**Final formal decision: PASS_REAL_C_B1_1SERVER_1SIM_FUNCTIONAL_LOOP_SUBGATE.**

This validates the first complete C-B1 real RoboCasa Policy Action Path, 15+1 source history and transaction/cleanup on the reviewed pair. **It does not approve full Stage3A A/B/C SR or latency benefit** and does not show the robot learned to close the fridge.

Next recommended narrow experiment is **B original server_vae vs C B1** using the *same checkpoint L, same task and seed, single Policy Server/single Sim topology* and compare first-action, steady replan P50/P95, Step and end-to-end cost and outcomes; optional A No-TTT is a separate checkpoint N and cannot be considered a same-weight Local-TTT ablation. Do not launch a new 900EP or Stage3B B8 Action Path without a distinct Gate; B8 strict numeric/behavioral acceptance remains unresolved. Both PR25/PR7 must remain Draft and official V3 Gitlink unmodified.

**All later review/Inbox docs-only commits do not change the formal tested implementation SHA pair.**
