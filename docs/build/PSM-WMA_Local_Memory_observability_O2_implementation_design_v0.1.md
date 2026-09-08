# PSM-WMA Local Memory Observability O2 实现设计 v0.1

**日期**：2026-09-08  
**状态**：docs-only；未授权实现、生产接线、真实 I/O、GPU 或训练  
**任务/Gate**：`G0-R09-B-TTT-OBSERVABILITY-O2-DESIGN`  
**上游**：`PSM-WMA_Local_Memory_observability_extension_design_v0.2.md`（O2 定义）与 v0.3（payload-free/terminal/non-mutation override）  
**已关闭前置**：O1 root=`93b4accd8d547416333c447c708129a23e55d8d9` / child=`611174b8d8a30976b11442efb833f69890e85a06`。

## 1. 目的、范围与准入

O2 只为 canonical Local Memory route 建立一个**纯 CPU/static、非注册、非生产**的 detached-scalar telemetry producer。它消费由 canonical route 已经拥有的 Local token、fast-state 和 scheduler/transaction metadata；不得为了统计触发第二次 encode、K/Q/V projection、update、read、Cosmos forward 或 collective。

本设计获三方同 SHA `APPROVE_TO_IMPLEMENT_R09_B_TTT_OBSERVABILITY_O2_CPU_STATIC` 后，才可实现下列 child 文件：

```text
cosmos_framework/callbacks/local_memory_telemetry.py          (new)
cosmos_framework/callbacks/local_memory_telemetry_test.py     (new)
```

不在白名单：`callbacks/__init__.py`、callback defaults/recipes、trainer、model、packer、runtime authority、scheduler、Local core、`local_memory2llm`、optimizer、checkpoint、W&B backend、dataset 与任何现有 O1 文件。故本 Gate 不会把 producer 注册到训练，也不会改变 disabled parity。

禁止真实 model/data/cache/checkpoint I/O、CUDA/GPU、torchrun、训练、评测、推理、P4/P5、B2-T、LIBERO4IN1。O3 trace sink、O4 validator、O5 recipe enablement 和任何 production telemetry 均仍须独立 Gate。

## 2. 已审计入口与关键决定

1. `NormMonitor` 已由 O1 提供 slow parameter/gradient norm，O2 不重算或重复这些指标。
2. `packers.py` 仅将 Local token 作为 out-of-band conditioning payload 交给 prefix packer；`omni_mot_model.py` 负责 sparse Local payload 对齐。这两处是 production 路径，均不在本 Gate 白名单。
3. 当前源码没有已冻结、可由 callback 无副作用读取的“consumer hidden” owner、层号或 pre/post-norm tap。为取得它而增加 hook 或暴露 tensor 会修改 model/packer/forward contract。

因此 `local/token_vs_consumer_hidden/l2_ratio` **不得在 O2 v0.1 发射**，且不得以 Local token、输入 payload、任意 prefix token 或任意 block activation 冒充 consumer hidden。该 metric 的取点、normalization、生命周期和额外 read 风险留待独立 `O2-HIDDEN-TAP-DESIGN` Gate；O2 v0.1 只记录其缺席，不记录 `NaN`/伪零。

## 3. 纯数据合同

实现唯一公开的纯 Python value object：

```python
@dataclass(frozen=True)
class LocalTelemetrySnapshot:
    local_tokens: Tensor | None
    fast_state: Tensor | None
    fast_update: Tensor | None
    consumer_valid_count: int
    local_present_count: int
    admitted_segments: int
    committed_segments: int
    pad_count: int
    transient_failures: int
    suffix_retries: int
    retry_exhausted: int
    scaler_skips: int
    slow_optimizer_steps: int
```

`LocalMemoryTelemetryProducer.record(snapshot)` 返回仅由 Python `float`/`int`/`bool` 组成的不可变 mapping；不保留任何 Tensor、Parameter、module、payload、identity 原文、RNG 或 mutable scheduler reference。

输入要求：

- `local_tokens` 只能是 canonical route 已产生的 `[N_present, K_local, D_local]` 或 `[N_present, D_local]` tensor；不接受 opaque consumer payload、visual、action、evidence 或 hidden state。
- `fast_state`/`fast_update` 只能是已经存在的 fast-state/readout 的 detached observation；传入者负责提供，producer 不从 runtime/model 取值。
- 所有计数为非负 Python `int`；`local_present_count <= consumer_valid_count`；`pad_count` 不得被计入 valid/local present。
- `local_tokens is None` 当且仅当 `local_present_count == 0`；反之首维必须等于 `local_present_count`。shape、dtype、非有限值或矛盾计数一律 `ValueError` fail-closed。

producer 在读取数值前执行 `detach()`；不得调用 `backward`、注册 hook、改变 `.grad`、调用 distributed API 或同步 device。CPU/static tests 仅使用 CPU tensors；本合同不声称 GPU/distributed correctness。

## 4. 指标与精确定义

每次 `record()` 返回下列 key；没有 Local token/fast observation 的 metric 不出现，而不是写零：

```text
local/token/l2_mean
local/token/l2_max
local/token/abs_max
local/token/present_fraction
local/fast/state_l2_mean
local/fast/state_l2_max
local/fast/update_l2_mean
local/fast/update_l2_max
local/fast/finite_fraction
local/exposure/admitted_segments
local/exposure/committed_segments
local/exposure/valid_consumers
local/exposure/pad_count
local/transaction/transient_failures
local/transaction/suffix_retries
local/transaction/retry_exhausted
local/transaction/scaler_skips
local/transaction/slow_optimizer_steps
```

令逐 token L2 为沿最后一维的 `sqrt(sum(float32(x)^2))`。`l2_mean`/`l2_max` 是全部 present token 的 mean/max；`abs_max=max(abs(float32(x)))`。`present_fraction=local_present_count/consumer_valid_count`；当 valid count 为零时为 `0.0`，但 token 必须 absent。`fast/finite_fraction` 只对存在的 fast observation 计算 `isfinite` 元素占比；任何非有限 Local token 或 fast observation 均 fail-closed，不发半真 scalar。

不发射：raw token、fingerprint/hash、identity、payload、consumer hidden ratio、per-rank summary、W&B event、JSON 文件或 stdout。累计/频率/flush 与 sink 属于 O3/O5，不是 O2 authority。

## 5. non-mutation 与因果边界

`record()` 只能读取传入 snapshot，且结果与下列状态逐位无关：模型参数/buffer、optimizer、scheduler、RNG、fast state、SegmentIdentity、GAWindowPlan、queue、admission、commit/retry/rebind decisions。它不得因为 S0/PAD/local absent 而尝试补读 evidence，也不得调用 superseded `materialize`/replay。

此约束的测试证据必须同时证明：输入 tensor 的值、requires_grad、`.grad`、版本计数保持；producer 不存 Tensor 引用；相同 snapshot 两次返回相同 scalar mapping；非法 snapshot 在任何 scalar 返回前失败。

## 6. CPU/static 验收矩阵

| 场景 | 必须断言 |
|---|---|
| present Local token | float32 L2/abs/max/present fraction 精确；无 Tensor 留存 |
| valid S0/local absent | token metric 缺席，present fraction=0，不读/不生成 token |
| PAD | 不计入 valid/local present，不能以 PAD 增加分子或分母 |
| `K_local>1` | 所有 present slot token 参与同一精确标量定义 |
| fast state/update | only-existing detached observation 的 norm/finite 定义正确 |
| no fast observation | fast key 缺席，不构造伪状态 |
| invalid finite/shape/count | 在输出前 `ValueError`，输入/grad/版本不变 |
| transaction/exposure | 计数逐 key 原样传递且全非负；`committed<=admitted` |
| mutation guard | Tensor、`.grad`、requires_grad、RNG 与外部 metadata 不变；无 distributed/W&B 调用 |
| hidden ratio | 输出中严格没有 `local/token_vs_consumer_hidden/l2_ratio` |

测试命令（仅在 implementation Gate 批准后执行）：

```bash
cd /disk/rl/psm_wma/cosmos-framework
LD_LIBRARY_PATH='' .venv/bin/python -m pytest \
  cosmos_framework/callbacks/local_memory_telemetry_test.py -q
```

CPU-only、无外网、无 checkpoint/data 输入；PASS 为所有上述 fixture 通过。随后仅对两白名单文件 `py_compile` 与 child/root `git diff --check`。任何 import 缺失、测试失败、非有限/shape/count 违约或意外文件变更均为 FAIL；不得改用真实训练掩盖。

## 7. 后续顺序

1. 本 docs-only O2 design 获三方同 SHA 批准；
2. 只实现本文件两白名单文件并作 CPU/static 验收；
3. 对 implementation 新 SHA 再次三方审核并关闭 O2；
4. 另起 O2-HIDDEN-TAP design，才可决定 `token_vs_consumer_hidden`；O3/O4/O5 分别独立设计、实现、审核。

任何顺序跳跃均不授权生产接线、GPU smoke 或 LIBERO4IN1 训练。
