# V3 Full Segment Prefetch Gate C0: independent CPU evidence and I001 correction

Date: 2026-10-13
New formal Implementation Root d45712a37318357ba2f57bde3d0f1f448aabbbd9 / Child Gitlink 8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1
Former paired implementation Root c666691b5bd5802a539567123f48873f5de83e9c / Child cb4088c75e3e2f62d16425b8e55d587792008011
Evidence receipt: docs/collab/chatgpt/evidence/2026-10-13_V3_full_segment_prefetch/DS_PRO_2026-10-13_full_prefetch_C0_CPU_owner_relay_and_I001_diff_receipt.md

**Verdict: REQUEST_CHANGES / LINT_RECHECK_PENDING (very narrow scope).** The original C0 code/functionality suite is CPU GREEN per DS (217 passed 2 skipped; 13 py_compile success; C0.1-C0.9 PASS), but Ruff failed with two I001 on the original pair. GPT has corrected exactly those two import-order blocks; NEW formal pair needs an independent Ruff pass and minimal import/CPU smoke on exact new SHA before C0 approval.

## Independent verification

1. Locked original Root/Child and source diff in GitHub. New Child diff old `cb4088c` → new `8f3672d1` is exactly two paths: `data/generator/augmentors/text_tokenizer.py` and `model/generator/mot/robocasa_exact_window_local.py`, import reordering only; Root implementation `d45712a3` updates Gitlink only. No new optimizer/TTT/Checkpoint/DataPlan logic.
2. Reviewed Owner-relayed DS isolated C0 report: ten modules 217 passed 2 skipped, no failures; 13/13 py_compile PASS; 13-file Ruff exactly 2 I001, exited1. The text_tokenizer legacy I001 existed on old Packed128 Child, while the local producer's I001 was newly introduced. Both resolved by ordering imports. Raw remote stdout not available directly to GPT; no claim GPT executed ruff.
3. Previous Packed128 CPU Gate A at Root c4731bca / Child c8dabbb remains an earlier separate approval; the new Full Prefetch Candidate Gate C0 is independent. Prior DS 217 test suite is original C0 pair evidence, not inheritable formal verdict for import-fix pair without scoped recheck.

## Findings

**Finding C0-LINT (MEDIUM → REMEDIATED IN SOURCE, RETEST PENDING)**: Ruff I001 old pair text_tokenizer and robocasa_exact_window_local. New code orders the imports correctly; request DS validate actual Ruff under original .ruff.toml on exact new Child.

**C0-FUNCTIONAL (CPU previous pair PASS, new pair SMOKE PENDING)**: All C0.1–C0.9 findings from DS report remain valuable. No non-import code changed in remediation. Recheck only two affected import modules and 13-file lint; repeating all 217 tests is unnecessary unless an observed source/Dependency issue appears or DS policy requires it.

**GPU DATA STALL (HIGH PENDING)**: `gpu_data_stall_ms` and `data=` existed before this change and still represent an uncalibrated training-stream gap estimate; NVTX markers added to support a future trace. No causal DATA-wait GPU attribution, no real GPU perf benefit or p50/p95 documented; full optimization NOT ACCEPTED on performance grounds.

**RNG/Resume boundary**: Keyed augmentation explicitly has distinct digest; keyed-sync vs keyed-full-mode is the proper parity comparator, not unkeyed legacy. Existing old Index8 iter1300 DCP still requires separate permitted migration to run Packed128; do not confuse these gates.

**Formal training HOLD**: Gate C0 CPU remediation does not authorize Gate B 8×H100 GPU gradient parity, GPU stall profile, cross-layout migration or full30k. No changes to source DCP/latest pointer or the actual running jobs.

DS narrow retest: docs/collab/chatgpt/requests/2026-10-13_DS_PRO_full_prefetch_C0_import_order_remediation_narrow_retest.md