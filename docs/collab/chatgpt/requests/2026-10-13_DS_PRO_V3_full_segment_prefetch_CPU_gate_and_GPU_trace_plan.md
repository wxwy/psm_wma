# GPT → DS_PRO: corrected V3 Full Segment Prefetch & GPU Stall CPU Gate / separate GPU trace

Date: 2026-10-13. This supersedes the FALSE absence-of-gpu_data_stall conclusions in DS read-only report.
New Root Implementation c666691b5bd5802a539567123f48873f5de83e9c
New Child/Gitlink cb4088c75e3e2f62d16425b8e55d587792008011
Previous Packed128 Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686
Review: docs/collab/chatgpt/reviews/2026-10-13_V3_full_segment_prefetch_and_stall_audit_implementation_review_c666691b_cb4088c.md

## First acknowledge critical source corrections
- `corrected_telemetry.py` in old and new Child ALREADY has `gpu_data_stall_ms/status/scope/sampled` and `_sample_gpu_data_stall()`. Console `data=` already consumes it via `_gpu_data_stall_display`. Do not ask GPT to add a duplicate field or revert to `data_prepare_ms`.
- This is an uncalibrated current-stream gap proxy, NOT a proof that entire GPU waits for data. Old ~11.5s Host Data Prepare is per optimizer window, not per member, and cannot be asserted exposed GPU time without trace.
- Current RoboCasa JSON Prompt formatter bypasses IdleFramesTextInfo separate dropout; CFG dropout0.1 DOES use Python random. New opt-in keyed RNG handles it; default mode still calls original global Python random.
- Two-CUDA-event 'previous last -> next first' gap alone also cannot establish data-caused GPU idle. Nsight/NVTX plus host data-ready and GPU stream/NCCL events are required.

## Gate CPU_ONLY, authorized now; do not touch Formal30k working tree
Use isolated new Root/Child checkouts pinned to exact above hashes; verify Gitlink and module __file__, full venv, HF_HUB_OFFLINE=1. Run Python -m pytest -q on:
`cosmos_framework/data/generator/action/utils/transform_random_test.py`
`cosmos_framework/data/generator/augmentors/text_tokenizer_test.py`
`cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py`
`cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch_test.py`
`cosmos_framework/model/generator/mot/robocasa_full_segment_prefetch_test.py`
`cosmos_framework/trainer/local_memory_grouped_test.py`
`cosmos_framework/trainer/local_memory_grouped_resume_test.py`
`examples/psm_wma_robocasa_corrected_phase5_test.py`
`examples/psm_wma_robocasa_corrected_telemetry_test.py`
`examples/psm_wma_robocasa_formal_monitor_test.py`
Run `python -m py_compile` and `ruff check` for all 13 changed Child paths (source and tests). Retain per-command exit code and first raw stack on any failure. Fail fast; DS validation only, do not modify production code.

### CPU contract checks
1. **Legacy no-change**: default `--num-workers 0` and no full-prefetch flag remain identical original path, original global RNG consumption and same Packed128 config_digest. Existing raw-only nw>0 path unchanged.
2. **New opt-in keyed sync parity**: `--transform-rng-mode consumer_keyed_v1` with nw0 gives deterministic consumer-specific CFG/dropout, equal on replay and never consumes global Python random. Test TRUE FullMode with same keyed baseline and fixed source/model RNG — not legacy global vs keyed new outputs.
3. **Full member async**: enable only `--full-segment-prefetch --transform-rng-mode consumer_keyed_v1 --num-workers 1`; one GA member B8xT16 full128, terminal partial correct, native payload object order stable, and worker-computed CPU collate same ABI. One outstanding future maximum.
4. **Cross-window & failure**: current GA1 full prep overlaps GA0 compute; speculative next GA0 from candidate frontier is read-only, exact identity check after next optimizer commit; abort/future errors/drain/restart/Close no stale results/Frontier mutation. Include two-window and terminal tests.
5. **Observability**: original `gpu_data_stall` status and `data=` unaffected; new JSONL full-prefetch mode/readiness flags correct; `PSM_V3_NVTX_STAGE_RANGES=1` shows balanced CPU stage NVTX push/pop in mock; default=0 inert.
6. **DCP**: `consumer_keyed_v1` produces NEW config_digest. Original iter1300 Index8 DCP must NOT be directly Strict Resumed; full-prefetch candidate is separate from the old checkpoint migration project.

## Gate GPU TRACE (NOT authorized by this CPU handoff)
After CPU Green and separate Owner explicit permission on isolated 8xH100: compare CURRENT Packed128 keyed nw0 vs keyed full-prefetch nw1 on identical real RoboCasa consumers and source identity. Capture Nsight `--trace=cuda,nvtx,osrt` with env PSM_V3_NVTX_STAGE_RANGES=1. Compare time-aligned CPU `data_prepare`, native `batch_collate`, H2D, Local Scan, F/B, NCCL, and raw-vs-full data-ready timeline. If the existing gpu_data_stall_ms proxy != causally attributable GPU wait, report exact false-positive/false-negative and leave `data=n/a` or `estimate` rather than certifying precise GPU idle. Measure p50/p95/peak, slowdown from NVTX and profiler, and actual 256 consumers/rank; never treat previous Index8 40s as Packed128 performance baseline.

GPU and Cross-layout checkpoint migration remain distinct gates. No GPU experiments or Formal30k restart should occur from this instruction.

## Output
Submit one report `DS_PRO_V3_FULL_SEGMENT_PREFETCH_CPU_GATE_2026-10-13.md` with pair provenance, per-test exit codes/results, 13-file lint/compile, all CPU invariants, first fail, optional source-based issues, and GPU TRACE follow-on readiness. Stop after CPU Gate and return results to GPT. No DS code modifications.