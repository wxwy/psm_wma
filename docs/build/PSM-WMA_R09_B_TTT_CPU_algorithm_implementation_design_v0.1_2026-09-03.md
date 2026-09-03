# R09-B TTT v0.2.1 CPU Algorithm/Gradient Implementation Design v0.1

**日期**：2026-09-03

**状态**：REVIEW；实现前必须取得 ChatGPT、Kimi、MM 对同一 root SHA 的批准。

**任务**：`G0-R09-B-TTT-V02-CPU-ALGORITHM-IMPLEMENTATION-DESIGN`

**设计 authority**：

- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md`
- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.1.md`
- `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.2_2026-09-03.md`
- source-audit remediation `39ec772720603ce9cae98b7e30cb41c10437f64e`

**实现基线**：root `f504d67d8eed407af1dc0b55804e94403989b493`，
`cosmos-framework` HEAD/Gitlink 均为
`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。

**本 Gate 权限**：只冻结 CPU functional core 与 CPU-only contract tests；本文不授权修改
Cosmos、导入/运行 torch、GPU、训练、评测、推理、chronology/loss/runtime 接线、
optimizer/config refreeze、P4/P5 真实操作或 B2-T。

---

## 1. 结论

首个实现不原地改造旧 `TTTLocalMemoryBackend`，而是在同一模块新增独立的
`ContinualTTTLocalMemoryCore`。旧类继续作为 superseded B0/B1 prototype 保留，production
构造和 `LocalHistoryRuntime` 本 Gate 均不改。这样 CPU core 可以独立证明新算法与梯度合同，
而不会把未审核的 state owner、packing 或 inference 行为带入现有 runtime。

首版冻结值：

| 字段 | 冻结值/合同 |
| --- | --- |
| `evidence_dim` / `D_e` | `256` |
| `local_dim` / `D_local` | `32` |
| `ttt_dim` / `D_ttt` | `64` |
| `fast_hidden_dim` / `D_ff` | `128` |
| activation | `torch.nn.functional.silu`，非 inplace、无参数 |
| fast bias | 两层均有 bias |
| `inner_lr` | Python float `0.1`；finite 且 `>0`；不是 parameter/buffer |
| `ttt_tbptt_steps` | 唯一截断长度配置，正整数，默认 `16`，与 RoboTTT 对齐 |
| CPU parameter/state dtype | `float32` |
| future production fast storage | `bfloat16`；不在本 Gate 执行，只保留 dtype-preserving API |
| inner compute | 无论 state storage dtype，K/Q/V、fast forward、inner loss 与 inner grad 均 `float32` |
| CPU equivalence tolerance | `atol=1e-6, rtol=1e-5` |

`ttt_tbptt_steps` 只限制一个 CPU `scan_segment()` 可接受的最大时间长度。改变它不初始化、
清空或截断 fast-state 数值；本设计不新增 `alignment` 字段。完整 segment 如何与 episode、
packer 和 backward 边界对齐，仍属于后续 chronology/loss Gate。

---

## 2. 最小实现面

获批后的 implementation commit 只允许修改：

1. `cosmos-framework/cosmos_framework/model/generator/mot/local_evidence.py`
2. `cosmos-framework/cosmos_framework/model/generator/mot/local_evidence_test.py`

不得在本 Gate 修改：

- `LocalHistoryRuntime`、`OmniMoTModel` 或 model construction；
- `OmniMoTModelConfig`、recipe、optimizer selector 或 checkpoint loader；
- dataset、manifest、sampler、packer、trainer 或 native loss；
- action server、closed-loop client或任何 inference schema；
- 根仓 runtime tooling、P3/P4/P5 authority 或真实配置。

不新增依赖和新测试文件；只复用标准库 `math`/`typing.NamedTuple`、`torch`、`torch.nn`、
`torch.nn.functional` 与现有 pytest。

---

## 3. 类型与注册对象

### 3.1 四成员 fast-state pytree

模块级新增：

```python
class ContinualTTTFastState(NamedTuple):
    fast_in_weight: torch.Tensor
    fast_in_bias: torch.Tensor
    fast_out_weight: torch.Tensor
    fast_out_bias: torch.Tensor
```

对 batch `B`，exact shape 为：

| field / canonical member | shape | CPU dtype | future storage dtype |
| --- | --- | --- | --- |
| `fast_in_weight` / `W.fast_in.weight` | `[B,128,64]` | fp32 | bf16 |
| `fast_in_bias` / `W.fast_in.bias` | `[B,128]` | fp32 | bf16 |
| `fast_out_weight` / `W.fast_out.weight` | `[B,32,128]` | fp32 | bf16 |
| `fast_out_bias` / `W.fast_out.bias` | `[B,32]` | fp32 | bf16 |

每 sample 为 `12,448` elements；bf16 payload 为 `24,896` bytes/sample，fp32 CPU reference
为 `49,792` bytes/sample。`NamedTuple` 中不得加入 `initialized`、step counter、valid、done、
momentum、eta、normalization 或其他 tensor。chronology metadata 由后续 owner 管理。

### 3.2 Slow registered parameters

新增 module：

```python
class ContinualTTTLocalMemoryCore(nn.Module):
    key_proj: nn.Linear       # 256 -> 64
    query_proj: nn.Linear     # 256 -> 64
    value_proj: nn.Linear     # 256 -> 32
    w0_fast_in_weight: nn.Parameter   # [128,64]
    w0_fast_in_bias: nn.Parameter     # [128]
    w0_fast_out_weight: nn.Parameter  # [32,128]
    w0_fast_out_bias: nn.Parameter    # [32]
```

本 core 的 trainable slow elements 为：

```text
key_proj    = 64*256 + 64 = 16,448
query_proj  = 64*256 + 64 = 16,448
value_proj  = 32*256 + 32 = 8,224
learned W0  = 12,448
total       = 53,568
```

`inner_lr`、`ttt_tbptt_steps` 与维度均保存为普通 Python 属性，不进入 `state_dict()`；除
Q/K/V 和四个 W0 外不得新增 parameter/buffer。未来挂在
`local_history_runtime.recurrent_backend` 下时，注册名自然与 source audit 提案一致；该挂载
本 Gate 不执行。

### 3.3 初始化

Q/K/V 使用 `nn.Linear` 现有 `reset_parameters()`。

四个 learned W0 使用与相同 shape 的两层 `nn.Linear` 默认初始化等价的规则：

```text
w0_fast_in_weight  <- kaiming_uniform_(a=sqrt(5))
w0_fast_in_bias    <- uniform(-1/sqrt(64),  1/sqrt(64))
w0_fast_out_weight <- kaiming_uniform_(a=sqrt(5))
w0_fast_out_bias   <- uniform(-1/sqrt(128), 1/sqrt(128))
```

禁止全零 W0；否则会让两层 fast MLP 的部分 meta-gradient 在初始步退化。构造器只调用私有
`_reset_w0_parameters()`，不在本 Gate 改写现有 `LocalHistoryRuntime.reset_parameters()`。
meta-device/materialization 初始化属于后续 runtime Gate。

---

## 4. Exact constructor 与校验

```python
def __init__(
    self,
    evidence_dim: int = 256,
    local_dim: int = 32,
    ttt_dim: int = 64,
    fast_hidden_dim: int = 128,
    inner_lr: float = 0.1,
    ttt_tbptt_steps: int = 16,
) -> None:
```

全部维度和 `ttt_tbptt_steps` 必须是非 bool 的正整数；`inner_lr` 必须可转为 float、finite
且严格大于零。非法值统一在构造时 `ValueError`，错误信息必须包含字段名。

`local_dim` 虽可用于小尺寸 CPU fixture，但 production candidate 仍固定为 32；`ttt_dim`、
`fast_hidden_dim`、`inner_lr` 和截断长度可显式覆盖以做 CPU reference tests。覆盖值不会静默
改变其他字段。

---

## 5. Functional API

### 5.1 `initial_state()`

```python
def initial_state(
    self,
    batch: int,
    *,
    device: torch.device | None = None,
    dtype: torch.dtype | None = None,
) -> ContinualTTTFastState:
```

- `batch` 为非 bool 正整数；
- `device=None,dtype=None` 时沿用 W0 parameter 的 device/dtype；
- 对每个 W0 做 `unsqueeze(0).expand(batch,...).clone()`，得到独立 per-sample storage；
- cast 保留从 slow W0 到初始 fast state 的 autograd path；不得 detach；
- 返回恰好四成员 state。

### 5.2 `project_evidence()`

```python
def project_evidence(
    self, evidence_t: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
```

输入 exact `[B,evidence_dim]`、finite。计算并按 `(key_t, query_t, value_t)` 返回：

```text
K = F.linear(evidence.float(), key_proj.weight.float(), key_proj.bias.float())
Q = F.linear(evidence.float(), query_proj.weight.float(), query_proj.bias.float())
V = F.linear(evidence.float(), value_proj.weight.float(), value_proj.bias.float())
```

输出 shape 分别为 `[B,ttt_dim]`、`[B,ttt_dim]`、`[B,local_dim]`，compute dtype 固定
fp32。slow parameter 的 `.float()` cast 必须保留 autograd path，使 future bf16 module 仍能
接收 meta-gradient；不得把 cast 后 weight/bias detach。训练 `step()` 直接调用；未来 inference Gate 可在外部
`torch.no_grad()` 下调用并把 detached ordinary K/Q/V 交给 `step_projected()`。

### 5.3 `step_projected()`

```python
def step_projected(
    self,
    *,
    key_t: torch.Tensor,
    query_t: torch.Tensor,
    value_t: torch.Tensor,
    state_in: ContinualTTTFastState,
    valid: torch.Tensor,
    create_graph: bool,
) -> tuple[torch.Tensor, ContinualTTTFastState, torch.Tensor]:
```

返回 `(token [B,1,local_dim], state_out, present [B])`。

硬约束：

1. 外层必须不是 `torch.inference_mode()` 且必须启用 grad；否则在任何计算/修改前
   `RuntimeError`；`create_graph` 必须是 bool。
2. K/Q/V 必须分别为 `[B,ttt_dim]`、`[B,ttt_dim]`、`[B,local_dim]`，fp32 compute 且
   finite；`valid` 为 `[B]` 并转 bool；state 每个 member 的 batch/shape/device/dtype必须
   一致且 finite。
3. 每个 valid row 的四个 state member 先转 fp32。若 member 已经 `requires_grad`，必须保留
   现有 graph；若它来自 `detach_state()` 或 future inference detached carry，则在不改数值的
   前提下变成新的 `requires_grad=True` leaf。不得为了恢复 grad 复制 W0 或连接旧 segment。
4. 每个 valid sample 独立计算，不能先对 batch/valid 数做 reduction：

```text
pred_before_b = fast_mlp(W_b,t-1, K_b,t)
L_inner,b,t   = mean_feature((pred_before_b - V_b,t)^2)
g_b,t[p]      = autograd.grad(L_inner,b,t, W_b,t-1[p], create_graph=create_graph)
W_b,t[p]      = W_b,t-1[p].float() - inner_lr * g_b,t[p]
m_b,t         = fast_mlp(W_b,t, Q_b,t)
```

5. `autograd.grad` 的 inputs 必须同时包含四个 member，不能遗漏 bias，不能使用 batch mean。
6. update 后各 member cast 回对应 `state_in` dtype；cast 不得 detach。
7. valid sample 的 read 必须使用更新后的 `W_b,t`。
8. invalid sample 不调用 inner grad、不读取 W0、不产生 token：四成员输出值逐 bit 等于输入，
   token exact zero，`present=false`。其他 sample 内容/mask/数量不得改变当前 sample update。
9. per-sample loop 是首版 canonical reference；未来 vectorization 只有在 CPU tolerance 内等价
   才可替换。
10. 全部 API 为 functional、无 in-place state mutation；成功或异常返回后，`state_in` 的四个
    tensor 值均不得被改写。

`create_graph=True` 用于训练 meta-gradient；`False` 仅提供未来 W-only inference 数值核心。
本 Gate 不构造真实 inference context，也不声称 `False` 自动冻结 slow parameter；未来调用者
仍必须按 v0.2.1 在 `no_grad` 下形成 detached K/Q/V，并仅令 detached W leaf requires grad。

### 5.4 `step()`

```python
def step(
    self,
    evidence_t: torch.Tensor,
    state_in: ContinualTTTFastState,
    valid: torch.Tensor,
    *,
    create_graph: bool = True,
) -> tuple[torch.Tensor, ContinualTTTFastState, torch.Tensor]:
```

只做 `project_evidence()` 后委托 `step_projected()`，不得存在第二套 update 数学。

### 5.5 `scan_segment()`

```python
def scan_segment(
    self,
    evidence: torch.Tensor,
    valid: torch.Tensor,
    state_in: ContinualTTTFastState | None = None,
    *,
    create_graph: bool = True,
) -> tuple[torch.Tensor, ContinualTTTFastState, torch.Tensor]:
```

- `evidence=[B,T,evidence_dim]`，`valid=[B,T]`；`1 <= T <= ttt_tbptt_steps`；
- `state_in=None` 时调用 `initial_state(B, device=evidence.device)`，dtype沿用 W0；
- 严格按 `t=0..T-1` 调用同一个 `step()`；
- 返回 token `[B,T,local_dim]`、末状态和 `present=[B,T]`；
- 不在内部 reset、detach、backward 或 optimizer step；
- `T > ttt_tbptt_steps` fail-closed，绝不自动分段；
- `ttt_tbptt_steps` 默认 16，与 RoboTTT 对齐，但可在构造器设置任意正整数；它不是 memory
  horizon。

### 5.6 `reset_mask()` 与 `detach_state()`

```python
def reset_mask(
    self, state: ContinualTTTFastState, done: torch.Tensor
) -> ContinualTTTFastState:

def detach_state(
    self, state: ContinualTTTFastState
) -> ContinualTTTFastState:
```

`reset_mask()` 对 `done=[B]` 的 true rows 复制完整 learned W0，false rows 数值逐 bit保持；不
清零、不遗漏 bias、不 detach 未 reset row。`detach_state()` 对四个 member逐项 `.detach()`，
数值和 dtype/device/shape不变，不复制 W0。这是 TBPTT 边界唯一允许的 core 操作。

---

## 6. 梯度合同

### 6.1 Canonical training graph

对 `scan_segment(..., create_graph=True)` 的 valid token 构造任意 finite outer scalar并
`backward()` 后，以下 slow parameter 必须得到 finite gradient：

```text
key_proj.weight/bias
query_proj.weight/bias
value_proj.weight/bias
w0_fast_in_weight/bias
w0_fast_out_weight/bias
```

CPU deterministic fixture 中每一组（K、Q、V、W0）至少一个 gradient element 必须 nonzero。
K/V 只能经 differentiable inner update 到 outer loss，因而该测试直接证明
`create_graph=True` 没有被静默降为 first-order detached update。

### 6.2 Boundary semantics

```text
state_0 = initial_state(B)                 # connected to W0
tokens_0, state_1 = scan_segment(...)
outer_loss(tokens_0).backward()            # graph lifetime ends here
carry_1 = detach_state(state_1)            # values preserved, graph cut
tokens_1, state_2 = scan_segment(..., carry_1)
```

CPU core 只提供这些 primitives；后续 chronology/trainer Gate 必须保证 detach 发生在完整
segment/backward 边界。不得让 core 按 pack 位置猜测边界。

### 6.3 Numerical reference

CPU fp32 的 `step_projected()` 必须与显式逐 sample、逐 member
`torch.autograd.grad(..., create_graph=True)` reference 在 `atol=1e-6,rtol=1e-5` 内一致。
invalid 与 reset/detach 的值合同使用 `torch.equal`，不使用 tolerance。

---

## 7. CPU-only contract test matrix

相邻测试文件新增以下最小覆盖；所有新增测试函数名必须包含 `continual_ttt`，均标记
`@pytest.mark.L0`，固定 `torch.manual_seed()`，只用 CPU fp32、小维度 fixture：

| ID | 断言 |
| --- | --- |
| C01 | constructor 接受默认值与显式 `ttt_tbptt_steps={1,7,16}`；拒绝 bool/0/负数维度或 steps，以及 NaN/Inf/非正 `inner_lr`。 |
| C02 | `named_parameters()` 只有 Q/K/V 与四个 W0；`state_dict()` 无 `inner_lr`、steps、额外 buffer；元素数公式正确。 |
| C03 | `initial_state()` 四成员 shape/dtype/device正确，batch rows 数值同 W0且 storage 独立；初始 state 对 W0 保持 grad path。 |
| C04 | `step_projected()` 对单 sample 的 KVB loss、四 member gradient、SGD update与 post-update query read逐项匹配手写 reference，且不修改 `state_in`。 |
| C05 | batch size、相邻 sample 内容、valid mask变化不改变目标 sample 的 token/state；证明无 batch coupling。 |
| C06 | invalid row 的四成员 `torch.equal`、token exact zero、present false；valid neighbor 正常更新。 |
| C07 | `reset_mask()` 只把 done rows 的完整四成员复制为当前 learned W0，其他 rows `torch.equal`；partial/full reset均覆盖。 |
| C08 | `detach_state()` 四成员值逐 bit不变且无 `grad_fn`；绝不回到 W0。 |
| C09 | `scan_segment()` 与逐 timestep `step()` 的 tokens/present/final state等价。 |
| C10 | 两个 segment 之间 detach 后，第二段初始值等于第一段末值，并能从 detached carry 建立新 inner-grad graph；不同 `ttt_tbptt_steps` 不改变同一短序列数值。 |
| C11 | `T > ttt_tbptt_steps` fail-closed；`T=0`、shape/device/dtype错配与 nonfinite evidence/state/KQV 均在 update 前失败且不修改输入 state。 |
| C12 | valid outer loss 在 `create_graph=True` 下向 K/Q/V/W0 全部产生 finite gradient，且 K、Q、V、W0 每组至少一个 nonzero。 |
| C13 | `create_graph=False` 与 True 的单步 forward/state 数值在 fp32 tolerance内一致，但不把它冒充 training meta-gradient。 |
| C14 | `torch.no_grad()` 与 `torch.inference_mode()` 下直接调用 update 均 fail-before-mutation；在普通 grad mode 可执行。 |
| C15 | `project_evidence()` + `step_projected()` 与 `step()` 完全等价，证明 future inference 只有一套 update 数学。 |
| C16 | fast-state elements 与 bytes/sample 公式：默认 `12,448` elements，fp32 `49,792` bytes；future bf16 contract `24,896` bytes。 |

禁止测试：模型构造、LocalHistoryRuntime 接线、data/model/checkpoint读取、CUDA、GPU、server、
closed-loop、trainer、loss 或 optimizer。

---

## 8. 实现后的精确验证命令

实施者运行任何测试前必须按 `AGENTS.md` 向用户告知。获批后允许的命令仅为：

```bash
cd /disk/rl/psm_wma/cosmos-framework
python -m pytest -q cosmos_framework/model/generator/mot/local_evidence_test.py -k 'continual_ttt'

cd /disk/rl/psm_wma
python -m py_compile \
  cosmos-framework/cosmos_framework/model/generator/mot/local_evidence.py \
  cosmos-framework/cosmos_framework/model/generator/mot/local_evidence_test.py
git -C cosmos-framework diff --check
git diff --check
```

资源：CPU only、无外网、无模型/数据/checkpoint、无 CUDA/GPU。PASS 为所有定向测试通过、
py_compile 和双仓 diff-check 通过；任何失败均保持本 Gate IN_PROGRESS，不得绕过到 runtime。

---

## 9. 提交与后续 Gate

实现提交应保持两仓原子顺序：

1. 子模块只提交上述两个文件；
2. 根仓只 bump Gitlink，并更新 SESSION/TODO；
3. 对 exact root SHA + submodule SHA/Gitlink 重新申请三方 implementation review。

implementation closure 请求应为：

```text
APPROVE_TO_CLOSE_R09_B_TTT_V02_CPU_ALGORITHM_CORE
```

该 closure 即使通过，也只允许另起 chronology + native loss implementation design；不得直接
接 production runtime、GPU、推理或训练。

---

## 10. 本设计审核请求

请对本文所在 exact root SHA 与
`cosmos-framework@21d064f2b7c7aeeb67cfee50ac8d6722a944eddb` 返回：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_CPU_ALGORITHM_CORE
```

或带 severity 与 exact `file:line` 的 `REQUEST_CHANGES`。

批准范围仅为第 2 节的两个子模块文件、CPU-only tests、py_compile/diff-check 和必要的
Gitlink/SESSION/TODO 提交。仍禁止 chronology/loss/runtime integration、model config/recipe、
GPU/CUDA/torchrun、训练、评测、推理、optimizer/config refreeze、P4/P5真实操作与 B2-T。
