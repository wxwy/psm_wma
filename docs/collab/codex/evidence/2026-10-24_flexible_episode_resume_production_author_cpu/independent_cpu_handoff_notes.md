# DS_PRO 独立 CPU 复验建议

本记录只建议下一阶段的独立 CPU 执行边界，不是 GPT verdict 或 GPU/生产启动授权。顺序：作者提交并回读精确新 Pair → GPT 增量审核 → DS_PRO 独立 CPU → GPT 裁决。最终 Implementation Root SHA 已由 Parent 在提交后绑定；不能以本记录、文档 HEAD 或旧设计 SHA 代替。

- Root：`252d823cf7f0e65228aa60408d50778c5a13a307`，提交后重新读取 GitHub 确认。
- Child/Gitlink：`813a550dab5d6b5b5e3be90d38bb97527956b4dc`；DS 开始前独立核对 Root ls-tree、Child HEAD 和工作树清洁状态。
- 在新的 clean detached 验证工作树执行，不更新正在运行的18-task评测或 G1 工作树，不 reset/clean/force 或覆盖已有文件。无法安全锁定精确 Pair 则 BLOCKED。
- 使用服务器已有完整 CPU Python 环境；日志、JUnit、pytest临时目录和 HF/Matplotlib/XDG/pycache全部指向新的外部 Evidence 目录。固定 Ruff 0.12.7；不向仓库或默认 HOME 缓存写入。

## 五组组合

复现作者最终 commands 中的完整五组组合及原有选择条件，不以组件通过代替集成，不自行缩小测试集合：

1. `tools/v3/robocasa_resume_components_test.py`：生产组件与已审核语义对应、四参身份、实际哈希 I/O见证和边界、核心 Episode/原媒体、采样分流及槽位恢复。
2. `tools/v3/robocasa_resume_store_test.py`：同一 lease、锁前/内重验、显式 Resume、原始 digest重扫、只增预分配/映射、catalog不冒充完成、崩溃恢复、不可变历史与最新报告指针。
3. `tools/v3/robocasa_resume_execution_test.py`：真实 CPU OwnedProcess/HTTP边界、reserved batch约束、Worker异常、超时/取消/进程组清理、错误不被完成覆盖吞掉、callback/commit边界。
4. `tools/v3/robocasa_episode_resume_integration_test.py`：当前文件16项。真实默认 CLI/resolve → 四参/legacy bridge → flock → Store/持久 reservation → executor → 未修改 Child main/run_policy/LocalMemoryClient → HTTP ack/reset → 原始证据重验 → 当前报告。
5. `tools/v3/eval_robocasa_queue_identity_test.py`：作者最终组合中指定的既有 Queue 身份/生命周期回归；按最终命令保留全部所选用例，不把旧 Gate 历史数字叠加到本次结果。

第4组的外部 runtime/model/Kitchen/proprioception采用 CPU替身；Local client、真实 HTTP session/frontier/reset、审计输出和生产恢复链均执行。具体覆盖 fresh5 literal seed与单环境连续 reset，旧2+新3，新增 Task fresh与旧 Task gap并存，四参逐项不等的无写/无启动拒绝，全复用无 runtime probe且不占端口，缺少 `--resume`、真实 busy flock，第三集异常的 executed/failed计数与后续恢复，原媒体 none→新 all只录新增集，HTTP reset失败不能完成且新 Server可恢复，最终重扫失败保留执行器/清理错误并持久 PARTIAL，以及输出位于 Checkpoint/model或数据目录时无写拒绝。

Ruff check、format --check和语法/源码边界检查应使用作者最终15个 Python 文件清单，不扩展为全仓 GPU测试。记录完整命令、Python/依赖版本、精确 SHA/Gitlink、开始结束时间、退出码、测试统计、JUnit、stdout/stderr和失败 traceback。任何失败停止并提交原始证据，不修改生产源码、测试、配置或历史 Evidence。

## 证据与授权边界

- 作者第二次最终冻结五组组合 154 passed、72 subtests passed，0 failure/error/skip；精确统计见 STATUS/JUnit，不继承旧迭代数。此前本代理的集成 run04为13 PASS；后续新 report负例 run05为1 PASS/13 deselected；最后两项 namespace负例留给最终组合。不得将这些迭代相加冒充一次最终16项执行，更不能视为 DS独立 PASS。
- 集成 `run02.log/xml` 保留了真实 unfinished计数缺陷（错用 UI事件、executed/failed少计）及 traceback；修复后 run03聚焦回归通过。更早 fixture缺 lease/异常类型调整与最初未保留原始log的事实见 `integration/iteration_notes.md`；必须与生产缺陷、最终冻结结果分别报告。
- 作者 raw证据目录：`/tmp/psm-v3-episode-resume-production-20261024/`；其中 `final/` 为最终组合/静态结果，`integration/` 保存迭代。提交后 Parent会给 GitHub持久化路径与校验清单；DS不使用作者本地/tmp文件代替独立运行。
- 本轮不启用 GPU，不加载真实 Action Server模型，不调用真实 RoboCasa构造/reset/step，不读取、保存或恢复真实 DCP。微型 pickle/ZIP只是身份与恢复链 CPU fixture，不能证明真实 DCP可加载或物理 benchmark正确。
- 不操作活动评测、G1训练、Checkpoint/Config/Job Identity、原历史结果或 Vendor。CPU绿色只交 GPT裁决；真实模型加载、GPU仿真或任何训练继续需 Owner另行授权。
