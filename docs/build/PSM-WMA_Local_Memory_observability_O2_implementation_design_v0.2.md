# PSM-WMA Local Memory Observability O2 实现设计 v0.2

**日期**：2026-09-08  
**状态**：docs-only remediation；未授权实现、生产接线、真实 I/O、GPU 或训练  
**任务/Gate**：`G0-R09-B-TTT-OBSERVABILITY-O2-DESIGN`  
**取代**：仅取代 v0.1 的 snapshot schema、metric schema 与 fast-observation 语义；其余两文件 CPU/static 白名单、non-mutation 与禁止范围原样继承。  
**整改来源**：ChatGPT review `5b4361e` 对 formal root=`8f84f3f` / child=`611174b` 的两个 MEDIUM。

## 1. 不变范围

本设计仍只允许未来新增：

```text
cosmos_framework/callbacks/local_memory_telemetry.py
cosmos_framework/callbacks/local_memory_telemetry_test.py
```

不得改 `callbacks/__init__.py`、defaults/recipes、trainer、model、packer、runtime authority、scheduler、Local core、optimizer/checkpoint/dataset/W&B backend 或 O1 文件。无 registry、hook、collective、sink、真实 I/O、CUDA/GPU/torchrun、训练/评测/推理。producer 只消费调用方已拥有的 detached CPU observations，绝不重算 encode/project/read/write/update 或读取 payload/visual/action/consumer hidden。

`local/token_vs_consumer_hidden/l2_ratio` 继续严格不发射；其唯一 owner、层号、pre/post-norm、生命周期和无额外 read 证明属于独立 `O2-HIDDEN-TAP-DESIGN` Gate。

## 2. 唯一 snapshot ABI

未来的纯 CPU producer 只接收 frozen `LocalTelemetrySnapshot`；所有 `*_count`/transaction 字段均为非负 Python `int`，不接受 tensor、异常字符串或从 logger 推断的事件：

```python
@dataclass(frozen=True)
class LocalTelemetrySnapshot:
    local_tokens: Tensor | None                 # float32 CPU [N_present,D_local] or [N_present,K_local,D_local]
    fast_state: Tensor | None                   # float32 CPU [N_state,D_fast]
    fast_update: Tensor | None                  # float32 CPU [N_update,D_fast]
    consumer_valid_count: int
    local_present_count: int
    admitted_segments: int
    committed_segments: int
    pad_rows: int
    terminal_remainders: int
    initialized_fraction: float | None
    segment_progress_mean: float | None
    txn_backward_success: int
    txn_commit: int
    txn_transient_failure: int
    txn_suffix_retry_begin: int
    txn_scaler_skip: int
    txn_slow_optimizer_step: int
    txn_retry_exhausted: int
    txn_identity_failure: int
    txn_numerical_failure: int
    txn_outer_failure: int
```

`local_tokens is None` 当且仅当 `local_present_count==0`；否则首维必须等于该 count，允许的 `K_local` 每一行均是一个 token，故 `[N,K,D]` 的 token 总数是 `N*K`，但 `present_fraction=N/consumer_valid_count` 是**consumer** fraction，绝不以 slot 数作分母。`consumer_valid_count==0` 时 token 必须 absent 且 present fraction 为 `0.0`。`committed_segments<=admitted_segments`；`terminal_remainders<=admitted_segments`。

`initialized_fraction`/`segment_progress_mean` 是 scheduler/runtime 已计算的 detached Python scalar，不是 producer 从 state 推导；存在时必须为有限 `[0,1]` float。它们的现有生产 owner 尚未接入本 Gate，故 CPU fixture 只验证传递/边界，不声称 production observability 已实现。

## 3. fast observation 的唯一形状与归约

`fast_state` 与 `fast_update` 的唯一允许形式是 contiguous CPU `torch.float32` 二维 tensor `[N_rows,D_fast]`，其中 `N_rows>=1`、`D_fast>=1`。不接受 scalar、rank-1、rank-3+、空维、非 CPU、非 float32、DTensor 或非有限值；没有 observation 必须传 `None`，不能传空 tensor。producer 可先 `detach()`，但不得 dtype/device 转换、clone、同步或保留引用。

对任一允许 observation `x`，逐 row norm 唯一为：

```text
row_l2[i] = sqrt(sum_j float32(x[i,j]) ** 2)
l2_mean  = mean_i(row_l2[i])
l2_max   = max_i(row_l2[i])
```

`fast_state` 存在才发 `local/fast/state_l2_mean/max`；`fast_update` 存在才发 `local/fast/update_l2_mean/max`。两者至少一个存在时，`local/fast/finite_fraction` 按它们串接后的元素数计算；因非有限值 fail-closed，成功记录必为 `1.0`。两者都 absent 时所有 five 个 fast tensor-derived key 均缺席。`initialized_fraction` 与 `segment_progress_mean` 分别只在对应 optional scalar 存在时发射。

## 4. 精确 emitted/deferred schema

O2 v0.2 不得使用 v0.1 的 `local/transaction/*`、`pad_count` 或 `committed_segments` key。一次成功 `record()` 的 emitted key 是以下集合中满足 presence 条件的成员；无其它 key：

```text
local/token/l2_mean
local/token/l2_max
local/token/abs_max
local/token/present_fraction                    # always
local/fast/state_l2_mean, local/fast/state_l2_max               # fast_state present
local/fast/update_l2_mean, local/fast/update_l2_max             # fast_update present
local/fast/finite_fraction                                      # either fast tensor present
local/fast/initialized_fraction                                 # scalar present
local/fast/segment_progress_mean                                # scalar present
local/exposure/admitted_segments
local/exposure/valid_consumers
local/exposure/pad_rows
local/exposure/segments_committed
local/exposure/terminal_remainders
local/txn/backward_success
local/txn/commit
local/txn/transient_failure
local/txn/suffix_retry_begin
local/txn/scaler_skip
local/txn/slow_optimizer_step
local/txn/retry_exhausted
local/txn/identity_failure
local/txn/numerical_failure
local/txn/outer_failure
```

token L2 仍沿最后维；`[N,K,D]` 先视为 `N*K` 个 `[D]` row 后取 mean/max，`abs_max` 为所有 token 元素的 max abs。所有 numeric value 是 plain Python `float`/`int`；返回值必须是 `MappingProxyType(dict(...))`，不得包含 Tensor 或 mutable mapping。

下列 v0.2 inherited keys **明确延期而非删改**；O2 v0.2 必须断言它们 absent：

| 延期 key | 唯一权威/原因 | 后续 Gate |
|---|---|---|
| `local/token_vs_consumer_hidden/l2_ratio` | 尚无 approved side-effect-free consumer-hidden tap | `O2-HIDDEN-TAP-DESIGN` |
| `local/exposure/by_category/*`, `local/exposure/by_slot/*` | 只能来自 `RankLocalSegmentScheduler.snapshot()` 的 canonical stable-slot/category state；本 Gate 禁止读取 scheduler | `O2-SCHEDULER-SIDECAR-DESIGN` |
| `local/scheduler/target_exposure/*`, `actual_valid_exposure/*`, `deficit/*` | 只能由 scheduler authority 或与 `admit()` 同源的只读 helper 提供；observer 不得复制算法 | `O2-SCHEDULER-SIDECAR-DESIGN` |

该表是 v0.2 telemetry contract 对 O2 v0.2 的显式 supersession/defer；O3/O4/O5 亦不得提前重新命名这些 key。

## 5. CPU/static acceptance

除 v0.1 的 non-mutation、S0/PAD、payload opacity 与 no-extra-compute fixture 外，未来两个白名单文件必须新增：

1. 精确 emitted-key schema：full snapshot 的 key 集等于 §4；所有 deferred/旧 renamed key 均 absent。
2. `[N,D]` 和 `[N,K,D]` Local token 的精确 L2；multi-slot 的 norm 分母是 `N*K`，present fraction 分母仍为 valid consumer 数。
3. 各一个 `[N_state,D_fast]`/`[N_update,D_fast]` accepted fixture，逐 row L2 mean/max 与 combined finite fraction 精确；state-only、update-only、both-absent presence matrix。
4. rank、dtype、device、empty dimension、nonfinite 及 empty fast tensor 全部 `ValueError`，且在任何 mapping 返回前不变更输入、`.grad`、version、RNG 或 metadata。
5. initialized/progress optional scalar 的 present/absent、非有限/越界 fail-close；exposure 与全部 `local/txn/*` key 保留原 name 与精确计数。

实现 Gate 的测试仍只允许：

```bash
cd /disk/rl/psm_wma/cosmos-framework
LD_LIBRARY_PATH='' .venv/bin/python -m pytest cosmos_framework/callbacks/local_memory_telemetry_test.py -q
```

随后仅运行两白名单文件 `py_compile` 与 child/root `git diff --check`；未获 implementation Gate 不执行这些项目代码。

## 6. 审核与后续

本 v0.2 需三方对新 formal root/Gitlink 给出 `APPROVE_TO_IMPLEMENT_R09_B_TTT_OBSERVABILITY_O2_CPU_STATIC` 后才可创建两文件。新 implementation SHA 仍必须重新审核；任何 production、hidden tap、trace、validator、recipe、GPU smoke 或 LIBERO4IN1 训练均是之后独立 Gate。
