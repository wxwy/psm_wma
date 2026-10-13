# DS_PRO Full-Segment Prefetch Gate C0 CPU evidence — Owner relay and exact I001 diff

Date: 2026-10-13
Original implementation Root c666691b5bd5802a539567123f48873f5de83e9c / Child cb4088c75e3e2f62d16425b8e55d587792008011;
New import-only remediation Root d45712a37318357ba2f57bde3d0f1f448aabbbd9 / Child 8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1.
Source: user's uploaded DS_PRO text report `V3 Full Segment Prefetch — CPU Gate C0 Acceptance` at 2026-10-13; GPT independently verified GitHub exact original/new SHA and 2-file diff, not the original DS remote test outputs.

DS isolated CPU report of original pair:
- Root/Child/Gitlink checked in /tmp/ds_pro_v3_full_prefetch_cpu_20261013/{root,child}, old Formal30k worktree remains on root b159f459 / child 937066ff, no GPU, DCP, latest pointer or running inference mutation.
- pytest on ten named modules: 217 passed, 2 skipped, exit 0.
- py_compile all 13 changed child files PASS, exit 0.
- Ruff check all 13 changed files FAIL exit 1. Exactly two I001 diagnostics: `cosmos_framework/data/generator/augmentors/text_tokenizer.py` and `cosmos_framework/model/generator/mot/robocasa_exact_window_local.py`. DS classifies first as already present in older Child and second net-new, but both should be fixed for a clean candidate.
- C0.1–C0.9 old source contracts all marked PASS: legacy nw0/RNG digest unchanged; opt-in keyed RNG is deterministic; keyed sync/full-prefetch CPU synthetic parity; terminal-partial, next-window future, abort/close/state, config digest, NVTX mock status.
- DS correctly notes GPU Stall current-stream proxy uncalibrated and GPU Trace not run. CPU 9/9 checks and 217 test passes do not measure throughput.

New exact diff:
- GitHub compare `cb4088c...8f3672d1` includes precisely two files, each an import sort-only reordering (1 insertion+1 deletion); no business logic, imports added/removed or extra code changes.
- `text_tokenizer.py`: `cosmos_framework.utils.generator.data_utils` before `cosmos_framework.utils.lazy_config`.
- `robocasa_exact_window_local.py`: `data.generator.action.datasets.*` imports before `data.generator.action.utils.transform_random`.
- Child branch and Root gitlink fast-forward to new Sha; old Formal30k checkout and source Checkpoint not touched.
- Real Ruff invocation on NEW SHA has not been executed by GPT (training venv not accessible in current tool runtime). Thus no PASS claim yet.

Test evidence scope: previous 217/2 pass is for OLD child `cb4088c`; may be cited as prior functionality evidence but not a falsified new SHA test run. New pair's new change only sorts imports; request focused recheck.
Formal review: docs/collab/chatgpt/reviews/2026-10-13_V3_full_segment_prefetch_C0_I001_remediation_review_d45712a3_8f3672d1.md
DS focused request: docs/collab/chatgpt/requests/2026-10-13_DS_PRO_full_prefetch_C0_import_order_remediation_narrow_retest.md