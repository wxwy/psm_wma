# V3 full Segment Prefetch and GPU Stall telemetry — source-diff receipt

Date: 2026-10-13
New Implementation Root: c666691b5bd5802a539567123f48873f5de83e9c
New Child/Gitlink: cb4088c75e3e2f62d16425b8e55d587792008011
Previous Packed128 Gate A Child: c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686
Child diff: https://github.com/wxwy/cosmos-framework/compare/c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686...cb4088c75e3e2f62d16425b8e55d587792008011
Status: source committed, no project-complete pytest/ruff/py_compile execution available to GPT, no H100 Nsight trace or real performance benchmark, no formal process/checkpoint touched.

DS report reviewed: 2026-10-13 `DS_PRO: V3 Full Segment Prefetch and GPU Data Stall Audit` owner-pasted, readonly. Corrections independently source-confirmed:
- DS §5.1 claims `gpu_data_stall_ms` absent and console `data=` uses `data_prepare_ms`. This is FALSE at frozen child c8dabbb3: `corrected_telemetry.py` already has DATA_STALL_CPU_STAGES and `_sample_gpu_data_stall`, JSON fields `gpu_data_stall_ms/status/scope`, and formal_monitor.py::_gpu_data_stall_display displays it, else n/a. Existing metric remains an uncalibrated current-stream CPU-stage-gap estimator, NOT fully attributable device-wide GPU stall.
- DS §2.3/§7 claims ~11 seconds of host `data_prepare` is definitely GPU idle and describes it per member. No CUDA kernel trace grounds this; the 11.5s historical value was per optimizer-step summed Host stage timing, not per member. Raw Future wait near 0 only means the queued raw future was complete.
- Current RoboCasa exact cache SFT sets `cfg_dropout_rate=0.1`, so global Python `random` in TextTokenizer is genuine. However `format_prompt_as_json=True` and `ActionTransformPipeline` constructs IdleFramesTextInfo only when its JSON formatter is absent, so the separate idle-frames random branch is NOT active in this present recipe; hardened fallback still preserves non-RoboCasa consumers.
- DS proposed same-stream Event at prev member end and next first kernel directly measures 'data wait'. This is FALSE as causal inference: any stream gap can include host dispatch, NCCL/other streams, Local scan or scheduling; needs NVTX/Nsight timing + data readiness.

New Child source implementation (13 changed paths):
1. `data/generator/action/utils/transform_random.py`: context-local deterministic RNG with unmodified legacy fallback, no global random draw under keyed mode.
2. `data/generator/augmentors/text_tokenizer.py`, `idle_frames_text_info.py`: opt-in transform_draw for CFG and per-field RNG, preserve default original global RNG behavior.
3. `model/generator/mot/robocasa_exact_window_local.py`: optional `transform_rng_mode=consumer_keyed_v1`, identity-bound seed from source binding+slot+episode+epoch+step, only active when explicitly chosen; segment contract preserved.
4. `model/generator/mot/robocasa_full_segment_prefetch.py`: exactly one bounded future, a single tokenizer worker (no concurrent tokenizer processor use), per-member read/transform/Segment validate/Native Collate, private reader LRU, data identities, async abort/drain and speculative across-optimizer-window lookahead after freezing candidate next frontier. H2D+Model/Local state remain on trainer thread.
5. `trainer/local_memory_grouped.py`: explicit full_segment_prefetch bind, preserves preexisting nw=0 and raw-only modes; full mode passes worker prepared collate after verifying payload object identity; schedule GA1 during GA0 compute and next-step GA0 during GA1 compute; fail-closed abort; unchanged optimizer/commit semantics.
6. `examples/psm_wma_robocasa_corrected_phase5.py`: CLI `--full-segment-prefetch` + `--transform-rng-mode consumer_keyed_v1`, requires `--num-workers 1`; keyed RNG gets new config_digest (legacy default digest stays unchanged), so CANNOT silently old-index8 or default-Packed128 resume into altered augmentor semantics. New distinct namespace required for test.
7. `examples/psm_wma_robocasa_corrected_telemetry.py`: full-prefetch wait reason and flag, NVTX stage range hooks via optional `PSM_V3_NVTX_STAGE_RANGES=1`, default0; existing gpu_data_stall estimator/display unchanged, not called 'actual GPU idle'.
8. New/extended tests for keyed RNG across threads, text tokenizer and idle augmentor, bounded full member read/identity/abort, multi-window/terminal continuation CPU parity, CLI/digest, opt-in NVTX markers, existing workflow expectations.

Activation **only on new isolated CPU/GPU diagnostic namespace** (after Gate): `--full-segment-prefetch --transform-rng-mode consumer_keyed_v1 --num-workers 1`. Opt-out is original Packed128 synchronous or raw-only behavior. There is no unsafe default full-prefetch enable.
Perf expected: unknown until matched 8×H100 profile; prior Index8 nw0 ~40s/nw8 ~60s are not Packed128 results. No claim that 11s disappear, that GPU gap=0, or that non-mutating data prefetch produces bit-exact same stochastic decisions as legacy_global; compare keyed sync vs keyed async.
Review: docs/collab/chatgpt/reviews/2026-10-13_V3_full_segment_prefetch_and_stall_audit_implementation_review_c666691b_cb4088c.md
DS CPU and profiling request: docs/collab/chatgpt/requests/2026-10-13_DS_PRO_V3_full_segment_prefetch_CPU_gate_and_GPU_trace_plan.md