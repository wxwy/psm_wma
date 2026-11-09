# Issue31 — Prefix-aware text K/V: independent incremental review request

Author: Codex. Status: **REVIEW**, not an independent approval. Date: 2026-11-09 CST.

Local-TTT currently disables native text K/V reuse whenever a Memory Prefix is
present. This candidate fills the text cache once per generation request and
skips repeated text-tower work, while projecting and injecting the current
Prefix on every layer and every denoising step.

## Exact implementation identity

| Object | SHA |
|---|---|
| Formal Root | `5b89f3eddbfe27ee72c173696a386e0b756d7866` |
| Child / Root Gitlink | `4446be0f6dad9b6dc887ef90af52d0af754d4682` |
| Approved unmerged baseline Root | `53b5273c7907e2d7a8fb1831ac0e0ec8b9fa973a` |
| Latest baseline Root documents, preserved | `ca3a08acf8697b5ff316fcc476c4f0820d8f3b13` |
| Baseline Child | `4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe` |

Draft [Root PR32](https://github.com/wxwy/psm_wma/pull/32) and
[Child PR10](https://github.com/wxwy/cosmos-framework/pull/10) are separate
candidates stacked on the existing history-K branches. Later evidence/Inbox
commits do not replace this Formal Pair. Prior PR29/30 and Child8/9 are unchanged.

## Implementation and scope

- `omni_mot_model.py`: enable only eligible B1/single-sample, two-way,
  guidance=1, inference requests. Allocate caches inside the generation call;
  clear even partially populated caches in `finally` and restore dispatch.
  `use_prefix_text_kv_cache=False` retains the original Prefix-on reference.
- `inference_text_kv_memory.py`: carry explicit Prefix length and native padding;
  require the complete current Prefix on every forward. First step fills UND
  K/V; later steps reuse UND K/V while retaining the native attention layout.
  Dynamo symbolic booleans use direct branches, not `SymBool != bool`.
- `unified_mot.py`: pass current Prefix context through the gen-only decoder.
- `cosmos3_vfm_network.py`: narrowly permit this explicit inference-only memory
  state with the existing Local-TTT guards; other unsupported paths stay closed.
- `attention.py`: inference-only private capture of UND K/V from the **actual
  materialized native GEN attention K/V buffers**. Preserve native padding,
  varlen/backend and Prefix assembly. Return empty unused GEN cache sentinels
  so exporting pre-scatter GEN tensors does not alter compiled rounding.
- One new Child test file; Root adds only benchmark and its CPU checks, Gitlink,
  and bookkeeping. Exact tracked differences and protected-method AST hashes
  are archived in `scope.json` and full `root.diff`/`child.diff`.

Pack-template reuse with Prefix remains disabled. There is no second-stage
packing/backend optimization, precision change or recompile-limit increase.
No training, VAE, Sim/Worker, scheduler, model-mode/DCP validation or strict
K/H/M/B Resume changes. `_encode_action`, `_decode_action` and
`scan_local_memory` have identical ASTs to baseline. No V3 merge or deployment.

The hit path reconstructs dummy UND queries to preserve native attention
operands/padding and discards their outputs. This deliberately retains some
attention work to keep numerical equivalence; it does not claim the entire
No-TTT fast path or its historical latency.

## Focused author CPU/static evidence

Exact clean Pair: **187/187 PASS**, zero failures/errors/skips, Shell 0,
`gate.status=PASS`, **1486/1486 source fingerprints unchanged**. Eight changed
source/test/tool files pass format, AST and scoped Ruff checks.

Tests include real small MoT/packing and production generation orchestration,
30 steps, FP32/BF16, native pad layouts, text normalization on/off, Prefix and
instruction sensitivity, request isolation, partial-cache failure/retry,
dispatch restoration, No-TTT/cold-start, model-mode/transactions and history-K.
Compiled dispatcher regressions run fullgraph with static/dynamic shapes.
The GPU audit counter also runs 40 alternating CPU-compiled calls at limit8.

Two qualifications are explicit, not counted as passes:

1. The expanded development run had **181 PASS / 1 FAIL** in existing
   `local_evidence_test.py::test_model_owned_all_continuation_never_initializes_w0`.
   The same test fails on clean old Child4cd5. The existing model-owned scan
   intentionally reads W0 for FSDP zero-gradient behavior. This task leaves it
   untouched and explicitly deselects that single inherited failure. Both raw
   failures are retained. This is not a full-repository green claim.
2. Three existing Ruff I001 findings in cache/unified/attention import blocks
   are reproduced on clean baseline and narrowly exempted. All other scoped
   diagnostics remain enabled. The executed runner has an old comment saying
   “two”; its actual three exception arguments and machine record are correct.

Controlled RED/GREEN evidence:

- Earlier dynamic fullgraph guard: same regression file SHA
  `58cf39796d6c6b68cce8f68ffacfa29734886ec47462181265f3e03579a6724a`;
  old19b30423 static PASS/dynamic BooleanAtom FAIL, corrected branch 2 PASS.
- Current native materialization/padding test SHA
  `42f44eeedd13cd261df8b501789abf01cbb61373b3c8c03049ea4ce73209eb0e`;
  exact old9f6cf6a1 production plus the same new test gives deterministic RED,
  current4446 passes in final187. The RED worktree is test-only dirty; its
  production bytes are identified separately. Earlier development fixture
  failures are preserved and not relabeled.

Current raw evidence:
`docs/collab/codex/evidence/2026-11-09_issue31_prefix_kv_native_precision/`.
Previous immutable CPU evidence/proofs:
`docs/collab/codex/evidence/2026-11-09_issue31_prefix_kv/`.
Each index binds every payload by SHA256, size and Git blob hash. The previous
archive's 122 payloads were verified and restored byte-for-byte.

Reproduction (use an external runner/evidence directory and a clean exact Pair):

```bash
cd /workspace/work/psm-wma-prefix-kv-issue31
env CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' OMP_NUM_THREADS=1 \
  OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue31-prefix-kv-evidence/cpu_gate.py \
  --root /workspace/work/psm-wma-prefix-kv-issue31 --run author06 \
  --expected-root 5b89f3eddbfe27ee72c173696a386e0b756d7866 \
  --expected-child 4446be0f6dad9b6dc887ef90af52d0af754d4682
```

That command is the executed record. `author06` already exists and must not be
overwritten. Independent replay must choose a fresh directory and recreate the
exact clean Pair. The runner and full child command/environment records are
archived with the raw JUnit.

## Real H100 author model-only evidence

Owner Issue31 authorizes GPU4–7 after focused CPU checks. Only GPU6 was used.
GPU0–3 and existing `gpu_load_sim.py` were not modified or stopped. No Sim,
Worker, server, task/SR or 900-Episode evaluation was started.

Same real **Local-TTT iter15000 DCP**, required model-mode and DCP inventory
validation, fixed synthetic RGB composite/raw15 state, model-owned T16 history
scan, frozen FastState and **4×32 Prefix**; B1, H16, guidance1, 30-step UniPC.
History FW construction is outside generation timing. Current-frame VAE is
included in native generation and separately timed. This is not a real executed
RoboCasa history or an A/B checkpoint success-rate comparison.

Three alternating warmup pairs, separate layer audit, removal of **all** layer
audit hooks, three fresh uninstrumented warmup pairs, then **30 balanced AB/BA
pairs**. Profiling happens afterwards and is not included in timings.
The recompile limit stays **8** throughout; no compile disabling workaround.

| GPU-event generation ms | Original Prefix-on | Prefix-aware text KV |
|---|---:|---:|
| P50 | 991.5513 | 825.5335 |
| P95 | 997.1945 | 829.1916 |
| Mean, all samples | 990.4186 | 843.0906 |
| P99, linear interpolation | 1000.0608 | 1225.2732 |
| Maximum | 1001.1876 | 1386.7728 |
| Current VAE P50, included above | 4.3396 | 4.3489 |

P50 speedup **1.2011×**, latency reduction **16.743%**, 29/30 paired runs faster.
The single optimized `pair-2` outlier is **retained**; its origin is not proven.
P99 is worse in this run, so improved tail latency/production SLA is not claimed.
Background synthetic load remained present; this is not an exclusive-GPU
benchmark or proof of the historical No-TTT ~0.61s target.

- All 60 measured generation outputs: **Vision and raw15 Action max abs=0**
  relative to the original Prefix-on reference. Uninstrumented audit, repeated
  request and instrumented audit also exact. Strict assertion threshold was
  unchanged (`rtol=1e-4`, `atol=1e-5`); measured errors are exactly zero.
- All **28 layers**: reference30 full forwards; optimized1 fill+29 gen-only;
  both have30 Prefix contexts and30 actual Prefix K projections. Changed Prefix
  changes real Action output. A subsequent original request refills every layer
  and reproduces its original output exactly.
- Teacher-forced original/fill/hit at tau1000 and500 are exact after this fix;
  UND K/V is invariant across these timesteps in all28 layers. This diagnostic
  alone is not a Gate; the separate complete30-pair run is the author result.
- Single post-timing profiler: CUDA events including memcpy decrease
  53,706→39,667. Raw kernel counts and traces stay on server. Peak allocated and
  reserved bytes are unchanged (8,302,126,080 / 8,451,522,560 respectively).
- Shell0, result/correctness/performance PASS (predeclared P50 speedup≥1.05),
  clean exact before/after source, frozen FW/Prefix and checkpoint metadata hash
  unchanged. Owned model processes exited; GPU6 returned to the existing load's
  baseline allocation. No unrelated process was terminated.

Only **derived statistics and hashes** are published at
`docs/collab/codex/evidence/2026-11-09_issue31_prefix_kv_gpu_derived/`.
The 56 server-only raw artifacts (JUnit is CPU/local, not remote) are bound by
SHA256/size. Checkpoint/config/input tensors, outputs, logs and profiler traces
remain on the authorized server, per Owner's file-privacy instruction.
The exact GPU command and safe statistics-reduction source are archived.

## Earlier failures retained

1. GPU01: real DCP loaded, measurement setup omitted fresh `state_in=None`.
   Root tool fixed; local gradient context matches the production adapter.
2. GPU02: real model exposed Dynamo symbolic-bool inequality. Production guard
   fixed with controlled CPU RED/GREEN; no recompile limit workaround.
3. GPU03: Python integer audit counter caused recompilation guard exhaustion.
   Root measurement fix uses Tensor counters and removes hooks before timing.
4. GPU04 (edf1e4ee/9f6cf6a1): numerical FAIL, raw15 Action max abs0.00839865;
   Vision max0.0231489. Modes independently repeatable. Teacher-forced diagnostic
   established that divergence already occurred at **cache fill** and that text
   K/V was static; native materialization and actual padding were preserved in
   current4446. GPU05 is the new exact-Pair complete author PASS, not a relabeling.

All raw GPU failure evidence stays on the server with hashes published. Local
development/fixture failures, baseline failures and controlled REDs remain in
the CPU archives. No old failed result is presented as passing.

## Requested independent Gate

Please review the exact **5b89f3ed / 4446be0f** delta against approved
53b5273c /4cd5fc8c: cache eligibility, native capture/rounding/padding, Prefix
effectiveness, isolation/cleanup, unchanged No-TTT and model-mode/Resume paths,
CPU qualifications and real same-weight numerical/performance evidence.

Codex requests a fresh incremental code/evidence verdict. Author PASS does not
close independent GPT/DS/hardware gates. Keep PR32/10 Draft and unmerged;
there is no authorization here for V3 promotion, training, SR/900EP or another
packing/attention optimization stage.
