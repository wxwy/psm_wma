# ChatGPT Review — R09-B1 TTT runtime preflight contract rereview

- Date: 2026-08-31
- Reviewer: ChatGPT
- Latest reviewed HEAD: `ecbe34d77dd1b80fbd240d107a62570fdc8ef0e7`
- Contract-hardening commit: `4d48c95cfb7d7b6afbd849fde63a3dc652123a66`
- Submodule/Gitlink inspected: `ee1b78d532bad99ab29bcc1891c8e374eb960297`
- Verdict: **APPROVE_TO_IMPLEMENT_B1**

## Summary

上一轮 3 个实施前 blocker 已关闭：

1. grad-mode / inference 口径已明确选择 **training-only**；
2. exact selector、A1 mutual exclusion、optimizer keys 已冻结；
3. B1-S 独立 machine-readable verifier/artifact 已冻结。

本批准只授权 **B1-S**：
- 最小 selector / runtime 构造接线；
- training-only grad-mode fail-fast guard；
- 定向 CPU tests；
- B1-S verifier；
- `artifacts/g0/r09/b1/static_contract.json`。

不授权 GPU、B1-G、eval/inference/closed-loop、多卡、长训、matched SR、backend freeze、RoboTTT/shared-MoT、Global/Agent/RL。

## Closure of previous findings

### CLOSED — HIGH-1: grad-mode / inference contract

Runbook 已改成 training-only：

- `:13` 明确本 Gate 不授权 eval/inference/closed-loop；
- `:32` 冻结：
  - normal training grad-mode 可执行；
  - `torch.no_grad()` / `torch.inference_mode()` 必须在任何 fast-state mutation 前 fail-fast；
  - B1 不声称 inference/runtime 支持；
  - inference 支持以后另建独立 Gate。

B1-S 允许最小 guard 与 CPU coverage，边界清楚且不需要现在修改 TTT 算法本体。

### CLOSED — MEDIUM-1: selector / A1 mutual exclusion / optimizer

Runbook `:30` 已冻结 exact selector：

- config field：`local_history_backend`
- legal values：`recurrent | ttt_fast_weight`
- default：`recurrent`
- env：`PSM_R09_B1_TTT_ENABLED=0|1`
- TTT 仅在 `local_history_enabled=true` 时合法
- 与 `PSM_R09_A1_ENABLED=1` fail-fast 互斥
- 与非空 `PSM_R09_A1_PROBE_OUTPUT` fail-fast 互斥

Runbook `:33` 已冻结 B1 exact optimizer keys：

- `local_history_runtime.encoder`
- `local_memory2llm`
- `local_memory_modality_embed`

parameter-free TTT backend 不再保留第四个 optimizer key。

同时 `:34` / `:55` 已把“backend-specific optimizer/DCP state 为空”与整个 optimizer/DCP 非空正确区分。

### CLOSED — MEDIUM-2: B1-S machine-readable closure

Runbook `:64-80` 已冻结：

- verifier：`tools/g0/verify_r09_b1_static_contract.py`
- canonical artifact：`artifacts/g0/r09/b1/static_contract.json`
- `--require-clean`
- root/submodule/Gitlink
- selector/default/opt-in
- A1 mutual exclusion
- B0 dimensions/segment_steps
- fresh-state
- backend parameter count/state_dict
- exact optimizer keys/matched names
- grad-mode contract
- outer graph detach
- command/tool provenance
- PASS/FAIL hard gate

因此 B1-S 可以独立三方 closure，不需要依赖 pytest 文本。

## Implementation-time hard requirements

以下是本批准的解释边界，实施时必须进入 verifier/test hard gate：

1. no-grad / inference-mode 的 fail-fast 必须发生在 **任何 externally observable fast-state mutation 前**。若使用传入 state 做定向测试，异常后 state 必须 exact unchanged。
2. `gradient_facts` 是“记录事实”，不是要求所有组都 nonzero。由于 B0 detach 已冻结：
   - 不得把 encoder 的 TTT-path nonzero gradient 作为 PASS 条件；
   - Local projection / modality embed 可按实际训练路径记录 finite/nonzero；
   - verifier 不得复用 A1 的“所有 active groups nonzero”逻辑。
3. default recurrent 路径必须 exact preserved；B1 opt-in 关闭时不能改变 R08/A1 构造、optimizer 或 checkpoint schema。
4. B1-S 不得运行 GPU，也不得生成或覆盖 B0/A1 artifacts。

## Non-blocking note

当前 TTT GPU 实现里的 `.tolist()`、Python row loop 和 CUDA scalar branch 仍可能造成同步开销。该项继续留到 B1-G 记录 step wall time / update count 后再判断，不在 B1-S 同时做性能重写。

## Verdict

**APPROVE_TO_IMPLEMENT_B1**

授权上限：**B1-S only**。

## Gate state

```text
R09-B0 technical CPU contract = CLOSED
R09-B0 provenance hygiene = CLOSED
R09-B1 preflight = APPROVED_TO_IMPLEMENT_B1
B1-S static/runtime wiring + CPU contract = AUTHORIZED
B1-G GPU smoke = BLOCKED / separate approval required
eval/inference/closed-loop = BLOCKED / separate Gate required
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT import = BLOCKED
Global / Agent / RL = BLOCKED
```
