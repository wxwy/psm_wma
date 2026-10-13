# DS_PRO → GPT — V3 Packed128 Native Gate A CPU验收（Owner转交）

Date: 2026-10-13. Source: DS_PRO isolated read-only CPU test report transmitted by Owner. GPT independently verified remote GitHub code refs/diff, not the original remote pytest logs/process filesystem. This file records the supplied evidence faithfully.
Formal Root implementation: c4731bca1a590663db88bd6cd74dbcf9fd513a85
Formal Child/Gitlink: c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686
Docs HEAD at evidence: 16492ca31546d5312eaecc52841a988d302029d6
Old Index8 Child: 5ac9a904c46da658e1b3e0816d3a7d95ce99c945

CPU isolation: /tmp/ds_pro_v3_packed128_cpu_20261013/{root,child}, root/child detached exact SHAs. Python imports explicitly from isolated child; venv /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv, torch2.10.0+cu128, pytest9.0.2, pyarrow21.0.0, transformers4.57.6, LeRobot available. LD_LIBRARY_PATH='', HF_HUB_OFFLINE=1. No GPU, torchrun or real MoT training.

Single-file pytest reports (all process exit0):
| File | Passed | Skipped | Wall |
|---|---:|---:|---:|
| cosmos_framework/model/generator/mot/local_memory_grouped_window_test.py | 13 | 1 | 15.37s |
| cosmos_framework/trainer/local_memory_grouped_test.py | 24 | 0 | 15.09s |
| cosmos_framework/trainer/local_memory_grouped_resume_test.py | 31 | 0 | 16.27s |
| examples/psm_wma_robocasa_corrected_telemetry_test.py | 25 | 0 | 4.53s |
| examples/psm_wma_robocasa_corrected_phase5_test.py | 58 | 1 | 23.03s |
| TOTAL | 151 | 2 | 0 failed/errors |

py_compile 9/9 PASS, exit0; Ruff check same9 files PASS, exit0 (ruff0.12.7). Exact Child diff 9 files, GitHub compare independently confirms counts 346 insertions / 125 deletions. DS observed no unexpected untracked or modified production files.

DS Gate A outcomes: A1 consumer full 128, slot-major identity/S0/terminal PASS; A2 n_member/n_window 128/256 + terminal 128/136 & 8/136, synthetic FP32 packed/index objective & local slow-grad oracle PASS; A3 create_graph=True and non-detached prefixes + nonzero slow grads PASS; A4 2 native F/B per GA2 window, one optimizer/scheduler update, abort/overflow no live state commit, resumed state tests PASS; A5 trace-only Index-major identity hash, exact effective consumers/telemetry counts, strict native layout config digest differentiation PASS. These are CPU/synthetic scope; not a real model numerical audit.

DS two nonblocking observations: `examples/psm_wma_robocasa_corrected_phase5.py` digest marker `v2_a2_member_packed_slot_major_v1` vs `examples/psm_wma_robocasa_corrected_telemetry.py` JSONL diagnostic marker `v2_a2_slot_major_packed_member` (same semantic layout, distinct literals; no observed equality-dependent consumer); GPU native MoT packing/sigma/noise/FSDP equivalence not proven by CPU smoke.

DS separately reports Formal30k old Index8 code pinned Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982. Last rank0 progress iter1400 at 2026-10-13 03:08:22, wall~40.4s, no active training process detected; infer no GPU run occurred during CPU acceptance. Inference/eval processes at iter1300 exist separately. DCP folder iter_000001400 exists, but latest_checkpoint.txt=iter_000001300. **Do not infer iter1400 is complete or resumable merely from the folder; pointer inconsistency requires read-only per-rank DCP component/completeness and job writer provenance check.**

DS did not modify live Formal worktree, DCP, dataset, model or logs; `git fetch` advanced tracking refs only. GPU Gate B expressly not authorized by this evidence.
GPT CPU closure review: docs/collab/chatgpt/reviews/2026-10-13_V3_packed128_native_gateA_CPU_acceptance_closure_c4731bca_c8dabbb3.md
Prior new-pair review: docs/collab/chatgpt/reviews/2026-10-13_V3_packed128_native_implementation_incremental_review_c4731bca_c8dabbb3.md