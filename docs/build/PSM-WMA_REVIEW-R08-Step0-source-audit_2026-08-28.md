# R08 Step 0 source audit 独立复核报告

> 审查方：Kimi
> 被审文件：
> - `tools/g0/audit_r08_source.py`
> - `artifacts/g0/r08/source_audit.json`
> - 对照源码 `cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py`
> 当前提交：根 `d13f7b2`，子模块 `10bc410`（audit 文件未提交）
> 审查方式：只读，不执行代码/GPU
> 结论：**APPROVE（带 MEDIUM 观察项；需在 R08 Gate-0 前补齐 provenance 与两项断言）**

---

## 1. 审查范围

1. `audit_r08_source.py` 是否正确读取四 suite parquet 的当前字段、observation.state、action、timestamp、index、episode_index、task_index。
2. observation.state schema/finite/alignment 是否被正确审计，且未推断物理语义。
3. action `j < t` 边界是否被记录，且与 loader 源码一致。
4. exact-window cache 的 17 帧窗口、`[5,48,H,W]` latent、`window_frame_indices`、`latent_source_frame_indices` 是否与源码一致。
5. source_evidence 中的源码行号是否准确。
6. 产物是否具备机器可读的 provenance。

---

## 2. 核验结果

| 检查项 | 证据 | 结果 |
|---|---|---|
| 当前未提交文件 | `git status --short` 显示 `?? tools/g0/audit_r08_source.py`、`?? artifacts/g0/r08/` | PASS |
| 脚本语法 | `py_compile` 通过（仅 import 检查，未运行） | PASS |
| schema_version | `source_audit.json:13` = `r08_source_audit_v1` | PASS |
| status | `source_audit.json:14` = `PASS` | PASS |
| 四 suite 覆盖 | `audit_r08_source.py:15` SUITES；`source_audit.json:25-553` 含 libero_spatial/object/goal/10 | PASS |
| loader 当前字段 | `source_audit.json:4-10` 列出 index/episode_index/task_index/timestamp/action；`audit_r08_source.py:130` 声明 loader 不读取 observation.state | PASS（与 `libero_lerobot_dataset.py:164` 读取列一致） |
| observation.state schema | 四 suite 均为 `float32`、shape `[8]`、`info_features_state` 一致 | PASS |
| observation.state finite | 四 suite `state.finite = true` | PASS |
| observation.state 语义未推断 | `source_audit.json:138` semantic_status 明确因 duplicate gripper 不做物理映射 | PASS |
| action 边界 | `source_audit.json:147`、`audit_r08_source.py:90` 明确 anchor t 只取 j<t | PASS（与 `libero_lerobot_dataset.py:415` 的 `raw = _row_action[start:start+chunk_length]` 一致） |
| exact-window 17 帧 | `source_audit.json:50-68` sample_window_frame_indices = 0..16 | PASS |
| latent_source_frame_indices | `source_audit.json:43-49` = 0,4,8,12,16 | PASS |
| latent shape | 四 suite 均为 `[5,48,12,20]`，dtype float32 | PASS（与 manifest `latent_shape` 一致） |
| cache manifest schema | `source_audit.json:69-83` = `exact_window_v1`；vae_encode_contract 与 `vision_vae.py:12-13` 一致 | PASS |

---

## 3. 源码行号核对

| source_evidence 条目 | audit 中声明 | 实际当前文件位置 | 偏差 |
|---|---|---|---|
| loader_parquet_read | `libero_lerobot_dataset.py:159-176` | `:162-169` | 行号范围略宽，内容正确 |
| cache_manifest_validation | `:280-329` | `:280-329` | 精确 |
| cache_window_validation | `:331-377` | `:331-377` | 精确 |
| sample_target_action_and_extras | `:393-436` | `:393-436` | 精确 |
| action_conversion | `:438-446` | `:438-446` | 精确 |
| concat_view | `:448-465` | `:448-465` | 精确 |
| vae_exact_duration_constants | `vision_vae.py:12-13` | `:12-13` | 精确 |

---

## 4. 发现

### BLOCKER

无。

### HIGH

无。

### MEDIUM

1. **`source_audit.json` 缺少 provenance 字段。**
   - 证据：`source_audit.json:1-555` 无 git commit、运行命令、时间戳、执行者、`dataset_root`、`cache_root`、hostname 等；`audit_r08_source.py:110-138` 的 `main()` 未写入 `provenance` 块。
   - 依据：`AGENTS.md` 要求 R Gate 产物机器可读且可追溯；R08 supplement `§18` 也将 "machine-readable provenance retained" 列为 DONE 条件。
   - 建议的最小修复：在 `audit_r08_source.py:117-135` 的 report dict 中增加：
     ```python
     "provenance": {
         "root_commit": "...",
         "submodule_commit": "...",
         "dataset_root": str(args.dataset_root),
         "cache_root": str(args.cache_root),
         "command": "python tools/g0/audit_r08_source.py --dataset-root ... --cache-root ... --output ...",
         "timestamp": datetime.now().isoformat(),
     }
     ```
   - 是否阻止 Step 0 结论：**否**；是否必须在 Gate-0 前补齐：**是**。

2. **`loader_does_not_currently_read_observation_state` 是硬编码布尔值，未由源码实际推导。**
   - 证据：`audit_r08_source.py:131` 直接写死 `True`。
   - 影响：当前确实正确（`libero_lerobot_dataset.py:164` 未读 observation.state），但若未来有人修改 loader 加入 state，audit 不会自动发现。
   - 建议：在 `audit_r08_source.py:27-107` 的 suite audit 中，或新增一个独立检查，反射/读取 `libero_lerobot_dataset.py` 的 parquet columns 并断言 `"observation.state" not in loader_parquet_columns`。
   - 是否阻止 Step 0：**否**；建议 Gate-0 前关闭。

3. **`state.row_aligned_with_index_episode_timestamp` 的判定等价于 `row_count_matches_parquet_rows`，未额外验证按 index 排序后的逐行对齐。**
   - 证据：`audit_r08_source.py:77` 直接赋值为 `state_rows_match_parquet_rows`。
   - 判断：由于所有列共用同一 `order = np.argsort(index)` 排序，对齐在逻辑上成立；但字段名暗示了更强的断言。
   - 建议：要么重命名为 `row_count_aligned_and_sorted_by_common_index`，要么增加一次轻量检查（例如抽查若干行 `state[i]` 与 `timestamp[i]` 是否来自同一 parquet row index）。
   - 是否阻止 Step 0：**否**。

### LOW

1. **`source_evidence.loader_parquet_read` 行号范围 `:159-176` 略宽于实际 `:162-169`。**
   - 建议改为 `:162-169` 或说明包含 surrounding comments。

2. **Audit 产物未记录 cache manifest 中的 `target_h`/`target_w`。**
   - 证据：manifest 实际含 `target_h=192`、`target_w=320`，latent shape 为 `[5,48,12,20]`。`source_audit.json` 只记录 `latent_shape`。
   - 建议：在 `exact_window_cache` 块中增加 `target_h`、`target_w`，便于 Gate-0 设计时知道实际 VAE 输入分辨率。

3. **Audit 未输出每 suite 的 episode 数、frame 数、valid window 数。**
   - 这些对 R08 history horizon 设计有用，但不是 Step 0 必需；可在后续 source_audit v2 中补充。

---

## 5. 已核验的源码锚点

- `tools/g0/audit_r08_source.py:15` — SUITES 列表
- `tools/g0/audit_r08_source.py:27-107` — `_audit_suite` 核心逻辑
- `tools/g0/audit_r08_source.py:110-138` — `main()` 与 report schema
- `tools/g0/audit_r08_source.py:130-131` — loader 字段声明
- `artifacts/g0/r08/source_audit.json:1-555` — 产物本体
- `cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:162-169` — loader parquet read
- `cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:280-329` — cache manifest validation
- `cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:331-377` — cache window validation
- `cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:393-436` — `_build_item` sample builder
- `cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:438-446` — `_build_frame_wise_action`
- `cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:448-465` — `_load_video` concat_view
- `cosmos_framework/model/generator/vision_vae.py:12-13` — exact duration constants

---

## 6. 已执行的只读命令

```bash
# 1. 检查未提交状态
git -C /gemini/code/psm_wma status --short
# 结果：audit_r08_source.py、artifacts/g0/r08/ 为未跟踪文件

# 2. 脚本语法检查
/root/venvs/psm_wma/bin/python -m py_compile /gemini/code/psm_wma/tools/g0/audit_r08_source.py
# 结果：PASS

# 3. 读取并校验 JSON
python3 -c "import json; json.load(open('/gemini/code/psm_wma/artifacts/g0/r08/source_audit.json'))"
# 结果：PASS

# 4. 核对 loader 源码行号
grep -n "pq.read_table\|_validate_latent_cache_manifest\|_load_cached_latent\|_build_item\|_build_frame_wise_action\|_load_video" \
  /gemini/code/psm_wma/cosmos-framework/cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py
```

---

## 7. 未执行的验证及原因

| 未执行项 | 原因 |
|---|---|
| 实际运行 `audit_r08_source.py` | 本次为只读复核，未执行代码/GPU；产物已由 Codex 生成且 JSON 完整可读。 |
| 抽查 parquet 中的 state 与 timestamp 逐行对应 | 理论上由共用 index sort 保证；可在下一版 audit 中增加抽查断言。 |
| 验证 cache manifest 的 `target_h`/`target_w` 与 VAE 输入是否一致 | 属于 Gate-0 实证内容，本次只读审查未运行 VAE。 |

---

## 8. 是否满足验收条件

- ✅ 四 suite observation.state schema 一致、`float32`、shape `[8]`、全部 finite。
- ✅ state 语义未推断，duplicate gripper 已记录。
- ✅ loader 当前字段确认不含 observation.state。
- ✅ action `j < t` 边界与 loader 源码一致。
- ✅ exact-window cache 17 帧、`[5,48,12,20]` latent、anchor indices 与源码一致。
- ⚠️ 产物缺少 provenance（MEDIUM-1）。
- ⚠️ loader state 读取状态为硬编码（MEDIUM-2）。
- ⚠️ state 对齐断言命名略强于实际检查（MEDIUM-3）。

**结论：R08 Step 0 source audit 通过；可在补齐 MEDIUM-1/2/3 后进入 Gate-0。**
