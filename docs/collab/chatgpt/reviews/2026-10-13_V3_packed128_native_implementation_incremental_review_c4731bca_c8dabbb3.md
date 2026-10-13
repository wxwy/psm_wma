# V3 Native Packed128 — New formal implementation pair incremental review

Date: 2026-10-13
Formal Root Implementation SHA: c4731bca1a590663db88bd6cd74dbcf9fd513a85
Child/Gitlink SHA: c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686
Compared with old Child 5ac9a904c46da658e1b3e0816d3a7d95ce99c945; previous static design archived in docs/collab/chatgpt/reviews/2026-10-13_V3_Packed128_owner_decision_and_gradient_semantics_contract.md
Verdict: REQUEST_CHANGES. Implemented and committed, but project-complete CPU and real 8-rank H100 evidence are pending. Do not interpret earlier V2 APPROVE as this pair's authorization.
Source receipt: docs/collab/chatgpt/evidence/2026-10-13_V3_packed128_native/implementation_diff_receipt_c4731bca_c8dabbb3.md

Source review:
- local_memory_grouped_window.py:51-95,162-227 uses one slot-major Packed Native callback per member. It validates row identity, no duplicate consumer, correct S0/no Local, exact terminal count, and retains candidate Local state until successful backward and optimizer.
- local_memory_grouped.py:257-295 calls model.training_step once with all128 payloads and corresponding Local prefixes, then backward once. Old FSDP optimizer and DCP machinery untouched.
- corrected_telemetry.py:204-246 and :604 adjusts Loss metric coverage and forward/backward counts from 32 to2, records native_batch_layout.
- training_audit.py:133-185 retains time-major canonical audit hash on original consumer identities; no model input reorder after slot-major packing.
- corrected_phase5.py:57,204 fingerprints native-layout version into config_digest, preventing silent same-job resume of older Index8 checkpoints. Root implementation changes only child Gitlink.
- Source-only tests added/updated across window, trainer, telemetry and config module; no actual pytest run available in GPT local runtime.

Unresolved finding A — HIGH; local_memory_grouped_window.py:200-216, local_memory_grouped.py:257-284.
Root cause: merging 16 model forwards at Batch8 into Batch128 may alter MoT sample weighting, packed attention masks, CFG sigma/noise mapping, auxiliary loss contribution, floating-point reductions, FSDP gradient accumulation and Local Slow higher-order gradient path. Synthetic CPU test cannot prove real native numerical equivalence.
Contract: matched128 consumers, correct per-consumer loss, gradient through Local scan create_graph=True, same trainable FQN inventory, valid total and terminal weights, correct Slow/Action/Generation grads and completed optimizer step.
Closure: CPU clean then real-model fixed-sigma/epsilon per-sample paired V3 Index8 vs V3 Packed128 with true FSDP8 rank gradients/weights/FQN and Local after-state, strict DCP resume and no collective failure. Predeclare tolerance before evaluating differences; V2 old 5% is not automatic.

Unresolved finding B — HIGH; local_memory_grouped.py:257-281.
Root cause: Batch128 runtime/VRAM/throughput and FSDP collective ordering have not been tested. Owner explicitly allows direct128 and sufficient VRAM; still fail on OOM without shrinking batch.
Closure: independently authorized isolated 8xH100 short GPU smoke; per rank native calls2; consumers256; peak/allocated/reserved, p50/p95 wall vs V3 nw0 ~40s, GPU/host timing and distinct Job namespace. GPU performance must not be inferred from mock.

Unresolved finding C — MEDIUM; local_memory_grouped_window_test.py:104, corrected_phase5_test.py:143, corrected_telemetry_test.py.
Root cause: V3 full dependencies (pyarrow/transformers/LeRobot) absent locally; new pytest, py_compile and Ruff have not been executed on exact Child. Authored tests are not evidence.
Closure: DS_PRO isolated CPU tests using exact Root/Child SHA, full stdout and first failure stack, no production changes.

Further math boundary: Packed GA loss is still current V3 full native scalar multiplied by n_member/n_window. V2 objective weights Consumer and Auxiliary separately; in unequal terminal members and when aux_loss_gen/und exists, one cannot assert mathematical equivalence without real evidence. Same seed alone is not same per-consumer sigma/epsilon/dropout. Keep strict checkpoint/exposure contract.

Production deployment HOLD. Current Formal30k root/child/checkpoint and running process remain untouched. Old Index8 DCP cannot automatically continue under new config digest; CPU-only acceptance does not authorize real GPU/full30k.
DS handoff: docs/collab/chatgpt/requests/2026-10-13_DS_PRO_V3_packed128_native_CPU_Gate_and_GPU_parity_handoff.md