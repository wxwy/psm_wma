# V3 Production 六项源码发现 — 增量静态审核与修复裁决

**日期：**2026-10-15  
**角色：**GPT 独立 Code / Design / Gate reviewer  
**正式生产实现基线（Root / Child）：**`2f4dec43eb6b1e35b33a99d844d67813df5922a6` / `1d56320c08c56b0f8dd248919d152d81ae12ea7b`。核验时 `origin/V3=e07adeb1cfdafbf3555eac39828721dced009fe9`，相对基线仅有两项 B1 审核文档提交；生产源码和 Gitlink 不变。  
**范围：**仅用户提供的六项 production findings 的真实源码局部复核与修复规划；不是 V3 全仓审核，未运行 GPU、真实 DCP 或训练；用户报告的合成 CPU 复现为外部证据，GPT 未自行运行。  
**独立 B1 诊断不受本审核影响：**`a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`，B1 CFG CPU closed、GPU 仍待独立 Owner 授权。不得移植/替换 B1 Source/Target 冻结版本或混用 Child。

## 总裁决

- **P0 HIGH / implementation blocker before next new formal screening:** #3 worker 基础设施错误不可丢失；#6 simulator subprocess 必须有可取消的整体 deadline 与清理。**一并做 Batch E1，先于恢复功能。**
- **P1 HIGH / evaluation resume correctness:** #2 同身份 episode prefix、独立 attempt、不覆盖旧证据、Seed/Reset 语义。**Batch E2**；实现前注意现有 `make_env(seed)` 只在创建 env 时设置 seed，`for t: run_policy` 连续调用 `env.reset()`，无 per-episode RNG checkpoint；从新进程直接跳到 episode 1 不能声称场景相同。旧协议安全基线是新 attempt 从 episode 0 重跑整 task，直到证明严格 scene equivalence 才可跳过已完成前缀。不得静默改变 seed 协议/评测 digest。
- **P1 MEDIUM / performance remediation, not established correctness defect:** #1 CUDA parameter-wise host sync。**Batch T1** 保留前/后 hook 两处验证和 all-rank fail-closed，合并本地有限性 flags，减少逐参数同步；提升幅度只能以后测量。
- **P2 MEDIUM instrumentation correctness:** #5 step wall 口径未含 post-commit；**Batch P1a** 新增独立 telemetry/end-to-end 口径并保留旧字段，实际优化先测量。
- **P2 LOW measurement-first:** #4 Source/Raw 每 worker 两个独立 episode reader（当 rank shared 缓存 flag off），各只有 2 entries；**Batch P1b** 先做定量 working-set / RSS / torch.load / evictions 证据，满足数据等价后再判断 worker-local 共用 reader 或 rank-shared opt-in。不得默认打开缓存或进行451GB扫描。

建议实施顺序：**E1(worker/errors+timeout) → E2(resume/attempt) → T1(gradient) → P1(telemetry measurement + cache counters) → 仅测量论证充分后另立缓存/采样调优 Gate**。P1 的只读监测设计可并行，但不同 implementation SHA 分别 Gate；禁止打包六项一次审批。

## Finding-03 — HIGH / confirmed code hazard / E1

**位置：**Root `scripts/eval_robocasa_18task_queue.py:379-388, 210-232, 406-415`；`scripts/v3_evaluation_identity.py:155-177`。  
**根因：**worker outer exception 写 `results["_worker_N"]`，而 `publish()` 只取 tasks 名称，`screening_metrics` 仅考察 task rows；main 最终检查 `missing/failed` tasks，而不检查 worker_errors。另：`subprocess.Popen` 在 worker outer try 之前（queue.py:270-278），启动失败可成为未记录线程异常。  
**违反契约：**执行失败证据/退出状态不可与 task-count completeness 混淆；`COMPLETE` 与 exit0 不得遮蔽 worker infrastructure error；不得伪造或回填成功率。  
**验收条件：**按 worker 结构化记录 `execution_status, worker_errors[]`，包含 worker ID、GPU、phase、exception type/message、traceback 和日志/路径、失败 exit code；final exit!=0 且 `execution_status != COMPLETE`，即使所有 tasks 自身均完成。Task-level counts、task outcome、success 等保留原值，官方可用 SR 不得在基础设施失败时被标记为完整有效。server Popen 失败、wait_server 失败、post-tasks worker fail、非零 simulator returncode 与多 worker 并发发布均有合成负例；保留错误和原输出，禁止删除历史证据。

## Finding-06 — HIGH / confirmed unbounded wait hazard / E1

**位置：**Root `scripts/eval_robocasa_18task_queue.py:335-343, 397-404`。  
**根因：**`subprocess.run` 无总 timeout；子进程在 native `env.step` 卡住时 HTTP `--timeout` 无法释放；worker 的 thread.join 无有效上界/取消链。  
**违反契约：**所有外部 simulator 子进程、拥有的 descendant 和 worker 的等待都必须被可配置总 deadline 与显式取消绑定；不干涉其他用户进程。  
**验收条件：**保留 HTTP timeout 的独立含义；显式进程级 task deadline + graceful terminate/wait + bounded kill fallback，POSIX 只清理本次创建的进程组/子进程，不能动其它 GPU/server；stop event 触发时可中止正在运行的 task；超时、取消、强杀分别写 typed infra failure / partial evidence pointers、stdout/stderr/traceback；worker join/所有 wait 有最终边界。合成 sleeping/ignoring-TERM/process-child/orphan/stop 测试全部退出有界；保留已有 on-disk partial evidence，不得宣称完整 video。

## Finding-02 — HIGH / proven failure on partial resume / E2

**位置：**Root `scripts/eval_robocasa_18task_queue.py:196-206`，`scripts/v3_evaluation_identity.py:104-125,129-153`；Child `cosmos_framework/utils/rollout_evidence.py:52-65`, `cosmos_framework/simulation/robocasa/closed_loop_eval.py:440-449,479-515`。  
**根因：**strict full-length validator 被用于中间 prefix；半途失败产生 `rolloutXX_actions.jsonl`，下次 `open("x")` 与相同 basename 冲突；模拟器仅构造一次 seeded env，顺序 reset 消费状态，不能安全认为跳过 prefix 不改变后续场景。  
**违反契约：**manifest 固定 source/checkpoint/seed/protocol；有效 episode prefix 必须连续、完整、同 digest、带 typed outcome 和证据；尝试必须隔离且 append-only，不得覆盖/混合/降低历史错误。  
**验收条件：**新增严格 prefix-validator 而非放松已有 full validator；独立无冲突 attempt 命名空间和 atomic claim，保留每次失败/中断 evidence；1/2、orphan actions、坏 digest/duplicate/holes、同 ep retry、不同 seed/checkpoint/protocol、旧 format 和并发 claim 均 fail-closed；结果只能从一个被验收的 complete attempt 生成，不能拼接不同 scene/attempt 的任务 SR。最小安全 legacy 恢复：同 identity 下在新 attempt **task 从 ep0 重跑**，完整验证后发布；若要真正 skip completed episode，必须额外证明 replay 后 RNG/scene 与不中断一致，或明确新 protocol v2 + 新 digest + Owner 批准，绝不静默更改旧基线。不得做 arbitrary mid-episode simulator/Local fast-state resume。

## Finding-01 — MEDIUM / structural sync-performance risk / T1

**位置：**Child `cosmos_framework/trainer/local_memory_grouped.py:167-206,363-369`。  
**根因：**对每个 CUDA gradient 执行 `bool(torch.isfinite(gradient).all())` 触发参数级 host sync；hook 前后两次，且跨 rank all-reduce 均存在。静态可见；真实 GPU 性能收益未测。  
**违反契约：**任何非有限/缺失梯度都必须 fail-closed（所有 rank 同一结论），失败时不得执行 optimizer step 或发布 Local fast state；两个安全边界不可删除。  
**验收条件：**把所有本地 gradient 有限性归并为 device flag，不对单一 CUDA gradient 做 `.item()/bool()/tolist()`；最后在既有 collective 边界统一回主机；保留 DTensor `to_local`、sparse、None、不存在任何 gradient 的跨 rank语义、两处 hook 前后验证和无死锁，参数归属不能漂移。CPU 合成矩阵：finite、NaN、±Inf、all-none、some-none、sparse、DTensor local shard、hook 在第二次检查前写 NaN，以及两 rank gloo 异常单侧触发，全部检验 no-step/no-commit。未取得 GPU profiler 前不得承诺吞吐提升或改变 checkpoint/optimizer/模型行为。

## Finding-04 — LOW / measured optimization hypothesis / P1b

**位置：**Child `cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch.py:36-58`、`robocasa_full_segment_prefetch.py:58-78`；`cosmos_framework/data/generator/action/datasets/robocasa_shared_episode_reader.py:51-113`。  
**根因：**共享缓存开关 `PSM_V3_SHARED_EPISODE_CACHE` 默认 `0`，每 worker 的 Source/Raw 使用分别构造的 `RoboCasaExactWindowEpisodeReader(max_cached_episodes=2)`；重复加载/淘汰是合理风险假设，不是已测量的性能故障。现有 opt-in rank-shared reader 已提供 byte+entry bound 和 cache_stats；不应另造未经测量的 rank cache。  
**验收条件：**先采集每 reader 的 episode hit/miss/eviction、真实 torch.load 次数、RSS peak、loaded bytes、重复 key 与 eight-slot working-set 命中，在相同输入序列下对照；不要求全数据集遍历。若进一步修改 worker-local reader 身份，保证 immutability/owner isolation/TTL-free visibility、双路径完全一致、memory bound 和 fail-close；新 implementation 必须 fresh review，默认 cache flag 不变。

## Finding-05 — MEDIUM / measurement semantics / P1a

**位置：**Child `examples/psm_wma_robocasa_corrected_telemetry.py:461-585`；`cosmos_framework/utils/training_audit.py:204-209`。  
**根因：**`step_wall_s` 在 `_sample_cuda_events`、loss scalar materialization、`audit_record` fingerprint 和日志前读时钟；记录的 step throughput 不能代表包括 rank0 post-commit telemetry 的 end-to-end iteration throughput。已存在独立 `state_fingerprint_ms`，但不覆盖其余开销。  
**违反契约：**计时口径明确、不把 pre-telemetry time 标成 end-to-end；审计 fingerprint 必须绑定实际 committed iteration。  
**验收条件：**保留旧 `step_wall_s` 及其 scope 原义，新增清楚标注的 `telemetry_ms`（含同步、CPU快照/hash、日志）、对应 rank0 end-to-end iteration/throughput 指标和每个采样点实际是否可用状态；不额外制造全 rank collectives；如果日志写出成本不能包含在同一条 record，另写 iteration-indexed terminal event 或下一条 carry-forward，但不可漏记/错绑。before/after 计时和失败异常测试、不重复 commit/hashes；异步哈希仅允许 immutable bounded snapshot，必须证明旧审计 digest 一致，不得直接借用 live mutable sidecar；未经证据不改变默认采样频率。

## Gate 管理 / Fresh Review

1. Codex 仅在最新远端上开隔离实现分支；改动前比较 ROOT/Gitlink/目标 file blob；禁止 force push 或覆盖协作者提交。Root child 新代码须先在 child 独立提交，再更新 root gitlink，形成 exact new root+child pair；所有分批实现 SHA 各自 fresh review。
2. Batch E1 与 E2 为新**评测可信性** Gate；Batch T1 为训练代码静态/CPU Gate（不构成真实训练或 GPU 授权）；P1 先 instrument/measurement Gate，禁止静态报告冒充性能证明。
3. Codex 自行实施并做窄范围 CPU regression + negative；DS_PRO 只读 clean detached 在独立环境重新执行 scoped Gate、提供 SHA、命令、return codes、failure evidence；GPT 独立读取 diff/契约/test 然后 verdict。任一 failure `REQUEST_CHANGES`，新 SHA 必须 fresh review，不继承旧 appro­val。
4. 每批将 review 和 canonical handoff 写入 `docs/collab/chatgpt/reviews/` 与 append-only `docs/collab/chatgpt/CODEX_INBOX_2026-10-15_CONTINUATION.md`。Review/bookkeeping 只改变 V3 HEAD，不等于新的 formal implementation.
5. 当前不启动 GPU、Fresh/Resume、任何正式 DCP IO，不重跑 B0/451GB，不修改 frozen B1 Source/Target 或数字阈值。不做 V3 全仓审核，直到用户单独授权。

**Disposition:** static findings triage accepted; HIGH correctness/safety problems `REQUEST_CHANGES` on scoped production evaluation reliability, without any claim of GPU training failure or performance speedup. 此为修复指令前置审核，不是任何候选实现 Gate 的批准。
