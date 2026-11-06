# Issue22 Local-TTT pipeline — Child Draft PR / author handoff

2026-11-07 (Asia/Shanghai). **Author targeted CPU PASS; independent GPT review and real hardware performance OPEN.** Related: https://github.com/wxwy/psm_wma/issues/22 .

## Exact review target and integration boundary

| Identity | Full SHA |
|---|---|
| Candidate Child | `5fe2b8def58f4caae8c63581ed3649ac8fb3e0c6` |
| Parent / official Child at start | `1ca308055fc41fb69efaeb9efaa23808f164a18e` |
| Root V3 observed at start | `8aeb2442993620ee4513834a73064a4ea1eca38c` |
| Root context used by final CPU | `631a36225f4d4d93ffe30076ea95a2f890085363` |
| Root Gitlink, deliberately unchanged | `1ca308055fc41fb69efaeb9efaa23808f164a18e` |

Isolated Child branch `v3-local-ttt-pipeline-issue22-20261107`, PR base `v3-local-ttt`. Root branch with the same name contains design/task/evidence/Inbox only. **This is a Child candidate, not a new matching Formal Root/Child Pair.** Final CPU ran with committed clean Child and expected Root working-tree status `M cosmos-framework`; Root index/Gitlink stayed baseline. This is recorded in raw fingerprints, not relabelled a clean Root or production source-verification PASS. Later evidence/ledger SHAs do not replace the Child target.

Fresh prepublication V3 is `2ff873bde87465a2cc8815eb801d69692f54a396`, with the same official Child `1ca30805`. Its two newer commits (`4abaa42d`, `2ff873bd`) change only G2 documentation. They remain on official V3. No official ref, G2 source, training queue, L2000/L4000 directory or runtime was modified.

## Concrete change

Previously, after a Sim stopped for Replan, the model owner encoded every history composite independently and ran the whole history's adaptation before native generation. Now required Local-TTT in the existing Phase-B batch profile advertises `pipeline=per_frame_v1`:

1. The assigned Sim client copies RGB/raw15 **after successful env.step**, then enqueues bounded PNG/upload work. Sim does not wait for Encode1 or adaptation. HTTP admission ACK does not clear evidence; exact policy ACK remains authoritative.
2. `/v2/local-memory/completed` authenticates the complete registered lease, freezes the completed row, and admits contiguous, exactly-once work. Each Session is bounded to H16, with global item and 128MiB wire-byte capacity; capacity exhaustion is explicit, never silent dropping.
3. The original single model executor interleaves completed units with native inference/media. It advances dependencies before sealing a Replan; it does not wait on its own Future under `_model_lock`. Completed work does not hold Store/metadata locks across GPU work or event waits.
4. The first history source reuses the previously generated Policy current-frame Visual96. The capture is from the **full padded Wan return before Policy latent cropping**, with exact T1 input/canvas/normalization/identity checks. Missing, changed, reordered or unsupported captures fail closed without an Encode1 fallback. The other 15 history frames use independent T=1 Encode1 with fresh VAE state. VAE streaming/retained causal caches are not enabled.
5. Model-owned T=1 scans build detached **unpublished** candidate Fast Weight/Prefix, preserve `inference_mode(False)` + grad + `create_graph=False`, and accumulate all inner-loss/update telemetry. Replan validates the full original evidence/digests and committed anchor before staging the original pending capability. Generation success still publishes Fast/Visual/CachedResponse in one snapshot. Abort/reset/End cancel and drain owned work; failed drain quarantines the owner.
6. No-TTT never instantiates this machinery or injects Local kwargs. Legacy non-batch Local requests retain their explicit prior path. Training, model parameters/keys, checkpoint, cache schema, Manifest and strict M/B Resume logic are unchanged.

20 Child Python files changed: 12 source files limited to inference/server/simulation and 8 new test files. Git tree identities for `model`, `trainer`, `configs`, `checkpoint`, `data`, and `evaluation` are byte-identical to parent. Root production source and Gitlink are unchanged. Scope and exact Child delta are archived.

## CPU evidence and numerical limits

[Summary](../../../../artifacts/local_ttt_pipeline/2026-11-07_issue22_cpu/final_summary.json), [raw final JUnit](../../../../artifacts/local_ttt_pipeline/2026-11-07_issue22_cpu/author-final/junit.xml), [command/environment](../../../../artifacts/local_ttt_pipeline/2026-11-07_issue22_cpu/author-final/command.json), [numeric witnesses](../../../../artifacts/local_ttt_pipeline/2026-11-07_issue22_cpu/numeric_witnesses.json), [evidence README](../../../../artifacts/local_ttt_pipeline/2026-11-07_issue22_cpu/README.md).

| Check | Actual evidence |
|---|---|
| Frozen Child final targeted run | **428/428 PASS**, 155 new + 273 prior, zero failures/errors/skips, shell exit0 |
| Identity | Child5fe2b8de clean; Root context/Gitlink distinction above; all1273 fingerprint entries unchanged |
| Static | 20 Python Ruff/format/AST PASS; protected trees identical; exact source diff whitespace PASS |
| Current-frame source boundary | Actual RoboCasa prep → Omni → tiny real Wan BF16: T1 input, full pre-crop latent and Visual96 bit-exact; crop-after negative; A→B→A; 128/256 numeric and128/192/256/320 spatial |
| Public Service B2 capture | Actual `_transaction_batch` + Omni + Wan path, one T1 encode/sample, correct16×15 output/state-row stripping/capture mapping/restoration; denoiser doubled |
| Whole vs single-step actual model scan | 12 FP32/BF16 × fresh/continuation ×1/4/16 groups: Fast Weight and Prefix max absolute difference **0**; aggregate telemetry max difference `3.814697265625e-6` |
| Online Prefix/action projection | 3 partial-history groups: state/Prefix/action projection max difference **0**; inner-loss sum max difference `2.905726432800293e-7` |
| Tolerance | Explicit scan/telemetry `rtol=2e-5, atol=2e-6`; fp32 summation order is not claimed bit-exact. No reuse of old0.0625 acceptance threshold |
| Call counts | A completed16-row interval: **15 independent Encode1,16 legal T1 updates**, no extra Replan scan/encoding; actual counter assertions |
| Transaction/concurrency | Pending/committed separation, B2 mapping, Session/epoch/lease/bytes isolation, duplicate/replay, late/changed/out-of-order, blocked scan/encode admission, worker fault attribution, abort/reset/End/close/quarantine, no future evidence |
| Author-side cross-check | Three MED source findings corrected: cleanup masking primary, failure before a Replan exists losing its cause, and Python3.10 add_note compatibility. Static reviewer found no remaining confirmed HIGH/MED; not GPT/DS acceptance |

Final pytest55.99s, recorder61.066s. Original development run **422PASS/4FAIL out of426** is retained. Failures were a partial-drain helper incorrectly asserting an empty queue and a scan spy installed after Adapter captured its callback; fixtures were corrected without relaxing those assertions. Focused35PASS and service1PASS are separate development evidence, **not added to428**. Static first import errors are retained too.

Environment: existing Python3.12.14, Torch2.10.0+cpu, pytest9.0.2, Ruff0.12.7, offline access, GPU visibility/LD_LIBRARY_PATH empty, BLAS1 and isolated caches. No dependency installations or dependency-source changes. Transaction tests reuse their existing explicit `/proc` clock-identity fixture because this CPU cloud lacks the native timens identity; this is not host preflight. Tests patch script initialization and VAE weight loading to generated tiny weights; real VAE math/casts/scales are retained. Tiny DCP inventory fixtures are generated locally; no actual model checkpoint is accessed. Python3.10's missing-add_note path is simulated on3.12, not a separate3.10 interpreter run.

## Profiling and remaining hardware gate

The implementation records client composite/PNG/enqueue/upload, Sim stepping, server work queue/preparation, independent Encode1, Visual96, Fast update and native generation. Bounded recent-window P50/P95 use a disclosed nearest-rank formula. CUDA stages use device events and finish before reading elapsed durations; CPU samples are labelled. Per-window server metrics travel with the original prediction log; assigned-client metrics are saved to non-authoritative `local_pipeline_profile.json`, which explicitly does not assert Core validity.

Measured call count reduction for Local history is16→15 (6.25% fewer independent history encodes). This does **not** establish end-to-end H100 speedup, GPU queue latency or Ep/h. Controlled CPU tests prove overlap while scan/encode is blocked; they do not emulate real simulator throughput.

**Real before/after encoding, TTT, queue, inference latency P50/P95 and valid-Episode/hour remain OPEN / NOT RUN.** Also unrun: actual DCP load, CUDA BF16/grouped_mm, CUDA graph/FSDP, complete model Local-TTT adaptation and real RoboCasa. Hardware benchmarking/900EP is not authorized while L2000/L4000 occupy GPU4–7. No remote server files/processes/source/results/checkpoints were read or copied.

## Requested review and integration instructions

Review the exact Child increment and CPU raw evidence; return APPROVE_CODE / REQUEST_CHANGES. Draft status is intentional. Do not automatically merge or update V3 Gitlink. After independent approval and appropriate hardware authorization, integrate that Child into a new Root candidate based on **then-current V3**, preserve G2/training changes and reviews, commit its Gitlink and freeze a new matching Pair and new Fresh Manifest. Keep source verification and strict M/B Resume; do not source-switch Resume a running or historical evaluation.

For a CPU reproduction only, check out Root context631a3622 and nested Child5fe2b8de explicitly, then use the archived `run_targeted.py` / `targeted_files.json` / `run_cpu.py` with a fresh output directory. The expected Root Gitlink drift must remain visible; this checkout is not a production CLI source-identity authorization. GPU comparisons must use matching real checkpoint/config, raw15/H16 and independent new outputs, after L2000/L4000 resource boundaries allow it.
