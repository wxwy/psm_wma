# ChatGPT Review — R09-B1 B1-S implementation / static verifier

- Date: 2026-08-31
- Reviewer: ChatGPT
- Latest reviewed root HEAD: `fdd5a7a3874978851b6440f986114ce8a2bcd7e2`
- Submodule/Gitlink: `0381335d58b7988a53e5ef9d209cfaf878cd3077`
- Previous authorization: `APPROVE_TO_IMPLEMENT_B1` (B1-S only)
- Verdict: **REQUEST_CHANGES**

## Summary

本轮实现范围总体符合上一轮授权：

- selector 默认 recurrent、B1 opt-in TTT；
- A1 flag/probe 与 B1 互斥；
- TTT training-only guard 在任何 fast-state mutation 前执行；
- production Local runtime 仍以 `replay(..., state=None)` 使用 backend；
- 未运行或提交 GPU/B1-G 证据；
- 未引入 eval/inference/closed-loop 支持。

因此 **runtime wiring 本身不要求重做**。

当前 blocker 在 `tools/g0/verify_r09_b1_static_contract.py`：它尚不能可靠生成我们冻结的 B1-S canonical machine-readable closure evidence。

## Findings

### HIGH-1 — verifier 的 `_recipe()` / `importlib.reload()` 共享 module 状态导致 selector/optimizer hard-gate 不可靠，clean run 很可能自相矛盾

Relevant lines:

- `tools/g0/verify_r09_b1_static_contract.py:29` — `_recipe(...)`
- `:88-89` — `default_recipe = _recipe(b1=False)` / `ttt_recipe = _recipe(b1=True)`
- `:93` — conflict case 再次 `_recipe(...)`
- `:103-104` — 之后重新调用 module function 判断 default / TTT selector
- `:114` — 从同一个 module object 读取 optimizer keys

问题有两层：

1. Python import module 是同一个可变对象。  
   `default_recipe` 和 `ttt_recipe` 实际引用同一个 module；后一次 `importlib.reload()` 会原地重写前一个引用。

2. `_recipe()` 在 `finally` 中恢复环境变量后才返回给调用方使用。  
   因此 `:104` 再调用：
   `ttt_recipe._action_policy_libero_edge_model_config()`
   时已经不在 `PSM_R09_B1_TTT_ENABLED=1` 的隔离环境中，通常会重新得到 `recurrent`，而不是 `ttt_fast_weight`。

更严重的是，`:93` 的 A1 mutual-exclusion negative case 会在 module reload 的全局配置构造阶段抛异常。被异常中断的 reload 可能已把同一个 module 的 `action_policy_libero_edge_all` 重置到部分初始化状态；随后 `:114` 再从这个 module 读取 optimizer keys，结果同样不再是可靠的 B1 snapshot。

因此当前 verifier 的 selector/optimizer PASS/FAIL 取决于共享 module 的 reload 时序和 ambient env，而不是被审核的精确配置合同。

**Required fix**

不要返回/缓存 live module object 作为不同 env case 的证据。二选一：

- 推荐：每个 env case 在独立 subprocess 中 import recipe，并输出 immutable JSON snapshot；
- 或在 `_recipe` 的 env context **内部**就提取并 deep-copy 所需 immutable facts（model config、optimizer keys 等），返回普通 dict；negative cases 也必须保证失败 reload 不污染后续 positive snapshot。

至少独立得到：
- default recurrent snapshot；
- B1 TTT snapshot；
- B1+A1 negative snapshot；
- B1+A1-probe negative snapshot。

verifier 的最终 hard gate 只能基于这些隔离 snapshot，不得依赖同一 live module 的后续状态。

### HIGH-2 — frozen optimizer/gradient evidence 尚未真正测量；当前关键字段缺失或被硬编码

上一轮批准时明确要求 B1-S artifact hard-gate：

- exact three optimizer keys；
- **actual matched parameter names**；
- backend parameter count=0；
- backend-specific optimizer state empty；
- gradient facts；
- encoder 不要求 TTT-path nonzero grad。

当前 verifier：

- `:114` 只检查 recipe 中三个 key 字符串是否相等；
- `:123` 直接写：
  - `backend_specific_state_empty: True`
  - `gradient_facts` 只有 `ttt_token_requires_grad` 与一个“required=False”声明；
- 没有 `matched_parameter_names`；
- 没有从实际 parameter set / optimizer selection 派生 backend 是否进入 optimizer；
- 没有实际 gradient present/finite/nonzero facts。

这与 frozen runbook 的 B1-S schema/hard gate 不一致。字符串 allowlist 正确，不等于实际 optimizer membership 正确。

**Required fix**

verifier 必须从实际参数对象派生证据，而不是声明：

1. 构造最小真实 Local module（encoder + TTT backend + Local projection/modality embed），或使用项目已有轻量 optimizer-selection helper；
2. 用实际 B1 `keys_to_select` 运行与训练 recipe 同源的 parameter-selection 逻辑；
3. 序列化：
   - exact keys；
   - 每个 key 实际 matched parameter names；
   - selected optimizer parameter names；
   - TTT backend matched names = []；
   - backend parameter count = 0；
   - backend-specific optimizer state 是否为空（从实际 optimizer/selection 事实派生，不能常量 True）；
4. 做一个 CPU representative backward，机器可读记录每组 gradient：
   - present
   - finite
   - max_abs / nonzero
   - encoder TTT path 允许 absent/zero，不能把 A1 “all groups nonzero”复用为 PASS。

如果 static verifier 不实际创建 optimizer，也至少必须证明 selected parameter IDs/names 完全来自同一 optimizer builder；“backend-specific optimizer state empty”只能在有实际 optimizer evidence 时声称。

### MEDIUM-1 — current commit 还不是 B1-S closure：canonical artifact 尚未提交

当前 root `fdd5a7a` 已有 verifier 与 Gitlink，但远端尚不存在：

`artifacts/g0/r09/b1/static_contract.json`

这本身可以作为“实现中间提交”，不算 scope violation；但不能据此关闭 B1-S，也不能申请 B1-G。

修完 HIGH-1/2 后，应：

- 从 pushed-clean exact root/submodule 运行 verifier；
- 生成 canonical `static_contract.json`；
- artifact 内记录 exact root/submodule/Gitlink、tracked-clean、command/tool provenance；
- 提交并 push artifact；
- 再发 B1-S closure review。

## Accepted implementation details

以下部分本轮审查通过，可保留：

### training-only fail-fast

`cosmos_framework/model/generator/mot/local_evidence.py:232-233`

在读取/修改 state 前先检查 `torch.is_grad_enabled()`，no-grad/inference-mode 立即抛错。定向 test 同时确认传入 state exact unchanged。符合上一轮 training-only contract。

### selector / A1 mutual exclusion

Recipe 已实现：

- strict `PSM_R09_B1_TTT_ENABLED=0|1`
- B1 要求 R08 Local history enabled
- B1 与 A1 enabled 互斥
- B1 与 A1 probe output 互斥
- B1 exact optimizer keys 三项

### default-off wiring

`OmniMoTModelConfig.local_history_backend` 默认 `recurrent`；`OmniMoTModel.build_net` 只有 opt-in 时构造 TTT backend，默认 recurrent constructor 的参数保持原样。

### scope

Submodule `0381335` 只修改：

- model config
- LIBERO Edge recipe
- Local backend guard
- Local tests
- OmniMoT model selector

Root `fdd5a7a` 只增加 verifier、更新 Gitlink/TODO/SESSION。

未发现 GPU、多卡、长训、eval/inference/closed-loop、shared-MoT、Global/Agent/RL scope creep。

## Verdict

**REQUEST_CHANGES**

只修 B1-S verifier / CPU evidence；runtime wiring 不要求回退或重写。

在新的 canonical artifact 经独立 closure 审核前：

```text
R09-B0 = CLOSED
R09-B1 preflight = APPROVED
B1-S implementation = REVIEW / REQUEST_CHANGES
B1-S closure = NOT APPROVED
B1-G GPU = BLOCKED
eval/inference/closed-loop = BLOCKED
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT = BLOCKED
Global / Agent / RL = BLOCKED
```
