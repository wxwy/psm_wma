# R07 Gate C 运行结果独立审查报告

> 审查方：Kimi  
> 被审产物：根 `fa5c16a` → `916b309`，子模块 `10bc410`  
> 被审 artifact：`artifacts/g0/r07/runtime_smoke/sensitivity.json`  
> 审查方式：只读（不执行训练/推理，不重跑 compare）  
> 结论：**APPROVE（带 MEDIUM 观察项，需在 Gate C 正式关闭前补齐）**

---

## 1. 审查范围

1. `artifacts/g0/r07/runtime_smoke/sensitivity.json` 的字段、schema、数值判据。
2. sidecar tensor schema（`r07_sensitivity_tensors_v1`）与 JSON summary schema（`r07_no_memory_parity_v1`）是否对齐 `compare_r07_sensitivity.py` 的校验。
3. 命令语义：是否同一 CKPT_5 独立重载 Normal/Zero/Shuffle，而非三模式分别训练。
4. 与 Gate C 合同的对照：
   - `docs/build/PSM-WMA_G0_runtime_execution_plan_v0.6_aligned.md` §7 R07 检查清单；
   - `MEMORY/DECISIONS.md` D015 R07 范围；
   - `SESSION.md:35-38` 描述的固定权重 sensitivity 流程。

---

## 2. 核验结果

| 检查项 | 证据 | 结果 |
|---|---|---|
| 当前 HEAD | 根 `916b309`，子模块 `10bc410` | PASS（与提交声明一致） |
| 代码自 prep 以来无变更 | `git diff fa5c16a..916b309 --name-only` 仅 `SESSION.md`、`TODO.md`、`sensitivity.json` | PASS |
| `compare_r07_sensitivity.py` 语法 | `/root/venvs/psm_wma/bin/python -m py_compile` | PASS |
| `r07_parity_capture.py` 语法 | 同上 | PASS |
| JSON schema 校验 | `schema_pass=true`, `tensor_schema_pass=true` | PASS |
| 14 项输入/结构不变量 | `invariant_exact` 14/14 全 `true` | PASS |
| Local payload 存在性 | `shuffle_present_local_count=128` | PASS（>2，prep 阶段的 LOW 观察已解决） |
| Zero 干预有效性 | `normal_vs_zero.local_memory.l2_diff=54.17`, `relative_l2_diff=1.0` | PASS（Normal 与全零 Local 可区分） |
| Shuffle 干预有效性 | `normal_vs_shuffle.local_memory.changed_items=128`, `relative_l2_diff=0.0016` | PASS（Local 内容重排影响输出） |
| Vision/Action sensitivity | N-v-Z vision `1.097%`、action `0.495%`；N-v-S vision `0.970%`、action `0.396%` | PASS（`l2_diff > 0`） |
| 状态机 | `payload_pass=true`, `sensitivity_pass=true`, `status=PASS` | PASS |

---

## 3. 代码与 artifact 行为复核

### 3.1 比较器逻辑（`tools/g0/compare_r07_sensitivity.py`）

- `INVARIANT_KEYS`（:14-29）覆盖 vision/action 的 `x0/xt/sigma`、text、indexes、split_lens、attn_modes、position_ids，与 `r07_parity_capture.py` 输出字段一一对应。
- :99-100 强制 `r07_no_memory_parity_v1` 与 `r07_sensitivity_tensors_v1` schema；缺 schema 会 fail-fast。
- :101-107 使用 Python `==` 对三个 summary dict 做精确比较；`iteration`、`loss` 等未纳入比较，符合“固定权重、同 batch”的假设。
- :117-127 的 `payload_pass` 已验证 `present_local_count >= 2`；实际为 128，prep 阶段的 LOW 观察项已消失。
- :128-141 的状态公式完整：所有不变量 exact + schema pass + payload pass + sensitivity pass 才输出 `PASS`。

### 3.2 sidecar 采集（`cosmos-framework/cosmos_framework/callbacks/r07_parity_capture.py`）

- :66-94 summary JSON schema 为 `r07_no_memory_parity_v1`；与 `compare_r07_sensitivity.py:99` 预期一致。
- :99-110 tensor sidecar schema 为 `r07_sensitivity_tensors_v1`；保存 `preds_vision`、`preds_action`、`local_memory`，均 `detach().cpu()`，无梯度泄漏。
- :96-98、:108-110 使用 `.tmp` 原子 rename，写入安全。

### 3.3 与 Gate C 合同的对照

- 合同要求：`Normal/Zero/Shuffle content 不改变 shape/index contract`（`Runtime Plan:289`）。
  - `invariant_exact` 14/14 证明 shape/index/text/position/mRoPE 完全一致，符合。
- 合同要求：`has_*=false` 与 `has_*=true+zero content` 可区分（`Runtime Plan:290`）。
  - `normal_vs_zero.local_memory.relative_l2_diff=1.0` 证明 Local 存在但为零时，输出与 Normal 不同，符合。
- 合同要求：未来 world 与 action output 记录 sensitivity（`Runtime Plan:384`、`Runtime Plan:529`）。
  - `preds_vision` 与 `preds_action` 在 Zero/Shuffle 下均有非零 L2，符合。
- D015 明确 R07 仅验证 optional-modality contract，不进入 R08/R09；本次实现范围吻合。

---

## 4. 发现

### BLOCKER

无。

### HIGH

无。

### MEDIUM

1. **原始 sidecar（Normal/Zero/Shuffle 的 `.json` summary 与 `.pt` tensor）未保留在 artifact 目录，独立复现受限。**
   - 证据：`find artifacts/g0/r07/runtime_smoke -type f` 仅列出 `no_memory_parity.json`、`sensitivity.json`、log 文件，没有 `*_normal.json/*.pt` 等输入文件。
   - 依据：`AGENTS.md` 要求 R Gate 产物需机器可读且可复核；`compare_r07_sensitivity.py:89-95` 需要这些文件作为输入。
   - 影响：无法在本机独立重跑 `compare_r07_sensitivity.py` 验证 `sensitivity.json` 的生成过程；也无法在后续审计时重新提取其他统计量。
   - 建议的最小修复：
     - 方案 A：将三模式 sidecar 作为本次 Gate 证据保留（可压缩后存于 `artifacts/g0/r07/runtime_smoke/sensitivity_inputs/`）；
     - 方案 B：在 `sensitivity.json` 中增加 `input_sidecars` 字段，记录三个 `.pt` 与 `.json` 的相对路径 + SHA256，确保至少可追溯。
   - 是否阻止 REVIEW-R07 通过：**否**，但应在 Gate C 正式关闭前补齐。

2. **`sensitivity.json` 缺少 provenance 字段，机器可读性与可重复性不足。**
   - 证据：`artifacts/g0/r07/runtime_smoke/sensitivity.json:1-79` 仅有结果与指标，无命令、环境、git commit、checkpoint 路径、时间戳、数据集/cache 路径、GPU 信息。
   - 依据：`AGENTS.md` 要求产物包含精确命令、输入输出、provenance；`SESSION.md:35-38` 描述的流程信息未沉淀到 artifact。
   - 建议的最小修复：在 compare 脚本或 runner 中写入 `provenance` 块，至少包含：
     ```json
     "provenance": {
       "root_commit": "916b309",
       "child_commit": "10bc410",
       "checkpoint_path": ".../iter_000000005",
       "command": "python tools/g0/compare_r07_sensitivity.py ...",
       "env": {"PSM_LOCAL_DUMMY_MODE": "...", "PYTHONHASHSEED": "0", "CUBLAS_WORKSPACE_CONFIG": ":4096:8"},
       "dataset": "LIBERO-4in1 exact-window cache",
       "timestamp": "2026-08-27T..."
     }
     ```
   - 是否阻止 REVIEW-R07 通过：**否**，但应作为 Gate C DONE 前的最后一项回填。

3. **sensitivity 的相对 L2 很小（vision ~1%、action ~0.5%），判据仅检查 `l2_diff > 0.0` 可能过于宽松。**
   - 证据：`compare_r07_sensitivity.py:118-122` 使用 `> 0.0`；实际 `normal_vs_zero` vision `0.010973`、action `0.004952`。
   - 判断：数值确实非零，且 `changed_items=128/108` 证明影响覆盖大量样本；但相对幅度说明当前 dummy Local 对输出的因果贡献较弱，符合“dummy 而非真实 Memory”的预期。
   - 建议的最小修复：Runbook 中明确 R07 Gate C 的接受阈值（例如 `relative_l2_diff > 0` 且 `changed_items > 0`），避免未来把接近零的数值噪声误判为 sensitivity。
   - 是否阻止 REVIEW-R07 通过：**否**。

### LOW

1. **`r07_parity_capture.py:105` 未校验 `data_batch["local_memory"]` 的类型。**
   - 若某路径返回单个 tensor 而非 list，sidecar 会保存 tensor，导致 `compare_r07_sensitivity.py:117` 的 `sum(tensor is not None for tensor in ...)` 语义改变。
   - 当前 `present_local_count=128` 证明实际为 list，但建议加 `assert isinstance(local_memory, list)` 或统一 collate 返回类型，增强防御性。

2. **`compare_r07_sensitivity.py:89-95` 的 argparse 未在 `sensitivity.json` 中记录实际使用的输入路径。**
   - 属于 provenance 的一部分；可在 runner 层把 `--normal-json` 等路径写回 JSON，便于审计。

---

## 5. 已核验的源码锚点

- `tools/g0/compare_r07_sensitivity.py:14-29` — INVARIANT_KEYS
- `tools/g0/compare_r07_sensitivity.py:89-148` — 比较器主逻辑
- `cosmos-framework/cosmos_framework/callbacks/r07_parity_capture.py:55-110` — 采集 schema 与 sidecar
- `cosmos-framework/cosmos_framework/callbacks/r07_parity_capture_test.py` — CPU 单元测试（prep 已审，本次未重跑）
- `artifacts/g0/r07/runtime_smoke/sensitivity.json:1-79` — Gate C 结果
- `docs/build/PSM-WMA_G0_runtime_execution_plan_v0.6_aligned.md:253-296` — R07 检查清单
- `MEMORY/DECISIONS.md:143-155` — D015 R07 范围
- `SESSION.md:35-38` — 固定权重 sensitivity 命令语义

---

## 6. 已执行的只读命令及关键结果

```bash
# 1. 检查 artifact 目录结构
find /gemini/code/psm_wma/artifacts/g0/r07/runtime_smoke -type f
# 结果：仅 no_memory_parity.json、sensitivity.json、若干 log；无三模式 sidecar 文件

# 2. 确认自 prep 审查以来代码无变更
git -C /gemini/code/psm_wma diff fa5c16a..916b309 --name-only
# 结果：SESSION.md、TODO.md、artifacts/g0/r07/runtime_smoke/sensitivity.json

# 3. 确认 HEAD
git -C /gemini/code/psm_wma rev-parse HEAD        # 916b309c6c6196b24a425fa885ac0c07e330bf8b
git -C /gemini/code/psm_wma/cosmos-framework rev-parse HEAD  # 10bc41085de448d60d2f71b342c03a4cfcca9ee1

# 4. 语法检查（不加载 checkpoint）
/root/venvs/psm_wma/bin/python -m py_compile \
  tools/g0/compare_r07_sensitivity.py \
  cosmos-framework/cosmos_framework/callbacks/r07_parity_capture.py \
  cosmos-framework/cosmos_framework/callbacks/r07_parity_capture_test.py
# 结果：PASS
```

---

## 7. 未执行的验证及原因

| 未执行项 | 原因 |
|---|---|
| 重跑 `compare_r07_sensitivity.py` | 三模式 `.json`/`.pt` sidecar 未保留在 artifact 目录，无法重跑。 |
| 从 GPU log 中提取完整命令与环境变量 | log 文件中未出现 `PSM_R07_PARITY_TENSOR_OUTPUT`/`PSM_LOCAL_DUMMY_MODE` 等关键字；且本次为只读审查，不重新采集。 |
| 校验 CKPT_5 权重在三次重载中未被修改 | 临时 checkpoint 已删除；依赖 `SESSION.md:35-38` 的流程说明与 `invariant_exact` 间接证明。 |
| 对 `preds_vision`/`preds_action` 做额外 shape/范围检查 | sidecar `.pt` 已删除；JSON summary 中的 shape/dtype/max 正常。 |

---

## 8. 是否满足验收条件

**核心验收条件已满足：**

- schema 校验通过；
- 14 项输入/结构不变量在 Normal/Zero/Shuffle 间完全一致；
- Local payload 存在且 Zero/Shuffle 均产生非零输出变化；
- Vision 与 Action 预测对 Local 干预均有 sensitivity；
- 状态机输出 `PASS`。

因此，**REVIEW-R07 Gate C runtime 通过，结论为 APPROVE**。

**但在将 `G0-R07-RUNTIME-SMOKE` 标记为 DONE 前，建议关闭以下两项：**

1. 保留或记录三模式 sidecar 的 SHA256/路径（MEDIUM-1）。
2. 在 `sensitivity.json`（或 companion `.provenance.json`）中回填 git commit、checkpoint 路径、命令、关键环境变量与时间戳（MEDIUM-2）。

---

## 9. 若需 REQUEST_CHANGES 的修复清单（本报告为 APPROVE）

- [ ] MEDIUM-1：补充 sidecar 保留或 SHA256 记录。
- [ ] MEDIUM-2：补充 `provenance` 字段。
- [ ] MEDIUM-3：在 Runbook/合同中明确 relative L2 接受阈值。
- [ ] LOW-1：在 `r07_parity_capture.py` 加 `local_memory` 类型断言。
- [ ] LOW-2：在 `sensitivity.json` 记录 compare 输入路径。
