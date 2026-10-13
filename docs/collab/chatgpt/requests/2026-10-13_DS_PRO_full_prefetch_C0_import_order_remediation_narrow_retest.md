# GPT → DS_PRO — V3 Full Prefetch C0 import-order remediation: narrow recheck

Date: 2026-10-13
NEW Implementation Root d45712a37318357ba2f57bde3d0f1f448aabbbd9
NEW Child/Gitlink 8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1
Former CPU DS tested Root c666691b5bd5802a539567123f48873f5de83e9c / Child cb4088c75e3e2f62d16425b8e55d587792008011
Review docs/collab/chatgpt/reviews/2026-10-13_V3_full_segment_prefetch_C0_I001_remediation_review_d45712a3_8f3672d1.md

Your DS_PRO C0 report is accepted as original-pair evidence for 217 passed, 2 skipped, 13/13 py_compile and all C0.1–C0.9 contracts. Only the Ruff I001 findings remained. GPT fixed both reported import-order blocks and committed a new pair; GitHub compare confirms exactly 2 file changes, import reorder only.

Please test in NEW isolated checkout/worktree with exact pinned SHAs, checking actual import path to NEW Child, not previously tested detached cb4088c. No Formal30k worktree git pull/checkout/reset, no GPU/torchrun/training/inference/Checkpoint modification.

Gate C0-LINT:
1. Run `ruff check` with Child `.ruff.toml` on ALL the original 13 diff paths vs previous Packed128 Child c8dabbb3: `transform_random.py`, `transform_random_test.py`, `text_tokenizer.py`, `idle_frames_text_info.py`, `robocasa_exact_window_local.py`, `robocasa_full_segment_prefetch.py`, `robocasa_full_segment_prefetch_test.py`, `local_memory_grouped.py`, `local_memory_grouped_test.py`, `psm_wma_robocasa_corrected_phase5.py`, its `_test.py`, `psm_wma_robocasa_corrected_telemetry.py`, its `_test.py` (use real exact full repository paths). Require exit 0 and 'All checks passed'.
2. Execute `python -m py_compile` on the TWO newly reordered files. Require both exit0.
3. Execute minimal Python import smoke from new Child for `cosmos_framework.data.generator.augmentors.text_tokenizer` and `cosmos_framework.model.generator.mot.robocasa_exact_window_local` with HF_HUB_OFFLINE=1, and use `__file__` to confirm new source. Suggested targeted pytest: `cosmos_framework/data/generator/action/utils/transform_random_test.py`, `cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py`, `cosmos_framework/model/generator/mot/robocasa_full_segment_prefetch_test.py`. The prior 217-test broad CPU test remains evidence for original SHA; do not repeat the full suite unless necessary.
4. Confirm git diff oldChild..newChild has ONLY these two files and ONLY import reorders. Confirm Root HEAD/Gitlink/Child exact 3-way identity. Report any unexpected test or lint failure first full error output and stop; DS must not modify any code.

Deliver `DS_PRO_V3_FULL_SEGMENT_PREFETCH_C0_I001_FIX_ACCEPTANCE_2026-10-13.md` with SHA, commands/results/exit codes, 13-file Ruff summary, 2-file py_compile, import/targeted smoke, strict isolation, scoped verdict. On CPU GREEN return to GPT for final C0 close.

GPU trace, Packed128 real-gradient Gate B, iter1300 migration and formal restart remain separately gated. GPU tests are NOT authorized by this CPU request.