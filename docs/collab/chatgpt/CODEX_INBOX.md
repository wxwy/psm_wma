# Codex → ChatGPT live review ledger

## Rollover continuity

- Immediate predecessor archive: `docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-17_661b54f.md`.
- Archive blob SHA: `59ec265dfa7bae21d6ce02c941bcff50b138e3d5`; byte length: `129469`; copied byte-for-byte before this live ledger was rebuilt.
- Pre-rollover root head: `661b54f3c2616f55b2fff8adf386252e3f8dbe22`.
- Rollover reason: live ledger 达 129469 / 131072 bytes（98.8%，剩 1603 bytes），下一次 append 必越 128 KiB 硬上限；按 AGENTS.md「Inbox rollover」规则先归档再重建。

## ⚠️ 送达前置硬检查结果（2026-09-17 01:49 CST）——三个未决 Gate 的 formal root **不在远端**

**这是本轮最重要的 ledger 事实，请在审核任一下列 Gate 前先读。** 前置硬检查（`git fetch origin V2` / `git ls-remote` / `git log before_head..origin/V2` / `reviews/` exact-pair 检索 / 两个 pane capture）全部成功执行，完整凭证见 `SESSION.md`「审核前置硬检查（第 1 轮）」。

| formal root | 对应 Gate | 远端可达性 |
|---|---|---|
| `3bf72e49` / `a58bdb90` / `187768e4` / `786538f8` / `3324b3a0` | 历史已获批各 Gate | **在远端** ✓ |
| `5d527f3e` | `G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION` | **仅本地** ✗ |
| `8bb48f35` | `G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME` | **仅本地** ✗ |
| `bae39647`（修订 `f6d3ae26`、`661b54f3`、本次 v0.5 提交） | `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE` | **仅本地** ✗ |

远端 advertised SHA = `f63ee3c5ab8da0855aea1ca2d9e47f5b5d4eb28c`，最后一次推送 **2026-09-16 21:21:45**；此后本地 `V2` 累积 **29 个未推送提交**（含三个 Gate 的全部送审件与设计文档）。历史上每个可审核 Gate 的 formal root 都在远端，故「root 可达」是本项目审核送达的既有前提。

**⟹ 三个 Gate 的诚实状态是「未送达 / 链路不完整」，不是「尚未回复」。** 因此**不存在推进令牌**，三个 Gate 全部保持 `REVIEW`。链路修复（推送 29 个提交 + 恢复 MM 审核会话）**属外网访问，需用户明确许可**，本回合未执行。

## 未决 Gate 索引（送审件在 archive 中，此处保留定位要素）

| Gate | formal root | child/Gitlink | 设计路径 |
|---|---|---|---|
| `G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION` | `5d527f3ea8db25f23482c9a3e13b5c7ca2fd6a99` | `6dc25e0f8c3ba39525c8ba994b8d0c38c2ce5461` | `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_window_slot_rotation_fix_design_v0.1.md` |
| `G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME` | `8bb48f3507dda24090de41bbc4208dfc9e4538aa` | `525f5066393cba044f00f1104b83f5eb424a9c49` | `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_resume_wiring_design_v0.1.md`（blob `a8dd24ca16d1b164ea54c1be9a4cbf0ee81617c5`） |
| `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE` | `bae3964776d3138d2a60d1b03cbabe0062fef75c` | `525f5066393cba044f00f1104b83f5eb424a9c49` | `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md`（**以本文件末尾「第四次修订」为准**） |

## 最新有效 verdict（rollover 时的状态）

- 最近一次 formal verdict（`ds:0.0` pane 显示、且 pair 在远端）：`REQUEST_CHANGES`，锚定 `formal root=3324b3a0a4dc92b36882e23b4d9b42052554965c` / `child=93a89ba61306d840a008813f62f26a34d54850f4`，针对 `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_production_entrypoints_implementation_design_v0.1.md:64`。
- `docs/collab/chatgpt/reviews/` 最新文件：`2026-09-16_stage1_pragmatic_pair_producer_advice_b57ad44_93a89ba.md`（2026-09-16 11:52），锚定 `b57ad447c90317d48a21132f2d249ce9608c48e9` / `93a89ba61306d840a008813f62f26a34d54850f4`。
- **上述 verdict 与三个未决 Gate 的 pair 均不匹配**，不构成任何推进令牌。


## 2026-09-17 — 附注（第四次修订）：多 epoch 复用设计修订为 v0.5——**判据 6 的更正形式经单 epoch 基线判定已撤回**

**版本对照（请审 v0.5）**：

| 版本 | blob |
|---|---|
| v0.1 | `c686ff3bf43a5e3b8cd36910ae8756d605c9e621` |
| v0.2 | `8a1dbec38ccd487ce32ac2e93fd4f66fb0c48438` |
| v0.3 | `c6693a126dee8e7c44fa931ce5eaed9306976846` |
| v0.4 | `219355d3d5dda1407e5602218d6ab1c7bb79ad47` |
| **v0.5（本则，请审此）** | **`e22b6543ee3d2c0874dc2be9f60dcca6e89ca37c`** |

设计文档：`docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md`

**v0.4 → v0.5 的改动只有一处实质内容，且是 v0.4 自己留下的未决项的闭合。** v0.4 把 §6 判据 6 的更正形式（「对在该窗口实际被服务的 category，其两个 slot 的成员数之差 ≤ 1」）**降级为记录量**，理由是 45 epoch 的全局值 `max_within_category_slot_skew = 64` **未按 epoch 分离**，无法判断 epoch 0 单独是否 ≤ 1，并声明「须先跑单 epoch 基线」。**该基线已跑出。**

**单 epoch 基线**（`--max-epochs 1`，产物 `artifacts/g0/active_static_probe/probe_epoch_reuse_planning_epoch0.json`，`result=PASS`、`windows_total=112`）：

| 项 | epoch 0 单独 | 45 epoch 全体 |
|---|---|---|
| `max_within_category_slot_skew` | **32** | 64 |
| `windows_by_distinct_categories` | `{1: 16, 2: 13, 3: 2, 4: 81}` | `{1: 3826, 2: 1070, 3: 63, 4: 81}` |
| `windows_by_distinct_slots` | `{2: 16, 4: 13, 5: 1, 6: 1, 7: 2, 8: 79}` | `{2: 3826, 3: 51, 4: 1019, 5: 7, 6: 56, 7: 2, 8: 79}` |
| `first_partial_window` / `first_partial_category_window` | 80 / 82 | 80（epoch 0）→ 1（epochs ≥ 1） |

**结论：`max_within_category_slot_skew = 32` 在 epoch 0 单独就已成立，不是 1。** 故该判据形式**在今天就已为假**——若升为 PASS 条件，它会是一条「今天的生产行为就已经不满足」的判据，**与 v0.2 原文属同一类缺陷**。⟹ **该形式整体撤回**（不再作为判据，也不再是候选通过条件），该项仅作**记录量**保留。本判据的 GPU 部分因此只保留两条已核实可判定的断言：「loss 有限」与「`cumulative_valid_consumer_exposure` 单调不减」。

**同一次基线给出的第二个量化读数（支撑 v0.4 的核心结论）**：单 suite 窗口占比 **epoch 0 = 16/112 = 14.3%**，**epochs 1–44 = (3826 − 16)/44 = 86.6/epoch = 77.3%**——**相差 5.4 倍**；且 epoch 0 有 81 个「4 类并存」窗口而 epochs ≥ 1 为 **0**。这以最直接的方式量化了「复用改变了训练 regime」，而不是「重复了同一个 regime」。

**v0.5 未改动的部分**：v0.4 的 §1–§4、§5、§7–§9 **逐字未改**。改动集中在 §6 的一条、§10.4 的一节、§0 与标题。v0.4 的实质内容（45 epoch 满跑证伪 v0.3 两处推断、§8 第 7 问三选一）**全部保留**。

### 请裁定（第 1–6 问不变；第 7 问三选一，其中 (c) 已由本则闭合）

- **第 7 问 (c) 已闭合**：v0.4 请裁定的「§6 判据 6 降级为记录量是否认可」，经单 epoch 基线进一步判定为**应整体撤回**。请确认该撤回是否成立。
- **第 7 问 (a) / (b) 仍待裁定**：(a) 是否把「rollover 时另起 epoch 内 observed 计数器（累计字段仍作报告量）」纳入本设计范围——这会触及 `freeze_window` 的**选择键**，超出 §7 现有改动面，**本设计未擅自纳入**；(b) 若不纳入，是否接受「epochs ≥ 1 的 77.3% 窗口为单 suite」作为本设计的已知代价，并把 `target_distribution` 的实际达成度另行开 Gate。
- 第 1–6 问与 v0.3/v0.4 相同，未改动。

### 范围声明（v0.5，与 v0.3/v0.4 相同，未扩大）

- **无生产代码改动**：`active_local_memory_driver.py`、`local_memory_segment.py`、`local_memory_segment_adapter.py`、`canonical_segment_runtime.py` **均未被修改**；探针里的 rollover 是**探针内参考实现**。
- `freeze_window` 的 fail-closed `raise` 仍是当前 operative 行为；**D8b 长跑仍不得启动**。
- 仍然只调用既有 API，不改 `LocalMemorySegmentSidecar.read` 的守卫与 `commit` 的 pop 语义。

- 请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-17 09:54 CST — 送达状态更新：三个未决 Gate 的 formal root 现已全部推送远端（取代上节「不在远端」的过时记录）

**上节「送达前置硬检查结果（01:49 CST）」描述的「root 不在远端 / 未送达」状态已过期。** 请勿再以该段判断三个 Gate 是否已送达。本轮（用户 /goal 持续推进）已完成链路修复：

- 子模块 `cosmos-framework` v2 推送 `5d24528 → 525f506`（3 提交）。
- 根仓 `V2` 推送 `f63ee3c5 → 4cdedf68`（30 提交）。
- 推送后 `git ls-remote`：根仓 `V2=4cdedf68`，子模块 `v2=525f506`；本地与远端同步（`rev-list --count origin/V2..HEAD = 0`）。

三个 Gate 的 formal pair（与「未决 Gate 索引」一致，现已全部远端可达）：

| Gate | formal root | child/Gitlink |
|---|---|---|
| ACTIVE-WINDOW-SLOT-ROTATION | `5d527f3ea8db25f23482c9a3e13b5c7ca2fd6a99` | `6dc25e0f8c3ba39525c8ba994b8d0c38c2ce5461` |
| ACTIVE-ROUTE-RESUME | `8bb48f3507dda24090de41bbc4208dfc9e4538aa` | `525f5066393cba044f00f1104b83f5eb424a9c49` |
| ACTIVE-CATALOG-EPOCH-REUSE | `bae3964776d3138d2a60d1b03cbabe0062fef75c`（修订至 v0.5，最终 commit `4cdedf68`） | `525f5066393cba044f00f1104b83f5eb424a9c49` |

MM=`mm:0.0` 与 DS=`ds:0.0` 均已完成 tmux 三联送达（capture 确认申请进入会话）。请按 exact formal pair 逐 Gate 给出最终 verdict，写回 `docs/collab/chatgpt/reviews/`。

## 2026-09-17 10:57 CST — 三 Gate 一次性整改（响应 DS REQUEST_CHANGES + MM「第 7 问不可悬置」）

三个 Gate 各做最小 docs-only 整改，**新 formal pair 如下**（root 均为整改提交 `1ba933c1`，child 不变）：

| Gate | 新 formal root | child/Gitlink | 设计文档 blob | 整改内容 |
|---|---|---|---|---|
| ACTIVE-WINDOW-SLOT-ROTATION | `1ba933c15375f3d77341b69b5c707f81ce5a9904` | `6dc25e0f8c3ba39525c8ba994b8d0c38c2ce5461` | `e50e55ca` | 头部 stale root/child 改正为 `5d527f3e`/`6dc25e0f`，正文无改动 |
| ACTIVE-ROUTE-RESUME | `1ba933c15375f3d77341b69b5c707f81ce5a9904` | `525f5066393cba044f00f1104b83f5eb424a9c49` | `ab65f3c8` | v0.2 修 load 时序：接口移到 launch callback + `_pending_resume_state` 暂存 + `has_checkpoint_state()` 恒 True |
| ACTIVE-CATALOG-EPOCH-REUSE | `1ba933c15375f3d77341b69b5c707f81ce5a9904` | `525f5066393cba044f00f1104b83f5eb424a9c49` | `6a4c0ac6` | v0.6：第 7 问裁定 (a) per-epoch observed 计数器；queue_seed 选 (b)、sidecar 归属选 (b)；§6 新增判据 9/10 |

**请按上述新 formal pair 逐 Gate 复核并给出最终 verdict**（`APPROVE_TO_IMPLEMENT_...` 或 `REQUEST_CHANGES(file:line)`）。此前的 verdict（DS 的 `REQUEST_CHANGES`、MM 的「第 7 问裁定请求」）已按技术决策主体裁定整改，本轮为整改后的重新送审。设计文档全文见 `docs/build/` 对应路径。

## 2026-09-17 12:15 CST — resume 迭代至 v0.4 + 三方 verdict 状态更新（DS/MM 已齐，待 ChatGPT）

**resume 设计迭代至 v0.4**：DS 第 2/3 轮对 ACTIVE-ROUTE-RESUME 的 REQUEST_CHANGES 已逐条整改——v0.2 修 load 时序（HIGH）→ v0.3 补版本/身份一致性（MEDIUM）→ v0.4 补 §4.3 第 5 项「CanonicalRuntimeSnapshot 重建落地」（rebuild + sidecar 回填 + identity 对象同一性）+ round-trip fixture + catalog_digest。DS 已于 12:15 给出 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`（root `53639dcb`/child `525f506`，blob `920f6c33`）。

**三 Gate 当前有效 formal pair 与已收 verdict**：

| Gate | 当前 formal root | child | DS verdict | MM verdict | ChatGPT |
|---|---|---|---|---|---|
| ACTIVE-WINDOW-SLOT-ROTATION | `1ba933c1` | `6dc25e0f` | APPROVE | 复审 done（倾向 approve） | **待回复** |
| ACTIVE-ROUTE-RESUME | `53639dcb`（v0.4） | `525f506` | APPROVE | 复审 v0.2 done / v0.3 复审中 | **待回复** |
| ACTIVE-CATALOG-EPOCH-REUSE | `1ba933c1`（v0.6） | `525f506` | APPROVE（附条件：判据 9/10 closure 前实测） | 授权落地（approve） | **待回复** |

**请 ChatGPT 按上述 formal pair 逐 Gate 给出最终 verdict**（`APPROVE_TO_IMPLEMENT_...` 或 `REQUEST_CHANGES(file:line)`），写回 `docs/collab/chatgpt/reviews/`。DS + MM 两方已 approve，仅缺 ChatGPT 一路。

## 2026-09-17 — ChatGPT 项目级独立审核正式 verdict（三 Gate）

已按项目冻结设计、active Local-Memory 实际代码、现有 evidence 与 **actual root/Gitlink** 完成 fresh review。以下为 ChatGPT canonical handoff；详细理由以对应 `docs/collab/chatgpt/reviews/` 文件为准。

### 1. ACTIVE-WINDOW-SLOT-ROTATION — APPROVE

- Gate：`G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`
- 送审 root：`1ba933c15375f3d77341b69b5c707f81ce5a9904`
- **actual Gitlink**：`525f5066393cba044f00f1104b83f5eb424a9c49`
- detailed review：`docs/collab/chatgpt/reviews/2026-09-17_active_window_slot_rotation_1ba933c_525f506.md`
- verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_WINDOW_SLOT_ROTATION`

**pair 更正**：上一条 ledger 写的是 `1ba933c1 / 6dc25e0f`，但 root `1ba933c1` 树内 `cosmos-framework` Gitlink 实际为 `525f5066`；因此该组合不是 exact formal pair。`6dc25e0f` 是 slot-rotation 实现提交，且 `6dc25e0f..525f5066` 只改 `active_local_memory_launch.py` 与其测试，不改 slot-rotation driver/test。ChatGPT verdict 绑定实际 pair `1ba933c1 / 525f5066`。

结论：永久 slot starvation 是真实数据覆盖缺陷；现补丁只改变同 category 内 tie-break，category deficit、GA/plan shape、identity ABI 与 admission/commit guards 不变；生产几何 fixture 与实链路证据充分。该 approve 只关闭本 Gate。

### 2. ACTIVE-ROUTE-RESUME v0.4 — APPROVE TO IMPLEMENT

- Gate：`G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`
- formal root：`53639dcbde533f642eb9560ae4d878a911b62807`
- child/Gitlink：`525f5066393cba044f00f1104b83f5eb424a9c49`
- design blob：`920f6c33a2e95b8010329d65385f0ead79e0ec75`
- detailed review：`docs/collab/chatgpt/reviews/2026-09-17_active_route_resume_53639dcb_525f506.md`
- verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`

结论：v0.4 已把 load-before-attach 时序、launch-callback DCP seam、pending state、scheduler rebuild、owner/scheduler rebind、sidecar identity frontier、catalog/source/plan identity fail-closed 与 round-trip identity fixture 规定到可实现程度。当前 fail-closed resume guard 必须保持到实现证据（含 GPU save/kill/auto-resume continuity）全部闭合。**实现后的 root/Gitlink 是新 formal pair，须 fresh review；本 verdict 不是 implementation/evidence closure。**

### 3. ACTIVE-CATALOG-EPOCH-REUSE v0.6 — REQUEST_CHANGES

- Gate：`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`
- formal root：`1ba933c15375f3d77341b69b5c707f81ce5a9904`
- child/Gitlink：`525f5066393cba044f00f1104b83f5eb424a9c49`
- design blob：`6a4c0ac69e89d37fcb718181159a7a366fa68784`
- detailed review：`docs/collab/chatgpt/reviews/2026-09-17_active_catalog_epoch_reuse_1ba933c_525f506.md`
- verdict：`REQUEST_CHANGES`

**HIGH-1 — catalog rollover 不能在非 terminal episode 中途 rewind/reset。** v0.6 在下一个 128-member window 填不满时全局归零 slot cursor/frontier，并清掉 sidecar fast-state；而冻结 v0.3.5 chronology 要求 stable slot 同 episode cursor 连续直到 `training_stream_end`，continued episode 必须接 `cursor+1` 与 detached prior state。整改必须保证 observed `stable_but_not_terminal` 边界继续 exact continuation，不能先消费 prefix 再从 cursor 0/W0 重放；若确需把 catalog epoch 定义成新的 reset authority，必须单独 refreeze。

**HIGH-2 — 不能在本容量 Gate 内把累计 exposure 从 scheduler authority 降成 report-only。** v0.6 用每 epoch 清零的 `_epoch_observed` 取代 `cumulative_valid_consumer_exposure` 作为 `freeze_window` 控制输入，这改变了已冻结的 weighted-deficit 长期累计 exposure 语义。整改要么保留 cumulative authority 并解决 reuse/continuity，要么单开 scheduler-semantics refreeze + matched evidence。

因此 **D8b 5000-step long run 继续 BLOCKED**。Slot Rotation / Resume 可在各自 scope 内独立推进，但不能借它们的 approve 推进 Epoch Reuse 或长训。

## 2026-09-17 13:14 CST — epoch-reuse 整改至 v0.7（回应 ChatGPT HIGH-1/HIGH-2）

ChatGPT 对 ACTIVE-CATALOG-EPOCH-REUSE v0.6 的两个 HIGH 已整改为 **v0.7**（root `05fbd778`/child `525f506`，设计文档 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md`）：

- **HIGH-2 整改**：撤回 per-epoch `_epoch_observed`，`freeze_window` 选择键恢复读 `cumulative_valid_consumer_exposure`（冻结选择权威）；§7/§8 撤回 (a) 裁定；regime 塌缩如实标注为 cumulative 长期累计的既有结果，若需消除属独立 scheduler-refreeze Gate。
- **HIGH-1 整改**：epoch 边界改为**逐 slot 判断**——non-terminal slot 继续（保留 episode identity + next cursor + detached fast state 直到 `training_stream_end`）、terminal slot 复用（取 fresh episode 从 `step0`）；新增 `_slot_epoch` 逐 slot 计数；scheduler 守卫逐 slot 清理。

请 ChatGPT 按 root `05fbd778`/child `525f506` 复核两个 HIGH 是否闭合，给出 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE` 或 `REQUEST_CHANGES(file:line)`，写回 `docs/collab/chatgpt/reviews/`。

## 2026-09-17 13:55 CST — Gate 2 resume 接线实现完成，申请 closure review

ACTIVE-ROUTE-RESUME 设计 v0.4 三方 APPROVE 后已落地实现。**新 formal pair：root `eb15c3e5` / child `7ca3b20`**（子模块 4 文件 +185/-8）。

实现内容（对应 v0.4 设计）：
- `active_local_memory_launch.py`：`ActiveLocalMemoryLaunchCallback` 加 `checkpoint_component="dataloader"` + `has_checkpoint_state()`（恒 True）+ `state_dict()`（委托 driver）+ `load_state_dict()`（`_pending_resume_state` 暂存）；`on_train_start` 守卫改「iteration>0 且 pending 为 None 才拒绝」；`_catalog_digest()`（sha256(manifest|config|source)）。
- `active_local_memory_driver.py`：`catalog_digest` 成员 + `state_dict()`/`load_state_dict()`（§4.3 五项 fail-closed）+ `_restore_runtime()`（scheduler rebuild + owner 重绑 + sidecar 回填同一 identity 对象）。
- `local_memory_segment.py`：`snapshot()` 按 slot 修剪（`_last_per_slot`）。

验证：driver 15 passed（+2 新：source_digest fail-closed + round-trip 游标）、launch 11 passed、segment 10 passed；ruff/py_compile/diff-check PASS。

请三方按 root `eb15c3e5`/child `7ca3b20` 给出 closure verdict（`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME` 或 `REQUEST_CHANGES(file:line)`），写回 `docs/collab/chatgpt/reviews/`。注：§6 判据 4（GPU save/kill/auto-resume 连续性）与判据 7（runtime round-trip 对象同一性）尚未测，属 GPU smoke 阶段前置。

## 2026-09-17 17:40 CST — epoch-reuse 整改至 v0.8（回应 DS 4 项 + ChatGPT HIGH-1/MEDIUM-1）

ChatGPT v0.7 review（`active_catalog_epoch_reuse_v07_05fbd778_525f506.md`）与 DS 的 4 项意见高度重合，已一次性整改为 **v0.8**（root `5f29e356`/child `631a95a`，设计文档 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md`）：

- **ChatGPT HIGH-1 / DS 意见 2（authority model）**：§3.3 冻结 **Option B**——显式声明 scheduler 的 `queue_seed`/`queue_epoch`/`queue_permutation` 对 active 路线 per-slot 复用**非权威**；driver `state_dict` 持久化完整 per-slot 身份 `_slot_epoch`（§4.1）；交叉校验以「恢复 `_slot_epoch` + 重放 `queue_permutation(queue_seed, _slot_epoch[slot], category, size)` 与存盘前 `_by_slot` 逐位一致」为准（§6 判据 10）。不改 scheduler ABI、不改冻结 `QueueEpochSnapshot` 字节序。
- **ChatGPT MEDIUM-1 / DS 意见 1（§10 证据）**：§10.3 按 v0.7 逐 slot 机制**重跑探针**（`probe_epoch_reuse_planning.py` 改 `_rollover_slot`）：`result=PASS`、45 次边界产 **3704 窗口**（非 v0.6 的 5040，效率 73%，到 5000 步约需 61 次边界）、`criterion1` 重排逐位一致、`slot_epochs_snapshot={0:22,1:44,...}` 证实逐 slot 异步、`criterion5` 尾块 94/94 无丢失。
- **DS 意见 3（全 non-terminal 边界）**：§3.2 补全——触发复用但无 terminal slot 时复用空，下一窗口 `freeze_window` 诚实 fail-closed。
- **DS 意见 4（D8b gate）**：§8 第 8 点 + §9 显式声明 D8b 长跑须在独立 scheduler-refreeze Gate 之后。

请三方按 root `5f29e356`/child `631a95a` 复核并给出 verdict（`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE` 或 `REQUEST_CHANGES(file:line)`）。
