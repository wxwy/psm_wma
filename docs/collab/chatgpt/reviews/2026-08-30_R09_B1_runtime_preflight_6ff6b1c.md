# ChatGPT Review — R09-B1 TTT runtime preflight implementation request

- Date: 2026-08-30
- Reviewer: ChatGPT
- Latest reviewed HEAD: `6ff6b1c849bbafa43303e6ca893bc009ff82585e`
- Runbook provenance-alignment commit: `5005e4f755384b1fb4b4b2963ebbdccaf28efa80`
- Submodule/Gitlink inspected: `ee1b78d532bad99ab29bcc1891c8e374eb960297`
- Canonical B0 evidence: commit `4e85ba81a0514e3f93098eccdd45a41f1d5d5ce3`, recorded clean root `685ca9a78ca3421dc01d3cb7e8c440ef02615db7`
- Verdict: **REQUEST_CHANGES**

## Summary

B0 provenance 前置已经修正正确；本轮没有发现未经授权的 runtime/GPU 实现，当前仍是文档级 B1 preflight。

但现在还不能给 `APPROVE_TO_IMPLEMENT_B1`。B1 runbook 已正确识别 A1 GRU probe/optimizer/checkpoint 不能直接复用，也正确冻结了 per-forward fresh state、TTT parameter-free/detached 和独立 GPU Gate。剩余 blocker 主要集中在真正进入 production runtime 后的执行语义。

## Accepted

### B0 canonical provenance is now correct

`docs/build/PSM-WMA_R09_B1_TTT_runtime_preflight_runbook_v0.1_2026-08-30.md:5` 已同步为：

- current canonical artifact commit = `4e85ba8`
- recorded clean root = `685ca9a`
- submodule/Gitlink = `ee1b78d`
- `f4ca0fc/a9b7443` 仅为 historical initial-generation provenance。

上一轮 B0 provenance blocker 不再影响 B1。

### Good B1 separations

Runbook 已正确要求：

- default recurrent path 不变，TTT 只能显式 opt-in；
- production forward 每次从 `state=None` 开始，不跨 outer forward carry；
- TTT fast state 不进入 model field / optimizer / DCP / worker / episode cache；
- A1 `.cell` state probe、16 tensors / 142,784 elements、encoder nonzero-grad 等不能作为 B1 PASS；
- GPU smoke 必须在 B1-S 独立 closure 后再申请；
- B1 artifact 使用独立 `artifacts/g0/r09/b1/`，不得覆盖 A1/B0。

这些边界继续保留。

## Findings

### HIGH-1 — production TTT 的 outer grad-mode 合同未冻结；当前 backend 在 `no_grad/inference_mode` 下会直接失效

Runbook 将 B1 定位为 production runtime wiring：

- runbook `:9-11`：把 B0 backend 接入当前 Local production runtime；
- `:32`：要求 production forward 从 `replay(..., state=None)` 开始；
- `:49+`：后续还要做 fixed-weight Normal/Zero/Shuffle runtime capture。

但当前 B0 backend 的 inner update：

`cosmos-framework/cosmos_framework/model/generator/mot/local_evidence.py:243-246`

```python
work = W[row].detach().float().requires_grad_(True)
...
loss = ...
grad = torch.autograd.grad(loss, work, create_graph=False)[0]
```

依赖 autograd 开启。

如果外层调用处处于 `torch.no_grad()` 或 `torch.inference_mode()`，仅对 `work.requires_grad_(True)` 不会重新开启图记录，`loss.requires_grad=False`，随后 `torch.autograd.grad` 会报错。

这是 production runtime 级问题，不是性能 nit。B0 CPU contract 只证明了正常 grad-mode 下的算法合同，并没有覆盖 inference/no-grad 外层。

而当前 B1-S 允许范围（runbook `:43`）只允许 selector、Local runtime 构造/类型、probe/verifier/test，没有明确允许或冻结 backend 的 grad-mode 处理，因此实现者无法在不越界的情况下可靠修复这个 production 问题。

**Required fix**

实施前必须二选一并写进 runbook：

**方案 A（推荐）— production-safe inner-grad contract**

明确允许对 `TTTLocalMemoryBackend.replay` 做最小 grad-mode 包装，并冻结：

- inner fast-weight update 始终在显式 inner grad context 中执行；
- outer native graph 仍完全 detached，不允许通过 adaptation 回传；
- 在外层 normal-grad 和 `torch.no_grad()` 下得到相同 state/token/update-count；
- 如果项目真实 inference path 使用 `torch.inference_mode()`，也必须给出明确支持策略并加定向测试；不能默认 `torch.enable_grad()` 能覆盖 inference mode。

B1-S CPU hard gate 至少包含：
- normal-grad replay PASS
- outer `no_grad` replay PASS + 与 normal exact/approved tolerance
- actual inference context（若使用 inference_mode）PASS
- graph_detached 仍为 true。

**方案 B — 明确 B1 暂时只授权 training runtime**

如果不准备修改 backend，则 runbook 必须撤回“production runtime”表述，并明确 B1-S/B1-G 只覆盖训练 forward，禁止把该 backend 用于 eval/inference/closed-loop。之后需另建 inference-runtime Gate。

在当前表述下不能既称 production wiring，又不定义这个 grad-mode contract。

### MEDIUM-1 — selector / A1 interaction / optimizer allowlist 仍未冻结到 exact contract

Runbook `:30` 只写“新增一个仅 B1 opt-in 的 backend selector”，但没有冻结：

- exact config field / environment variable 名；
- legal values；
- default value；
- B1 enabled 时是否强制 `local_history_enabled=true`；
- 与 `PSM_R09_A1_ENABLED` 的互斥；
- 与 `PSM_R09_A1_PROBE_OUTPUT` 的互斥/禁止；
- B1 下 exact optimizer `keys_to_select`。

这不是纯命名问题，因为当前真实 recipe：

`cosmos-framework/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py:189-195`

A1 会把 optimizer allowlist 强制设置为四项：

```text
local_history_runtime.encoder
local_history_runtime.recurrent_backend
local_memory2llm
local_memory_modality_embed
```

而 runbook `:33,55` 又说 B1 只有“三条既有 prefix / 三个参数组”。必须冻结到底是：

- 保留四个 key，其中 backend key 对 parameter-free TTT 零匹配；
- 还是 B1 明确替换成三个 exact key。

同时 A1 runtime probe 当前直接访问：

`callbacks/r09_a1_runtime_probe.py`

- `backend.cell.weight_ih`
- GRU 两成员 state

如果 stale A1 probe env 与 B1 同时开启，会直接对 TTT backend 失效。runbook 只说“A1 专属 probe 不再被误用于 TTT”，但没有给 fail-fast 条件。

**Required fix**

在 runbook 冻结一个可直接实现的 exact selector contract，例如：

- exact field: `local_history_backend = "recurrent" | "ttt"`（名称可自定，但必须冻结）
- default = recurrent
- B1 recipe opt-in 的 exact env/config 映射
- `ttt` 仅在 `local_history_enabled=true` 时合法
- B1 与 `PSM_R09_A1_ENABLED=1` fail-fast mutual exclusion
- B1 与 A1 GRU probe env/callback fail-fast mutual exclusion
- exact B1 optimizer keys，逐项列出
- TTT backend prefix 预期 zero parameters 的处理口径。

另外把 runbook `:55` 的“TTT backend named_parameters(), optimizer 与 DCP state 均为空”改成“**backend-specific** optimizer/DCP state 为空”，避免与后半句“实际 optimizer membership 来自三个 Local slow groups”自相矛盾。

### MEDIUM-2 — B1-S 没有冻结独立 machine-readable closure artifact

runbook `:41-45` 把 B1-S 定义为一个需要三方 closure 才能进 GPU 的独立 Gate，但当前 §5 只给了后续 `r09_b1_ttt_runtime_v1` 的总体 runtime evidence schema，没有单独冻结 B1-S 的 canonical static/CPU artifact 与 verifier。

按现有项目治理，如果 B1-S 只以 pytest 文本或人工描述结束，下一轮无法像 B0/A1 一样做独立 machine-readable closure。

**Required fix**

在实施前冻结 B1-S 的最小 artifact/verifier，例如：

```text
artifacts/g0/r09/b1/static_contract.json
tools/g0/verify_r09_b1_static_contract.py
```

名称可调整，但 schema 至少 hard-gate：

- root/submodule/Gitlink + tracked clean
- selector default recurrent exact
- TTT opt-in exact
- default recurrent construction unchanged
- TTT construction exact B0 dimensions/segment_steps
- state fresh per forward
- backend parameter count = 0
- backend state_dict empty / fast state not serialized
- exact optimizer keys and actual matched parameter names
- A1 probe/flag mutual exclusion
- targeted gradient facts
- grad-mode contract from HIGH-1
- command/tool SHA
- status PASS/FAIL.

B1-S closure 后再单独申请 B1-G GPU，保持当前治理不变。

## Non-blocking note

当前 TTT backend 在 GPU 上对每个 timestep 使用：

- `valid.nonzero(...).flatten().tolist()`
- Python row loop
- CUDA scalar `if progress[row] == ...`

会产生 host/device synchronization 风险。B1-S 不需要为性能重写，但 B1-G 应记录 host step wall time / TTT update count，若 slowdown 明显再单独优化，不要在本 Gate 同时改算法和性能实现。

## Verdict

**REQUEST_CHANGES**

这次只需要修 B1 runbook / source-audit contract，不应开始 production wiring，也不应运行 GPU。

建议整改顺序：

1. 先冻结 outer grad-mode / inference contract；
2. 冻结 exact selector + A1 mutual exclusion + optimizer keys；
3. 冻结 B1-S machine-readable artifact；
4. 再重新申请 `APPROVE_TO_IMPLEMENT_B1`。

## Gate state

```text
R09-B0 technical CPU contract = CLOSED
R09-B0 provenance hygiene = CLOSED
R09-B1 runtime preflight = REVIEW / REQUEST_CHANGES
B1-S production wiring implementation = BLOCKED
B1-G GPU smoke = BLOCKED
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT import = BLOCKED
Global / Agent / RL = BLOCKED
```
