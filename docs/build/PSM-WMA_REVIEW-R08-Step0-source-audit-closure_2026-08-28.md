# R08 Step 0 source audit MEDIUM 项关闭复核

> 审查方：Kimi
> 被审文件：
> - `tools/g0/audit_r08_source.py`
> - `artifacts/g0/r08/source_audit.json`
> 当前提交：根 `d13f7b2`，子模块 `10bc410`（audit 文件未提交）
> 审查方式：只读，不执行代码/GPU
> 结论：**3 项 MEDIUM 已全部关闭；R08 Step 0 source audit 维持 APPROVE；可进入 Gate-0。**

---

## 1. 复核范围

复核上一轮审查 `docs/build/PSM-WMA_REVIEW-R08-Step0-source-audit_2026-08-28.md` 中提出的 3 项 MEDIUM 是否已最小修复：

1. `source_audit.json` 缺少 provenance。
2. `loader_does_not_currently_read_observation_state` 硬编码。
3. `state` 对齐字段断言弱。

同时复核新增要求：记录 `concat 256×512 -> pre-VAE canvas 192×320` 的来源证据。

---

## 2. 修复核验

| MEDIUM 项 | 修复位置 | 核验结果 |
|---|---|---|
| **MEDIUM-1 缺少 provenance** | `audit_r08_source.py:169-177` 新增 `provenance` 块 | ✅ 关闭 |
| | `source_audit.json:13-29` 包含 argv、root_commit、submodule_commit、dataset_root、cache_root、generated_at_utc、hostname | ✅ |
| **MEDIUM-2 loader state 读取状态硬编码** | `audit_r08_source.py:31-39` 新增 `_loader_parquet_columns()`，从 loader 源码静态提取 `pq.read_table(..., columns=...)` | ✅ 关闭 |
| | `audit_r08_source.py:148` 调用该函数 | ✅ |
| | `audit_r08_source.py:165` `loader_does_not_currently_read_observation_state = "observation.state" not in loader_columns` | ✅ |
| | `source_audit.json:4-11` 显示当前 loader 列不含 observation.state，且 `loader_does_not_currently_read_observation_state=true` | ✅ |
| **MEDIUM-3 state 对齐断言弱** | `audit_r08_source.py:77-79` 仍使用共同 stable index permutation，但新增说明 | ✅ 关闭 |
| | `audit_r08_source.py:84` 计算 `index_strictly_increasing` | ✅ |
| | `source_audit.json:141` 新增 `common_index_is_strictly_increasing: true` | ✅ |
| | `source_audit.json:163` `row_alignment_method` 明确说明共同排序方法 | ✅ |
| **新增 concat/VAE canvas 记录** | `audit_r08_source.py:131-135` 每个 suite 的 `exact_window_cache` 中新增 `current_concat_and_vae_canvas` | ✅ |
| | `source_audit.json:46-53` 记录 `concat_layout` 与 `pre_vae_model_canvas: [192, 320]`，evidence 指向 `cosmos-framework/docs/action_policy_libero_posttrain.md:50-53` | ✅ |

---

## 3. 新增 source_evidence 核验

- `current_concat_and_vae_canvas`: `cosmos-framework/docs/action_policy_libero_posttrain.md:50-53`
- 实际文档内容（:50-53）：
  > "`concat_view` (third-person + wrist, each 256×256 → 256×512), `quantile_rot` normalized. The pipeline snaps the 256×512 concat to a 192×320 model canvas"
- 来源准确，与 manifest 中 `latent_shape=[5,48,12,20]` 一致（192/16=12，320/16=20）。

---

## 4. 代码/产物质量检查

```bash
# 1. py_compile
/root/venvs/psm_wma/bin/python -m py_compile tools/g0/audit_r08_source.py
# PASS

# 2. JSON 可读
python3 -c "import json; json.load(open('artifacts/g0/r08/source_audit.json'))"
# PASS
```

`git diff --check` 对未跟踪文件不适用，但脚本内无 trailing whitespace / 混合换行等明显问题（肉眼复核）。

---

## 5. 剩余发现

- 上一轮 LOW 项中：
  - `loader_parquet_read` 行号已修正为 `:162-169`（`source_audit.json:38`、`audit_r08_source.py:155`）。✅
  - `target_h`/`target_w` 已通过 `pre_vae_model_canvas: [192, 320]` 记录。✅
  - 每 suite episode/frame/valid window 数仍未输出；仍列为 LOW，但不阻塞 Gate-0。

**无 MEDIUM/HIGH/BLOCKER 遗留。**

---

## 6. 结论

- ✅ MEDIUM-1/2/3 已关闭。
- ✅ concat/VAE canvas 合同已明确记录并有文档来源。
- ✅ `source_audit.json` 现在具备机器可读的 provenance。
- ✅ loader 字段读取状态由源码推导，不再硬编码。
- ✅ state 对齐方法说明 + 严格 index 递增断言已到位。

**R08 Step 0 source audit 正式通过，可进入 R08 Gate-0（z0 suffix-invariance diagnostic）。**
