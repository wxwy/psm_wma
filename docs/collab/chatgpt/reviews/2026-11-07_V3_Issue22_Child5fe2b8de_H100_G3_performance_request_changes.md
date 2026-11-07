# Issue22 Local-TTT Streaming — independent H100/G2/G3 Performance Gate

- Date: 2026-11-07 (Asia/Shanghai).
- **Gate finding**: `REQUEST_CHANGES` — **HIGH performance blocker**, not a numerical correctness failure.
- Candidate Child `5fe2b8def58f4caae8c63581ed3649ac8fb3e0c6` vs base `1ca308055fc41fb69efaeb9efaa23808f164a18e`.
- Isolated local test Root SHA: `4c04f887d78518fe9a98be851dd075a3f2bdb5ee`, Gitlink pinned to `5fe2b8de`. This is **not** official V3; no official V3 Gitlink changed, no source hot-switch during a formal run. Old baseline frozen Root `c447d9f4cc1bb5fe2dd79ca527c5a8e246565ada`, Child `1ca30805`.
- GitHub Child Draft PR #4 new findings: https://github.com/wxwy/cosmos-framework/pull/4#pullrequestreview-5811441395 (COMMENT only: GitHub API forbids own-PR REQUEST_CHANGES; literal shown here indicates reviewer's requested disposition, **not** native GitHub blocking state).
- Prior independent **CPU static candidate assessment remains unchanged**: no confirmed HIGH code contract violation from that earlier evidence. This is a fresh GPU/performance evidence Gate, not redundant code re-review.
- Evidence location (data server, distinct run outputs): `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/v3_issue22_gpu_gate_20261107/`.

## G1 — Real H100 numerical evidence: PASS

1. Actual Wan2.2 VAE BF16 weights `Wan2.2_VAE.pth`, GPU6: Policy pre-crop Visual96 capture vs independent Encode1 over A→B→A all max_abs=0. Exact source parity, no redundant boundary-frame encode. Evidence `g1_real_wan_visual96_h100.json`. This subtest did not load the trained DCP but used genuine Wan weights.
2. Genuine RoboCasa Local-TTT iter15000 DCP + frozen train config, GPU6: T16 vs 16×T1 model-owned FastState/token/Prefix max_abs0, inner telemetry differences0. Evidence `g1_real_dcp_fast_state_parity.json`. Initial test harness incorrectly dereferenced `model.local_memory_runtime` instead of `model.net.local_memory_runtime`, failed *before comparison*; harness corrected in isolated test workspace; second attempt passed exit0. Candidate production code unchanged.
3. Same real trained DCP, 30-step UniPC action sampling, seed0, identical observation, Prefix from whole vs streaming: action tensor 17×15 (state row included) max_abs0, exit0. Evidence `g1_real_dcp_action_parity.json`. Single deterministic request parity is not full simulator regression coverage.

## G2 / G3 — matched 36-episode real RoboCasa: correctness PASS

- Same iter15000 DCP, 18 tasks × 2 Episodes (36 total), seed0, phase_b M16/B8, 2 Policy Servers GPU6/7 + 32 Sims GPU4/5, 30 diffusion steps, H16/raw15. Two **separate** fresh output dirs and manifest model identity; only source Child differed. Candidate G2 output `g2_issue22_pipeline_18tasks_2eps` (root4c04f887/child5fe2b8de); original G3 output `g3_old_local_baseline_18tasks_2eps` (rootc447d9f4/child1ca30805), run sequentially.
- **Both**: `valid=36, success=18, failure=18, invalid=0, pending=0, results_qualified=true, clean_execution=true, unresolved_process_errors=0, exit_code=0`. Qualified 36/36 is **not** a 900-episode generalization claim.
- G2 pipeline finished UTC 2026-11-07 09:21:15; G3 baseline finished UTC 09:35:35. Both cleaned up, no GPU4–7 processes remained at end. Real DCP and real sim used, not CPU synthetic.
- New pipeline GPU6 native Batch histogram `{1:604,3:1}`; GPU7 `{1:529,2:2,3:1}` → mean batch≈1.00/1.01; old GPU6 mean 3.34, old GPU7 mean 2.80. B8 native aggregation **collapsed**.
- `g3_matched_performance_results.json` combines original per-prediction `predictions.jsonl` timing and Episode data (1,145 pipeline vs 1,100 legacy requests). Independent analysis script in isolated test folder; first run failed only because tuple keys of task/episode map were non-JSON-serializable, then corrected in isolated analyzer and succeeded; **not** a production bug.

## Measured performance (G3 FAIL)

| Metric | Candidate pipeline | Old Local-TTT baseline | Observed |
|---|---:|---:|---|
| EP/h (manifest-to-summary, includes init) | 82.53 | 170.37 | **−51.6%** |
| Mean Episode elapsed | 890.30 s | 284.72 s | ×3.13 |
| Client request P50 | 25.23 s | 4.61 s | ×5.48 |
| Queue P50 | 23.02 s | 1.40 s | ×16.40 |
| Queue P95 | 38.88 s | 5.98 s | ×6.50 |
| Batch Prepare P50 | **0.107 s** | 1.056 s | **−89.9%** |
| Batch Prepare P95 | 0.144 s | 2.483 s | −94.2% |
| Native Generation P50 | 1.916 s | 1.980 s | close |
| Actual average GPU6/GPU7 batch | **1.00 / 1.01** | 3.34 / 2.80 | serious B8 failure |

The intended replan preparation optimization **worked**, but queue amplification destroyed throughput. This is enough evidence for **HIGH performance Gate blocker** even though correctness/transaction Gate passed. Short 36 episode run; not a claim about full 900 EP distribution.

## Concrete code focus and remediation contract

**Severity HIGH**, focus `cosmos_framework/inference/robocasa_batch_transactions.py:354–402`:
- L359 selects only `_pipeline_ticket_ready()` members.
- **L378–388** computes available native batch wait `self.wait_s - (now - self._enqueued[oldest.key])` from original *enqueue* timestamp while ticket can wait on causal evidence for many seconds before becoming READY. Thus 20ms wait budget may have already expired when a ticket is first runnable; B1 singleton seal likely. Shared `_execute_completed` model executor interleaving may contribute; **do not assert sole proven cause before profile**.
- Acceptance: establish readiness-based aggregation (or equivalent scheduler strategy) under unchanged **immutable original ticket deadline**; preserve no-future evidence, no action until all prior evidence completed, fixed Session/Lease/epoch/ACK/abort/retry semantics. No architecture rewrite.
- New regression: multiple initially-not-ready tickets whose prerequisite T1 scans finish at staggered times `>20ms` after enqueue; assert compatible READY requests yield B>1 in bounded wait without extending deadlines; stale, duplicate, changed evidence, cancel/timeouts fail closed and no starvation.
- Fresh independent CPU/GPU G1 and matched G2/G3 36EP rerun under new candidate SHA, same config; qualified + action/state parity and no material EP/h throughput regression vs old baseline. Require real histogram, P50/P95 Queue/Prepare/Gen, GPU utilization, elapsed. If failure remains investigate further, do not claim B8 restored by synthetic tests alone.

## Authorization / disposition

**No merge, no official V3 Gitlink update, no reinterpretation of the preceding CPU-only PASS.** The previous candidate-level static review identified no production contract blocker; this new GPU performance finding prevents claiming the optimization objective is met. The linked account owns the PR, so GitHub blocked native `REQUEST_CHANGES` with 422; review comment id `5811441395` records the clear requirement. On new Child SHA, repeat narrow fresh review with evidence and exact pair. Formal production approval remains OPEN, not implied by correctness PASS.
