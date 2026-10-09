# PSM-WMA V3 — w0_fast 梯度缺失及 FSDP2 规约一致性修复候选

Date: 2026-10-09. Code owner / Gate decision: GPT/Codex.
**Result: Missing Gradient Identity Audit PASS; FSDP2 parity fix CANDIDATE / CPU and GPU retest PENDING. Formal30k FRESH remains ON HOLD.**

## Verified evidence and decisive source trace

DS_PRO validated Root `4c482af93c3098a451e3552918f66e4ddbec86a2` / Child `9656efc4dc7221710f0017bad662430c83893430`: CPU **72 passed / 1 skipped**, Ruff/format/compile pass; 8xH100, 24/24 rank x iter audit `AUDIT_OK`, three committed steps, no numeric error. The four absent gradients were exclusively `net.local_memory_runtime.core.w0_fast_in_weight`, `w0_fast_in_bias`, `w0_fast_out_weight`, `w0_fast_out_bias`. Each FSDP Shard(0) contains nonempty local elements and `requires_grad=True`. Iter1: 8/8 ranks zero missing. Iter2: 8/8 ranks four missing. Iter3: ranks 0,1,2,5,6 four missing; ranks 3,4,7 zero.

The core `local_evidence.py::initial_state()` constructs a differentiable copy from w0 for fresh slots; the Sidecar returns detached state for continuing slots. In `local_memory_segment_adapter.py::scan()` all-continuation supplies a detached state with `continuation_mask=None`; mixed fresh/continuation is handled with a differentiable `torch.where(mask, detached_state, w0)` inside `Cosmos3VFMNetwork.scan_local_memory()`. Thus absent w0 gradients during all-continuation are **expected TBPTT behavior**. Fast state inner updates remain active and have nonzero telemetry.

**However PyTorch 2.10 FSDP2 compatibility is not assured.** The installed version's `torch/distributed/fsdp/_fully_shard/_fsdp_param_group.py::post_backward` (v2.10.0, around lines 511-590) builds `fsdp_params_with_grad` separately per Rank based on non-None gradients, then passes that list to `foreach_reduce`. Actual iter3 Rank divergence presents an unsafe parameter-list mismatch risk even if the bounded diagnostic exited 0. This is a blocker for a high-cost formal job, not evidence of corrupt optimizer state in the completed diagnostic. Reference: https://github.com/pytorch/pytorch/blob/v2.10.0/torch/distributed/fsdp/_fully_shard/_fsdp_param_group.py.

## Submitted correction

New Child `v3-persistent-dataset-index-20261009` SHA: `5f5dc38f84caf83ccf3656e812ba83970e26e8d2`. New Root candidate is the final HEAD containing this Review, inbox and Gitlink update. No production branches moved.

- `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`: in all-continuation case (non-None state, no mixed mask), construct the same learnable w0 initial state and an all-True continuation mask, returning `torch.where(all_true, state.detach(), w0)`. Forward state and Local tokens preserve their values; the computation graph retains w0 with **present but zero-valued gradients**. All-fresh and mixed paths maintain their original semantics. No extra collective added.
- `cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py`: new all-fresh/mixed/all-continuation CPU gradient participation tests, exact all-continuation forward/candidate parity and strict mask validation tests.
- **Important optimizer caveat**: Previously `grad=None` skipped Adam updates. With zero-valued gradient, Adam momentum and weight decay may now update w0 during all-continuation; this is an intentional optimizer-behavior correction. Do **not** label it identical backward/optimizer numerics. Existing DCP from the old implementation must never initialize a new formal run.
- Dataset Index, Data Source, w0 parameter inventory, Local inner update rule, scheduler values, DCP format and formal parameter config are unchanged. Code SHA therefore matters independently of frozen `config_digest=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`.
- An independent isolated PyTorch **2.10 CPU** `torch.where(all_true)` test gave unchanged forward and non-None zero w0 gradients (after correcting the simplified detached input's grad setup). **It does not establish project-level pytest or GPU FSDP correctness.**

## Gate A — DS_PRO CPU/static, mandatory before GPU

Use the only existing `psm_wma_v3` checkout; safe FF fetch, verify exact Root HEAD / Child `5f5dc38f84caf83ccf3656e812ba83970e26e8d2` / Gitlink, Child clean and original MM `SESSION.md`, `TODO.md` and evidence preserved. No worktrees, reset/clean, code modification or format-write.

Set `HF_HUB_OFFLINE=1` before pytest and Child-first `PYTHONPATH`. In existing Child venv:

```bash
pytest -q -p no:cacheprovider cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py cosmos_framework/model/generator/mot/local_memory_grouped_window_test.py examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_corrected_phase5_test.py
ruff --version
ruff check cosmos_framework/model/generator/mot/cosmos3_vfm_network.py cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py
ruff format --check cosmos_framework/model/generator/mot/cosmos3_vfm_network.py cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py
python -m py_compile cosmos_framework/model/generator/mot/cosmos3_vfm_network.py cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py
```

Expect Ruff **0.12.7**. Any FAIL: STOP, send complete logs + `ruff format --diff` without fixing code; only GPT edits GitHub.

## Gate B — only after CPU all GREEN

Authorize DS_PRO to execute exactly **one fresh bounded 8xH100 3-optimizer-step** diagnostic on new precise Root/Child, using the accepted external Verified Index/source/cache and the official DROID DCP. Use entirely new `--job-name bounded_w0_fsdp_parity_r1` under external output root; `--phase fresh --stop-after-iter 3 --audit-missing-grads`, `--max-iter 30000 --warmup 500 --save-iter 100 --t 16 --b 8 --ga 2 --k 4 --world-size 8`. Child first in PYTHONPATH; `HF_HUB_OFFLINE=1`. Root and Child expected SHA must equal this Review handoff. Frozen config digest must match.

Save rank0 ordinary telemetry, 8 Rank stdout/stderr, 24/24 `AUDIT_OK`; require selected=314, present=314, missing=0, **all four w0 grads present at each iteration on all 8 ranks**, including iter2 all-continuation and iter3 mixed. Require exactly 3 optimizer commits and no iter4, finite loss/grad/local telemetry, successful DCP 8 rank states, no warnings of abnormal collective behavior. Do not resume any diagnostic DCP.

If any mismatch, stop and report. A valid count is necessary but not sufficient proof of correct numeric reduction, so record any unusual FSDP/NCCL behavior and provide a focused w0-gradient evidence witness where supported. No formal30k or prod promotion until GPT reviews Gate B and authorizes anew.

## Authorization boundary

**Current formal30k launch explicitly SUSPENDED**. The previous 24 AUDIT_OK audit remains valid for *identifying the old condition*, not for passing this changed code. DS is executor only, never code editor. No repeat of closed Dataset/VAE/optimizer Readiness gates.
