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

## 2026-09-17 18:45 CST — Gate 2 closure 整改 + Gate 3 v0.8 二次整改（回应 ChatGPT/DS 最新 verdict）

新 formal pair：root `f86513a1` / child `c9a0111`（两 Gate 整改后同一 root）。

**Gate 2 ACTIVE-ROUTE-RESUME closure 整改**（回应 ChatGPT `active_route_resume_closure_dae010c_631a95a.md`）：
- **HIGH-1（两阶段 restore）**：`load_state_dict` 改为 ① pure staging/validation（`_stage_active_stream`/`_stage_frontier`/`_stage_runtime` 旁路 rebuild + stage sidecar + 手动词组复现 `owner.snapshot():181-188` 校验，不 mutate live）→ ② atomic apply（`_apply_runtime`）。加 4 个 causal mutation fixtures，每个断言**失败时零 live mutation**。driver 22 passed。
- **HIGH-2（GPU/DCP witness）已验证**：Phase 1 跑到 iter_3 存出完整 DCP + `dataloader/rank_0.pkl` → kill → auto-resume `Loaded checkpoint .../iter_000000003 (same-job, local) in iteration 3` → **训练从 iteration 4 续跑**（loss=1.644157，不抛 cannot resume）。

**Gate 3 ACTIVE-CATALOG-EPOCH-REUSE v0.8 二次整改**（回应 ChatGPT `..._v08_5f29e35_631a95a.md` + DS）：
- **HIGH-1（authority）选 option A**：§3.3 显式 supersede `canonical_segment_production_adapter_scheduler_design_v0.2.md:86` 的 global rollover clause（严格限于 active 路线）；`_slot_epoch` 为 canonical queue-identity authority；scheduler 单值字段降为兼容性元数据、不作 resume witness；本 Gate 显式框定为 active-route queue-semantics refreeze。
- **HIGH-2（capacity）**：探针改为跑到 `windows_total >= target`（非固定边界）+ `result`/exit 纳入 capacity 判据。**实测跑到 5107 窗**（`capacity_target_met=true`、`criterion2_meets_target=true`、63 边界、`slot_epochs_snapshot={0:25,1:50,...}` 证实逐 slot 异步）；§10.3 用该直接实测更新。
- **MEDIUM-1 / DS LOW**：§2.1/§4.1/§4.3/§5/§8/§6 全部统一为单一 authority（判据 7 并入判据 10）。

请三方按 root `f86513a1`/child `c9a0111` 复核两个 Gate 并给出 verdict。

## 2026-09-17 19:55 CST — 两 Gate 最终送审（GPT 复核请求）

当前 formal pair：root `04ab6f9a` / child `c9a0111`（含两 Gate 的全部整改）。

**Gate 2 ACTIVE-ROUTE-RESUME closure**：
- HIGH-1 两阶段 restore（staging/validation → atomic apply）+ 4 个零突变 causal fixtures；driver 22 passed。
- HIGH-2 GPU resume witness 闭环：Phase1 iter_3 存 DCP + `dataloader/rank_0.pkl` → kill → auto-resume「...iter_000000003 (same-job,local) in iteration 3」→ 训练从 iteration 4 续跑至 iter_6（loss finite，不抛 cannot resume），iter_6 存出完整 DCP + `dataloader/rank_0.pkl`。

**Gate 3 ACTIVE-CATALOG-EPOCH-REUSE v0.8**：
- HIGH-1 authority：显式 supersede `canonical_segment_production_adapter_scheduler_design_v0.2.md:86` 的 global rollover clause（限 active 路线）；`_slot_epoch` 为唯一 queue-identity authority；本 Gate 显式框定为 active-route queue-semantics refreeze。
- HIGH-2 capacity：探针按 v0.7 category 级重排重跑，跑到 **5112 窗**（≥5040、`capacity_target_met=true`、`criterion1=true`、`full_coverage=true`/`stranded=[]`）；探针 result/exit 纳入 capacity 与覆盖判据。
- MEDIUM-1 / DS LOW：§2.1/§4.1/§4.3/§5/§6/§8 统一单一 authority（判据 7 并入判据 10）。

请 GPT 对两个 Gate 分别给出 verdict，写回 `docs/collab/chatgpt/reviews/`。

## 2026-09-26 — V3-STAGE-A-EDGE-RAW15 closure request（仅治理 bookkeeping）

- Gate：`V3-STAGE-A-EDGE-RAW15`。
- formal target root：`fb6a72c11aa5e7888b9425bb4a50817eab95e10c`。
- formal target child/Gitlink：`196b93b70b579023ef008030b0c18a6fde353c82`。
- 本次新增 root commit 仅追加本 request，属于治理 bookkeeping；不改变上述 formal implementation/design pair，不以 bookkeeping SHA 替代 formal target。
- 本 Gate 唯一允许的 close literal：`APPROVE_TO_CLOSE_V3_STAGE_A_EDGE_RAW15`。
- 另一个允许的 verdict：`REQUEST_CHANGES`。
- 请仅使用上述两个 verdict 之一；通用 `APPROVE`、其他 Gate 的 close literal 或其缩写均不能关闭本 Gate。
- 审核依据：上述 formal root 中的 `SESSION.md`、`TODO.md`、`docs/build/PSM-WMA_V3_upstream_bootstrap_2026-09-26.md`，以及上述 formal child 中的 Edge recipe、server/wrapper 和对应 CPU contract tests；证据入口以该 formal pair 的既有记录为准。
- 审核范围：按既有技术合同及可核验证据判断该 Gate 是否满足 closure 条件；本 request 不新增、放宽或替代验收条件，不声明 Gate 已关闭，不改 TODO/SESSION 技术合同，不授权新的生产代码、测试、GPU 或 artifacts 操作。
- 请将正式结果写入 `docs/collab/chatgpt/reviews/`，明确记录 Gate、上述完整 formal root/child pair 和最终 verdict；若为 `REQUEST_CHANGES`，附具体依据及适用的 `file:line`。

## 2026-09-26 — ChatGPT formal closure verdict: V3-STAGE-A-EDGE-RAW15

- Gate: `V3-STAGE-A-EDGE-RAW15`
- formal implementation root: `fb6a72c11aa5e7888b9425bb4a50817eab95e10c`
- formal child/Gitlink: `196b93b70b579023ef008030b0c18a6fde353c82`
- closure-request bookkeeping root: `8ff08edd350fc49df3d6ae60e549fa188b1928cd` (not part of the formal implementation pair)
- detailed review: `docs/collab/chatgpt/reviews/2026-09-26_V3_stage_a_edge_raw15_closure_fb6a72c_196b93b.md`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_A_EDGE_RAW15`

Closure basis: exact-pair CPU contract tests `26/26 PASS` with zero skips; one-step Edge raw15 training produced a complete finite DCP; the formal wrapper-launched server loaded that DCP with raw15/chunk32/fps20/state contract; official RoboCasa `CloseFridge` closed loop completed the full 900-step horizon with exit code 0; all 29 action chunks were `32x15` and finite.

Capability boundary: the 1-step policy obtained `0/1` task success. This verdict therefore closes the **runtime/integration Gate only** and does not approve RoboCasa task capability, longer training, Local-TTT, persistent-memory behavior, or any later V3 Gate.

No additional technical review was performed for the bookkeeping-only closure-request SHA because the formal implementation/design pair did not change.
## 2026-09-27 — ChatGPT formal review: V3-STAGE-B1-LATENT-PRODUCER

- Gate: `V3-STAGE-B1-LATENT-PRODUCER`
- formal implementation root: `bedef75b6bc76cb167f2e27aeaecfe303865f9ab`
- formal child/Gitlink: `5f9c39464761665843b0f08c5e1d578f72114b33`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b1_latent_producer_bedef75b_5f9c394.md`
- verdict: `REQUEST_CHANGES`

Independent exact-pair CPU rerun: 98/98 PASS. B0 files are unchanged.

Current blockers are real-cache production-contract mismatches:
1. HIGH — reader requires nonexistent H5 attr `source_video_frames`; real cache uses `frame_count`.
2. HIGH — reader rejects legal terminal `F-1` endpoint used when the last frame is off the 4-frame grid.
3. HIGH — camera authority is caller-selectable, while Stage A is frozen to `left_wrist`; B1 must deterministically use left + wrist and retain visual96 via parameter-free two-view latent-statistic fusion.

This verdict only blocks B1 closure. Stage A and B0 conclusions are unchanged.

## 2026-09-27 — ChatGPT formal closure verdict: V3-STAGE-B1-LATENT-PRODUCER

- Gate: `V3-STAGE-B1-LATENT-PRODUCER`
- formal implementation root: `93db96df841a14c4c3ef73bf6b4488142adcf567`
- formal child/Gitlink: `1ecebf1ab2fa64bc1d5906959c4cb1fe1d1edc5a`
- design authority: `65271367978537c5d7b5bae5fa50b1ee8056f356`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b1_latent_producer_closure_93db96df_1ecebf1.md`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B1_LATENT_PRODUCER`

Fresh exact-pair review independently reran 132/132 CPU tests in 7.25 s. The three blockers from the rejected pair are CLOSED: real H5 uses root `frame_count`; endpoint authority is 4-grid plus terminal `F-1` when needed; camera authority is fixed to Stage-A `left_wrist` and fuses left+wrist into parameter-free visual96.

ds then directly exercised production reader/producer on 3 tasks × 3 real episodes. Future-endpoint, camera endpoint mismatch, invalid selected latent, cache/loader identity or length mismatch, raw15-source violation and policy-chunk/T16 reinterpretation were all 0. H5 native 12D action is not used; evidence action is V3-loader-derived raw15.

Scope: this closes only cached RGB latent -> causal left+wrist visual96 -> B0 SegmentBatch. It does not authorize trainer integration, cached latent as main policy input, GPU training/eval, checkpoint/resume or SR claims.

## 2026-09-27 — ChatGPT formal closure: V3-STAGE-B2A-NATIVE-MEMORY-PREFIX-CPU-STATIC

- formal root: `21f20f2c436e9627a938148afca039da6023d145`
- formal child/Gitlink: `366501b3b4626f30f0739d2e5765139a52f2308f`
- design authority: `d57ef855404cabceed9c4190b13d435a98a30206`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2a_native_memory_prefix_closure_21f20f2c_366501b3.md`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2A_NATIVE_MEMORY_PREFIX_CPU_STATIC`

Fresh exact-pair review independently reran 153/153 CPU tests. ds independent checklist: 48/48 PASS, 0 hard-fail. Local-only optimizer inventory is exactly 165,312 params at Edge hidden=2048; Local is K/V-only for generation queries; native geometry/reasoner path remains unchanged; full encoder→TTT→bridge outer gradients are finite/non-zero; detach negative control removes those gradients; frozen host params have no grad and remain bitwise unchanged.

Scope stops before segment transaction/backward integration, trainer, GPU, DCP, inference and H100 formal training.

## 2026-09-27 — ChatGPT formal closure verdict: V3-STAGE-B2B-SINGLE-SEGMENT-GRADIENT-RELAY-CPU-STATIC

- Gate: `V3-STAGE-B2B-SINGLE-SEGMENT-GRADIENT-RELAY-CPU-STATIC`
- formal root: `81fa515593e7cd8e2d4f7d226efb915b17be3b5b`
- formal child/Gitlink: `bf6c80e679812b7d2881d6a54aa0b518299e3869`
- design authority: `bf5c8d134014d0023a03c25f95d8e971922f40fd`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2b_gradient_relay_closure_81fa5155_bf6c80e6.md`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2B_SINGLE_SEGMENT_GRADIENT_RELAY_CPU_STATIC`

Independent exact-pair review reran the seven-file suite at 175/175 PASS. ds independently reported B2-B 22/22, B0/B1/B2-A 153/153 and 27/27 independent numerical checks with 0 hard-fail/blocker. Serial relay matched monolithic Local gradients with max_abs_diff 7.451e-09; fast state/frontier remained unpublished until after Local-only optimizer.step; all tested failure paths produced zero new commit.

Scope: CPU/static one-slot serial gradient relay only. It does not approve the real RTX4090 OmniMoT callback, trainer/DCP/inference, grouped GA, H100 formal training or SR claims.

## 2026-09-27 — ChatGPT Phase-1 review: V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE

- design authority: `ced270eb07bbf9fac321e410f6d1992911d591cb`
- formal harness root: `3c125a51af39bfcadeeeb02f83795784e23a1d66`
- formal harness child/Gitlink: `7de65c8e752c47359786e5ff2535a8d3cd5ddced`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_phase1_harness_3c125a51_7de65c8e.md`
- Phase-1 conclusion: **PASS — B2-C §10 harness precondition satisfied; ds is authorized to execute one exact Phase-2 RTX4090 S1 run.**
- B2-C Gate remains `REVIEW`; this is not Gate closure.

Fresh review basis: ChatGPT independently ran the exact-pair eight-file CPU suite (187/187 PASS) and real frozen-asset CPU preflight (PASS). ds independently obtained harness 12/12, production regressions 175/175, real preflight PASS and 16/16 harness checks with 0 blocker/hard-fail. The harness adds only two example files, reuses the closed B2-B relay, locks exact CloseFridge ep0/raw15/RGB and Stage-A DCP authority, selects exactly 165312 Local parameters, freezes the host, and records controlled failure/OOM Evidence without fallback.

Phase-2 is authorized for one exact run only. Any code/config/formal-child change invalidates this execution authorization. Final B2-C closure still requires fresh review of the actual RTX4090 GPU Evidence.

## 2026-09-27 — ChatGPT Phase-2 failure review: V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE run01

- design authority: `ced270eb07bbf9fac321e410f6d1992911d591cb`
- reviewed harness formal pair: root `3c125a51af39bfcadeeeb02f83795784e23a1d66` / child `7de65c8e752c47359786e5ff2535a8d3cd5ddced`
- execution review bookkeeping root: `7f76075fa51b76b006facd5c633e5caff55cc5fa`
- run Evidence: `artifacts/v3/stage_b2c_4090_s1/run01/`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_phase2_run01_failure_7f76075f_7de65c8e.md`
- verdict: `REQUEST_CHANGES`
- no retry is authorized.

run01 failed before native consumer work at `b0_scan`: B1/B0 evidence is a plain Tensor while the model-owned Local encoder/core parameters are FSDP2 DTensors, and direct `adapter.scan -> encoder/core` bypasses the root model FSDP unshard lifecycle. The DTensor state originates from training-mode root `fully_shard` during model build, not from the later DCP load; DCP correctly skipped 20 Local keys.

This was not OOM. Recorded peak was ~14.90 GB allocated / ~15.21 GB reserved before consumer forward. The failed Evidence is retained unchanged. Required remediation is a narrow model-owned Local scan entrypoint registered with `register_fsdp_forward_method`, preserving exact B0/B2-B module identity and transaction semantics. Fresh implementation review and a new explicit execution authorization are required before any second 4090 run.

## 2026-09-27 — ChatGPT closure: V3-STAGE-B2C-R1-FSDP-LOCAL-SCAN

- formal root: `cae1c4bf5d681f93228a9b1a5c74e14d1b5acee4`
- formal child/Gitlink: `558f364efaf6704c9d65037c17ec250a9331be8a`
- design authority: `b5404e9896892b2156e2cca11ef64db871b34def`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_r1a_fsdp_local_scan_closure_cae1c4bf_558f364e.md`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2C_R1_FSDP_LOCAL_SCAN`

Fresh review independently reran 205/205 CPU/static tests; ds independently reported 205/205 plus 26/26 verification with 0 blocker/hard-fail. The fix keeps Local parameters under root FSDP and routes B0 scan through registered model-owned `scan_local_memory`; unregistered DTensor Local ownership fails before scan. No .to_local/ignored-param/FSDP-disable shortcut was introduced.

This approval authorizes one tiny R1-B RTX4090 FSDP lifecycle micro-smoke only. It does not authorize full B2-C run02. run01 remains immutable.

## 2026-09-27 — ChatGPT Phase-1 approval: V3-STAGE-B2C-R1B-TINY-FSDP-MICRO-SMOKE

- formal harness root: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- formal child/Gitlink: `8029b5ff002a350d22ee955db0463cc2e2d3665a`
- design authority: `544bbe0976aa60e935eee431350b20f38c47f28c`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_r1b_phase1_harness_5cc69c6f_8029b5ff.md`
- conclusion: **PASS — one exact RTX4090 R1-B micro-smoke is authorized.**

ChatGPT: 216/216 CPU/static PASS + exact preflight PASS. ds: 216/216 + 22/22 independent checks, 0 blocker. Child adds only the tiny harness and its CPU/static tests. No retry is authorized. Full B2-C run02 remains blocked pending fresh review of the GPU Evidence.

## 2026-09-27 — ChatGPT R1-B closure + one B2-C run02 authorization

- R1-B formal root: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- formal child/Gitlink: `8029b5ff002a350d22ee955db0463cc2e2d3665a`
- design authority: `544bbe0976aa60e935eee431350b20f38c47f28c`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_r1b_micro_closure_and_run02_authorization_5cc69c6f_8029b5ff.md`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2C_R1B_TINY_FSDP_MICRO_SMOKE`
- execution authorization: **exactly one full B2-C RTX4090 S1 run02**.

R1-B GPU run01 PASS: Local params were DTensors, B0 evidence remained ordinary Tensors, registered scan/backward completed, visual_proj and slot_queries gradients were finite/non-zero, process group destroyed cleanly. No retry occurred.

Full S1 harness is unchanged from its original approved version. run02 must use execution pair `5cc69c6f... / 8029b5ff...`, new output `artifacts/v3/stage_b2c_4090_s1/run02`, and no retry/fallback. B2-C closure still requires fresh review of run02 Evidence.

## 2026-09-27 — ChatGPT B2-C run02 failure review

- execution formal root: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- child/Gitlink: `8029b5ff002a350d22ee955db0463cc2e2d3665a`
- run: `artifacts/v3/stage_b2c_4090_s1/run02/`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_run02_torchcodec_env_failure_5cc69c6f_8029b5ff.md`
- verdict: `REQUEST_CHANGES`
- no run02 retry authorized.

run02 failed at `episode_source` because TorchCodec could not dlopen `libnppicc.so.13`. The library exists under the V3 venv CUDA13 lib directory; the run omitted that directory from `LD_LIBRARY_PATH`. This happened before model/B0/native-consumer work and is not OOM or a Local/FSDP regression. A dedicated environment preflight is required before any new full run.

## 2026-09-27 — ChatGPT R2 closure + one B2-C run03 authorization

- execution formal root: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- child/Gitlink: `8029b5ff002a350d22ee955db0463cc2e2d3665a`
- R2 design authority: `f798a405de3717abfbbb13812f4db2f79d330224`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_r2_torchcodec_env_preflight_and_run03_authorization_5cc69c6f_8029b5ff.md`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2C_R2_TORCHCODEC_RUNTIME_ENV`
- execution authorization: **exactly one full B2-C RTX4090 S1 run03**.

R2 preflight: 26/26 PASS. Frozen CUDA13 lib path resolves TorchCodec NPP dependencies; official exact CloseFridge ep0 TorchCodec decode succeeds with action [33,15], video [3,33,256,512], step0/step8 raw15 overlap max diff 0.0, no fallback.

run03 must use the same formal pair and unchanged harness, new output `artifacts/v3/stage_b2c_4090_s1/run03`, and prepend the frozen CUDA13 lib path to LD_LIBRARY_PATH. No retry is authorized.

## 2026-09-27 — ChatGPT B2-C run03 failure review

- execution pair: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61 / 8029b5ff002a350d22ee955db0463cc2e2d3665a`
- run: `artifacts/v3/stage_b2c_4090_s1/run03/`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_run03_text_token_failure_5cc69c6f_8029b5ff.md`
- verdict: `REQUEST_CHANGES`
- no run03 retry authorized.

run03 passed the frozen CUDA13/TorchCodec environment, full Stage-A host load, Local-only optimizer setup and real R1-A FSDP Local scan/B0 scan. It failed at native consumer0 because the harness feeds raw `RoboCasaLeRobotDataset` payloads directly to `training_step`; those payloads have `ai_caption` but lack the Stage-A `ActionSFTDataset/ActionTransformPipeline` outputs `text_token_ids` and model-ready prompt/action metadata.

R3 authority: `docs/build/PSM-WMA_V3_stage_b2c_r3_stage_a_text_transform_remediation_design_v0.1_2026-09-27.md`. A new full run requires narrow harness remediation, fresh review, and explicit authorization.

## 2026-09-27 — cx 请求审核 V3 B2-C R3 Stage-A text transform fresh pair

- Gate：`V3-STAGE-B2C-R3-STAGE-A-TEXT-TRANSFORM`；设计 authority root `3091df07983d15f4ecad3a30b27fd721522aede4`，`docs/build/PSM-WMA_V3_stage_b2c_r3_stage_a_text_transform_remediation_design_v0.1_2026-09-27.md`。
- **Formal implementation target**：root `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0`；child/Gitlink `f8b81133f22ab01197b7b36003207cf5cfeb2e41`。此后 Inbox 提交仅为 bookkeeping，不改变 formal target。
- 修复范围：child 仅修改 `examples/psm_wma_robocasa_local_s1.py` 与其测试。保留 raw CloseFridge ep0/索引/raw15 重叠校验；每个原始 payload 的深拷贝经 frozen Stage-A `ActionTransformPipeline`；native callback 接收其 `text_token_ids`、`sequence_plan`、`action_raw` 与 padded64 action。固定 Python seed 0；cfg dropout 仍为 Stage-A 0.1，16 个 consumer 均须保留非空结构化文本。cached latent 不进主 policy forward。
- Evidence：`docs/build/PSM-WMA_V3_stage_b2c_r3_stage_a_text_transform_implementation_2026-09-27.md`；V3 CPU 十文件 207/207 PASS，Stage-A 独立进程 26/26 PASS；真实资产 CPU preflight `/tmp/cx_v3_b2c_r3_preflight_20260927_01/result.json` PASS，consumer0 152 tokens、digest `854e3c085df7ab1b392c0e4960875673123b22e5afd4d051c11c9ac119380aad`，CUDA trace 为空；两文件 Ruff/format 与两仓 diff-check PASS。Stage-A 测试结束后进程全局 grad mode=False，故它与 Local 梯度套件分进程执行。
- 请按 R3 v0.1 对 exact pair 做 CPU/static fresh review，给出明确 `APPROVE` 或 `REQUEST_CHANGES` 及定位到 `file:line` 的意见。ds 独立复核尚未取得；当前请求不授权 RTX4090 run04、8×H100、训练、DCP save、eval 或 Gate closure。run01–run03 Evidence immutable；若后续批准单次 run04，需另行冻结执行命令与全新输出目录。

### R3 同一 formal pair 的补充 CPU Evidence（2026-09-27）

冻结目标仍为 root `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0` / child `f8b81133f22ab01197b7b36003207cf5cfeb2e41`。对不变 child 再执行一次独立真实资产 `--preflight`，新目录 `/tmp/cx_v3_b2c_r3_preflight_20260927_02/` 为 PASS。与首次 `/tmp/cx_v3_b2c_r3_preflight_20260927_01/` 比较：两次 seed0、16 payload、consumer0 完整摘要完全相同；均为 152 tokens，SHA256 `854e3c085df7ab1b392c0e4960875673123b22e5afd4d051c11c9ac119380aad`；两份 CUDA trace 均为空。此补充仅是 CPU Evidence，不更改正式审核 target 或 run04 授权状态。

## 2026-09-27 — ChatGPT R3 closure + one B2-C run04 authorization

- formal implementation root: `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0`
- formal child/Gitlink: `f8b81133f22ab01197b7b36003207cf5cfeb2e41`
- design authority: `3091df07983d15f4ecad3a30b27fd721522aede4`
- detailed review: `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_r3_text_transform_closure_4c128e6a_f8b81133.md`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2C_R3_STAGE_A_TEXT_TRANSFORM`
- execution authorization: **exactly one B2-C RTX4090 S1 run04**.

Independent exact-pair evidence: R3/Local suite 207/207 PASS; Stage-A native contract 26/26 + 10 subtests PASS in a separate process; fresh frozen-asset CPU preflight PASS with consumer0 152 text tokens, SHA256 `854e3c085df7ab1b392c0e4960875673123b22e5afd4d051c11c9ac119380aad`, structured Stage-A JSON prompt, action [33,64], action_raw [33,15], condition action frame [0], and no CUDA work.

run04 must use formal pair `4c128e6a... / f8b81133...`, new output `artifacts/v3/stage_b2c_4090_s1/run04`, the frozen R2 CUDA13 LD_LIBRARY_PATH, and no retry/fallback. run01/run02/run03 remain immutable. B2-C remains REVIEW pending fresh run04 GPU Evidence.


## 2026-09-29 — H3-E Route-B Stage 3A/3B CLOSED; Stage 3C full B1 H5 build authorized

**Formal implementation pair** (bookkeeping commits after this entry do not replace it):

- root: `a707c80393f927e8e30ace877473d475fd24c6cf`
- child/Gitlink: `55582980b992dac10481b0ba9e86cd8075cef33c`

Verdict: `H3E_ROUTE_B_STAGE3B_CLOSED`.

Evidence summary: Stage 3A CPU/static repository gate fully green; Stage 3B repository builder produced exactly
the three authorized CloseFridge episodes with real Wan2.2 latent caches, passed frozen H5 schema,
`RoboCasaLatentReader`, causality, finite-output and no-rewrite resume checks.

**Authorization:** `APPROVE_TO_RUN_H3E_ROUTE_B_STAGE3C_FULL_B1_H5_BUILD`.

Stage 3C must build exactly 9036 production-train H5 caches from
`/mnt/data1/data_v2_0617/robocasa365_official_v30` into
`/mnt/data1/data_v2_0617/robocasa365_official_v30_wan2.2vae_latent_b1`,
then fully validate and recompute the frozen catalog digest. The expected digest remains
`a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`.
A mismatch is fail-closed; do not re-freeze automatically.

Full verdict and acceptance criteria:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_route_b_stage3b_closure_a707c803_55582980.md`.


## 2026-09-29 — Stage 3C BLOCKED on multi-file camera video offsets

Frozen formal pair remains:

- root `a707c80393f927e8e30ace877473d475fd24c6cf`
- child/Gitlink `55582980b992dac10481b0ba9e86cd8075cef33c`

Stage 3C full B1 build exposed a builder-only bug for 43 train episodes in
`SlideDishwasherRack/20250820`: global dataset row offsets were used inside camera video file 1.
Production source/loader remain valid.

Candidate child fix: `ba1996c85cc4de41df2e8bd22c0289ea4deef736` (not formal until CPU + targeted GPU regression passes).

Formal status: `H3E_ROUTE_B_STAGE3C_BLOCKED`.

Review and promotion conditions:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_route_b_stage3c_multifile_video_blocked_a707c803_55582980.md`.


## 2026-09-29 — Stage 3C multi-file fix PROMOTED; full build resume authorized

Formal Stage 3C recovery pair:

- root `16f296cd959820c93ae36e9d8abf16546cd637ea`
- child/Gitlink `ba1996c85cc4de41df2e8bd22c0289ea4deef736`

The prior multi-file camera offset blocker is closed by exact CPU + targeted GPU evidence:
ep461 uses wrist file1 local start 474 derived from per-camera timestamp, and candidate decode is
bit-exact to the production loader.

Verdict: `APPROVE_TO_RESUME_H3E_ROUTE_B_STAGE3C_FULL_B1_H5_BUILD`.

Resume all eight original worker partitions against the existing formal cache output only after
old 55582980 workers have finished or been stopped; never overlap old/new builders on the same
partition/output. Preserve valid H5 files and rely on validation+skip.

Stage 3C closure still requires full 9036 validation and exact manifest digest
`a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`.

Full promotion review:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_route_b_stage3c_multifile_fix_promotion_16f296cd_ba1996c8.md`.


## 2026-09-29 — H3-E Route-B Stage 3C CLOSED; Stage 3D H100 Stage-A warmstart authorized

Formal implementation pair remains:

- root `16f296cd959820c93ae36e9d8abf16546cd637ea`
- child/Gitlink `ba1996c85cc4de41df2e8bd22c0289ea4deef736`

Stage 3C final evidence: 9036/9036 H5 valid, missing/extra/duplicate/invalid all zero, and production
catalog manifest digest exactly
`a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`.

Verdict: `H3E_ROUTE_B_STAGE3C_CLOSED`.

Next authorization:
`APPROVE_TO_RUN_H3E_ROUTE_B_STAGE3D_H100_STAGE_A_WARMSTART`.

Stage 3D must use the existing `examples/psm_wma_robocasa_native.py` Stage-A entrypoint, one
authorized H100, `CloseFridge`, one optimizer iteration, the frozen raw15 contract, and a fresh
H100-local output root. It must stop after producing/validating config.yaml + iter_000000001 DCP.

Full closure and Stage 3D conditions:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_route_b_stage3c_closure_16f296cd_ba1996c8.md`.


## 2026-09-29 — H3-E Route-B Stage 3D CLOSED

Formal implementation pair remains:

- root `16f296cd959820c93ae36e9d8abf16546cd637ea`
- child/Gitlink `ba1996c85cc4de41df2e8bd22c0289ea4deef736`

Verdict: `H3E_ROUTE_B_STAGE3D_CLOSED`.

H100-local Stage-A authority:

- output root: `/mnt/data1/data_v2_0617/psm_wma_v3_stage_a_h100`
- config SHA256: `f64036c499f891979213469523a160ac08cb3d976a2add8d8fdf93750c5a5439`
- iter1 model metadata SHA256:
  `53adef43a58e23f37d1132c4868ea8055be1b095cf76762b2e3e0b69ea287731`

Next gate is H3-E H100 asset rebinding + CPU/preflight. Do not run the 8×H100 H3-E smoke until
that implementation is reviewed and its preflight evidence passes.

Full closure:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_route_b_stage3d_closure_16f296cd_ba1996c8.md`.


## 2026-09-29 — Stage 3E style blocker fixed; H3-F formal budget frozen at 30k

New formal pair:

- root `db08117786a2483ca5cc7f4b58a0c3518e78bccc`
- child/Gitlink `b43097c74982f13e67c071ece729c7b6929cad52`

The prior Stage-3E CPU blocker was only two Ruff-format hunks. Child `b43097c74982f13e67c071ece729c7b6929cad52` fixes
those hunks without changing H100 authority/catalog/preflight semantics.

At owner request, the future RoboCasa H3-F formal training budget is now frozen as:

- `max_iter = 30000`
- checkpoints/eval = `1k,2k,4k,8k,12k,16k,20k,24k,30k`

Historical LIBERO 5000-step records are preserved unchanged. H3-E smoke remains fresh=1,
resume-to-2 and must not be expanded to 30k.

Stage 3E remains pending exact-pair revalidation; no 8×H100 run is authorized yet.

Review:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_stage3e_preflight_format_fix_h3f_30k_budget_db081177_b43097c7.md`.


## 2026-09-29 — H3-E Stage 3E PREFLIGHT CLOSED; 8×H100 fresh smoke authorized

Formal pair remains:

- root `db08117786a2483ca5cc7f4b58a0c3518e78bccc`
- child/Gitlink `b43097c74982f13e67c071ece729c7b6929cad52`

Verdict: `H3E_ROUTE_B_STAGE3E_PREFLIGHT_CLOSED`.

Static + real preflight evidence is fully green: 11 tests, Ruff/format/diff clean, exact H100
Stage-A digests, 9036 catalog, exact manifest digest, and production grouped 8-slot native batch.

Authorization: `APPROVE_TO_RUN_H3E_8XH100_FRESH_ITER0_TO_ITER1`.

Only the fresh 8-rank smoke is authorized. Preserve its exact output for a separately authorized
same-job resume Gate. H3-F remains frozen at max_iter=30000 but is not authorized to start.

Full review:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_stage3e_preflight_closure_db081177_b43097c7.md`.


## 2026-09-29 — H3-E 8×H100 fresh smoke WAITING_FOR_GPU

Formal pair remains:

- root `db08117786a2483ca5cc7f4b58a0c3518e78bccc`
- child/Gitlink `b43097c74982f13e67c071ece729c7b6929cad52`

Status: `H3E_8XH100_FRESH_WAITING_FOR_GPU`.

At the GPU readiness check, all eight H100s were occupied by another user's active 8-rank
training at high utilization. No process was preempted and no H3-E torchrun/output was created.

Once all eight H100s are simultaneously available and authorized, continue directly with the
already-approved fresh iter0→iter1 smoke. Do not rerun earlier Route-B stages or Stage-3E
preflight. Resume iter1→iter2 remains unauthorized until fresh closes.

Review:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_8xh100_fresh_waiting_for_gpu_db081177_b43097c7.md`.


## 2026-09-29 — Owner authorized co-resident 8×H100 fresh smoke

Formal pair remains:

- root `db08117786a2483ca5cc7f4b58a0c3518e78bccc`
- child/Gitlink `b43097c74982f13e67c071ece729c7b6929cad52`

The owner explicitly authorizes using all eight H100s concurrently with the currently resident
wzy training job. Status changes from `WAITING_FOR_GPU` to
`APPROVE_TO_RUN_H3E_8XH100_FRESH_ITER0_TO_ITER1_CORESIDENT`.

Treat the run as a functional integration smoke, not a throughput/performance measurement.
Take a fresh GPU snapshot immediately before launch, do not kill/pause other processes, do not
change geometry, and stop on OOM/system instability.

Only fresh iter0→iter1 is authorized. Resume and H3-F 30k remain unauthorized.

Review:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_8xh100_fresh_co_resident_authorization_db081177_b43097c7.md`.


## 2026-09-29 — H3-E fresh OptimizersContainer blocker fixed

The co-resident fresh launch on the previous pair failed before the first optimizer step because
the H3-E harness accessed `.param_groups` directly on the framework
`OptimizersContainer`.

New exact formal pair:

- root `9bb0d9160f95a1df8081a7c18de3516f0273acfa`
- child/Gitlink `b858106897c17b39888fc1df2b72b189bab5827a`

Fix: unwrap `OptimizersContainer.optimizers`, union inner optimizer param groups, preserve all
existing optimizer inventory checks. Added regression coverage for multi-inner-container,
single optimizer, and empty-container fail-closed behavior.

Status:
`H3E_8XH100_FRESH_ITER1_BLOCKED_FIXED_PENDING_REVALIDATION`.

ds must run the CPU/static + preflight checks on the new pair. If green, fresh iter0→iter1 is
authorized again using a new OUT; preserve the prior failed OUT untouched. Resume remains
unauthorized.

Review:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_8xh100_fresh_optimizer_container_fix_9bb0d916_b8581068.md`.


## 2026-09-29 — grouped trainer OptimizersContainer blocker fixed

Fresh2 on `9bb0d916.../b8581068...` verified the harness fix and completed 32 native
forward + 32 backward events per rank with finite losses and no OOM, then failed before the
optimizer step because `GroupedLocalMemoryTrainer._require_finite_gradients` still accessed
`optimizer.param_groups` directly.

New exact formal pair:

- root `e7dada7d3aff98af110e0bde5e038a09fef8ec82`
- child/Gitlink `910d43d514dfb21aff84b9aaf1db484807f2ff57`

The trainer now normalizes both plain optimizers and `OptimizersContainer.optimizers`, with
fail-closed checks and trainer-level regression tests.

Status:
`H3E_8XH100_FRESH_ITER1_BLOCKED_FIXED_PENDING_REVALIDATION`.

After CPU/static + exact preflight pass, fresh iter0->iter1 is authorized again using a new
fresh3 OUT. Preserve both earlier failed OUTs. Same-job resume and H3-F 30k remain unauthorized.

Review:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_8xh100_fresh_grouped_trainer_optimizer_container_fix_e7dada7d_910d43d5.md`.


## 2026-09-29 — H3-E fresh iter1 CLOSED; same-job resume iter1→iter2 authorized

Formal pair remains:

- root `e7dada7d3aff98af110e0bde5e038a09fef8ec82`
- child/Gitlink `910d43d514dfb21aff84b9aaf1db484807f2ff57`

Verdict: `H3E_8XH100_FRESH_ITER1_CLOSED`.

Fresh3 completed 8/8 ranks with exact 32/32/1/1 events, finite losses/gradients, one optimizer
step, one Local/frontier commit, and complete iter1 DCP including dataloader rank0..7 state.

The rank4-7 zero local witness for `slot_queries` is accepted as an empty local shard artifact
of sharding a 4-row tensor across 8 ranks; the global gradient is non-zero.

Authorization:
`APPROVE_TO_RUN_H3E_8XH100_SAME_JOB_RESUME_ITER1_TO_ITER2`.

Resume must use the exact same fresh3 OUT/job and formal pair. Do not create a new job for
resume. H3-F 30k remains unauthorized.

Review:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_8xh100_fresh_iter1_closure_e7dada7d_910d43d5.md`.


## 2026-09-29 — H3-E CLOSED; H3-F 30k launcher implemented

H3-E is fully CLOSED on:

- root `e7dada7d3aff98af110e0bde5e038a09fef8ec82`
- child `910d43d514dfb21aff84b9aaf1db484807f2ff57`

Fresh iter1 and same-job resume iter2 both passed. No iter3 smoke is required.

H3-F has now been implemented on a new formal pair:

- root `eeb869d0f2c65d9f9f4cfc86f1c99afb0d378052`
- child/Gitlink `a71c7be99f8d485f3066128c34d210ef709a1440`

New launcher:
`examples/psm_wma_robocasa_h3f.py`

Formal contract: 8×H100, 8 slots/rank, T16, GA2, K4, max_iter=30000, scheduler cycle=30000,
warmup=500, save every 1000, primary eval checkpoints
1k/2k/4k/8k/12k/16k/20k/24k/30k.

The H3-F launcher has its own long-run config digest, O(steps) progress observer, same-job
resume attempt identity, and rank0+barrier evidence-directory publication.

Status:
`H3F_LAUNCHER_IMPLEMENTED_PENDING_READINESS`.

Next action for ds is CPU/static + exact read-only H3-F preflight + disk/checkpoint-size/timing
budget evidence. Do **not** start the 30k run yet.

Reviews:
- `docs/collab/chatgpt/reviews/2026-09-29_V3_h3e_overall_closure_e7dada7d_910d43d5.md`
- `docs/collab/chatgpt/reviews/2026-09-29_V3_h3f_30k_launcher_design_implementation_eeb869d0_a71c7be9.md`


## 2026-09-29 — H3-F CPU Ruff I001 blocker fixed

New exact H3-F formal pair:

- root `7301046714d0adf2dc2ec5e612df5405a4c330d5`
- child/Gitlink `e3e62b10b5939447bb6447a731187969853269e2`

Previous CPU result: 27 pytest PASS; only blocker was Ruff I001 import ordering in
`examples/psm_wma_robocasa_h3f.py`.

The fix is style-only: `config_digest as h3e_config_digest` is moved into the separate import
block Ruff requested. No training contract or runtime logic changed.

Continue the H3-F readiness gate from CPU/static on this new pair. If CPU/static is green,
continue with read-only preflight, storage budget, and timing budget. Do not launch 30k yet.

Review:
`docs/collab/chatgpt/reviews/2026-09-29_V3_h3f_cpu_import_order_fix_73010467_e3e62b10.md`.


## 2026-09-30 — H3-F CPU formatter round2 fixed

New exact formal pair:

- root `91c8d187074c9f7262d539688708bf9ed06f9f97`
- child/Gitlink `b42e325be45a62b93c7c89d3d61af1045e4167a9`

Previous pair already had 27/27 pytest PASS and Ruff check PASS. The only blocker was
`ruff format --check` on two test function signatures. This is a style-only fix.

Re-run full CPU/static. If all green, continue directly with H3-F read-only preflight, checkpoint
storage sizing, and steady-step timing budget. Do not start the 30k GPU run yet.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_cpu_format_round2_fix_91c8d187_b42e325b.md`.


## 2026-09-30 — H3-F owner launch facade implemented

New exact formal pair:

- root `a70fa27bfc4967462301e3ac13df03e9bb7b5c12`
- child/Gitlink `d7ee697df5800be3c6fda90de23ea4014ff34a90`

Owner-facing entry point now exists:

`examples/launch_sft_action_policy_robocasa_edge_all_target_atomic.sh`

It drives the current grouped H3-F trainer through 8-rank torchrun and supports same-job
fresh/resume semantics.

The owner environment variables are now first-class launch/preflight inputs, including
ROBOCASA_ROOT, latent cache, BASE_CHECKPOINT_PATH, Edge, VAE, OUTPUT_ROOT, CUDA devices,
ROBOCASA_NUM_WORKERS, SAVE_ITER and TTT_ACTIVE_GA.

SAVE_ITER is now a real formal runtime input (default 500), is applied to checkpoint cadence and
included in the config digest. No automatic retention was added.

Owner OUTPUT_ROOT under the ignored root worktree `outputs/` subtree is explicitly supported.

Status:
`H3F_OWNER_LAUNCH_IMPLEMENTED_PENDING_REVALIDATION`.

Next ds action: full CPU/static + bash -n + exact preflight + 10-step H3-F readiness smoke.
Do not start the 30k long-run yet.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_owner_launch_contract_a70fa27b_d7ee697d.md`.


## 2026-09-30 — H3-F owner launch formatter blocker fixed

New exact formal pair:

- root `422899072dce46a1602ea76ef767d498c709f469`
- child/Gitlink `00241445e17bccbec63f9c29ee75531712bc3de1`

Previous pair already had 32 pytest PASS and Ruff check PASS. The only blocker was
`ruff format --check` on the H3-F launcher and test file.

This is formatter-only; no runtime/training semantics changed.

Please re-run full CPU/static on the new pair. If green, continue the previously authorized
owner-env preflight → 10-step readiness smoke → fail-closed matrix. Do not start the 30k run.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_owner_launch_format_fix_42289907_00241445.md`.


## 2026-09-30 — H3-F formal profile switched to Reasoner + Local-TTT

New exact formal pair:

- root `5c643045534fa080612239a6ba752a55226ef6c3`
- child/Gitlink `69dcb48fa0e188f95d43590300dad7542b6a9ab5`

H3-F no longer trains the H3-E generation/action host selector.

Formal H3-F now trains exactly:

- `net.language_model.*` excluding `*_moe_gen`;
- `net.local_memory*`.

The action/generation host path is frozen.

The H3-F config digest binds this trainable profile, the optimizer inventory checks exact equality,
and the readiness observer now requires a non-zero Reasoner gradient witness in addition to the
Local gradient witness.

Status:
`H3F_REASONER_TTT_PROFILE_IMPLEMENTED_PENDING_REVALIDATION`.

Please re-run CPU/static + owner-env preflight + short readiness smoke on this exact pair. Do not
start the 30k long-run yet.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_reasoner_plus_ttt_trainable_profile_5c643045_69dcb48f.md`.


## 2026-09-30 — old H3-F readiness10 accepted only for old trainable profile

The evidence on:

- root `422899072dce46a1602ea76ef767d498c709f469`
- child `00241445e17bccbec63f9c29ee75531712bc3de1`

is accepted as:

`H3F_OWNER_LAUNCH_READINESS10_CLOSED_FOR_OLD_PROFILE`.

It validated the owner facade, grouped runtime, 10-step execution, DCP, fail-closed matrix, and
provided useful timing/memory evidence.

However, that run still trained the old H3-E-derived generation/action + Local profile.

The current formal H3-F pair is:

- root `5c643045534fa080612239a6ba752a55226ef6c3`
- child `69dcb48fa0e188f95d43590300dad7542b6a9ab5`

and now trains Reasoner + Local-TTT only.

Therefore the 30k run remains blocked. Re-run CPU/static + exact preflight + short readiness on
the current pair, with explicit evidence for Reasoner optimizer inventory and non-zero Reasoner
gradient.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_old_profile_readiness10_closure_and_current_revalidation_gate.md`.


## 2026-09-30 — Reasoner+Local-TTT formatter blocker fixed

New exact formal pair:

- root `970c50c1d8cd1975c822f672afa823f2a8ea7573`
- child/Gitlink `b72c7bd1c53e3767d69dd10c2223fa5057259738`

Previous pair already had 34 pytest PASS, Ruff check PASS, bash -n PASS, diff-check PASS, and clean
worktrees. The sole blocker was Ruff formatting of two set-comprehensions.

This commit is formatter-only. Re-run full CPU/static; if green, continue owner preflight →
Reasoner+Local-TTT readiness10 → fail-closed matrix. Do not start the 30k run.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_reasoner_ttt_format_fix_970c50c1_b72c7bd1.md`.


## 2026-09-30 — Reasoner+Local-TTT formatter round2 fixed

New exact formal pair:

- root `6f9b693fe51882b02d4ac2a55bdfeeba9644d861`
- child/Gitlink `380ba039ea19f314dd1c7cd9e6b94fc01f131f59`

Only the Ruff-stable multiline formatting of `forbidden_host` changed. Previous pair already
had 34 pytest PASS and Ruff check PASS. Re-run full CPU/static; if green, continue owner preflight
→ Reasoner+Local-TTT readiness10 → fail-closed matrix. Do not start formal 30k yet.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_reasoner_ttt_format_round2_6f9b693f_380ba039.md`.


## 2026-09-30 — H3-F switched to V2-semantic generation + Local-TTT

New exact formal pair:

- root `759f04fe2321dae27ac02d07eb80df0e6bb5d138`
- child/Gitlink `fdde28b37b25fe29b1dd550b41ec7b37845ba371`

Owner decision applied:

- align trainable modules with V2 RoboCasa Local-TTT generation+local;
- DO NOT align the dataset/action contract to V2.

Formal trainables now use generation/action keys plus the V3-equivalent Local four blocks.
Reasoner is frozen.

The current V3 dataset remains official_v30 / 9036 / raw15 / manifest a8cad3f0..., and the current
H100 dp_shard8 mesh remains unchanged.

Previous Reasoner+Local readiness evidence is invalidated by this profile change.

Please run CPU/static -> owner preflight -> readiness10 -> fail-closed matrix on this exact pair.
Do not start the 30k run.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_v2_semantic_generation_local_profile_759f04fe_fdde28b3.md`.


## 2026-09-30 — generation+Local formatter blocker fixed

New exact formal pair:

- root `e272a589ce2204f5b4324e79c0f1227d855f3e97`
- child/Gitlink `f89876a4bb013d9a48d622db776996ded295884b`

Only three Ruff-formatting changes were made in the H3-F launcher. Previous pair already had 25
pytest PASS, Ruff check PASS, bash-n PASS, diff-check PASS, and clean worktrees.

Re-run complete CPU/static. If green, continue owner preflight -> generation+Local readiness10 ->
fail-closed matrix. Do not start formal 30k yet.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_generation_local_formatter_fix_e272a589_f89876a4.md`.


## 2026-09-30 — H3-F generation+Local readiness10 CLOSED; formal 30k authorized

Accepted exact formal pair:

- root `e272a589ce2204f5b4324e79c0f1227d855f3e97`
- child/Gitlink `f89876a4bb013d9a48d622db776996ded295884b`

Verdict:

`H3F_OWNER_LAUNCH_READINESS10_CLOSED_FOR_V2_SEMANTIC_GENERATION_LOCAL`

Long-run Gate:

`APPROVE_TO_START_H3F_FORMAL_30K_V2_SEMANTIC_GENERATION_LOCAL`

The 8×H100 readiness passed 8/8 ranks with exact generation+Local inventory, selected Local
params=165312, selected reasoner params=0, non-zero generation/action/Local gradient witnesses,
finite losses, complete iter10 DCP, and full fail-closed matrix.

The formal training contract remains official_v30/raw15, not V2 ego20D.

Operationally, SAVE_ITER=500 remains owner-managed retention. The observed readiness median was
~139.4 s/optimizer step, so the 30k job is a multi-week run; use the frozen milestone checkpoints
as evaluation/recovery control points.

Review:
`docs/collab/chatgpt/reviews/2026-09-30_V3_h3f_v2_semantic_generation_local_readiness10_closure_and_30k_gate.md`.


## 2026-10-04 — V3 RoboCasa Local-TTT current-frame evidence remediation

New exact formal implementation pair:

- root `fc453ef7967cced3323ddf40ac480538c2a0ec19`
- child/Gitlink `da6a9b972575af829af63e7747fad2fd73ae8157`

ChatGPT fixed the V3 RoboCasa online Local-TTT evidence path.

The previous implementation re-encoded the growing episode RGB prefix. The new implementation
uses the existing model VAE authority and encodes only completed **current frames** with temporal
length T=1. Future 4x4-frame training labels are not reconstructed at inference. Episode-long RGB
history storage was removed; exact replay keeps only the last committed visual digest/summary and
raw15 batch.

Evidence protocol is now:

- `current_frame_visual96_executed_action15_v4`
- `robocasa_current_left_wrist_raw15_v2`

Tests cover replan evidence counts 4 / 8 / 16.

ds / ds_pro: **do not modify code**.

Authorized execution only:

1. sync this exact pair;
2. run relevant CPU/static tests;
3. run minimal iter500 RoboCasa required-mode smoke;
4. verify adapted_steps for action_horizon/replan 4, 8 and 16;
5. record GPU memory after server load and across replans to confirm it no longer grows with episode history;
6. only if green, rerun the same 18 target-atomic x seed0 screening and preserve MP4s/task results.

Do not continue long training before this Gate returns.

Detailed review:
`docs/collab/chatgpt/reviews/2026-10-04_V3_robocasa_current_frame_local_evidence_fc453ef7_da6a9b97.md`.


## 2026-10-04 — V3 migration authority refreeze; iter500 B1 causal streaming

New exact formal implementation/design pair:

- root `3e86f2b178b9f1e77603716217a487b18f0c4ee8`
- child/Gitlink `c00a014444083c7c554fff7626f48cceaf5c5c31`

Canonical design:

`docs/build/PSM-WMA_V3_migration_detailed_design_v1.1_2026-10-04.md`

Formal verdict:

`REQUEST_CHANGES`

This is **Evidence-only**. Current source review found no production semantic blocker.

Important correction:

- The previous pair `fc453ef7... / da6a9b97...` and its per-frame-T=1 execution Gate are superseded.
- Do **not** run that old Gate.
- iter500 remains the required checkpoint; **do not retrain**.
- H3-F training ABI remains raw15 / T16 / K4 / generation+Local. No parameter/checkpoint ABI changed.

The corrected online Local evidence now reproduces the B1 training distribution:

- endpoint0 = one-frame prime;
- endpoint4/8/12/... = four newly observed frames per camera through causal Wan streaming;
- intermediate source steps reuse the latest endpoint visual96;
- left and wrist are independent VAE streams batched on B;
- no episode-length RGB history is retained;
- VAE stream candidate + Local fast-state candidate are transactional with generation success.

Shared authorities are now centralized for endpoint policy, visual96, normalization, wire protocol and
Wan stream-state lifecycle.

ds / ds_pro: **execution and Evidence only; do not modify code.**

Run in this order on the exact pair above:

1. CPU/static:
   - `cosmos_framework/model/generator/mot/robocasa_latent_evidence_test.py`
   - `cosmos_framework/model/generator/tokenizers/wan2pt2_vae_stream_state_test.py`
   - `cosmos_framework/inference/robocasa_local_memory_policy_test.py`
   - `cosmos_framework/inference/local_memory_online_test.py`
   - `cosmos_framework/simulation/robocasa/local_memory_client_test.py`
   - `cosmos_framework/simulation/robocasa/closed_loop_eval_contract_test.py`
   - `tools/v3/build_robocasa_b1_h5_cache_test.py`
   - Ruff check/format on changed files, root/child diff-check, and Python syntax check for
     `scripts/eval_robocasa_18task_queue.py`.

2. Real Wan observational parity:
   - run `tools/v3/verify_robocasa_b1_streaming_parity.py` on one known frozen train episode;
   - first run **without** `--max-fp16-abs`;
   - return the report with per-endpoint fp16 and visual96 diffs;
   - do not invent a threshold locally.

3. After ChatGPT/owner freezes a numeric tolerance from that evidence, rerun parity with the frozen
   threshold and obtain PASS.

4. iter500 required-mode RoboCasa closed-loop smoke for `ACTION_HORIZON=4`, `8`, and `16`:
   - adapted_steps equals newly completed evidence count;
   - prefix present after cold start;
   - fast_state_norm / inner_loss_mean finite;
   - no replay/reset/chronology error;
   - record server GPU memory across increasing replans and show a bounded plateau.

5. Only after 1-4 are GREEN, run the 18 target-atomic × fixed seed0 screening with:
   `scripts/eval_robocasa_18task_queue.py`
   using 8 GPUs and the same iter500 checkpoint.

Preserve:

- all rollout MP4s;
- per-task `results.json`;
- queue `screening_summary.json`;
- server/eval logs;
- parity report;
- GPU-memory observations.

Do not continue/restart formal training under this Gate.

Detailed review:

`docs/collab/chatgpt/reviews/2026-10-04_V3_migration_iter500_b1_streaming_3e86f2b1_c00a0144.md`.


## 2026-10-04 — Owner-confirmed Corrected V3 Detailed Design v3.0 published; old B1/iter500 Gates superseded

Formal design target (not an implementation approval):

- root design SHA: `32c02bf6e295bdecf333b89619a07ac213600f53`
- unchanged child/Gitlink SHA: `c00a014444083c7c554fff7626f48cceaf5c5c31`
- document: `docs/build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md`
- review: `docs/collab/chatgpt/reviews/2026-10-04_V3_design_v3.0_review_32c02bf6_c00a0144.md`

Owner has confirmed the design item-by-item and requested recheck/publication only.
The v3.0 document retains all 61 items, clarifies H_pred/R/T, exact V2 visual96 pooling,
pre-action/completed chronology, official env12 ordering/mode/clipping, cache corpus reporting,
and the distinction between absent future ground truth and model-generated/noise future slots.

Current operative contract:

- latest official Cosmos RoboCasa/raw15 host; V2 Local-TTT functional donor;
- training corpus is determined by the specified local latent cache, not raw-dataset enumeration;
- one composite `[left|wrist] -> VAE` definition shared by Policy and Local;
- cache default: 17 frames -> current latent + 4 future latents; Local consumes current only;
- inference encodes only current observed frame (T_pixel=1), reuses the same z_t, no B1 streaming;
- H_pred/chunk_length default16 and eval R/replan_steps default16; T independently configurable;
- direct-DROID -> Local-TTT training, no native-training prerequisite;
- iter500 is excluded from Corrected V3 initialization/evaluation; preserve all historical artifacts;
- prefer zero modifications to cosmos-framework; enumerate any necessary minimal seam before implementation;
- print and persist actual accepted corpus/task/episode/window/consumer statistics at startup;
+- W0 is model state; per-slot W_t is episode runtime and separate training-resume state.

Supersession:

All earlier B1 dual-camera/causal-endpoint/streaming and iter500 reuse execution instructions in this
ledger are historical. In particular, the fc453ef7/da6a9b97 and 3e86f2b1/c00a0144 Gates MUST NOT be
continued under their old design. Earlier statements that c00a0144 had only Evidence blockers do
not apply under the newly confirmed v3.0 contract: its visual implementation still needs migration.

Implementation-conformance verdict on the unchanged child: `REQUEST_CHANGES`.
This does not reject publication of the Owner-confirmed design; it prevents mistaking documentation
publication for production conformance, training approval, or an SR result.

Scope of this handoff:

- ChatGPT is the sole code/official-test/commit/push/gitlink modification authority; ds/ds_pro only execute
  explicitly authorized tests and collect Evidence, never repair code.
- No production code, child ref/gitlink, training data, checkpoints or experiment outputs are modified
  by this design publication.
- Next permitted planning work is exact V2/upstream file mapping and listing the required extension
  seams. Actual implementation/execution remains subject to the Owner-aligned phase/Gate scope.
- No GPU run, new long training, native ablation, cache rebuild, checkpoint deletion or iter500 retry
  is authorized by this entry.

This entry is append-only; earlier ledger history is preserved as historical evidence.


## 2026-10-05 — Corrected V3 Phase 0 implementation mapping；请求 GPT/Owner 审核

- Gate：`V3-CORRECTED-PHASE0-MAPPING`；**formal docs-only root**：`7a0cb5ef20fa08efcbefb749d8ed19b312cf99d0`；**unchanged child/Gitlink**：`c00a014444083c7c554fff7626f48cceaf5c5c31`。
- 唯一设计 authority：`docs/build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md`；提交的 evidence/mapping：`docs/build/PSM-WMA_V3_corrected_implementation_mapping_v0.1_2026-10-04.md`。
- 对照固定 official upstream `cf5d68c00d97ccd2480a2320ed652b92dec63102` 与 V2 donor `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92`。文档逐文件列 KEEP/ADAPT/RETIRE/ADD WRAPPER、现状、authority、改动原因、测试与 core seam，并列 A–J、阶段顺序、旧 B1/iter500 退出和待裁决冲突。
- 请重点审核：cache-first corpus 的实际 schema 尚待只读核验；fixed upstream 缺 `video_latent` cache-hit；B1 mean/RMS 与 V2 pool 不等价；`env.step` 前 evidence 与 completed-only 冲突；H_pred32/T16 固定点、executed raw15 canonicalization；候选最小 upstream seam 是否准确。
- 验收范围：只确认 Phase 0 mapping 与最小 seam/冲突清单是否足以指导分阶段实施；请给 `APPROVE_PHASE0_MAPPING_ONLY` 或 `REQUEST_CHANGES(file:line)`，并对未决项给出裁决。**不请求**生产实现批准、Gitlink 更新、GPU/训练/仿真/评测或旧 B2-B/iter500 Gate 复活。
- 最新 Owner 角色：GPT 设计/审核，cx 负责实现、正式测试与提交，ds/ds_pro 仅执行/Evidence。此条取代上一历史 ledger 中 ChatGPT 独占代码/提交权的旧口径。Phase 0 child production/test/Gitlink 未变；root formal diff 仅 mapping、TODO、SESSION。


## 2026-10-05 — Corrected V3 Phase 0 mapping 修订；以新 exact pair 为准

- Gate：`V3-CORRECTED-PHASE0-MAPPING`。**新 formal docs-only root**：`ad2817a5cd323cf37c2354cbaf81cba6fe35edf4`；**unchanged child/Gitlink**：`c00a014444083c7c554fff7626f48cceaf5c5c31`。前一申请 root `7a0cb5ef20fa08efcbefb749d8ed19b312cf99d0` 已被本次修订取代，请勿按旧 SHA 给当前 mapping verdict。
- mapping/evidence：`docs/build/PSM-WMA_V3_corrected_implementation_mapping_v0.1_2026-10-04.md`；authority 仍为 v3.0 设计。新 formal diff 仅此 mapping 与 SESSION，child production/test/Gitlink 未动。
- 修订 1：固定 upstream `cf5d68c` 中官方 `action_policy_robocasa_nano.py`/transforms 列 KEEP UP；当前 `action_policy_robocasa_edge.py` 明确列为项目 ADAPT/replace wrapper，fixed upstream 无此文件。
- 修订 2：逐文件列 `local_memory_grouped_window.py` 的 T16/8 slot/GA2 固定点及 `trainer/local_memory_grouped.py` 的 GA2 固定点；关联 `robocasa_grouped_segment.py`，要求 T16/32 真正可运行，B_stream/GA 默认 8/2 但独立配置，不从 T16 常量派生。
- 请 GPT/Owner 对新 exact pair 给 `APPROVE_PHASE0_MAPPING_ONLY` 或 `REQUEST_CHANGES(file:line)`；只审核 docs-only mapping 与冲突/seam 清单。本请求不授权 production/test/Gitlink 修改、GPU、训练、仿真、评测或旧 B2-B/iter500 Gate。

## 2026-10-05 — Corrected V3 Phase 0 mapping 第二轮修订；请求 GPT 审核新 exact pair

- Gate：`V3-CORRECTED-PHASE0-MAPPING`。**新 formal docs-only root**：`2c6d99b6a6cd0e8dc87bd4aa2713919f071b181f`；**unchanged child/Gitlink**：`c00a014444083c7c554fff7626f48cceaf5c5c31`。本请求取代前一 mapping root `ad2817a5cd323cf37c2354cbaf81cba6fe35edf4` 的审核目标；正式 verdict 请只锚定新 exact pair。
- 唯一设计 authority：`docs/build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md`；本轮证据/审核对象：`docs/build/PSM-WMA_V3_corrected_implementation_mapping_v0.1_2026-10-04.md`。Owner 指明先前三条 tmux 意见为 GPT 对旧 mapping 的 direct review findings，可直接作 docs-only 修订；正式 review 文件由 GPT 在本新 root 后处理。
- 修订 ①：`local_memory_grouped_window.py` 当前逐 slot 完整 scan 已明确列为偏差；目标是同一局部 index 跨 `B_stream` slot 一次 batched fast-update、T 维串行、每行独立 W_t/PAD，保留 row-mean 后求和及有效 consumer reduction。验收加入 scalar-vs-batched 逐步 inner loss/W_t/token/outer loss 与 W0/KQV/encoder/host 梯度 parity。
- 修订 ②：推理 correctness 默认对每个 completed pre-action composite 用同一 preprocessing 与同一 VAE helper 做 `T_pixel=1` Encode1；匹配 RGB 的 offline Encode17[0] parity 必验。暴露 policy current-z callback 仅是同值复用的 optional optimization。训练 `video_latent` cache-hit 仍是必要最小功能 seam，cache miss fail-closed。
- 修订 ③：加入 dataset→`ActionSFTDataset`→`ActionTransformPipeline`→grouped binder/model 的 `video_latent` key/shape/dtype/window identity 传递测试；`robocasa_grouped_segment.py:434,452` 当前拒绝 raw/transformed `video_latent` 的 guard 必须改为 cache-required。
- 自检：`git diff --check` PASS；`git diff-tree --no-commit-id --name-only -r 2c6d99b6a6cd0e8dc87bd4aa2713919f071b181f` 仅 mapping、SESSION、TODO；child worktree 与 Gitlink 未变。未运行项目代码、正式测试、GPU、训练、仿真，也未访问训练服务器。
- 请 GPT 对新 exact pair 给出 `APPROVE_PHASE0_MAPPING_ONLY` 或 `REQUEST_CHANGES(file:line)`，重点确认上述三条闭合及逐文件最小 seam。审核仅限 docs-only Phase 0 mapping；不请求生产/test/Gitlink 修改批准，不授权 GPU/训练/仿真/评测或旧 B2-B/iter500 Gate。角色：GPT 设计/审核，cx 实现/正式测试/提交，ds 执行/Evidence。

## 2026-10-05 — Corrected V3 Phase 0 mapping server-side 职责修正；请求 GPT 审核最新 exact pair

- Gate：`V3-CORRECTED-PHASE0-MAPPING`。**最新 formal docs-only root**：`08bda92f5d837377dd9ef83b78fc2f4bbaf70626`；**unchanged child/Gitlink**：`c00a014444083c7c554fff7626f48cceaf5c5c31`。此条取代前一 root `2c6d99b6a6cd0e8dc87bd4aa2713919f071b181f` 的审核目标；前一请求的 bookkeeping SHA `abb527e2` 不作为 verdict authority。
- 审核对象：`docs/build/PSM-WMA_V3_corrected_implementation_mapping_v0.1_2026-10-04.md`；设计 authority：`docs/build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md`。此前三项 direct findings 已在前一 root 写入，本新 root 保留其全部内容，另按 Owner 补充修正 simulator/server 职责。
- 新修正：`local_memory_client.py` 只保留 pre-action composite RGB，`env.step` 成功后把 composite + canonical executed raw15 标为 completed 并发送；不导入、不运行 Wan VAE。模型/VAE 所在进程的 server-side `robocasa_local_memory_policy` adapter 才以同一 preprocessing/VAE helper 对 completed composite 做 `T_pixel=1` Encode1，再按序提交 Local。Phase 6 和验收加入 client 无 VAE 依赖、失败步零发送/零 Local 更新、server Encode17[0]/Encode1 parity。
- 自检：`git diff --check` PASS；`git diff-tree --no-commit-id --name-only -r 08bda92f5d837377dd9ef83b78fc2f4bbaf70626` 仅 mapping、SESSION、TODO；child production/test/Gitlink 未动。未运行项目代码、正式测试、GPU、训练、仿真；未访问训练服务器。
- 请 GPT 仅对最新 exact pair 给 `APPROVE_PHASE0_MAPPING_ONLY` 或 `REQUEST_CHANGES(file:line)`，确认三条 direct findings 与本次职责边界均闭合。本申请不授权 production/test/Gitlink 修改、GPU/训练/仿真/评测或旧 B2-B/iter500 Gate。角色：GPT 设计/审核，cx 实现/正式测试/提交，ds 执行/Evidence。

## 2026-10-05 — Corrected V3 Phase 0 exact-duration 修订；请求 GPT 审核最新 exact pair

- Gate：`V3-CORRECTED-PHASE0-MAPPING`；**最新 formal docs-only root**：`861849491488258214e96e778cff7d1bd0309089`；**unchanged child/Gitlink**：`c00a014444083c7c554fff7626f48cceaf5c5c31`。此条取代前一 mapping root `08bda92f5d837377dd9ef83b78fc2f4bbaf70626` 的审核目标；此前 Inbox bookkeeping SHA 不作 verdict authority。
- 审核对象：`docs/build/PSM-WMA_V3_corrected_implementation_mapping_v0.1_2026-10-04.md`；唯一设计 authority：`docs/build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md`。
- Owner 本轮补充的必要项：current 项目 Edge wrapper `action_policy_robocasa_edge.py:23` 固定 `tokenizer.encode_exact_durations=[33]`，H100 `psm_wma_robocasa_h100.py:265` 亦要求 `[33]`。V2 donor `vision_vae.py:12` 与 RoboCasa exact-window builder 的参考 contract 为 `[17,61,73]`；corrected H_pred16 的 17 帧窗口要求有效 exact durations 至少含17，且 resolved config/实际 VAE helper 与指定 cache manifest 的 `vae_encode_contract`（dtype、exact durations、chunk frames 等）及 fixed tokenizer 能力精确匹配。实际完整列表必须以真实 manifest 为准，禁止只改 chunk16、猜列表、cache miss 在线回退或为适配配置重新编码。
- mapping 已在 Edge overlay、H100 入口、default32 污染及 Phase 2–3 验收中列明以上要求；先前 B_stream batched scan、server-side Encode1、`video_latent` 透传/guard 修订保持。`git diff --check` PASS；formal `git diff-tree --no-commit-id --name-only -r 861849491488258214e96e778cff7d1bd0309089` 仅 mapping、SESSION、TODO；child production/test/Gitlink 未动，未运行项目代码、正式测试、GPU、训练、仿真，未访问训练服务器或实际 cache manifest。
- 请 GPT 对新 exact pair 给 `APPROVE_PHASE0_MAPPING_ONLY` 或 `REQUEST_CHANGES(file:line)`，重点确认 exact-duration authority 与 manifest/fixed tokenizer 校验的映射。本申请仅审核 docs-only Phase 0，不授权 production/test/Gitlink、GPU/训练/仿真/评测或旧 B2-B/iter500 Gate。角色：GPT 设计/审核，cx 实现/正式测试/提交，ds 执行/Evidence。

## 2026-10-05 — Corrected V3 Phase 1A cache catalog implementation；请求 GPT fresh review

- Gate：`V3-CORRECTED-PHASE1A-CACHE-CATALOG`；**formal root**：`7c214251f3535116e7b19f964ee907e8653fd388`；**formal child/Gitlink**：`e98f293f396df74bb7030d525c40faa21e7d226d`。child 已先推送 `v3-local-ttt`，root 后推送 `V3`。前置 Phase0 mapping root `861849491488258214e96e778cff7d1bd0309089` 的 GPT review 为 `APPROVE_PHASE0_MAPPING_ONLY`；本条请求新 pair 的独立审核，不继承旧 verdict。
- 任务范围与 authority：`/tmp/CX_PHASE1A_CORRECTED_V3_CACHE_CATALOG.md`、v3.0 详细设计 §6/10–13/60、Phase0 mapping 的 Phase1 行。证据文件：child `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py` 与同目录 `robocasa_exact_window_cache_test.py`；root `SESSION.md`、`TODO.md`、Gitlink。formal child diff 仅两个新增文件；formal root diff 仅 SESSION/TODO/Gitlink。
- 实现：仅从 `dataset_manifest.json` 构建 exact_window_v1 cache-first catalog，推导可移植 episode 路径；验证 manifest 核心合同/身份、必需文件和所有 `tasks/*/episodes/episode_*.pt` 的额外文件；保留完整 VAE contract，要求 exact durations 含17；提供 manifest SHA、排除机器路径的语义 corpus digest、task/episode/window/effective consumer/unique-frame 统计。首次按需读取 episode 时验证 payload，精确 start key、finite fp32 `[5,48,H,W]`、17 帧与 5 anchors；无 raw dataset enumeration、VAE fallback 或 B1 endpoint。
- GPT early findings 已处理且有定向测试：`episodes` 公开排序 records 而非 keys；未声明 task 目录的 episode payload 计为 extra，strict fail-closed。另覆盖缺/空 compute_dtype、非法 encode_chunk_frames，以及 source_video_frames/window_count 不一致。
- cx synthetic tmp_path CPU 自测：指定测试文件 `57 passed`（既有 V3 venv、`-o addopts=''`、CPU/离线）；两文件 Ruff check、Ruff format --check 与 child staged/root diff-check PASS。系统 pytest 缺 `omegaconf` 和禁插件导致 conftest hook 失败的两次预备尝试已在 SESSION 记录；最终不改配置即通过。尚无 ds 独立测试、真实 cache manifest/schema 或 runtime 性能证明。
- 请 GPT 对 exact pair 给出 `APPROVE_PHASE1A_CACHE_CATALOG_ONLY` 或 `REQUEST_CHANGES(file:line)`，检查 manifest/episode/window fail-closed、统计/digest 与任务 12 条验收。仅请求 Phase1A review；不请求 Phase1B source binder、ActionSFT/OmniMoTModel/trainer/inference/server/eval 修改，不授权训练服务器访问、cache 重建、GPU、训练或仿真。GPT=设计/独立审核，cx=实现/正式测试/提交，ds=后续执行/Evidence。

## 2026-10-05 — Corrected V3 Phase 1A cache payload audit 修复；请求 GPT fresh source review

- Gate：`V3-CORRECTED-PHASE1A-CACHE-CATALOG`；**新 formal root**：`459ff4bd30959cba916813c30c85faf51fad1db0`；**新 formal child/Gitlink**：`a40e8b782e0692e0a24e2f60893e9f4f8d858961`。本请求取代旧 pair `7c214251f3535116e7b19f964ee907e8653fd388` / `e98f293f396df74bb7030d525c40faa21e7d226d`；旧 `APPROVE_TO_RUN_PHASE1A_CPU_STATIC_EVIDENCE_ONLY` 已被 r2 `REQUEST_CHANGES` 撤销，不能用于 ds 执行。
- 审核依据：`docs/collab/chatgpt/reviews/2026-10-05_V3_phase1a_cache_catalog_source_review_r2_7c214251_e98f293f.md`（原样纳入新 formal root）；设计 authority 为 v3.0 详细设计、Phase0 mapping 与 `/tmp/CX_PHASE1A_CORRECTED_V3_CACHE_CATALOG.md`。唯一 source blocker 是 `_audit_files` 曾只扫描 canonical `episode_*.pt` 并跳过 malformed 文件名。
- child 仅修改 `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py` 与同目录 `_test.py`：现在审计 `tasks/*/episodes/*.pt` 全部 payload；未声明 canonical episode、`episode_bad.pt`、`episode_7.pt`、`foo.pt` 均计 extra，strict fail-closed，non-strict 统计可见。新增后三类逐一 strict/non-strict 定向测试。未改其它 child 文件；root formal diff 仅 Gitlink、SESSION、TODO 与原样 r2 review。
- cx 合成 `tmp_path` CPU 自测：target pytest `60 passed`；两文件 Ruff check、Ruff format --check、child staged/root staged diff-check PASS。未访问真实 cache/训练服务器；无 ds 独立 Evidence、GPU、训练、仿真。证据见 child 两文件与 root SESSION。
- 请 GPT 对上述**新 exact pair** 审核 r2 blocker 是否闭合，给出 fresh `APPROVE_TO_RUN_PHASE1A_CPU_STATIC_EVIDENCE_ONLY` 或 `REQUEST_CHANGES(file:line)`。仅请求 Phase1A source review；未请求 Phase1B、model/trainer/inference/server/eval 修改或训练/仿真授权。GPT=设计/审核，cx=实现/正式测试/提交，ds=收到 fresh 放行后才执行独立 Evidence。
