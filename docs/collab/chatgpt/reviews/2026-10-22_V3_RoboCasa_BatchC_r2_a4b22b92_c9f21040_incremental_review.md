# V3 RoboCasa Batch C r2 — C01/C02 独立增量审核

日期：2026-10-22
技术结论：**APPROVE — 仅本精确 Pair 的 C01/C02 生产整改及作者 CPU Evidence 范围。**
正式记录条件：本 review 与 canonical CODEX_INBOX.md 的对应追加同时完成，才构成项目正式 verdict。DS_PRO 目标机独立 CPU 验收及真实运行/物理 Gate 单独保留，不由本批准替代。

## 1. 锁定版本与范围

- Formal Implementation Root：`a4b22b929175e462b6a8db57ad2abee7e220dd37`。
- Child/Gitlink：`c9f21040f462a114d597fc83773cb9b6a9e96214`，与上一轮完全相同。
- Vendor 可重建 commit：`1ac174585293ed998ffc9cf73e47439798cf6f6c`，未变。
- 前一 formal Root：`a2f3a6a367395b2f2a6006cfc4e7c9effa606713`；前一 review 为 `2026-10-22_V3_RoboCasa_BatchC_a2f3a6a3_c9f21040_independent_incremental_review.md`。
- 本轮开始核对的远端 V3 HEAD：`1d6bc0ac136d0d9e8070a9ab97ffc03e033a949f`，仅用于记录远端状态；不替代上述 Formal Root。
- Author handoff：`docs/collab/codex/reviews/2026-10-22_RoboCasa_Batch_C_r2_C01_C02_author_handoff.md`。
- Incremental compare 实际功能改动只涉及 Root 三个生产文件：`scripts/eval_robocasa_18task_queue.py` (+17/-2)、`scripts/robocasa_eval_results.py` (+65/-2)、`scripts/robocasa_processes.py` (+9/-2)，以及相应三个测试文件和 Runbook 说明。其余新增历史 review/作者证据/SESSION/TODO 是归档，不是模型行为修改。
- GitTree 直接核对 Child mode160000 等于 c9f21040；third_party tree 与上一轮相同。G1、训练恢复、优化器、DCP、Local-TTT 数学及 Vendor 没有本轮增量。

## 2. HIGH-C01：CLOSED（本生产整改/CPU范围）

### 实现核验

`robocasa_eval_results.py::_validate_episode_progress` 在二进制模式逐行读进度，要求每行换行完整且不超过4KiB，恰为2N条按序 start/end。逐条核对 schema、run digest、Task/Attempt、严格整数 Episode 和事件次序；拒绝缺失、空文件、截断、重复、跨任务/attempt、额外记录、非有限JSON和重复JSON key。

`_validate_local_cleanup` 要求每个 `rolloutXX_cleanup.json` 包含 session_id/reset_ok/cleanup_error/rollout_error/media_error 全部字段，reset_ok 必须是布尔 True，三种错误必须显式为 null，session_id 必须匹配 unchanged LocalMemoryClient 的 `<32lowerhex>:0:<32lowerhex>` slot0 格式。没有用“服务进程退出”冒充 Episode reset 成功。

`validate_attempt()` 在原 result/runtime/process cleanup/action/media 验证上增加上述两个必需检查。`finish_attempt()` 与 `find_completed_attempt()` 仍共用该函数，因此首次 COMPLETE 和 Resume 跳过使用相同门槛。损坏 COMPLETE 只报错，不改写旧 marker 或文件来伪造修复。

`robocasa_processes.py::EpisodeProgress` 增加可选 expected attempt_id；Batch A 旧 process-only 调用保持兼容，但正式 Queue 创建监视器时明确传入 `Task/attempt_NNNN`，不是依靠默认 None。在线监视拒绝外来 Attempt；最终离线复查还会拒绝未完整写入的尾记录。

### 行为证据

直接阅读新负例实现 `test_progress_and_local_cleanup_required_for_commit_and_resume`：34种进度/清理缺陷 × finish/resume 两阶段，共68项；每个负例都验证抛错后原有证据逐字节不变，且不会将未完成 marker 提升为 COMPLETE。

实际 Queue synthetic 边界测试新增：先完整完成四任务，再删除进度、改写 Attempt 或伪造 Local reset 失败；第二次真实 queue.main/--resume 返回非零，不增加任何 Server/Simulator 启动次数，损坏原文件保留。在线 wrong_attempt_progress 直接导致 INCOMPLETE/FAILED。

旧版 baseline_missing_witness_accepted.json 记录：进度和逐集清理均缺失时旧 validator 仍 COMPLETE 并 skip。该原始失败见证与上一轮 finding 和本次整改方向一致。

因此 HIGH-C01 在上述 scoped code/author-CPU Gate 中关闭，不再列为当前生产 blocker。

## 3. MEDIUM-C02：CLOSED（本生产整改/CPU范围）

Root Queue 新 `task_video_files()` 只将完整匹配 `rollout<digits>.mp4` 的环境录像列入 rollout_mp4s，完整匹配 generated/每replan文件名的预测录像列入 generated_mp4s。正常 task_result 和无完整结果的错误 fallback 共用此分类；publish 分别汇总两组路径。

直接核对对应 Queue 测试及最终 JUnit：关闭环境MP4、分别启用 first/all 时，任务行和总 summary 的 rollout_mp4s 都为空，generated_mp4s 与每Episode结果一致；失败部分片段依旧保留为 generated_mp4s，整体状态仍 INCOMPLETE。其他名称的 rollout*_other.mp4 不被误归类。

因此 C02 已修复，未通过放宽媒体解码或成功率统计来获得通过。

## 4. 原始 Evidence 与计数

证据目录：`docs/collab/codex/evidence/2026-10-22_RoboCasa_Batch_C_r2_evidence_integrity_author_cpu/`，归档于 `1d6bc0ac136d0d9e8070a9ab97ffc03e033a949f` 可访问。

本轮直接阅读 handoff、gate.json、commands.json、source_checks.json、baseline_missing_witness_accepted.json、helpers.log、child.log、regressions.log 和 queue.xml，以及上述生产/测试实际内容。

- Helpers：221 passed（Attempt125 + Config70 + Process23 + Numba3），原日志12.73s。
- Child：58 passed，原日志2.60s；其中 reset/encoder error 为预期注入，最终无失败。
- Queue：35顶层方法 +72 passed subtests，JUnit tests=107、failures/errors/skipped=0；含新恢复损坏见证与两类视频分类路径。
- Regression：20 passed、50 deselected，原日志3.89s；deselected 不是 skip。
- 合计334顶层测试 +72 subtests；不能把Baseline预期红例、旧r1的255项或中间迭代重复相加。
- 作者 gate/source_checks 记录 Ruff0.12.7、12个Python AST、bash syntax和格式通过。

以上是 GPT 对实际源码及作者原始 Evidence 的独立阅读，不是 GPT 或 DS 在目标机重新执行334项。没有读取/修改运行中的G1或真实DCP，没有模型加载、GPU和Kitchen仿真。作者合成边界不能证明真实安装/控制器物理/策略效果。

## 5. 当前状态与后续

- 当前范围内无新增阻断性生产 finding。C01、C02 均 CLOSED；不要求 Codex 再修改这两项生产代码。
- 可将此精确 Root/Child 交 DS_PRO 在新的隔离 clean worktree 做定向独立 CPU 验收：三个变更测试文件及 Ruff/格式。建议以作者 commands.json 为执行依据，禁止使用当前 docs HEAD 代替 Formal Root；不必重跑 G1训练或无关历史 Gate。
- DS 重点报告：损坏 COMPLETE 的 --resume 非零且不新增进程；wrong Attempt 在线拒绝；缺失/失败 Local cleanup 拒绝；generated-only first/all 及失败片段分类正确；测试结束无残留自有进程。缺依赖应报 BLOCKED，不跳过或修改断言。
- Batch B 的目标机真实依赖正向检查、PandaOmron Kitchen create/reset/step、相机/状态/Legacy底盘/物理验证与真实Policy/Local-TTT全链运行仍未由本Gate证明。后续真实运行由Owner单独授权并手动执行。
- 本次只写审核/交接记录，不改生产源码、不改运行中的G1、不自动执行仿真。慢动作诊断由DS另行核实，不混入本轮C01/C02整改 Gate。

技术结论：APPROVE（精确 a4b22b92 / c9f21040 的 C01/C02 code + author CPU scope）；DS independent acceptance 未执行，真实运行 Gate 未关闭。