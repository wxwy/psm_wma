# V3 Flexible Episode Resume — 三项设计整改 r2

日期：2026-10-23。状态：**提交 GPT 增量设计审核；尚未授权生产接线。**

Owner 冻结契约：`cc7820bee1a73bd2bb2078cb7f00239944f66d37`。
本次基线：V3 `50ed1fdc87d1380be6b95219ea12b9d379f7edc7`；Child/Gitlink
`813a550dab5d6b5b5e3be90d38bb97527956b4dc`，Vendor `1ac174585293ed998ffc9cf73e47439798cf6f6c`。
整改依据为 GPT 对 r1 Design `44f0953ac75591d7e60394df6337a6ed133f3f08` / 同 Child 的正式
`REQUEST_CHANGES`：
`docs/collab/chatgpt/reviews/2026-10-23_V3_flexible_episode_resume_design_r1_44f0953_813a550d_review.md`。

本文件取代 r1 第4、6节中的冲突设计，并补全第5节恢复权威。r1 文件、审核及作者161项 Evidence 原样保留。
本次只变更 `tools/v3/episode_resume_prototype/` 的隔离原型、测试及设计/交接文档。
生产源码仍为 Root `e6a970caba4bdc77f7d9b56a6a8fbcdafe57f1e0`；不修改 scripts、Child、配置、Vendor、真实结果或活动工作树。

## 1. 保留的契约

模型旧新相等仍只比较 Checkpoint、num_steps、action_horizon、guidance 四项；任一不同在认领新执行前拒绝。
当前 Task 集合、Episode 数、Seed、媒体和资源参数属于 invocation plan。
原始 EpisodeRef 的 digest、物理编号、来源和证据不可改写。
当前视图只统计当前 Task、前N个有效完成来源；多余历史保留。正常 success 和 horizon behavioral_failure 可以复用，runtime_error/中断不能算完成。
新执行实际 Seed、旧来源 Seed、混合协议/版本/未知信息在计划与报告中保留，不能冒充单 Seed 正式 benchmark。

原 r1 的模型完整哈希与 legacy metadata/stat 桥接、稳定 locator 去重、原媒体核验、只读锁见证等未变。
其中 legacy 没有历史 payload SHA 的证据限制依然存在；当前完整哈希不能补造过去的权重证明。

## 2. HIGH-01：按 Task 分流采样

Root `build_plan()` 根据**该 Task 重新验证后可用的完成历史**选择模式，不按整次运行是否带 `--resume` 推断。
`plan_scene_sampling()` 必须显式接收 `sampling_mode`，不提供隐式派生种子的默认值。

| 该 Task 状态 | 模式 | Seed、环境和 Reset |
| --- | --- | --- |
| 无可用完成历史，包括4→18新增14项 Task | `fresh_task_stream` | 原始 literal requested Seed；每 Task 一个环境，按原流程连续 reset N次 |
| 有完成历史，需要补缺集且历史 RNG 不可恢复 | `resume_gap_independent` | 每个待执行逻辑槽独立派生 Seed、独立环境、physical Episode0 |
| 已有足够完成历史 | 不调度新执行 | 原来源与实际 Seed 不变；不为当前 requested Seed 虚报新执行 |

Fresh 模式保持 `sampling_protocol=legacy_task_stream`。`new_episodes` 的 logical/source_episode 均为0..N-1，
共同指向同一个 `execution_batch`；该 batch 明确 `environment_constructions=1`、`public_reset_calls=N`。
不能把该计划拆成N个“同 Seed 但每集新建环境”的子任务；那会重复初始随机流，并不等价于原采样协议。
Fresh 模式拒绝携带旧完成来源、非连续编号；不出现“派生 Seed”警告。
如果旧来源均隔离/不完整而没有可复用 Episode，本 Task 从0完整重跑原协议，隔离/失败诊断仍进入计划和报告。

Gap 模式只允许非空的已验证历史来源。派生函数保持 r1 的稳定版本与 SHA256 输入：requested Seed、Task、logical slot，
不含 invocation nonce、GPU、任务顺序或 attempt编号。每个新来源 physical0 映射回原 logical slot，不能改变 C01 的本地编号。
重试可新建物理 Attempt，但 logical identity 不变。当前 Seed 修改时，新执行遵从当前 Seed，旧来源实际 Seed 不变。
明确标记 `NOT_HISTORICAL_RNG_STREAM_CONTINUATION`；混合 legacy/independent 协议不能冒充原连续随机流 benchmark。
独立 Seed 不保证物理场景互不重复，也不证明与旧随机流等价。

隔离 fake-env 验证包括：原协议与 fresh5 的完整场景 trace、构造/Reset 次数相同；4→18新增14Task继续原协议；
同一计划同时包含旧 Task 补集和新增 Task；partial3→5 在 Seed不变/改变时来源、逻辑编号和种子映射正确。
这些是 CPU 协议见证，不代表真实 Kitchen RNG/物理等价验证。

## 3. MEDIUM-02：矛盾 COMPLETE 整项隔离

`_validated_complete_source()` 在产生任何可复用 Episode 前读取原 Attempt 状态。
若为 `COMPLETE`，以**原 manifest 的 trials、runtime、媒体策略、digest**调用未修改的生产 `validate_attempt()`，
并预先验证该 source 所有 Episode 的原型核心证据；只在全部成功后一次性返回来源列表。
单集公共 API `verify_legacy_episode()` 也必须走同一 guard，不能绕过 scanner 取出前两集。

发生矛盾时明确返回 `CORRUPT_LEGACY_COMPLETE_MARKER`，该 Attempt 不贡献任何可复用结果，包含后面才发现错误时的前缀。
不删除、不修补原状态和文件，不把 COMPLETE2/5 当正常完成2集。来源路径、Task、错误原因保留在 scanner diagnostics，
由 Parent 计划/结束报告继承。其他独立合法 Attempt 仍可按原去重规则选择。

原状态为 RUNNING/FAILED 时继续逐集验证闭合前缀；不会把 Task 最后的清理失败倒推为早先合法 Episode 无效。
原媒体未录制但当前计划想要录像，只报本次覆盖缺口；与原策略要求的媒体已丢失/损坏分开处理。
Task级 `process_cleanup.json` 的新增/变化属于共享观测，不形成新的 Episode locator；每次重用 COMPLETE 仍重新验证它，
不能因此放宽 Local cleanup、原始动作、预测或核心文件哈希检查。

CPU 正反例：COMPLETE2/5、5/5缺失/损坏进程清理、末集 Local acknowledgement 错误均整项隔离；
合法 COMPLETE5/5 全量接收且文件字节不变；RUNNING/FAILED 的2/5前缀仍可重用；新媒体升级不改原 COMPLETE 验收口径。

## 4. MEDIUM-03：重建持久槽位，不依赖内存 pending

新增只读 `reservation_recovery.py`，恢复权威有两类：

1. 重新验证的 EpisodeRef/catalog。冻结规则为 logical slot 从0连续分配、不重号，因此其最高已知编号以内的空洞可恢复为待重试槽。
   例如有来源 `{0,1,3,4}`，即使原 reservation 文件丢失，也能从这些来源及连续编号规则推导 slot2。
2. 持久 reservation/logical mapping 和旧 progress 的投影。它们可证明尾部已分配但未完成的槽位、Attempt/physical映射和原 reservation ID。
   原 progress 没有 logical ID 时必须有可核对的物理映射；不能凭 Episode0 猜成下一个逻辑编号。

`read_recovery_document(path)` 从普通 JSON 文件只读获取上述投影，记录实际文件路径、内容 SHA256和稳定读取见证。
重复 JSON key、符号链接或不稳定读取拒绝。旧 `completed_slots` 投影仅可证明“已分配”，绝不凭外部 `verified:true` 就复用 Episode。
真正完成来源仍要经原 Episode verifier 核验。本阶段投影读取尚不是生产旧 JSONL/目录发现器。

`build_plan(..., recovery_documents=...)` 自动读取输入的持久文档并调用恢复器；完成来源直接来自重新验证的 history。
恢复器以全部历史、未选来源和 reservation 为权威，独立于当前 requested 数量计算：

```text
known = completed logical slots ∪ persistent reserved/mapped slots
pending = [0..max(known)] - completed
new_slots = ascending pending 的前 new_count 个
不足部分从 max(known)+1 追加
```

每个推导空洞记录 `INFERRED_FROM_PERSISTENT_COMPLETED_SLOT_GAP` 和 source_refs；显式 reservation/progress 也保留其权威来源。
同一物理来源映射到两个逻辑编号、同一 reservation ID 跨槽或同槽身份冲突均 fail closed；不能跳过冲突而分配 slot5。
纯整数仅用于算法测试，不能在没有持久权威时补造缺口。

`pending_slots` 旧 API 只作为兼容提示：只能引用已由上述权威推导的 pending，不能新建未持久化槽位。
恢复结果中的 pending、stable identity、完整 source_refs、next_slot_floor 保存在每 Task 的 plan/report；终端计划包含待重试编号。
requested5→2 时不执行缺口，但仍保留 pending2；以后扩大为5，仍先执行2。
相同 requested Seed 的多次失败重试复用 logical ID 和派生 Seed，物理 Attempt独立。
没有完成来源的整个 Task 则走第2节完整 fresh 协议，不能借零散未完成标记改变新 Task 的场景协议。

CPU 覆盖：磁盘 JSON roundtrip 后不传 pending 的 `{0,1,3,4}`→执行2；尾部 start/reservation 的自动重建；
shrink→expand、同槽多次失败/新 Attempt、映射冲突、无权威拒绝、重读不改文件；完成结果与分配投影严格分离。

## 5. 验收与停止条件

作者侧只运行本次变更的 scene、Episode evidence、reservation recovery、plan 四组隔离 CPU 测试，
使用外部日志/cache目录和 Ruff0.12.7。实际数量以本次 JUnit/Evidence 为准；不把旧161项或未重跑的 identity45项记作新版本全量通过。
任一失败、跳过、生产文件差异或 Child/Gitlink 变化均不能报本阶段作者 PASS。
内部只读复核仅检查本次三项闭环，不替代 GPT verdict 或 DS 独立执行。

提交顺序：新 r2 Design/Prototype commit → 绑定该 SHA 的作者 CPU Evidence/交接 commit → 非 force发布 V3并回读 → 停止。
申请 GPT 对新的 Root/Child Pair 增量设计审核，**不自行进入生产接线**。

设计通过后的独立实现 Gate 仍须覆盖真实 CLI→同一 run lock→四参/legacy重验→持久分配→Worker/Local清理→当前统计的完整 CPU fake管线，
旧 progress/catalog 自动发现与投影、只增原子预分配、崩溃恢复和最新 invocation discovery。
模型全量哈希的实际 I/O成本、latest-summary入口与完整管线均保留在后续范围，不在本次扩大整改。
不启动 GPU、Action Server、模型或仿真，不读取真实 DCP，不更新正在运行的评测或 G1，不重跑已完成20集。
