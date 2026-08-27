# R07 Gate C 采集准备独立审查报告

> 审查方：Kimi
> 被审提交：根 `ef6993b`，子模块 `v2 10bc410`
> 审查方式：只读代码 + CPU 测试复跑 + synthetic fixture 验证
> 结论：**APPROVE**

## 审查范围

1. `cosmos_framework/callbacks/r07_parity_capture.py` —— sidecar tensor 采集
2. `cosmos_framework/callbacks/r07_parity_capture_test.py` —— CPU 单元测试
3. `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py` —— 环境变量开关
4. `tools/g0/compare_r07_sensitivity.py` —— Normal/Zero/Shuffle 固定权重比较
5. `tools/g0/compare_r07_no_memory_parity.py` —— schema/field-presence fail-fast 修复
6. `artifacts/g0/r07/runtime_smoke/no_memory_parity.json` —— 更新后的 no-memory parity 产物

## 核验结果

| 检查项 | 命令/方法 | 结果 |
|---|---|---|
| py_compile（4 文件） | `/root/venvs/psm_wma/bin/python -m py_compile` | PASS |
| CPU 单元测试 | `pytest cosmos_framework/callbacks/r07_parity_capture_test.py -q` | **4 passed** |
| 根 diff-check | `git diff --check` | PASS |
| 子模块 diff-check | `git diff --check` | PASS |
| synthetic sensitivity compare | 自建 Normal/Zero/Shuffle fixture | **PASS** |
| no-memory schema fail-fast | 完整字段/缺字段/错 schema 三态验证 | 完整字段 PASS，缺字段 FAIL，错 schema FAIL |
| no-memory parity JSON | 读取 `artifacts/g0/r07/runtime_smoke/no_memory_parity.json` | `schema_pass=true`, `field_presence_pass=true`, `status=PASS` |

## 代码要点复核

### 1. sidecar tensor 采集（`r07_parity_capture.py:99-110`）

- 仅当 `tensor_output_path is not None` 时写 `.pt` sidecar，默认不触发，不影响训练。
- 保存 `preds_vision`、`preds_action`、`local_memory` 三个 list[torch.Tensor | None]，schema_version 为 `r07_sensitivity_tensors_v1`。
- 使用 `temporary_path.replace()` 原子写，与 JSON 路径一致。
- tensor 通过 `.detach().cpu()` 保存，无梯度泄漏风险。

### 2. 环境变量开关（`action_policy_libero_edge_all.py`）

- callback 注册仍以 `PSM_R07_PARITY_OUTPUT` 为前提；`PSM_R07_PARITY_TENSOR_OUTPUT` 仅控制是否追加 sidecar。
- 默认关闭，不改变正式训练行为。

### 3. `compare_r07_sensitivity.py`

- 强制校验三个 summary JSON 的 `schema_version == r07_no_memory_parity_v1` 和三个 tensor sidecar 的 `schema_version == r07_sensitivity_tensors_v1`。
- `INVARIANT_KEYS` 覆盖 input/packing/mRoPE 14 个字段，要求 Normal/Zero/Shuffle 完全一致。
- `difference()` 计算 L2、relative L2、max abs、changed items，并输出 SHA256。
- `sensitivity_pass` 要求 preds_vision / preds_action 在 Zero 和 Shuffle 下均变化（`l2_diff > 0`）。
- `payload_pass` 要求：
  - normal_vs_zero 的 local_memory L2 > 0（Zero 为严格全零）
  - normal local_memory 中至少 2 个非 None
  - normal_vs_shuffle 的 local_memory changed_items > 0（Shuffle 真正重排）

### 4. `compare_r07_no_memory_parity.py` 修复

- 增加 `EXPECTED_SCHEMA_VERSION = "r07_no_memory_parity_v1"`。
- 所有字段比较前检查 `key in old and key in new`。
- loss 字段缺失时 `loss_diffs` 记为 `None`，`losses_pass` 为 false。
- 最终 `status = PASS` 当且仅当 `schema_pass && field_presence_pass && losses_pass`。
- 原始 no-memory parity JSON 重跑后仍为 PASS。

## 发现

**LOW（观察项，不阻塞）**

- `compare_r07_sensitivity.py:121-124` 的 `payload_pass` 要求 `present_local_count >= 2`。该值取决于单个 packed batch 中 present local memory 的数量。若训练 batch 较小或 packing 后仅含 1 个 local memory slot，则即使 Zero/Shuffle 逻辑正确也会判 FAIL。建议 GPU 验证时检查 `shuffle_present_local_count` 字段；若实际为 1，需放宽为 `>= 1` 或明确本实验要求 packed batch 至少 2 个 local memory。

## 未执行验证

- GPU 真实训练 5 steps + 固定权重 3-mode 前向采集（按审查请求，本次只读/CPU）。
- R08/R09（项目范围外）。

## 结论

代码改动最小、开关显式、schema 校验 fail-fast、CPU 测试与 synthetic fixture 均通过。

**APPROVE**。下一步可由 Codex 在 GPU 上执行 Normal-only 5-step 训练 + 固定权重 Zero/Shuffle 采集，并验证 `compare_r07_sensitivity.py` 在真实数据上 PASS。
