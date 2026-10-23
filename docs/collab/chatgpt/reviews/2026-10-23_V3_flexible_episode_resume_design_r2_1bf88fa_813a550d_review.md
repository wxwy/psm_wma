# PSM-WMA V3 Flexible Episode Resume r2 — 设计/隔离原型增量独立审核

日期：2026-10-23（CST）
**VERDICT: `APPROVE` — 当前 Design + Isolated Prototype Gate 限定范围内通过。** 非生产实现、DS CPU 或真实仿真批准。

## 1. 精确对象与独立性

- **Formal Design/Prototype Root:** `1bf88fa624e58e521caa2213f2b1a44bf2f2871d`
- **Formal Child/Gitlink:** `813a550dab5d6b5b5e3be90d38bb97527956b4dc`（未改变）
- **Owner frozen contract:** `cc7820bee1a73bd2bb2078cb7f00239944f66d37`，`docs/collab/chatgpt/requests/2026-10-23_Codex_V3_RoboCasa_flexible_episode_resume_contract.md`
- **上一审核对象:** Root `44f0953ac75591d7e60394df6337a6ed133f3f08` / 相同 Child；上一 verdict `REQUEST_CHANGES`。
- 本轮修改基线 `50ed1fdc87d1380be6b95219ea12b9d379f7edc7`。新 r2 的 12 个改动路径仅为 design / isolated prototype / tests / SESSION / TODO；实际 Gitlink 与 `scripts/`、`configs/` tree 未变。最后已知生产实现 Root `e6a970caba4bdc77f7d9b56a6a8fbcdafe57f1e0`；未引入生产 Resume 调度。
- r2 设计 `docs/collab/codex/designs/2026-10-23_V3_RoboCasa_flexible_episode_resume_design_r2.md` 取代 r1 第 4/6 节冲突行为并补足恢复 authority；其他 r1 未修改的四参数身份、legacy 桥接及媒体契约仍按 r1 约束。
- 本结论从实际 GitHub source/tests、已有生产 validator / Child reset 行为、Owner 契约和提交的 JUnit 独立判断，**未在 GPT 环境中重新执行作者的 CPU 测试**。不是对 Codex 作者内部评审的继承。

## 2. 上轮 blocker 增量复核

### HIGH-01 — CLOSED：新 Task 保留原始连续场景采样

- **设计:** r2 `design_r2.md:27-52`。
- **实际代码:** `tools/v3/episode_resume_prototype/plan.py:202-265` 中依据**当前 Task 自身经验证的 history**决定 `fresh_task_stream` / `resume_gap_independent`；`scene_sampling.py:57-88,90-145` 要求显式 mode。Fresh 保留 literal requested Seed、一个 Task 环境、物理 Episode 0..N-1、连续 public reset，完整 batch 内不重新创建 N 个环境；Gap 独立派生稳定 Seed、每集单独物理 Episode0，并声明不恢复原 RNG。
- **真实既有 authority:** Child `cosmos_framework/simulation/robocasa/closed_loop_eval.py:184-213,593-599,627-651` 为每 Task 一次 `make_env(seed=args.seed)`，随后的 Task loop 连续 reset。r2 不再默改此首跑语义。
- **行为证据:** `scene_sampling_test.py:117-223` 用真实 action 消耗 RNG 的可控 fake env 对比 fresh5 场景轨迹、构造/重置计数、4→18 新 Task 与 partial3→5；`plan_test.py:308-342` 检查混合 old/new Task 同计划决策；隐式 mode 被拒绝。该证据是协议级 synthetic，不宣称真实 Kitchen 场景物理等价。

### MEDIUM-02 — CLOSED：矛盾 COMPLETE 整个来源隔离

- **设计:** `design_r2.md:54-71`。
- **实际代码:** `episode_evidence.py:423-471` 先用原 manifest trials/digest/runtime/media 调用未改生产 `validate_attempt`，然后缓冲检查所有原 Episode core；任一错误抛 `CORRUPT_LEGACY_COMPLETE_MARKER`，不发布此前的合格前缀，direct single-Episode API 同样不能绕开。扫描器 `episode_evidence.py:522-590` 输出原 path/Task/Attempt/原因的诊断，保留其它 RUNNING/FAILED 来源的闭合前缀。
- **真实既有 authority:** Root `scripts/robocasa_eval_results.py:299-350,446-451` 只有完整 Task audit/cleanup 后才能 commit COMPLETE。
- **行为证据:** `episode_evidence_test.py:256-367` 覆盖 COMPLETE2/5、COMPLETE5/5 正例、缺失或损坏 process cleanup、尾集 Local acknowledgement 破损、direct API 绕过负例、合法 FAILED 前缀和原字节不变。Task 共享 `process_cleanup.json` 不是独立 Episode ID；`plan.py:33-36` 从 stable core snapshot 排除该共享观测，但 COMPLETE 重新使用时仍重验真实来源。

### MEDIUM-03 — CLOSED：自动恢复缺失逻辑槽位

- **设计:** `design_r2.md:73-107`。
- **实际代码:** 新 `reservation_recovery.py:70-116,134-253` 只读解析持久 projection，保存内容 hash、拒绝重复 JSON key/符号链接/变更；以已验证 Episode 来源及可靠 reservation/progress 映射恢复 `[0..max(known)] - completed`，检测物理映射/ID 冲突，不接受 `verified:true` 作完成证明。`plan.py:157-160,211-245` 自动读取文档、优先使用重建 pending；可选 `pending_slots` 不能发明无持久证据的槽；current request 缩小不删除历史保留的 missing slot。
- **行为证据:** `reservation_recovery_test.py:63-225` 覆盖 sparse `{0,1,3,4}` 回收 slot2、独立 OS 进程重读、尾部 reservation/progress、shrink→expand、同槽跨 Attempt 重试及冲突 fail-closed；`plan_test.py:344-411,443-453` 验证无 in-memory hint 的 gap plan 和稳定 source/logical 映射。
- **范围限定:** 当前读取的是显式提供的持久 *projection JSON*，不是生产历史 JSONL 自动发现器。后续 implementation Gate 必须证明真实目录 → 权威 projection → 原子 reservation → 新 Worker 的闭环，不得把 prototype source-bearing hints 误当作已验证真实 Episode。

## 3. Evidence 审核

- 作者 Evidence：`docs/collab/codex/evidence/2026-10-23_flexible_episode_resume_design_r2_author_cpu/`，交接：`docs/collab/codex/reviews/2026-10-23_flexible_episode_resume_design_r2_author_handoff.md`。
- 仓库 JUnit 单次运行 `tests=185, errors=0, failures=0, skipped=0`；按实际测试文件为 scene53 + Episode53 + recovery34 + plan45。日志 `185 passed in 2.93s`。Ruff0.12.7 check / format 与 11 文件语法检查在作者证据记录为 PASS。
- 实际源文件与声明的 exact design root/Child、protected production tree 符合；设计提交后 `277457606baae6105eacc97013f4d8fe23d33d4e` 是纯 handoff / evidence 文档 commit，不是新的 Formal Design Root。
- 未变的 `model_identity_test.py` 45 项本轮未重跑；不能把 r1 的161与 r2 的185合并成新的全集验证。**185 是作者 CPU 证据，不是独立 DS 测试。**

## 4. 本 Gate 的后续边界

**当前阻断项：无。** HIGH-01、MEDIUM-02、MEDIUM-03 均 CLOSED；无本轮新增 production defect 声称。

本次 `APPROVE` 仅允许沿此冻结设计展开**下一阶段最小生产 Resume 接线代码开发**，不表示生产 Resume 已可使用，也不关闭未来 Implementation Gate。

后续独立 Gate 必验：真实 CLI→同一 `.run.lock`→四参数 fail-before-write/launch→legacy 身份及完整 Episode 重新验证→持久 projection 自动发现与只增原子 reservation→Task 首跑/partial 补集分流→Local required session 生命周期与资源隔离→来源引用/媒体覆盖/最新 invocation summary→故障及并发恢复的 fake-server/CPU 全链。真实模型 DCP 全哈希性能、路径安全、输出视图发现和重复/巨大逻辑 slot 限额，在接线中给出可验证行为。随后 GPT 审核**新的 exact implementation Root/Child pair**，由 DS_PRO 独立验收相应 CPU Gate。

**本 verdict 不授权**修改活动评测/G1 工作树或原始证据；不授权 GPU、真实 RoboCasa 仿真、模型加载、权重/Checkpoint 操作、训练/恢复、正式评测启动，也不要求重跑已完成 iter12000 20 集。
