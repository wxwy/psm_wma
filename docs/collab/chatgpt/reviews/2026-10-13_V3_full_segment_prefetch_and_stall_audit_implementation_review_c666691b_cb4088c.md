# PSM-WMA V3 — Full Segment CPU Prefetch + NVTX Stall Trace implementation fresh review

Date: 2026-10-13
New Formal implementation Root c666691b5bd5802a539567123f48873f5de83e9c / Child+Gitlink cb4088c75e3e2f62d16425b8e55d587792008011
Previous Formal Packed128 Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686
Source diff receipt: docs/collab/chatgpt/evidence/2026-10-13_V3_full_segment_prefetch/2026-10-13_source_diff_and_DS_audit_c666691b_cb4088c.md
Verdict **REQUEST_CHANGES / CODE_COMMITTED / CPU_RUNTIME_EVIDENCE_PENDING / REAL_GPU_TRACE_PENDING**.

## Independent source review

- This is a NEW formal pair: old Packed128 Gate A CPU PASS 151/2 is valid only for old pair, cannot be inherited. Fresh incremental review is scoped to 13 changed Child paths, not V2 or unrelated model code.
- Corrected DS report false premise: current `gpu_data_stall_ms` and console `data=` estimator already existed in old Child. It is NOT exact or causal data-caused GPU idle. This implementation adds optional NVTX stage markers, not new or falsified numeric interpretation. Real Nsight calibration not yet run.
- Data Prefetch candidate is opt-in, full member on 1 single background CPU worker; no tokenizer parallel calls within worker pool; Source Raw getter worker-private. Collates Native payloads before scan, then trainer validates **identical dict-object consumer order** before reusing the prepared native batch. CUDA H2D, model, Local scan, live candidate commit and optimizer remain main-thread.
- `consumer_keyed_v1` RNG substitutes only scoped Python random decisions in transforms. The default legacy/global path remains equivalent in behavior (global Python RNG fallback). User-requested stochastic-parity guarantee applies to **keyed sync vs keyed async**, not old legacy global vs new keyed random outputs.
- Dynamic pipeline: first GA0 sync, GA1 scheduled before GA0 model compute, next window GA0 scheduled read-only before current GA1 compute; a single outstanding FullMember future. On abort: cancel/drain stale speculative worker; next `begin()` recomputes matching deterministic planner metadata.
- Native layout remains Packed128; no new backward, loss weighting, consumer plan, model/optimizer change. Full prefetch uses separate `transform_rng_mode` included in config_digest only for keyed mode; default Packed128 config_digest is unchanged. Since new keyed mode changes RNG assignment, never use old Index8 iter1300 or original Packed128 DCP as direct strict same-job Resume.

## Pending gates and possible vulnerabilities to investigate in exact runtime

**Gate C0 HIGH — Fresh CPU implementation contract**: Need exact-pair CPU py_compile/ruff, existing Indexed/Grouped and new RNG/full worker tests, real cached SFT transform byte-parity keyed synchronous vs keyed async on same identity, explicit false mode compatibility, thread safety (shared tokenizer not concurrently used). Cannot call implementation PASS on authored tests.
**Gate C1 HIGH — Per-consumer stochastic RNG semantics**: `consumer_keyed_v1` is a new augmentation mapping, not bit-identical to old global Python RNG sequence. Hash includes source binding+slot+episode+epoch+step. Freeze new digest; paired throughput tests must use keyed synchronous baseline, not old unkeyed script. Standard pre-existing iter1300 DCP migration still needs separate gated process and must not be bypassed.
**Gate C2 HIGH — Full worker thread realism**: verify actual production HF SourceReader copy, tokenizer processor ownership, per-worker reader caches, 128 consumer Segment/Native collate ABI including action/vision/CFG; worker does not touch CUDA; no pending overrun, improper Future lifetime, shared tensor mutations or abort/resume leak.
**Gate C3 HIGH — Cross-window speculative lookahead**: candidate_frontier planning is pure/deterministic and must match next window begin after successful optimizer, and pending discarded on failure; need paired two-window tests and DCP strict resume after checkpoint (on fresh same-mode source). If mismatch fail closed, do not silently replan.
**Gate C4 HIGH — GPU Stall attribution**: CUDA event `gpu_data_stall_ms` remains *proxy*, and the user wants actual DATA-caused GPU wait. Need Owner-authorized Nsight/NVTX trace checking event behavior against actual stream idle and data-ready times. Only show causal metric once validated; otherwise label estimate/n-a; do not claim only CPU host time is idle.
**Gate C5 PERF — Actual speed**: real Packed128 step wall and NVTX p50/p95 under keyed sync vs keyed full-prefetch, with matching hardware/flags/data, GPU occupancy, memory and same 256/rank. No automatic speed guarantee from historical 11s host prepare.

## Formal restrictions

- No project complete CPU pytest/Ruff/py_compile was run by GPT (container lacks project LeRobot/pyarrow/transformers); no GPU trace or performance measurement. Newly committed source and test files require independent DS executor evidence. No current Formal30k worktree, old iter1300 DCP or latest pointer modified by GPT.
- `PSM_V3_NVTX_STAGE_RANGES` defaults0 and does not claim GPU causal measurement; opt-in1 only for independently approved GPU profiling on isolated job.
- Current Gate B (Packed128 baseline vs Index8 real GPU parity) and iter1300 migration are separate unfinished work; prefetch candidate must NOT hold old Gate A approval or be mixed with them before baseline pass.
- DS may run CPU tests in isolated checkout; **no torchrun/realGPU profiling or new training until Owner explicit authorization**.

DS acceptance request docs/collab/chatgpt/requests/2026-10-13_DS_PRO_V3_full_segment_prefetch_CPU_gate_and_GPU_trace_plan.md