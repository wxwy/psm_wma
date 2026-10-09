# PSM-WMA V3 — w0_fast FSDP2 parity Gate A Ruff EOF blocker remediation

Date: 2026-10-09
Owner and sole code modifier: GPT/Codex
Gate status: **Gate A BLOCKED previously; formatting blocker corrected and narrowly scoped STATIC RETEST PENDING**. Gate B 8xH100 **not executed** on this fix. Formal30k remains **PAUSED**.

## Source evidence and exact fix

DS_PRO executed the previous exact pair Root `2405db5ad11d6dcd8a39699d70bf721981e95b7f` / Child+Gitlink `5f5dc38f84caf83ccf3656e812ba83970e26e8d2`:
- **pytest 110 passed, 2 skipped**, focused five test files, exit 0;
- **Ruff 0.12.7 check PASS**, both source/test files;
- **Ruff format --check FAIL** only on `cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py`: final single additional blank line at EOF, one byte;
- py_compile not attempted because DS correctly stopped immediately after format FAIL.
- Child clean, Root only MM notes/DS Evidence; no unsafe source edit, worktree/reset/clean; GPU Gate B was NOT started.

GPT checked the actual Child file, confirmed it ends with exactly two newline characters and matches DS's full Ruff diff. **Only the second EOF newline character was deleted**, with no changed Python tokens, assertions, function definitions, or model code. New Child SHA: **`71e03c8501c94a2ad5fed60955af657d3f945b85`**. The Root Gitlink for this Review is rebound to that exact Child, without production branch changes.

There is no reason to rerun previous 110 passing unit tests solely for the deleted trailing blank line. Their passing evidence is carried forward only because the new Child diff vs `5f5dc38f...` is precisely one formatting byte. Do NOT relabel those tests as executed on the new SHA. Corrected Ruff 0.12.7 format, check and syntax plus exact lock must be verified by DS.

## Narrow Gate A continuation — DS_PRO only

Use **the single existing `psm_wma_v3` worktree**. Safely fetch/FF the Root candidate `v3-persistent-dataset-index-pair-20261009` and Child candidate `v3-persistent-dataset-index-20261009`. Obtain exact Root HEAD from the handoff commit containing this Review, confirm Child HEAD = Root Gitlink = `71e03c8501c94a2ad5fed60955af657d3f945b85`, child clean, preserve MM `SESSION.md`, `TODO.md`, all Evidence and existing DCP. No worktree, format-write, reset/clean, code edits, commits/uploads or force checkout.

In the existing Child venv with `HF_HUB_OFFLINE=1` preset, check:
```bash
ruff --version  # must be 0.12.7
ruff format --check cosmos_framework/model/generator/mot/cosmos3_vfm_network.py cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py
ruff check cosmos_framework/model/generator/mot/cosmos3_vfm_network.py cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py
python -m py_compile cosmos_framework/model/generator/mot/cosmos3_vfm_network.py cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py
```
Collect exit codes/output. If any FAIL, STOP and return `ruff format --diff` and full raw evidence; do not modify code. Underlying pytest **110 passed / 2 skipped** from previous exact implementation is accepted across EOF-only change (clearly label `CARRIED_FORWARD`). **Gate A is GREEN only after this rerun PASS.**

## Conditional Gate B already scoped by prior Review

Only if updated Gate A becomes GREEN: **exactly one fresh 8xH100 3-iteration parity diagnostic**, same as preceding `2026-10-09_V3_w0_fast_fsdp2_gradient_parity_fix_candidate.md`:
- Root: exact new HEAD of this Review; Child: `71e03c8501c94a2ad5fed60955af657d3f945b85`.
- `--phase fresh --stop-after-iter 3 --audit-missing-grads --job-name bounded_w0_fsdp_parity_r1`, completely fresh external output namespace.
- Formal scheduler 30000/500/100, T16/B8/GA2/K4, original Verified Index, Source/Cache, official DROID DCP, model witnesses, frozen digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`.
- Expect **24/24** `AUDIT_OK` (8 ranks x iter1..3), and 314 selected / 314 present / **0 missing** on *every* Rank/Step, with four `w0_fast_*` having present gradient tensors in all-continuation and mixed cases. Include three real optimizer commits (no iter4), finite gradients, normal Local-TTT evolution, all-rank DCP, NCCL/FSDP errors absent.
- Do not resume diagnostic DCP; do not touch production or start formal30k. Any mismatch or failure => STOP and return full logs to GPT for new Gate decision.

## Current verdict

**Only formatting-blocker candidate has been repaired. No new DS verification is claimed.** Gate A STATIC RETEST PENDING; Gate B CONDITIONAL and NOT RUN; Formal30k HOLD.
