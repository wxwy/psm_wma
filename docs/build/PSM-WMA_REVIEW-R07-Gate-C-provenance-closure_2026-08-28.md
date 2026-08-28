# R07 Gate C provenance closure 复审报告

> 审查方：Kimi  
> 被审提交：根 `db1d9b8`，子模块 `10bc410`  
> 新增产物：`artifacts/g0/r07/runtime_smoke/sensitivity_provenance.json`  
> 审查方式：只读（未重跑 GPU、未修改 Local 代码）  
> 结论：**APPROVE；Gate C / R07 runtime 可标记为 DONE**

---

## 1. 审查范围

1. `artifacts/g0/r07/runtime_smoke/sensitivity_provenance.json` 的字段完整性、与 `sensitivity.json` 的一致性、对 raw sidecar 缺失的披露。
2. `SESSION.md` / `TODO.md` 更新是否准确反映当前状态。
3. 在 raw sidecar 已删除的诚实 evidence limitation 下，Gate C 产物是否仍足以支持 DONE 判定。
4. 未进入 R08/R09 的范围约束是否保持。

---

## 2. 核验结果

| 检查项 | 证据 | 结果 |
|---|---|---|
| 当前 HEAD | 根 `db1d9b8`，子模块 `10bc410` | PASS |
| 本次变更范围 | `git diff 916b309..db1d9b8 --name-only` 仅 `SESSION.md`、`TODO.md`、`sensitivity_provenance.json` | PASS（无代码/Local 变更） |
| provenance JSON 可读 | `json.load` 通过 | PASS |
| schema 声明 | `sensitivity_provenance.json:2` 为 `r07_fixed_weight_sensitivity_provenance_v1` | PASS |
| 与 `sensitivity.json` 一致 | `result_status=PASS`，relative L2 数值与 `sensitivity.json:41,49,67,75` 一致 | PASS |
| 训练后 checkpoint 保留 | `sensitivity_provenance.json:9-15` 声明路径 `artifacts/g0/r07/runtime_smoke/sensitivity_ckpt5/iter_000000005`，`deleted_after_gate=false` | PASS（目录存在，约 17GB） |
| raw sidecar 缺失披露 | `sensitivity_provenance.json:50-61` 明确 `retained=false`、原路径、缺失原因、comparator-derived SHA 仍存于 `sensitivity.json` | PASS（诚实披露） |
| 固定权重语义 | `cosmos_framework/trainer/__init__.py:483` 返回 `output_batch` 在 optimizer step（:505）之前；`on_training_step_end`（:423）接收的是前向输出 | PASS（捕获时权重未变） |
| 范围约束 | `MEMORY/DECISIONS.md:143-155` D015 仍禁止 R08/R09；provenance 未越界 | PASS |

---

## 3. 关键判断：诚实 evidence limitation 是否可接受

**结论：可接受，Gate C 可 DONE。**

理由：

1. Gate C 的核心判据已经在 `sensitivity.json` 中机器可读地记录并 PASS：
   - 14/14 非 Local 不变量 exact；
   - Local payload 在 Zero/Shuffle 下变化；
   - Future vision / action 输出对 Local 干预有非零 sensitivity。
2. raw sidecar 的缺失是因为先前临时清理，**无法恢复**；provenance 没有隐瞒，而是明确记录原路径、缺失原因和替代证据（`sensitivity.json` 中的 comparator-derived SHA256）。
3. 训练后的 checkpoint `sensitivity_ckpt5/iter_000000005` 仍保留在 artifact 目录，提供了重新运行 sensitivity 的物质基础。
4. `compare_r07_sensitivity.py:41-55` 的 SHA256 计算基于 tensor 原始字节，与 raw sidecar 文件级 SHA256 在逻辑上等价；只要重新加载同一 checkpoint 和同一份 sidecar，可复现相同 SHA。
5. 本次 closure 未引入新代码、未修改 Local 实现、未重跑 GPU，没有改变 Gate C 结果本身。

因此，缺失 raw sidecar 属于**已记录且可接受的 evidence limitation**，不构成对 DONE 的阻塞。

---

## 4. 发现

### BLOCKER

无。

### HIGH

无。

### MEDIUM

无。

### LOW

1. **`sensitivity_provenance.json:21` `capture_optimizer_updates: 1` 与 `:12` `fixed_weight_for_captures: true` 同时出现，可能误导。**
   - 证据：`cosmos_framework/trainer/__init__.py:423` 的 `on_training_step_end` 在 optimizer step 之后调用，但传入的 `output_batch` 来自 `:483` 的前向输出，因此实际捕获的 tensor 是在权重更新**之前**的固定权重结果。
   - 建议：在 provenance 中增加一句说明，例如 `"captured_tensors_are_pre_optimizer_update": true`，避免未来审计误解为“捕获时权重已变”。
   - 不阻塞 DONE。

2. **provenance 缺少精确启动命令 / runner 脚本路径。**
   - 证据：`sensitivity_provenance.json:1-72` 包含数据、环境、资源、合同字段，但没有 torchrun 命令或 runner 脚本路径。
   - 依据：`AGENTS.md` 要求产物记录“精确命令”。
   - 建议：增加 `"command"` 或 `"runner_script"` 字段，例如 `python tools/g0/run_r07_sensitivity.py ...` 的完整命令行。
   - 不阻塞 DONE。

3. **保留的 trained checkpoint 未记录完整性校验。**
   - 证据：`sensitivity_provenance.json:9-15` 仅记录路径，无 SHA256 或文件大小。
   - 建议：增加 checkpoint model/optim 状态的 SHA256（或至少总大小），以便 future rerun 时验证 checkpoint 未被污染。
   - 不阻塞 DONE。

4. **raw sidecar 删除应作为 future gate 的教训。**
   - 证据：`sensitivity_provenance.json:60` 已说明清理导致缺失。
   - 建议：后续 R08/R09 Gate 在最终 review 完成前保留 raw sidecar 或至少文件级 SHA，避免再次陷入无法独立重跑 compare 的境地。
   - 不阻塞 DONE。

---

## 5. 已核验的源码锚点

- `artifacts/g0/r07/runtime_smoke/sensitivity_provenance.json:1-72` — provenance 本体
- `artifacts/g0/r07/runtime_smoke/sensitivity.json:1-79` — Gate C 结果
- `tools/g0/compare_r07_sensitivity.py:41-55` — tensor SHA256 计算逻辑
- `cosmos-framework/cosmos_framework/trainer/__init__.py:450-510` — `training_step` 中 output_batch 与 optimizer step 的时序
- `cosmos-framework/cosmos_framework/trainer/__init__.py:401-423` — `on_training_step_end` 调用位置
- `cosmos-framework/cosmos_framework/callbacks/r07_parity_capture.py:55-110` — sidecar 采集代码
- `MEMORY/DECISIONS.md:143-155` — D015 R07 范围与 R08/R09 禁令
- `SESSION.md:37-39`（新行）— 本次 closure 状态更新
- `TODO.md:51` — `G0-R07-RUNTIME-SMOKE` 仍为 REVIEW，待本次审查后转 DONE

---

## 6. 已执行的只读命令及关键结果

```bash
# 1. 检查本次变更范围
git -C /gemini/code/psm_wma diff 916b309..db1d9b8 --name-only
# 结果：SESSION.md、TODO.md、artifacts/g0/r07/runtime_smoke/sensitivity_provenance.json

# 2. 读取并校验 provenance JSON
python3 -c "import json; json.load(open('artifacts/g0/r07/runtime_smoke/sensitivity_provenance.json'))"
# 结果：PASS

# 3. 核对 checkpoint 目录仍存在
ls -d /gemini/code/psm_wma/artifacts/g0/r07/runtime_smoke/sensitivity_ckpt5/iter_000000005
# 结果：存在（model/optim/scheduler/trainer）

# 4. 验证 trainer 回调时序（源码只读）
# cosmos_framework/trainer/__init__.py:483 返回 output_batch
# cosmos_framework/trainer/__init__.py:505 执行 optimizer step
# cosmos_framework/trainer/__init__.py:423 调用 on_training_step_end
# => 捕获 tensor 为前向输出，权重尚未更新
```

---

## 7. 未执行的验证及原因

| 未执行项 | 原因 |
|---|---|
| 重新生成 raw N/Z/S sidecar | 原文件已在临时清理中删除；当前保留的 trained checkpoint 可支持重跑，但会消耗 GPU 与存储，本次为 closure 复审，无需重跑。 |
| 校验 trained checkpoint SHA256 | provenance 未提供；建议后续补齐，但不影响本次 DONE 判定。 |
| 检查 `/opt/Cosmos3-edge-generation-libero4in1/iter_000002800` 是否存在 | 路径在系统盘 `/opt/`，本次只读审查不涉及外部存储探查；provenance 已声明其为基线。 |

---

## 8. 结论与下一步

- **R07 Gate C runtime 通过；可标记 `G0-R07-RUNTIME-SMOKE` 为 DONE。**
- 本次 provenance closure 诚实披露了 raw sidecar 缺失，并以 retained trained checkpoint + comparator-derived SHA 保留了足够的复核证据。
- 不存在 BLOCKER/HIGH/MEDIUM；仅有 4 条 LOW 建议，可在后续 gate 或文档小修中顺手补齐。
- **R08/R09 仍不得启动**，直到用户/项目流程明确授权。

建议 Codex 在获得本审查结论后：
1. 将 `TODO.md:51` 的 `G0-R07-RUNTIME-SMOKE` 状态从 `REVIEW` 更新为 `DONE`。
2. 可选：在 `sensitivity_provenance.json` 中补充 LOW-1/2/3 的三项字段，然后做一次只追加 provenance 的小提交。
