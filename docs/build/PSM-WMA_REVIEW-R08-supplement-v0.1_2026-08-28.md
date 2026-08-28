# R08 Causal Local Evidence Stream Implementation Supplement v0.1 独立审查报告

> 审查方：Kimi
> 被审文件：`docs/build/PSM-WMA_R08_Causal_Local_Evidence_Stream_Implementation_Supplement_v0.1.md`
> 被审提交：根仓 `V2@d13f7b2`，子模块 `10bc410`
> 审查方式：只读（不修改文件、不执行代码/GPU）
> 结论：**APPROVE（条件性）—— 可作为 R08 Step 0/1 设计基础；进入 R08 GPU Gate 前必须补充 R07 provenance hygiene 前置条件。**

---

## 1. 审查范围

1. R08 / R09 职责边界是否清晰、是否与 D015 一致。
2. R08 Step 0 → Gate-0 的执行顺序是否合理。
3. z0 suffix-invariance Gate（R08-Gate-0）的定义、覆盖、判定与 fallback 是否完整。
4. R07 provenance hygiene 是否被明确列为 R08 前置。
5. R08 禁止项是否与 SESSION/TODO/D015 一致。

---

## 2. 核验结果

| 检查项 | 证据 | 结果 |
|---|---|---|
| 当前 HEAD | 根 `d13f7b2`，子模块 `10bc410` | PASS |
| 文件存在且可读 | `docs/build/PSM-WMA_R08_Causal_Local_Evidence_Stream_Implementation_Supplement_v0.1.md` | PASS |
| R08/R09 边界 | 文档 :8、:129-154、:155-191 | PASS（R08=causal evidence stream + stateless readout；R09=persistent memory backend A/B） |
| Step 0 → Gate 0 顺序 | 文档 :1205-1219 | PASS（Step 0 只读 source audit；Step 1 只做 Gate-0 diagnostic；不接训练） |
| Gate-0 定义 | 文档 :388-501 | PASS（固定首帧、改变 suffix、比较 latent[0]；强 PASS/容忍 PASS/FAIL；FAIL 后有 Fallback A/B） |
| 禁止项 | 文档 :22、:109-110、:146-153、:855-867、:1175-1198 | PASS（无 recurrent/TTT/Global/Agent/RL；不改 native mRoPE / Policy cache） |
| 与 D015 一致性 | `MEMORY/DECISIONS.md:143-155` | PASS（R07→R08→R09 顺序；Local/Global 独立 optional modality；不提前冻结 compressor） |
| TODO 状态 | `TODO.md:51-53` | R07 runtime DONE；R07 provenance hygiene 仍为 TODO；R08 Step0 IN_PROGRESS |

---

## 3. 结论

文档整体结构完整、边界清晰、因果约束正确，与上游 frozen 设计、Runtime Plan、D015 和当前 TODO/SESSION 没有冲突。

**批准作为 R08 Step 0（source audit）和 Step 1（Gate-0 diagnostic）的设计基础。**

---

## 4. 发现

### BLOCKER

无。

### HIGH

无。

### MEDIUM

1. **未将 `G0-R07-PROVENANCE-HYGIENE` 明确列为 R08 GPU Gate 的前置条件。**
   - 证据：
     - 文档 `:7` 仅声明上游基线 "R07 runtime Gate 已关闭（root 13af0e3，submodule 10bc410）"。
     - 文档 `:1034` 的 R08 DONE checklist 要求 "R07 runtime Gate remains DONE"，但未提及 `G0-R07-PROVENANCE-HYGIENE`（`TODO.md:52` 仍为 `TODO`）。
     - `SESSION.md:19` 明确说明该 hygiene 任务 "可与 R08 Step 0/1 只读工作并行，但在 R08 GPU Gate 前应完成"。
   - 影响：若直接按文档进入 Step 7 GPU Gate A，可能遗漏精确启动命令与 retained checkpoint SHA256 的记录，导致 R08 产物 provenance 不完整。
   - 建议的最小修复：
     - 在文档 `§1.1 R07 → R08 Handoff Contract` 或 `§23 Codex Execution Order` 中增加一条：
       > "R08 Step 0/1 可与 G0-R07-PROVENANCE-HYGIENE 并行；R08 GPU Gate A（Step 7）必须在 G0-R07-PROVENANCE-HYGIENE 标记 DONE 后启动。"
     - 在 `§18 R08 DONE Criteria` 中增加一项：
       > `[ ] G0-R07-PROVENANCE-HYGIENE DONE`
   - 是否阻止当前文档作为 Step 0/1 基础：**否**。是否必须在进入 R08 GPU Gate 前关闭：**是**。

### LOW

1. **文档 `:7` 的 upstream baseline commit `13af0e3` 与当前审查提交 `d13f7b2` 不一致，可能让读者混淆。**
   - 说明：该字段用于标明 R07 Gate 关闭时的代码基线，不是当前 HEAD，本身无错。建议在首次出现时用括号注明 "as of R07 closure"，避免误读为当前根仓 HEAD。

2. **`:547-552` 的 visual summary baseline `adaptive_avg_pool2d(output_size=(1,2))` 的语义假设未经验证。**
   - 文档已在 `:560` 与 `:688` 说明这是 R08 smoke baseline、不是最终表征；符合 D015 未冻结 visual representation 的决策。仅作为 LOW 观察，不阻塞。

3. **`:1144-1151` 的预计代码 touches 包含 `omni_mot_model.py` 与 `cosmos3_vfm_network.py`。**
   - 这两处是 R07 已冻结的 Local 接口核心文件，任何改动都应经过与 R07 相当的独立 review。文档 `§24 Review Checklist` 已要求核对 "no Local loss/noise" 与 "native V/A mRoPE unchanged"，基本覆盖。建议 Codex 实际修改前先跑 R07 regression smoke。

---

## 5. 已核验的关键锚点

- `docs/build/PSM-WMA_R08_Causal_Local_Evidence_Stream_Implementation_Supplement_v0.1.md:8` — R08/R09 硬边界
- `:31-34` — R08 唯一任务声明
- `:129-154` — R08 = Causal Local Evidence Stream
- `:155-191` — R09 = Persistent Temporal Local Memory（A/B backend）
- `:193-249` — LIBERO source audit 要求
- `:267-333` — canonical time semantics 与 leakage 禁止
- `:388-501` — Gate-0 z0 suffix-invariance 定义、覆盖、判定、fallback
- `:564-592` — state evidence 处理
- `:643-675` — R08 sample schema
- `:736-775` — stateless LocalReplayReadout
- `:854-867` — hard FAIL leakage rules
- `:1029-1050` — R08 DONE criteria
- `:1205-1264` — Step 0 → Gate 0 → ... → R08 DONE 顺序
- `:1175-1198` — files/areas R08 must not touch
- `MEMORY/DECISIONS.md:143-155` — D015 R07-R09 顺序与冻结边界
- `TODO.md:51-53` — 当前任务状态
- `SESSION.md:15-19` — R07 closure 与 provenance hygiene 说明

---

## 6. 已执行的只读命令

```bash
# 1. 确认当前 HEAD
git -C /gemini/code/psm_wma rev-parse HEAD
# d13f7b849855e2234a84021a6515f00238d1fb76

# 2. 确认被审文件存在且为当前提交内容
ls -l /gemini/code/psm_wma/docs/build/PSM-WMA_R08_Causal_Local_Evidence_Stream_Implementation_Supplement_v0.1.md

# 3. 在文档中检索 provenance / hygiene / sidecar / R07 相关关键字
grep -n -i "provenance\|hygiene\|raw sidecar\|R07 runtime Gate" \
  docs/build/PSM-WMA_R08_Causal_Local_Evidence_Stream_Implementation_Supplement_v0.1.md

# 4. 核对 TODO/SESSION 中的 R07/R08 状态
grep -n "G0-R07-PROVENANCE-HYGIENE\|G0-R08-STEP0\|R08" TODO.md SESSION.md
```

---

## 7. 未执行的验证及原因

| 未执行项 | 原因 |
|---|---|
| 未核对文档中所有代码路径是否真实存在 | 本次为设计文档审查，代码路径存在性应在 Step 0 source audit 中完成。 |
| 未验证 Gate-0 的 suffix-invariance 假设 | 这是 R08 Step 1 的实证工作，需 GPU 运行 VAE；本次只读审查不涉及。 |
| 未审查 R08 预期新建模块的命名与 repo style 兼容性 | 可在实现阶段通过 `py_compile` / `diff-check` / review 验证。 |

---

## 8. 是否满足验收条件

- ✅ R08/R09 边界清晰，符合 D015。
- ✅ Step 0 → Gate 0 顺序正确，source audit 先于任何训练/模型修改。
- ✅ z0 suffix-invariance Gate 定义完整，有 PASS/FAIL 判定和 fallback。
- ⚠️ R07 provenance hygiene 前置未在文档中显式体现（MEDIUM-1）。
- ✅ 禁止项完整，与 SESSION/TODO/D015 一致。

综上，**文档在补充 MEDIUM-1 后可作为 R08 全流程正式设计基础；当前版本已足够支撑 Step 0/1 启动，但不应在未关闭 MEDIUM-1 前进入 R08 GPU Gate。**
