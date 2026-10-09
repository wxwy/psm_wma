# PSM-WMA V3 — Bounded GPU Smoke Gate Closure / DS_PRO Formal30k Authorization

Date: 2026-10-09
Owner: GPT/Codex (code review and Gate decision **only**; DS_PRO exclusively performs training-server sync, tests, execution and evidence)
Decision: **BOUNDED_GPU_SMOKE_PASS; AUTHORIZE ONE FRESH FORMAL30K RUN BY DS_PRO**
Evidence scope: DS_PRO's user-supplied execution report, plus Github source-path verification. Actual server log and DCP files not fetched by reviewer.

## Exact tested code pair

- GPU smoke executed at root `e940178c77d7c22600f1bcba1f0f38947f5e827d` / child & Root Gitlink `4923e494a8bb0e1e18d7943ae00bd17f71498d88`; 8xH100, fresh `--stop-after-iter 3`, no resumed diagnostic DCP.
- Candidate branches: root `v3-persistent-dataset-index-pair-20261009`, child `v3-persistent-dataset-index-20261009`.
- This review adds only Root docs/ledger. DS execution must use the **resulting new Root HEAD** plus the unchanged Child `4923e494a8bb0e1e18d7943ae00bd17f71498d88`; Gitlink must match.
- Production `V3` and `v3-local-ttt` untouched, unpromoted. Same formal digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`.

## Result: 3-step bounded GPU Smoke PASS at explicitly limited scope

- Exactly 3 rank0 `optimizer_committed` records (iterations 1,2,3) and bounded_stop completed_iteration=3; no iter4; max_iter=30000, warmup=500, save_iter=100 retained; digest equal frozen authority.
- Rank0 outer loss 15.0908 -> 14.9064 -> 14.6508; action 1.23002 -> 1.22677 -> 1.22056; vision 0.27906 -> 0.26387 -> 0.24452; Local inner_mean 0.06897 -> 0.01628 -> 0.00949.
- Rank0 generation, action and Local gradient norms nonzero and finite; `nonfinite_grad_tensors_rank_local=0` in all 3 steps. Local fast_update_mean 0.03164/0.01683/0.01331; valid consumers 256/256/250; native forward/backward 32/32 per step. No reported NaN/Inf, OOM, NCCL error or exception.
- Trainer source review confirms `window.finish` publishes Local candidate only after successful optimizer/scheduler step, and observer emits its successful post-commit record afterward.
- Verified Index warm dataset initialization 192.08s, largely LeRobot 185.85s; accepted as **frozen**, no further dataset startup optimization required.
- Rank0 peak allocated 7.904 GiB and reserved 9.631 GiB, not instrumented per-rank maxima for all GPUs. Step host wall 53.67,43.70,40.41s; CUDA timings available at step3. Reported bounded final DCP `iter_000000003` includes 8-rank model/optim/scheduler/trainer shards and dataloader rank_0..rank_7 states, not proven by direct artifact fetch.
- Diagnostic DCP must be treated **DIAGNOSTIC_ONLY_DO_NOT_RESUME** and never used as a formal seed or same-job resume.

## Missing-gradient diagnosis and disposition

- `missing_grad_tensors_rank_local=0 -> 4 -> 4` is a **count of rank0 selected named parameters whose `.grad is None` at pre-optimizer observation**, not nonfinite gradients and **not sparse-layout gradients**.
- The current observer increments only when `grad is None` and does not log those parameter names. Trainer calls `optimizer.zero_grad(set_to_none=True)` after a step, so a parameter unused in a subsequent conditional/dynamic computation path may have no gradient at that step. Exact root cause and parameter identities are **unknown**; no claim of proven benignity.
- The finite-gradient guard checks non-None gradient validity and presence of at least one selected gradient globally, **not presence for every selected tensor**. Generation/action/Local group norms remained nonzero, so this is **non-blocking technical debt** at 3-step readiness, but requires follow-up.
- Monitor reported missing-gradient count at formal first 100 iterations, especially whether it steadily increases, whether a required sub-group entirely loses gradients, and any concurrent Local/loss anomaly. Do not equate count stability with definite correctness. Identifying the four names would require instrumentation outside the existing report and should be undertaken by GPT code owner only if evidence makes it necessary; DS must not patch production code.

## Decision

Close `CORRECTED-V3-FORMAL-SCHEDULE-BOUNDED-GPU-TELEMETRY-SMOKE` as **PASS**. Permit DS_PRO to initiate exactly one **fresh** full formal30k job with monitoring and existing safety guards. No GPT-controlled server execution is requested/performed. No new GPU smoke or LeRobot optimization solely for existing static findings.

## Exact DS_PRO execution authority

- Single existing `psm_wma_v3` root directory; safe fast-forward this docs-only review Root, ensure Root / Child / Gitlink exact and Child clean. Preserve MM `SESSION.md`, `TODO.md`, Evidence, all prior checkpoints and any root local notes. No worktrees, reset, clean, source patch or upload by DS.
- `HF_HUB_OFFLINE=1`, Child-first `PYTHONPATH`; external existing Verified Index; source/cache/left_wrist/raw15; official DROID DCP fresh initialization. Unique new `--job-name formal_verified_index_30k` under external output root; reject name collision.
- `torchrun --nnodes=1 --nproc-per-node=8 --standalone examples/psm_wma_robocasa_corrected_phase5.py --phase fresh --dataset-index-root <EXISTING_INDEX> --output-root <EXTERNAL_OUTPUT> --source-root <ACCEPTED_SOURCE> --cache-root <ACCEPTED_CACHE> --edge <OFFICIAL_EDGE> --vae <OFFICIAL_WAN_VAE> --base-checkpoint <OFFICIAL_DROID_DCP> --root-worktree <ORIGINAL_ROOT> --expected-root <EXACT_REVIEW_ROOT_HEAD> --expected-child 4923e494a8bb0e1e18d7943ae00bd17f71498d88 --job-name formal_verified_index_30k --t 16 --b 8 --ga 2 --k 4 --world-size 8 --max-iter 30000 --save-iter 100 --warmup 500`.
- **Do not set `--stop-after-iter` or `--preflight` on real training**. The internal preflight must show `execution_scope=full_formal`, digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`, expected-root/child/gitlink match, Verified Index hit.
- Return a summary of rank0 per-step health and full `iter_000000100` DCP state after checkpoint 100, then warmup milestone 500. In the 100-step summary include `missing_grad_tensors_rank_local` distribution and gener/action/Local + Local sub-group norms, losses, inner/fast update, LR progression, 8 rank DCP completeness and current wall/VRAM. Report without intentionally stopping a healthy ongoing job.
- STOP and report on SHA/digest mismatch, index invalidation, data identity failure, numerical nonfiniteness, optimizer update failure, loss/gradient group disappearance, strongly worsening missing-gradient phenomenon together with other anomalies, Local state/frontier or DCP failure, NCCL/OOM, unwanted iter resume. No repeat or parameter workaround without code owner approval.
- A future interrupted formal-job resume is NOT preauthorized merely by diagnostic checkpoint structural validity. Require a separately reviewed same-job resume Gate with DCP/slot/optimizer/scheduler state validation.
- Formal training **does not** authorize production branch promotion, diagnostic DCP resume, benchmark runs, or code modifications.

## Evidence and limitations

- DS report states GPU smoke log `/tmp/psm_wma_v3_gpu_smoke_r1.log` (185 lines, 44,281 bytes) and bounded DCP under external `v3_gpu_smoke_outputs`; neither directly inspected from this environment. Acceptance derives from detailed DS-run metrics + implementation review, not independently rerun GPU.
- Three-step loss decreases are **not** proof that the 30k model will converge.
