# PSM-WMA V3 — FSDP2 w0_fast Parity Gate B Closure / Formal30k Fresh Authorization

Review date: 2026-10-10 (DS_PRO evidence report dated 2026-10-09)
Final code owner / Gate adjudicator: GPT/Codex
**Decision: Gate A GREEN, Gate B PASS, AUTHORIZE DS_PRO-ONLY fresh formal30k training.**
This supersedes the earlier temporary FORMAL30K HOLD. Existing V3 TBPTT/Local-TTT architecture stays **unchanged**; no new gradients are propagated between detached Segments.

## Exact observed source pair and doc-only successor

- DS_PRO executed candidate **Root `145e5aa91510804284edeba8776fd407ccc49fb9`**, Child/Gitlink **`71e03c8501c94a2ad5fed60955af657d3f945b85`**, with clean Child and Root containing permitted MM `SESSION.md` / `TODO.md` and DS-only Evidence. The new Root SHA is the commit **containing this Review/Inbox update**; it is docs-only, so Child+Gitlink remain **`71e03c8501c94a2ad5fed60955af657d3f945b85`**.
- Candidate Root: `v3-persistent-dataset-index-pair-20261009`; candidate Child: `v3-persistent-dataset-index-20261009`.
- Production Root `V3` / Child `v3-local-ttt` were not modified or promoted.
- Formal config digest frozen at `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`. The exact code SHA is a separate authority witness because digest by itself does not encode implementation source.

## Gate A — CPU/static acceptance

- DS's preceding full targeted pytest (five tests files) was **110 passed, 2 skipped**. In the last revision, the only Child diff was removal of a single trailing EOF newline from `local_memory_fsdp_scan_test.py`; this is semantic no-op, so tests are **CARRIED_FORWARD**, not independently rerun at the latest commit.
- DS executed Ruff **0.12.7** `format --check`: 2 already formatted; `check`: all passed; `python -m py_compile`: pass on the network+FSDP parity test. Gitlink triple SHA exact and Child clean.
- **Gate A verdict GREEN**, no further CPU repetition warranted by docs-only Root commit.

## Gate B — 8xH100 real bounded distributed verification

- DS_PRO executed one fresh `torchrun` job `bounded_w0_fsdp_parity_r1` with `--stop-after-iter 3 --audit-missing-grads`, existing exact-window Verified Index, official Cosmos3-Edge-Policy-DROID-dcp, T16/B8/GA2/K4, formal max_iter=30000/warmup=500/save_iter=100 and unchanged frozen digest.
- Rank-wise audit: **24/24 `AUDIT_OK`**, covering ranks 0..7 and optimizer iterations 1..3, all with `audit_errors=[]`, `selected=314`, `present=314`, `missing=0`, no missing names. Group inventory per rank action=5, generation=289, local=20.
- This includes iter2 **all continuation** (previously four `w0_fast_*` were `grad=None` on each rank) and iter3 **mixed new/continuing Slots** (previously rank-divergent 4-vs-0 missing). Now all four w0 gradients are present on all ranks/steps and the FSDP2 gradient-bearing parameter lists no longer diverge **for the audited parameters**.
- Exactly three rank0 `optimizer_committed`, `bounded_stop.completed_iteration=3`, no iter4; finite rank0 gradient norms with `nonfinite_grad_tensors_rank_local=0`; all observed local core w0 grad tensors present (`local_core_grad_tensor_count=11`), nonzero fast state update signal, no reported NCCL/FSDP collective errors, NaN/OOM or traceback.
- Step wall rank0 ~42.6/42.6/40.2s and peak reserved ~9.63 GiB rank0; 8-rank per-step missing audit completed. DCP `iter_000000003` reportedly contains 8 model/optim/scheduler/trainer shards and 8 rank dataloader state files; is **DIAGNOSTIC_ONLY_DO_NOT_RESUME**.
- DS log locations: `/tmp/psm_wma_v3_w0parity_r1.log`, `/tmp/psm_wma_v3_w0parity_r1_ranks/eb5f62d9-1981-4e55-b0c5-a06aeea886a9_yga3zqqj/attempt_0/{0..7}/{stdout,stderr}.log`. Evidence provided as user-pasted DS report; raw training-host file bytes not independently retrieved by GPT.
- **Gate B verdict PASS at bounded-3-step scope.** Present-gradient uniformity is a necessary distributed participation property, *not* a mathematical allreduce/numeric equivalence proof for all 30k iterations. It is sufficient together with the finite loss, three successful optimizer steps, DCP readiness and prior targeted tests to open monitored formal fresh training.

## Preserve original TTT/TBPTT contract

- Original PSM-WMA V3: `w0_fast_*` initialize **new** episodes/slots; Local inner updates within T=16 use `create_graph=True`; the committed Sidecar fast state is detached across Segments (truncated BPTT), with fast state values carried across Segments.
- The fix provides an all-continuation `torch.where(all_true, detached_state, fresh_w0)` forward-equivalent, zero-gradient path so FSDP2 parameters participate uniformly across ranks; it does **not** propagate outer loss from a continuing segment back to the prior segment's `w0`.
- **No design change**: no unbounded BPTT, no Episode-wide meta-gradient, no state or optimizer restructuring. Under zero-valued grad, existing Adam moments/weight decay may update w0 rather than skip it as when grad=None. This is an accepted side-effect of the FSDP2 participation correction; not falsely claimed as identical optimizer numerics. Do not optimize 185s LeRobot warm startup further.

## New owner authorization — DS_PRO executes, GPT never launches

1. **Authorize exactly one new fresh formal30k job** on the same verified Child SHA and the new **docs-only exact Root HEAD** pinned by this Review. DS_PRO is the *only* training-server operator. Before launching: original one `psm_wma_v3` directory, safe fast-forward only, never overwrite MM `SESSION.md`, `TODO.md`, previous Evidence/DCP, or create extra worktrees/reset/clean. Check Root HEAD, Gitlink, Child HEAD all match owner handoff and Child clean.
2. Set `HF_HUB_OFFLINE=1` and Child-first `PYTHONPATH` against old editable install. Use existing source/cache and external Verified Index, official DROID DCP; verify index fingerprints, root/child lock, DROID model witnesses and frozen digest on automatic Phase5 preflight.
3. New unique external formal output namespace, proposed `formal_verified_index_30k`, if and only if it does not already exist. `torchrun --nnodes=1 --nproc-per-node=8 --standalone examples/psm_wma_robocasa_corrected_phase5.py --phase fresh` with `--dataset-index-root`, `--output-root`, `--source-root`, `--cache-root`, `--edge`, `--vae`, `--base-checkpoint`, `--root-worktree`, `--expected-root <NEW_OWNER_REVIEW_ROOT_HEAD>`, `--expected-child 71e03c8501c94a2ad5fed60955af657d3f945b85`, `--job-name formal_verified_index_30k`, `--t 16 --b 8 --ga 2 --k 4 --world-size 8 --max-iter 30000 --warmup 500 --save-iter 100`.
4. **Omit `--stop-after-iter`, `--audit-missing-grads`, and `--preflight` in the real full run.** Phase5 internally executes strict preflight, then full training. Confirm `execution_scope=full_formal`, model source from official DROID and frozen digest. Bounded iter3 DCP never resumed/used as formal initialization.
5. Health checkpoints: DS reports at **iter100** (the first saved DCP) and **iter500** (warmup completion), without intentionally interrupting a healthy job. Report outer/action/vision/inner losses, gradient norms (generation/action/local), `missing_grad_tensors_rank_local` (expect 0 on rank0; report any nonzero), LR/warmup, active slots/fast state/fast update, full 8-rank DCP structure, per-step wall and peak VRAM. If evidence suggests loss/gradient divergence, inform GPT promptly and follow STOP conditions. The 3-step zero-grad result is not convergence proof.
6. STOP on SHA/Gitlink/config digest mismatch, index invalidation, DCP or data identity failures, nonfinite loss/grad, missing required gradient groups, a renewed w0 missing-grad anomaly, Local frontier/fast update errors, NCCL/OOM/optimizer failure, wrong iteration or formal namespace collision. DS may not change code/hyperparameters, reduce batch, relax checks or self-resume. An actual interruption requires a separately approved same-job strict-resume Gate after artifact inspection.
7. This authorization **does not** authorize production-branch merge, diagnostic DCP resume, new code edits by DS, evaluation workloads or parallel experiments. No recertification of previously closed VAE/Index gates merely due to this docs-only review.

## Verdict

**`CORRECTED-V3-W0-FAST-FSDP2-GRADIENT-PARITY-GATE` CLOSED/PASS at targeted CPU + bounded 8xH100 scope.** Existing TTT architecture frozen. Formal30k fresh may be started by DS_PRO using the next exact Root HEAD + Child `71e03c8501c94a2ad5fed60955af657d3f945b85`. Production branches remain untouched.
