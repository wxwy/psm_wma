# PSM-WMA V3 — RoboCasa Owner Manual Eval Batch A：7646d414 / e42a2468 独立增量审核

日期：2026-10-22
Gate：Batch A Local-TTT跨任务污染 / 受管子进程与硬timeout / 退出错误保真 **isolated candidate** 的 Implementation/Author CPU。
Verdict：**`APPROVE` — 此精确Pair的 Batch A source/author-CPU implementation Gate ONLY**。
**未授权**合并V3、启动GPU、正式RoboCasa评测、宣称历史SR有官方物理等价性、替代缺失的Batch B vendor pin 或 Batch C 参数化手动Launcher。
原设计合同：`docs/collab/chatgpt/requests/2026-10-22_V3_RoboCasa_Owner_Manual_Eval_Framework_Frozen_Contract.md`，设计Gate `docs/collab/chatgpt/reviews/2026-10-22_V3_RoboCasa_18task_Session_Vendor_ManualEval_Design_Gate.md`。

## 1. Formal SHA / 变更范围

- Implementation Root：`7646d41488a55d5a44ab193520a42c48cf5acc90`。
- Child/Gitlink：`e42a2468672d3ef8fcba708fc19e70daec7c790e`，已以Root GitTree直接核对。
- Root候选 `v3-robocasa-manual-eval-20261022`、Child独立 `v3-robocasa-eval-lifecycle-20261022`，**未合并到V3**；Codex归档 HEAD `e4f6c8a62993d83dc27c285ce9e223eeefee7f65` 并非Implementation SHA。
- 旧Baseline Root `c6d6dab11c97f87e94b8b8bd3601bab02dce33f8` / Child `35b0ea1ccee9ee26653ed6589c484f0997d1c586`。经GitHub compare，Root功能变更只在 `scripts/eval_robocasa_18task_queue.py` (+223/-104)、新增 `scripts/robocasa_processes.py` (179行)及两项CPU测试、Child Gitlink；Child仅修改 `cosmos_framework/simulation/robocasa/closed_loop_eval.py` (+81/-41)和新增定向 `closed_loop_eval_lifecycle_test.py` (119行)。SESSION/TODO只是增量协作记录。未触碰模型、训练器、optimizer、DCP、Local-TTT fast-state算法或配置身份权威。
- 另一候选 G1 cross-pair Resume `b910304d…/61bfa947…` 在**不同**隔离分支，绝不可机械替换这次的Child Gitlink；将来若两者需要合并，同步新Root/Child将是一个**新的整合Formal Pair和独立Gate**。

## 2. 合同→生产行为→直接验收

### HIGH-09（旧环境已观察的session-limit雪崩）— Batch A 实现范围 CLOSED，仍待真实模型E2E

- 原Queue为每GPU单个持久ActionServer跨Task复用；Child `OnlineLocalMemory(max_sessions=1)` 若客户端被SIGKILL、卡死或reset失败，先前session可能占唯一槽。新Root `scripts/eval_robocasa_18task_queue.py:401-628` 将Server/Simulator **均放在每Task生命周期**中创建和回收，默认且唯一允许的 `--server-lifecycle per_task`；每个Task启动新Server与新的Local session state，失败后不直接复用旧Server。没有引入TTL、新State静默清理或扩大`max_sessions`来遮掩。
- 同脚本 `--on-infrastructure-error stop` 是默认（失败即全局停止）；明确`continue_with_new_server`适用于诊断，异常Task保留worker_error、`status=INCOMPLETE`、`sr=null`、原primary error，下一Task必须新Server。Cleanup failure总是停止，不允许假COMPLETE。

### HIGH-11（任务卡死）— Batch A 进程超时实现范围 CLOSED，Batch C配置体验仍待开发

- 新 `scripts/robocasa_processes.py:1-179` 中 `OwnedProcess`以 `Popen(start_new_session=True)` 启动**自有** Server/Simulator进程组，Linux PR_SET_CHILD_SUBREAPER(36)协助回收孤儿孙进程；`/proc` PGID监督与 `os.waitpid(-pgid)` 用于有界销毁；先SIGTERM再grace后SIGKILL，仅限拥有的PGID，不使用`pkill -f`、不探测或终止其他Owner训练。平台不支持/无法验证时不假绿。
- `EpisodeProgress` 按 `schema=psm_episode_progress_v1`、不可变Eval digest、episode 0..N−1顺序严格读**完整**start/end JSONL；不允许外来digest、截断、双start、缺end或超长event伪造完成。服务器端未加模型请求logger作为身份权威；Task wall截止和Episode monotonic clock由父Queue观察，子进程时间戳无法延长deadline。
- Root `supervise_simulator()`逐次检查真实sim退出、server存活、Owner cancel、Task deadline、Episode deadline、进度协议完整性。只验证进度不足以报成功，退出后仍由原 `task_result()/validate_task_results()`检查相同digest且每Task指定N个 typed result。
- Root Queue新CLI区分server_start_timeout_s、predict_request_timeout_s、episode_wall_timeout_s、task_wall_timeout_s、terminate_grace_s；原`--timeout`只作startup/request默认，不再把HTTP timeout误当整体wall-clock监督。
- `Child closed_loop_eval.py:220-372`在env.reset之前进入try/finally（旧client原本已有正常展开的finally）并对媒体错误/Local reset cleanup错误记录独立`rolloutXX_cleanup.json`，主错误优先，全部episode evidence写入后发出end event；任一runtime_error停止当前task并由Queue销毁整个Server/Simulator组。实际 `Env make_env` 在写Episode首个start前，Supervisor以无进度时的episode wall预算覆盖初始化/结束停滞。原for-step raw15执行/Local evidence action逻辑未修改。
- 每Task生成 `commands.json`、`server_info.json`、`server_process.json`、`episode_progress.jsonl`、`process_cleanup.json`、各Eval日志及原JSONL/partial MP4。新的复用/ID机制仍拒绝foreign listener与错误checkpoint/config/mode，或错误iteration/job；旧 `--no-guardrails` 和chunk16不受影响。

## 3. 作者Evidence独立阅读

在固定候选归档 `docs/collab/codex/evidence/2026-10-22_RoboCasa_manual_eval_Batch_A_author_cpu/` 直接核对 `gate.json`、`final2.xml`、`identity-regression.xml`、`static.log`、真实生产/测试源码与测试路径：
- 最终Focus **72测试方法 +61 subtests**，JUnit133为含subtests的bookkeeping数，0failed/error/skip，36.443s；
- 另定向回归 **20 passed**，0failed/skip，2.728s；其他50deselected属预期范围；
- 合计作者报告 **92 passed +61 subtests**，Ruff0.12.7 check/format（6改动Python文件）、py_compile、diff检查均PASS。此前进程mock、TIME_WAIT、legacy late-Popen预期失败被保留，最终用实际流程回归，不是删除断言硬过关。
- CPU测试在真实`queue.main()/immutable identity`上使用本地临时Git repos、stdlib HTTP/进程组和Linux信号，取代的只是 Cosmos Model及robosuite模拟器的外部执行；1/2/8 workers ×4Task×5(8worker有idle)真实process管理fixture；HTTP400、session_leak、sim SIGTERM/SIGKILL、kill超时、missing progress/results、cancel、异步init失败、reap后cleanup故障与foreign process存活。Child测试直接AST执行未改`run_policy`函数主体并替代真实env/predict/media，验证普通异常优先于reset错误，以及cleanup见证和正常行为。
- **没有**独立DS目标机CPU复测、真实模型/实际8GPU Server/Simulator PID树、真实 RoboCasa env reset、视频codec、真实物理等价性。作者test的synthetic MP4只是占位，不能冒充真实视频成功证据。

## 4. 当前finding / 执行边界

- **Batch A范围内新发现的阻断性 production bug：未见。** HIGH-09会话跨任务复用已从生产设计中移除；HIGH-11 Task/Episode真正Wall时限与owned PGID清理已引入；并验证了故障不把正式SR假标COMPLETE。上述 **CLOSED仅限合成CPU源码Gate**，不是现场真GPU验收结论。
- **Batch B仍独立 `REQUEST_CHANGES/BLOCKED`**：真实RoboCasa/robosuite SHA/MuJoCo原生版本/旧DS四处兼容补丁需由DS read-only取证，尤其LEGACY移动底座控制器的语义不等价风险；当前脏editable环境的历史1/20 SR仍是诊断，不能当正式physics-consistent benchmark。
- **Batch C尚未实施**：`run_robocasa_eval.sh`、YAML/CLI选择任务/GPU/episode/视频none-first-all、list-tasks/dry-run、依赖版本进入identity及中断Task的全新attempt Namespace恢复等功能本次没有提交；不可宣称Owner已有可执行统一Launcher。
- **真实执行禁止**：未经Owner明确释放GPU与新Pair代码/DS focused CPU Gate、Batch B有效依赖/正式runbook Gate，不得真正启动18Task、旧训练或模型；不可修改现存G1 Config/Checkpoint/JobIdentity和DS脏Vendor工作树。
- 本Root/Child Candidate不能直接与 G1 Resume的两个不同 gitlink 拼接；后续两功能集成应生成新的精确正式Pair并复审。

**Formal Code/Author CPU Gate verdict：`APPROVE`，严格限于新 `7646d414/e42a2468` Batch A scoped。** DS可对这个exact Pair做定向独立CPU验证；未来Batch B/C须各自新Gate。
