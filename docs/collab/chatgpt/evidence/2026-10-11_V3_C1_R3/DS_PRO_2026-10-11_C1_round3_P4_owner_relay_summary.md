# DS_PRO — V3 C1 Round3 P4 8×H100 Load-only Evidence Intake

**DS date / GPT intake:** 2026-10-11
**Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Formal Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Job:** `formal_verified_index_30k`; **source candidate:** `iter_000000800`.
**Provenance:** This is a faithful structured record of the owner-relayed DS_PRO report. GPT did not directly inspect DS training-host `/tmp` JSON, rank logs, or harness source. All `PASS` values below are DS attestations, not independent re-execution.

## Reported status

| Item | DS status | Facts |
|---|---|---|
| P4-LOAD | 8/8 PASS | One successful 8-rank distributed **Shadow** `checkpointer.load()` returning iteration 800; source `warm_start=False`, keys dataloader/model/optim/scheduler/trainer |
| Model | PASS reported | 6 monitored core probe weights changed and finite; actual production `ModelWrapper.load_state_dict()` invoked, no missing/unexpected-key exception reported |
| Optimizer | PASS reported | Real FSDP2 `OptimizersContainer` flattened 628 state-tensor + 2,198 param-group keys = 2,826 metadata matches, finite |
| Scheduler | PASS reported | `last_epoch=800` all 8 ranks, `base_lrs=[5e-5,3e-4,3e-4]` |
| GradScaler | PASS reported | `enabled=False` and state empty (official disabled bf16 configuration) |
| RNG | PASS asserted by DS | Reported before/after RNG fingerprints changed (6 entries); generated 5-row random streams repeat after setting saved **post-load** state |
| Local Sidecar / GPU Live | 8/8 PASS | Each rank received `_pending_grouped_resume` and executed production `restore_grouped_local_state`; 71–79 live invariants per rank all OK |
| P4-J | 8/8 PASS | 8 ranks: live frontier/scheduler/4 fast tensors per slot/next GA plan match earlier P2 CPU data, `n_diffs=0` |
| P4-MONITOR | PASS reported | Source Formal30k manifest 232→232 `changed=[]`; latest iter800; source config hashes unchanged; GPU global memory total peak 52,051–53,819 MiB with external robotwin_server on each GPU |

**Shadow Root:** `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/`.
**Shadow Job Name:** `formal_verified_index_30k_shadow` — separate path and files, not original Formal30k.
**Original Job:** `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/`.
**Expected full config digest:** `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`; DS report says exact match.
**Run wall (success attempt):** ~218–222s/rank; monitor ~260.6s.

## P4 Harness execution chronology (important)

The report explicitly reveals **four total attempts**, not a single job invocation:

1. Attempt1: wrong working directory, relative model config path unavailable; `FileNotFoundError` before the required DCP load.
2. Attempt2: real DCP load succeeded to iteration800; external harness falsely asserted optimizer `state`/`param_groups` ordinary layout rather than FSDP2 flattened layout.
3. Attempt3: harness wrongly expected enabled GradScaler scale, while production `GradScaler(enabled=False)`; DCP load had already passed.
4. Attempt4: all harness assertions and 8 ranks PASS.

DS says all failures and revisions are in `/tmp/ds_pro_v3_c1_round3/load_run.log`, and no production code, checkpoint, or original Formal30k paths were modified. The monitor's `first_load_exception=None` appears scoped to the successful monitored attempt, **not to all four attempts**.

## Reports and original Evidence left on DS server

- `/tmp/ds_pro_v3_c1_round3/p4_load.py`, `load_run.log`, `rank_{0-7}.json`.
- `/tmp/ds_pro_v3_c1_round3/p4_monitor.py`, `monitor_summary.json`, `gpu_baseline.json`, `gpu_samples.csv`, `proc_samples.csv`, `job_before_manifest_r3.json`, `job_after_manifest_r3.json`, `job_invariance.json`.
- `/tmp/ds_pro_v3_c1_round3/p4j_crosscheck.py`, `p4j_result.json`.
- Prior CPU reference `/tmp/ds_pro_v3_c1_round2_p2/p2_result.json`.

## Explicit limits of the relayed text

1. The report does **not** enumerate `trainer/.metadata` keys containing `rng_state_0` ... `rng_state_7`. Changed state plus self-replay alone does not identify the persisted checkpoint as the source of the restored state.
2. Attempt1–3 first exceptions exist, but `first_load_exception=None` is reported for P4 monitor; do not merge per-attempt success/failure into an invented single successful initial attempt.
3. GPU peak above is total *device used* including pre-existing robotwin_server. No separate per-rank `torch.cuda.max_memory_allocated/reserved` values are shown in the summary; do not invent these.
4. Shadow strict Load-only is not iter801 loss/gradient/optimizer-step parity, policy success, or authorization to resume the original job.

**DS conclusion:** `C1_RESTORE_PASS`. **GPT formal Evidence decision:** see `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_R3_P4_evidence_review_444c232b_e9b8a41.md`.