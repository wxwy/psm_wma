# PSM-WMA V3 — Formal30k Observability and Bounded Raw Prefetch Contract
Date: 2026-10-10
Status: NEW IMPLEMENTATION CANDIDATE / CPU + REAL DCP + GPU GATES PENDING

## Unchanged training authority
- Original accepted training source: root `32e254326a574bff45111415430a8c1170cdea9a`, child `71e03c8501c94a2ad5fed60955af657d3f945b85`.
- Proposed Child implementation source: `98cb4fd0cc59e71f27543d67fa33cbf4f3703657` on `v3-local-ttt`; Root V3 Gitlink must match it.
- Original same-job name: `formal_verified_index_30k`. Last saved complete DCP iteration is UNKNOWN until DS reads the host; user reports healthy training manually stopped around iter800.
- Frozen config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`.
- Frozen 18 task classes / 9,126 episodes / 2,085,331 windows / raw15 / left_wrist / T16 / B8 / GA2 / K4 / world_size8 / max_iter30000 / warmup500 / save_iter100.
- No code changes to model, optimizer, scheduler, dataset identity, FSDP2 w0_fast or DCP grouped state serialization.

## New implementation
- `examples/psm_wma_robocasa_formal_monitor.py`: optional rank0 append-only JSONL/raw journal and CPU-only read-only DCP/PNG monitor; checkpoints are never written, altered, moved, or resumed by monitor.
- `examples/psm_wma_robocasa_corrected_telemetry.py`: timestamped readable rank0 progress and original complete JSON, rank-local FSDP norm scope preserved.
- `examples/psm_wma_robocasa_corrected_phase5.py`: `--num-workers` in 0..16 (actual per-rank RAW-READ threads, not upstream DataLoader processes), default 0; rank0 journal created beside same-job DCP, no new checkpoint ABI.
- `robocasa_exact_window_local.py`: split producer into `prepare` (raw, no text transform) + `materialize` (same original ordered transform) preserving `produce` API.
- `robocasa_async_segment_prefetch.py`: bounded one-next-GA-member `ThreadPoolExecutor`; private per-worker Episode .pt LRU; immutable HF/Arrow data view; no mutable SourceReader LRU sharing, no RNG/Local/optimizer/frontier access by workers.
- `local_memory_grouped.py`: only requests for candidate planned GA member may be prefetched; synchronous Member0 prep and concurrent Member1 RAW reading; all ordered tokenization, scan/backprop/commit remain on trainer thread; cancel/drain on abort and close after run. No prefetch queue persists in DCP.

## Invariants and Risks
1. Same-job resume with `--num-workers 0` is the no-prefetch reference path. `--num-workers 2` is a NEW execution variant requiring controlled parity evidence; it is not automatically validated merely because config_digest is unchanged.
2. Planner determines current window synchronously; prefetch never advances committed frontier, fast state, slot IDs or RNG state. GPU receives the exact consumer sequence and Local segment provenance. DCP is written only after successful GA/optimizer commit with empty prefetch queue.
3. The HF dataset must already be eagerly loaded and is accessed read-only. Real LeRobot `__getitem__` thread safety and CPU/RSS/storage contention need real-host testing.
4. Workers 0/1/2/4/16: 16 threads per rank could create 128 threads across 8 ranks; do not choose without CPU RSS and I/O evidence. Recommend validation first on 2 and 4.
5. Log append/plot activity is not an optimizer dependency; PNG generation is only from a separate CPU monitor. Previous iter1..800 numeric history cannot be reconstructed if terminal scrollback was lost.
6. Verify real latest DCP: pointer, model/optim/scheduler/trainer metadata and all 8 dataloader rank states, no fallback to prior owner-deleted optim states, no speculative iteration guess, no resume from diagnostic iter3.

## Gate A — DS_PRO CPU/static (not yet executed)
Run read-only in the existing one training worktree after Git exact FF. Environment:
`HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu`.
Required:
```bash
cd <EXISTING_ROOT>/cosmos-framework
python -m py_compile examples/psm_wma_robocasa_formal_monitor.py examples/psm_wma_robocasa_corrected_phase5.py examples/psm_wma_robocasa_corrected_telemetry.py cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch.py cosmos_framework/model/generator/mot/robocasa_exact_window_local.py cosmos_framework/trainer/local_memory_grouped.py
python -m pytest -q -p no:cacheprovider -o addopts='' cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch_test.py cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py cosmos_framework/trainer/local_memory_grouped_test.py cosmos_framework/trainer/local_memory_grouped_resume_test.py examples/psm_wma_robocasa_formal_monitor_test.py examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_corrected_phase5_test.py
ruff check cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch.py cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch_test.py cosmos_framework/model/generator/mot/robocasa_exact_window_local.py cosmos_framework/trainer/local_memory_grouped.py cosmos_framework/trainer/local_memory_grouped_test.py examples/psm_wma_robocasa_formal_monitor.py examples/psm_wma_robocasa_formal_monitor_test.py examples/psm_wma_robocasa_corrected_phase5.py examples/psm_wma_robocasa_corrected_phase5_test.py examples/psm_wma_robocasa_corrected_telemetry.py examples/psm_wma_robocasa_corrected_telemetry_test.py
ruff format --check <SAME_11_FILES>
```
All must GREEN (Ruff 0.12.7). Preserve complete output. Nonzero exit means BLOCKED, report exact diff/errors, no DS source edits or GPU.

## Gate B — real-source and DCP preflight
- Read actual latest complete DCP and all 8 rank states. Compare source/cache/index fingerprints and frozen digest exactly; `--phase resume --preflight` must not perform optimizer step or mutate DCP.
- Sample real windows from 18 classes including nonterminal, terminal, S0/previous evidence; compare RAW action/state/latent, token IDs, ordered segments/slot/frontier and torch RNG between synchronous `produce` and async `prepare + materialize` using a single accepted dataset, accounting for logged dtypes.
- Existing CPU smoke is insufficient evidence of LeRobot thread-safety on the real corpus.

## Gate C — bounded GPU and strict Resume (NOT YET AUTHORIZED)
- Only after A/B GREEN and owner review: a fresh isolated 8xH100 bounded 3-step `--num-workers 2` diagnostic (new output namespace, not formal DCP) to check latency, RSS/VRAM, all rank gradients, Local and DCP presence.
- A separate exact same-job strict-resume authorization must specify the verified full DCP and exact Root/Child SHA; do not run `--phase fresh`, switch to old source, or auto-resume.
- A healthy job must never be interrupted for monitoring changes. User has already manually stopped it; no process was operated by GPT.

## Change-control
DS_PRO: read-only Git FF, tests, GPU execution only after Gate authorization and evidence; never source edits/commits/uploads.
GPT: code/design/review ownership; formal review lives in `docs/collab/chatgpt/reviews/`.
Root `V3` and Child `v3-local-ttt` are requested production branches, but this code is an UNVERIFIED CANDIDATE until Gates close.
