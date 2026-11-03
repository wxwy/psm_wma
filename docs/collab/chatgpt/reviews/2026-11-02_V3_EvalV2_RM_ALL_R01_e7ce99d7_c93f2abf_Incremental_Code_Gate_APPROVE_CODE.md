# PSM-WMA V3 EvalV2 — RM-ALL-R01 历史媒体 ACK 增量独立代码审核

- 审核日期：2026-11-02
- **正式 verdict：`APPROVE_CODE`（本次 RM-ALL-R01 窄范围 Source Code Gate）**
- Formal Root implementation：`e7ce99d7a0bbb7a81ea7afcee7253548687dc223`
- Formal Child / Root Gitlink：`c93f2abf4fb27d36176ff8db094379a853cec796`
- 候选分支（Root/Child）：`v3-eval-v2-replan-ack-r01-20261102`
- 上轮正式 `REQUEST_CHANGES` Formal Pair：Root `d2041e388eda084e42a2d6b0d115db8beedfab44` / Child `0dd13d3d952aa7cbab39f966dfab04b23551f0c9`。
- 审核基准：前轮 RM-ALL-R01 finding、用户 `save_generated_video: all` 的有界完整视频/重试幂等契约，候选 Root/Child 真实 Git 代码、冻结公共 API 测试、原始作者 JUnit/静态检查/源码身份记录。此审核为**全新 Formal Pair 的增量复审**，并非重审不变的旧版媒体机制。

## 1. Formal diff / 隔离边界

通过远端 GitHub commit/compare/tree 和精确文件读取：
- 相对上一轮实现，**唯一 Child 生产改动**为 `cosmos_framework/inference/robocasa_batch_transactions.py`（26 insertions / 8 deletions）。其他 Child 生产文件、基础 Session 事务/客户端/编码器/策略/Local-TTT 模型链路均未改动。
- Root 新增 `tools/v3/eval_v2_replan_tests/ack_history_test.py`（339行），Root Gitlink 改为当前 Child，并更新 `SESSION.md` / `TODO.md`，没有其它 Root 生产逻辑修改。
- 已确认 Root 正式 Git 树中 `cosmos-framework` 的 gitlink = `c93f2abf4fb27d36176ff8db094379a853cec796`。`V3` 和官方 Child 不因本次审阅而合并或更新。
- 旧 `379` 项作者证据 tree 保留不变；本轮没有把历史案例计数纳入 122 项新验收。

## 2. 上轮 blocker RM-ALL-R01：**CLOSED**

**旧根因**：服务器 `self._acked_media[lease.session_id]` 只记最后一条已完成的 ACK。成功 Replan0 后完成 Replan1，迟到的 Replan0 预留会占用新的 spool job；旧 ACK 回放反而被拒绝。

**新代码核对，Child `robocasa_batch_transactions.py`：**
1. `:30–33` 增加固定 `MAX_MEDIA_REPLAY_RECORDS=100001`，与既有公共 media Replan/frontier 0..100000 上界相配；只存 digest/index 元数据，不存视频字节或完整 receipt。
2. `:154–161` 基于 `(session_id, request_key)` 查**所有已 ACK 历史**，对原 payload SHA 与 Replan index 严格匹配；同身份历史预留返回 `already_saved=true`，不会插入 `_media` 或重新生成动作、解码及视频。
3. `:168–179` 对已保存历史与当前尚未 ACK 的严格 `_media` reservation 共同施加 `100001` 数量上限；耗尽明确返回 `MEDIA_INCOMPLETE`，不淘汰老 authority，也不以无限缓存绕过限额；历史重放在该上限检查之前处理。
4. `:576–613` 严格首 ACK 仍要求 READY、匹配 lease/payload/VIDEO_SAVED receipt 后才记入 `_acked_media[session_id][key]=(sha,digest(receipt),replan)` 并清除媒体 job。以后任何历史 ACK 需原 key+payload SHA+receipt digest+index 一致才能幂等通过；改键、改摘要、改 index、改收据/foreign lease 仍拒绝。
5. `:622–630` 先保留 End202 等待期间的历史，只有父 Session `super().end` 真正 `acknowledged=true` 后才按 session 清除。新 Slot generation/lease 不能重用旧会话记录。
6. 资源与生命周期关系：保留原 `_lock` 串行临界区，未增加跨 GPU/Executor 等待或新长生命周期进程；`spool 4/512MiB`、`media_drain_timeout_s=300` 以及同步保存到 ACK 的原架构不改。

**独立判断**：上轮明确的“Replan0/1 均保存后迟到旧预留/旧 ACK”漏洞已由当前真实代码修复，未见本次增量引入新的 blocking contract violation，RM-ALL-R01 现可标 `CLOSED`。

## 3. 作者 RED/GREEN / Evidence 复核

证据目录：`docs/collab/codex/evidence/2026-11-02_eval_v2_rm_all_r01_author_cpu/`（在隔离候选，源 SHA 只作为技术审核对象）。直接读取：

- **旧生产 + 冻结新测试 RED**：`red_validated/junit.xml` = 2 tests / **2 expected failures** /0 errors/0 skips；两例分别为 *old reservation after two ACKs* 错误重新建 job，以及旧 ACK 回放误拒。来自实际 `transaction_dispatch` / Actor / 合成 CPU Encoder，非只测私有 helper。测试冻结字节 SHA256 `2114ca1435316be8ec2f4e13383badc0ebedcfee2da7a44966139fdf7ad53354`，与新 Root `ack_history_test.py` 和 GREEN invocation SHA 匹配。首次 external driver 有冗余消息校验 bug，但 `red_validated` 单独确认相同旧生产与冻结测试的预期 RED，不能将两次运行冒称四项。
- **新 Formal Pair GREEN**：`final/green/junit.xml` **74/74 PASS**（16新增+58相关，Python3.13.5），`final/regression/junit.xml` **48/48 PASS**（Batch Actor/Local/Fast/Native CPU回归，Python3.12.14）；汇总 `final/junit.xml` **122 distinct /0 failures/0 errors/0 skips**。不能写成同一解释器下的122，也不将历史379重复计数。
- 新16例重点覆盖：跨两次及六次 Replan 的旧 Reservation/ACK 幂等，反复迟到的旧请求不填满4-slot spool，后续合法新 Replan 不受阻；篡改 hash/index/frontier/receipt/assignment 均拒绝；其它有效 Session 隔离、精确容量及 pending job 计数、End202 历史保留、End ACK 释放及旧 generation 失效。两条合成媒体的帧顺序与实际 MP4 SHA 不同，避免只看数量的假覆盖。
- `final/static/gate.json`：Ruff0.12.7、format、syntax（2 files）PASS；Git blob/SHA256 2 source bindings；原始 JUnit、stdout、commands、版本、源码 before/after clean、40项 artifact checksums 已归档。
- 作者 122 Case PASS 不是 DS_PRO 独立运行；本轮 GPT 也**没有在训练服务器重跑**，没有使用 GPU、真实模型、RoboCasa、旧 out2/历史媒体。

## 4. 非阻断范围说明

- 当前每次 `all` 视频落盘仍可能有完整 CPU 全帧解码、FFmpeg flush/fsync、SHA 校验的额外成本；这属于上一 Formal Pair 已接受的 nonblocking 诊断性能问题，不属于本次 ACK replay 修复。需要后续单独授权的小规模真实 GPU/FFmpeg Canary 量化。
- 仅针对用户手动开启 `save_generated_video=all` 的 Replan 全量 MP4；默认 `none` / `first` 兼容与 900 Episode SR 实测/调度吞吐未因本次 patch 重新批准。旧 H3 缺少的80段历史视频不会自动补回。
- 不改变科学 Core/SR/Local reset authority，不批准任何训练、真实 checkpoint/模型、远程评测、硬件 Canary、正式 900EP、官方分支合并或访问 GPU0–3/修改 No-TTT/out2。

## 5. 最终 Gate 处理

**`APPROVE_CODE` — RM-ALL-R01 `CLOSED`，没有当前 blocking Production finding。**

批准严格绑定 Formal Root `e7ce99d7a0bbb7a81ea7afcee7253548687dc223` / Child-Gitlink `c93f2abf4fb27d36176ff8db094379a853cec796` 的**增量源码+已检查作者 CPU Evidence**。下一阶段如需验收：DS_PRO 在干净隔离 checkout 独立执行 RM-ALL-R01 定向 122 CPU集合（允许两个解释器按原证据分组）；随后经 Owner **单独授权**进行少量实际 `all` Replan 真机型模型+FFmpeg GPU Canary。不得把本次源码 `APPROVE_CODE` 视为真实 GPU、全媒体稳定性或正式 V3 合入的许可。

相关：
- 上次 `REQUEST_CHANGES`：`docs/collab/chatgpt/reviews/2026-11-02_V3_EvalV2_Replan_All_Durable_Media_d2041e38_0dd13d3d_Incremental_Code_Gate_REQUEST_CHANGES.md`
- Codex handoff：`docs/collab/codex/reviews/2026-11-02_V3_EvalV2_RM_ALL_R01_ACK_History_Author_Handoff.md`
- 原始本轮 Evidence：`docs/collab/codex/evidence/2026-11-02_eval_v2_rm_all_r01_author_cpu/`
