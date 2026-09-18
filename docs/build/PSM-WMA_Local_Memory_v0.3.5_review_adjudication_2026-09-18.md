# 三方审核评估与裁定（2026-09-18）

- 状态：**Codex 对 DS / MM / GPT 三方本轮审核的评估落盘**，供 GPT 复核。
- 原则：**不盲信任何审核者**；每条关键主张以代码/实测复核，标注「已验证/未验证」「采纳/部分采纳/驳回」。
- 名册：DS=`ds:0.0` + MM=`mm:0.0`（用户已移除 Kimi）；GPT 经 `docs/collab/chatgpt/reviews/`。

---

## 1. 训练范围 Gate（active 优化器 = baseline 生成+动作头 + local-mem）

### 1.1 三方 verdict

| 审核者 | verdict |
|---|---|
| MM | `APPROVE_TO_CLOSE_G0_R09_B_TTT_V035_ACTIVE_TRAINING_SCOPE_BASELINE_PLUS_LOCAL` |
| DS | 条件式 `REQUEST_CHANGES` → 补 ①②③ 后，再补「durable override 记录 + `config_checkpoint_contract` scope 界定」→ 判定通过（正文「本 Gate 只关闭『优化器训练范围 = baseline 生成/动作头 + local-mem』(D025)；不授权 D8b」；verdict 前缀被 TUI 缓冲截断，未能逐字读取） |
| GPT | `REQUEST_CHANGES`（root `5b04ad60`/child `60dd814`，技术性非 formal）：HIGH-1 选择器构造不纯净；MEDIUM-1 ckpt 预算过时；MEDIUM-2 contract 测试红 |

### 1.2 Codex 复核

| 主张 | 来源 | 复核方式 | 判定 |
|---|---|---|---|
| config `keys_to_select` 非「纯净 Nano7 + TTT4」 | GPT HIGH-1 | 实测组合后列表 = 14 项（Nano7 + `local_memory2llm`/`local_memory_modality_embed`/`local_history_runtime` + TTT4，含重复） | **已验证，采纳**（契约不洁；因选择器按 param 遍历，重复项运行期无害；`local_history_runtime` 在 active 路线未实例化） |
| readiness `ckpt_each_GiB=6.3` 过时 | GPT MEDIUM-1 | `du -sh iter_000000020` = **17G**（model 6.3G + optim 11G） | **已验证，采纳**（原 6.3G 是仅 local 的旧读数） |
| `ttt_lifecycle_test` 红 | GPT MEDIUM-2 | 实测 **5 failed / 29 passed**；失败名 `test_model_config_ttt_*`，`model_config.py` 最后修改 `fa964ef`（**本会话之前**） | **部分采纳**：确有失败，但**归因不准**——属既有 stale，非 D025 引起 |
| DS 的「durable override 记录」要求 | DS | 已加 `MEMORY/DECISIONS.md` D025 | 采纳（已落盘） |
| DS 的「`config_checkpoint_contract` scope 界定」要求 | DS | 已加 module docstring + `SELECTORS` 注释：只界定 local 四组慢参数，非完整 optimizer allowlist；生产只用 `validate_slow_inventory`；contract tests 15 passed | 采纳（已落盘） |

---

## 2. Member-shape refreeze Gate（option (A)）

### 2.1 三方 verdict

| 审核者 | verdict |
|---|---|
| DS | 裁定 **(A2)** + 条件性授权；提示 (A2) 须连锁重验 resume/epoch-reuse 判据、readiness 14.6 天须重估 |
| MM | `APPROVE_A2_G0_R09_B_TTT_V035_ACTIVE_MEMBER_SHAPE_REFREEZE` + 条件（CPU/static 先行 + 32+61 判据 + 2 新等价测试 + GPU 单窗 smoke + cascade 重验 4 项 + memory ≤60GB + TTT gradient 等价） |
| GPT | `REQUEST_CHANGES`：**HIGH-2** v0.1 的 A1 前向次数算术错；**HIGH-3** `SegmentBatch` 本就 `[B,T]`、不需 ABI 改动，不应把 `SegmentIdentity` 批量对象化，应复用 `MicrobatchPlanMember`；**HIGH-4** readiness 与「D8b 阻塞」矛盾；**HIGH-5** 证据未绑定实现身份 |

### 2.2 Codex 复核

| 主张 | 来源 | 复核方式 | 判定 |
|---|---|---|---|
| A1 前向次数 = 256（非 16）；A2 = 16 | GPT HIGH-2 | 2048 consumer ÷ 8/forward = 256（A1）；2048 ÷ 128 = 16（A2） | **已验证，采纳**（v0.1 §3 A1 描述错误） |
| `SegmentBatch` 已是 `[B,T]`、无需 ABI 改动 | GPT HIGH-3 | `consumer_visual_summary [B,T,96]` 等 B 为自由维 | **已验证，采纳**（缩小改动面） |
| 存在批量 fast-state 参考 | GPT HIGH-3 | `canonical_segment_adapter_scheduler.MicrobatchPlanMember.row_identities` + `CanonicalProductionFastStateFrontier` | **已验证，采纳**（复用/移植其语义） |
| 不应批量 `SegmentIdentity` | GPT HIGH-3 | `SegmentIdentity` 为单身份；`SegmentBatch` 的 slot/episode/category 按行 | 采纳 |
| readiness 自相矛盾 | GPT HIGH-4 | readiness `blockers=[]` vs member-shape 自称「D8b 阻塞」 | **已验证，采纳** |
| 证据未绑定 root/child | GPT HIGH-5 | 4 个证据 JSON 无 root/child 字段 | **已验证，采纳** |
| DS 裁定 (A2) | DS | GPT HIGH-2 独立得出 A2 | 采信（两方独立一致） |
| MM 的条件集 | MM | 与 GPT 的 HIGH-3/4 方向一致（CPU/static 先行、重验、重估） | 采信 |

---

## 3. 裁定与执行计划

**采信并执行**（三方一致或经复核）：
1. **member 形状 = (A2)**（batch=128/forward、16 次/update），修正 v0.1 的 A1 算术；**不改 `SegmentBatch` ABI**、**不批量 `SegmentIdentity`**、**复用 `MicrobatchPlanMember`/`CanonicalProductionFastStateFrontier` 语义**。
2. **修 config selector 构造**：纯净 `action_policy_libero_all_nano` 七项 + `TTT_SLOW_GROUP_SELECTORS` 四项（各一次），并加**精确列表 + 真实模型成员 fixture**（证明无 legacy `local_history_runtime`/readout/recurrent 进入 optimizer）。
3. **readiness 改 BLOCKED**（member-shape 为声明的前置），(A2) 落地并重估后再 READY。
4. **证据绑定**：每个证据携带并匹配 root/child + 相关输入 digest，或声明并核验 scope-invariance。
5. **ckpt 预算按 17G 重算**（100 份 ≈1.8 TB；磁盘 130 TiB 充裕）。
6. **TTT 批处理**：8 条 slot 各自 fast-state 独立，可在 `[B,T]` 上并行扫描（`local_evidence.py` 已支持）。

**部分采纳 / 说明**：
- GPT MEDIUM-2：确有 5 个 `ttt_lifecycle_test` 失败，但经查为 `model_config` 既有 stale（`fa964ef` 之前），**非 D025 引起**；仍会一并清理并为 D025 新增精确 scope 测试。

**驳回**：无（本轮三方意见经复核均不驳回）。

---

## 4. 请求 GPT 复核的点

1. 上述对 A1/A2 算术、`SegmentBatch`/`SegmentIdentity`、`MicrobatchPlanMember` 复用的复核是否成立。
2. 执行计划 1–6 是否足以关闭 `REQUEST_CHANGES`。
3. MEDIUM-2 的归因（既有 stale vs D025）是否有异议。
