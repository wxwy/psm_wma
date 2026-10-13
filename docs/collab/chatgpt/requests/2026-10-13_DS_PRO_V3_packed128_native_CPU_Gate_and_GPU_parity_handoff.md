# DS_PRO — V3 Native Packed128 bounded validation handoff

Date: 2026-10-13. Role: DS_PRO validates and reports; MUST NOT change any production code.
Formal Root Implementation: c4731bca1a590663db88bd6cd74dbcf9fd513a85
Child/Gitlink: c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686
Source review: docs/collab/chatgpt/reviews/2026-10-13_V3_packed128_native_implementation_incremental_review_c4731bca_c8dabbb3.md

Gate A — CPU-only, run now in isolated clean checkout; do NOT checkout/pull/reset the Formal30k pinned worktree. The currently running Formal job is not part of this Gate.
Use the existing complete training venv, export PYTHONPATH to the isolated new Child and HF_HUB_OFFLINE=1. Verify actual Python import path and exact Root/Child/Gitlink identities.

Execute test modules with python -m pytest -q on these five files:
cosmos_framework/model/generator/mot/local_memory_grouped_window_test.py
cosmos_framework/trainer/local_memory_grouped_test.py
cosmos_framework/trainer/local_memory_grouped_resume_test.py
examples/psm_wma_robocasa_corrected_telemetry_test.py
examples/psm_wma_robocasa_corrected_phase5_test.py

Run python -m py_compile and ruff check on all nine changed Child source/test files. Report exact exit codes, pytest counts, first failure traceback; any error STOPS Gate A, do not continue to GPU. Do not change production code.

Verify full member Batch128, GA2→2 native calls/optimizer/rank, 256 consumers/rank, terminal partial GA128+8 normalized 128/136+8/136, S0 None prefix, slot-major model input, index-major audit identity hash, Local Slow gradient nonzero & source-linked, no optimizer/frontier publish on failure, one optimizer step/GA2, exact config digest different from legacy layout, no unexpected JSONL schema loss.

Gate B — ONLY after Gate A green and an explicit separate Owner authorization, in isolated GPU namespace on approved resources. It is not authorized by this handoff.
Compare old V3 Index8 vs new Packed128 with matched genuine RoboCasa data, identical initial weights and per-consumer sigma/epsilon/dropout: losses (outer/action/vision/aux), all selected optimizer FQN gradients (group Generation/Action/Local, local w0_fast, encoder, slot_queries), grad-L2/cos, no missing/nonfinite, FSDP8 collective no hang, single optimizer step and persistent Fast State/Frontier parity, isolated strict DCP resume. Freeze tolerances before looking at evidence.
Direct Batch128 only (no staged16/32/64). Record 8rank VRAM and wall p50/p95 and actual native callback count. OOM or parity FAIL must be reported, no silent shrink, no checkpoint reuse or edits to the existing Formal job.

Report once as DS_PRO_V3_PACKED128_CPU_ACCEPTANCE_2026-10-13.md with command lines, exact SHA, CPU log, no interference with running Formal30k. Stop after Gate A and send to GPT.