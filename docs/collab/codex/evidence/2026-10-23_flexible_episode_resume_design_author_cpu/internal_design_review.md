# Flexible Episode Resume：内部只读封口复核

日期：2026-10-23。复核者：Codex 独立子代理 `/root/inherit_eval`。

审核生产基线：`cc7820bee1a73bd2bb2078cb7f00239944f66d37`。本记录属于设计及非生产 CPU prototype 的内部审查，不是 GPT 正式 Verdict，也不授予生产接线、GPU、Action Server 或仿真执行权限。

## 结论

此前复现的 Episode 双计和媒体覆盖统计问题已在当前 prototype 中关闭；Seed family 口径和 scanner 诊断保全也已补齐。未发现需要继续阻止本轮设计/prototype 提交的新增问题。可以将设计、源代码 diff 和 CPU Evidence 交 GPT 独立审核。

本次复核只读取源码、测试和已有日志，没有修改项目源码，也没有再次执行项目测试。读取到作者汇总日志 `prototype.log` 的结果为 **161 passed in 2.14s**；这是作者执行结果，不是本代理或 DS_PRO 独立执行结果。

## 已关闭的问题

1. **稳定来源与快照分离，禁止双计。** `tools/v3/episode_resume_prototype/plan.py:18` 的 source key 仅使用原始 digest、task、attempt 和原始 source episode；不再把文件 hash、路径或共享 Task 快照当作第二个 Episode 身份。`:29` 排除三类可变 Task 文件快照，`:161` 对同 locator 的不同核心文件快照报 `SOURCE_EVIDENCE_CHANGED`。`:168` 将 legacy physical index 明确映射到 logical slot，`:170` 对同槽重复来源只选一条并记录诊断；`:34` 的 numeric-first 排序不依赖 success。定向测试见 `plan_test.py:217`、`:227`、`:235`、`:250`。

2. **本次媒体策略重新计算视图。** `plan.py:40` 使用实际 availability、prediction count 和本次 requested policy 重算缺失；在构建计划 `:178` 和报告 `:289` 都应用。scanner 在 `episode_evidence.py:237` 保留实际 prediction count。关闭全部媒体不再沿用旧缺失列表，不改变历史文件也不重跑 Episode。测试见 `plan_test.py:260`、`:269`。

3. **诊断从扫描保留到最终报告。** `plan.py:140` 接收原 scanner diagnostics，`:153` 合并，`:333` 写入报告。实际 synthetic legacy 2/5 扫描至新增3集的组合测试在 `plan_test.py:448`，`:455` 显式传入 scan diagnostics，并验证历史文件字节保持不变。

4. **区分请求 Seed family 和真实环境 Seed。** `plan.py:88` 使用请求 family 判断 `MIXED_SEED`；`:98` 使用 `MULTIPLE_EFFECTIVE_ENV_SEEDS` 报告派生的真实环境 seed；不同采样协议另报 `MIXED_SAMPLING_PROTOCOL`。同一 requested seed 的独立 Episode 派生 seed 不再误称用户改变了 Seed family。测试见 `plan_test.py:286`。

5. **Config 和 Task metadata 保留为可比较性信息。** `plan.py:110`、`:114` 对混合 Config、同一 Task 的 metadata 变化给出明显标识，不形成第五项模型参数硬相等约束；测试见 `plan_test.py:295`。未知值同样有独立标识。

## Legacy 与统计边界确认

- `model_identity.py:313` 的 legacy ingest 仍以原始 manifest canonical digest 和原 metadata/hash/stat witnesses 进行 bridge 检查；不会把新读取的全模型 hash 冒充为历史 hash，返回范围明确标注为旧 stat bridge。
- Episode scanner 仍使用原始 manifest/digest、原始媒体策略、实际 Episode 文件及 Local-TTT/action/prediction 证据；共享文件不参与稳定来源身份，不意味着可以跳过重新验证当前原始证据。
- plan/report 只选择当前任务和数量；正常 behavioral failure 进入完成分母，runtime_error、未闭合或未验证 Episode 不进入完成分母。当前 invocation 的错误即使完成数量足够，仍导致 PARTIAL、非零退出和正式 SR 为空；历史失败不永久污染后续已补齐的 invocation。
- 新场景方案明确为逐 Episode 独立派生 seed 与新环境；不是历史随机流续接，也不保证物理场景绝不重复。fake-env 证据不能证明真实 RoboCasa 构造/reset 的 RNG 行为。

## 仍需后续独立 Gate 的事项

1. **完整受保护生产流水线尚未接线。** 当前四组模块和锁内快照 witness 没有组成 `legacy 模型裁决 → namespace lease → 锁内重验/原始证据扫描 → 只增 invocation/catalog → 新 attempt → 真实执行 → 验证/汇总` 的生产入口。组合测试的新增执行记录仍是 fake 完成记录，不是实际 Queue 执行。未来实施必须以真实受保护入口补集成负例，不能仅信任调用方提供的 `verified=True`。
2. `locked_snapshot` 仅对已有普通 `.run.lock` 做只读锁验证；无历史 lock 的非破坏迁移、首次命名空间创建、持久化计划/报告、crash 后 catalog 重建、原子提交都属于未来实施 Gate。
3. 当前生产 Queue、results、progress、video_view 仍沿用原严格整 Task 协议；本轮没有放宽生产 Resume，也没有影响当前运行的18任务。未来接线需适配跨 invocation 原始 digest、logical/physical 索引与当前计划媒体覆盖，继续保留 Worker 错误与 OwnedProcess 清理约束。
4. Full-byte hash/header 仅证明读取到的字节身份和有限容器结构，不证明真实 DCP 的 tensor/offset/分片完整性或可加载性；legacy stat bridge 不能追溯不存在的历史全权重 hash。
5. 当前 CPU 结果不能替代 GPT 独立审核、DS_PRO 独立生产 CPU Gate 或 Owner 单独授权的真实环境/GPU Gate。

只读核对 `git diff --name-only cc7820be -- scripts cosmos-framework configs` 输出为空。复核时关键源码 SHA256：

- `plan.py`: `298c1f02530254d7762c68d19451caa0841a9e7e67a59952e79605bd56348733`
- `plan_test.py`: `8e93cc70b703824b996e17b2e99ebf972e0f269a05b3444bd2eedaecb1ade85c`
- `episode_evidence.py`: `e8d4f715d58c41dcd5250607f7fcf029a198e31008b1ae3a8f64fe9e756cd938`
