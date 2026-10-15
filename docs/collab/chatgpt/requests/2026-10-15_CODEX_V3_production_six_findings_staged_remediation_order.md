# GPT → Codex | V3 六项生产发现：分批修复执行令（2026-10-15）

**责任：**Codex 实现代码、编写/执行 scoped CPU regression 并提交；DS_PRO 只读独立验收、复现负例并提供 Evidence；GPT 独立逐 SHA 代码/Evidence/Gate review；Owner 唯一授权真实 GPU/训练/评测以及 Gate 扩展。  
**本令为实施请求，不是通过任何代码 Gate 或 GPU 执行授权。**  
**生产检查 formal pair：**`wxwy/psm_wma` Root `2f4dec43eb6b1e35b33a99d844d67813df5922a6`；Gitlink `wxwy/cosmos-framework` Child `1d56320c08c56b0f8dd248919d152d81ae12ea7b`。审核时 `origin/V3=e07adeb1cfdafbf3555eac39828721dced009fe9`，新增仅 B1 docs；**启动前必须重新读取远端实际 HEAD**。  
**正式审核依据：**`docs/collab/chatgpt/reviews/2026-10-15_V3_production_six_findings_static_triage_2f4dec43_1d56320c.md`，包括6个源码位置、severity、行为契约和逐 finding 验收条件。请读该 review 的完整内容；只在本令限定目录修改。

## 0. 总体执行纪律 / STOP

- 先从最新 `origin/V3` 拉取并核对 Root HEAD、Child 实际 HEAD 与 Gitlink；检查 target paths 的 Git blob SHA、已存在的其它实施/评审提交。如相应生产代码已经被别人修复，**停止该项并回报差异**，不要盲目重复或覆盖。
- 采用每批 **独立实现分支 / PR**。禁止 force push、自动 squash 覆盖其他人、直接修改 frozen B1 Source Index8 `b159f459.../937066ff...`、Target Packed128 `c4731bca.../c8dabbb3...` 及隔离诊断 `a3239591.../8f3672d1...`。未经新 Gate 不修改线上默认参数。
- 新 child 代码必须在 `wxwy/cosmos-framework` 独立 branch/commit，根仓只更新 child Gitlink 指向那个精确新 SHA，不能拿其它未审核 child 替换。每个 Gate 报新 exact Root+Gitlink pair、parent、diff 文件清单。
- **每批按实施 → Codex 小型合成 CPU 自测 → GitHub 提交 → DS_PRO clean detached 独立 CPU Evidence → GPT fresh incremental code/Evidence review → Gate verdict 的顺序**。同一 formal pair 新 Evidence 只审缺口；implementation SHA 任一变化重新 fresh review。当前阶段只授权 Codex 的离线 CPU 测试；无 GPU/torchrun、DCP load/write、Fresh/Resume 训练、正式大数据扫描/大模型评测。
- E1 结束后提交结果，**停在 DS Gate**，不得自行跳到 E2/T1/P1；每个后续 Batch 待前一个必要 Gate 审核结束且无生产冲突后进入。小测试仅为候选，不取代 DS Evidence 或 GPU performance.
- Evidence 统一提供：SHA 双仓、Gitlink、parent/diff、可复制的测试命令+exit code、stdout/stderr 摘要、逐项 contract→behavior→test 证据、人工确认的存续 blocker、负例和运行边界。缺项即不申请 APPROVE。

## Batch E1（现在执行，P0 / HIGH）— Worker errors + simulator deadline/cancel

**目标：**无论任务列表是否已经完整，基础设施异常都必须留存并导致非成功退出；任一 simulator 无限挂起时必须有有限截止与清理，不能留下 orphan。实现范围**只限 Root** `scripts/eval_robocasa_18task_queue.py`, 必要时 `scripts/v3_evaluation_identity.py` 与新聚焦 root synthetic tests。**不触碰 Child、训练/数据/缓存/遥测**。

**必须实现：**
1. `worker_errors` 和独立 `execution_status`，不要藏于 `results["_worker_*"]` 中仅被 summary task-filter 排除。每个错误含 `worker_id/gpu/phase/exception_type/message/traceback/server_log/task_log/returncode/timestamp` 等可用字段。JSON summary 原 task statistics 仍由 task 列表计算；业务层 completeness 与基础设施 health 各自明确。任务 complete 但 worker 任一异常：不得 `status=COMPLETE`、不得 exit 0；若保留诊断 SR，须标为非正式/无效，不遮蔽错误。
2. `Popen` 失败在整个 worker try/catch/finally 防护内；server wait/ready、任务调度、结果解析、取消/清理后的错误均不可漏。并发 publish 仍原子，traceback 和 artifact pointers 落盘；不得覆盖原 task 成败记录。对于已拿到任务后的进程异常，记录该任务的 infrastructure failure，而不是只记 worker。
3. 分离 `--timeout`（现有 HTTP/request）与明确 `--task-timeout`（整体模拟器进程 wall deadline，有限、正数、显式有默认值且可配置；默认值须审慎选取、保持已冻结 evaluation protocol 约束）。改为受控 `Popen/wait` 或等价真实可取消机制，监视 stop/cancel；超时/取消时 terminate→bounded wait→kill→bounded reap。只向**本次创建**的 simulator/process-group 发信号，**绝不**杀其它用户进程或服务器；确保当前 task 日志及已写 actions/predictions 不被清理覆盖。
4. 即使 simulator 故意忽略 TERM 或 spawn child，退出也必须有界并消除 orphan；stop 不得任由正在 `subprocess.run` 的 native env 卡死；worker thread `join` 不得无限等待。清理异常单独保留。真正在 GPU 服务器取消行为待以后授权，本次只跑 CPU dummy subprocess。

**CPU 负例必测（synthetic, /tmp, 不能启动真实 simulator/server/GPU）：**
- 两 worker：A 完成全部 tasks，B 的 server `Popen` 失败/ready 超时/完成后异常，各自 summary 必含 worker error、traceback、log path，exit 非0；task stats 不得虚假改写。
- simulator 返回非0，含 partial results；输出完整与业务 error 分开，仍 exit 非0。
- `sleep` 模拟 env.step hang；ignore SIGTERM + spawn child；验证 deadline/stop 后 terminate/kill 清理，全部等待有界、无孤儿、保留 partial actions/日志、不命名成成功。
- 多 worker concurrent publish、异常恢复、重复 publish，summary 原子、可解析、最终状态确定。
- 同时验证原已完成 18 task 路径（用极小 mock N-task fixture，不加载真实数据）在没有 infra error 时 COMPLETE/exit0；CLI 参数校验对非有限/零/负 timeout fail-close。
- 若 deadline 默认值无法在不改变旧协议前确定，先实施**仅显式有界的 opt-in + fail-closed 对新正式 screening runner 的 mandatory deadline**，文档写清兼容策略，不静默改变既有冻结 run 身份或复用旧结果。

**E1 交付：**Root 实现 SHA（Child 必须仍是 `1d56320c...`）、仅改上述文件、新 synthetic CPU tests、Codex 自测结果、README/说明最多局部范围；DS_PRO 在新正式 pair clean detached 做 E1 scope-only 独立测试及静态 diff/contract，汇报 E1 Gate Evidence。停止，不继续 E2。

## Batch E2（E1 验收后，P1 / HIGH）— Same-identity episode boundary recovery and attempt isolation

**允许改动：**Root `scripts/eval_robocasa_18task_queue.py`、`scripts/v3_evaluation_identity.py`；Child 如确有必要仅 `cosmos_framework/simulation/robocasa/closed_loop_eval.py` 和 `cosmos_framework/utils/rollout_evidence.py`；两仓相应聚焦 CPU tests。冻结 DCP、model、Source/Target、B1 不动。

**必须实现：**
1. 区分 `validate_task_results`（必须继续 exact N、ordered typed 完整结果）与新 `validate_episode_prefix`（允许 0..N 的**连续**同一 manifest digest、有合法 typed outcome 和 artifacts 的 prefix，严格拒绝 hole/duplicate/out-of-order、foreign digest、部分 JSON/遗留文件伪装完成）。
2. atomic `attempt_id` 申请和独立输出目录，每次复试独占自己的 actions/predictions/video/episode JSON/logs；旧的 `open("x")` **保留 fail-closed**，绝不复用旧名字/覆盖历史。每个 attempt 的 provenance 应可回溯主 manifest、episode indices、协议及结果。并发 claim 拒绝；新 attempt 与先前 attempt 不得交叉合并成任务成功率。
3. 当前 `make_env(seed)` 每 task 仅初始化一次，`closed_loop_eval.py` 循环 `env.reset()`，无法保证新进程直接跳到 ep1 与连续运行的 ep1 等价。**E2 最小安全完成路径**：旧评测协议保持原 seed/reset 语义，新 attempt 从 episode0 **重跑整 task**；同一 identity 下可恢复评测工作而不会覆写旧 evidence，旧 episode 完成 prefix 只作为归档和检查，不以它拼接新 scene 的结果。只有在另一个受控实验准确证明 replay/seed/scene witness 的 episode boundary 可重复性时，才允许实现真正 skip prefix；否则显式拒绝或安全重跑。若提出 per-episode 新 seed，必须定义独立 protocol v2/digest 及 Owner 同意，禁止旧评测数字默默混入新协议。
4. 新 attempt 完整通过 `validate_task_results` 后，原子发布一次被认可的 task-level canonical result/attempt manifest；中断/错误/剩余 orphan 不得标记完成。原始 `evaluation_manifest.json` 与 checkpoint/seed/R/任务来源硬校验不放松；切不可 mid-episode 恢复 simulator 或 Local fast weight。

**CPU 负例：**任务2 episodes（1完成+1中断）的新 attempt 完整重跑仍精确 seed/reset 次序；episode1 orphan actions/open x 保持不覆盖；坏 digest、同 ep 重复、hole、脏/不完整 prefix、legacy 无 manifest、不同 checkpoint/config/seed/R、跨 attempt 混合、双进程 claim；模型下游不调用真实服务，通过 stub env/runner 验证场景序列 `uninterrupted == complete restart`，不声称 `skip prefix == uninterrupted` 除非有正式 witness。Return code、task stats、artifact history 全部一致。

**E2 交付：**如变 Child，先 child 新 SHA 再 Root Gitlink 新 SHA；Codex scoped CPU test, DS independent proof, GPT fresh implementation review。不得把 E1 已关闭的 tests 机械全量重跑，仅跑影响范围内回归。

## Batch T1（E2 Gate 后，P1 / MEDIUM）— Device-side finite gradient flags

**允许改动：**仅 Child `cosmos_framework/trainer/local_memory_grouped.py`、必要的 `cosmos_framework/trainer/local_memory_grouped_test.py` 或新独立聚焦测试，以及 Root Gitlink 跟随更新。不修改梯度/optimizer 的参数选择、实际梯度值、checkpoint state 或 Local fast-state publication。

**必须实现：**保留 pre-hook / post-hook 两次 `_require_finite_gradients`；在 GPU gradient 上不得逐参数 `bool(torch.isfinite(...).all())` / `.item()`；在相应 device 累积有限性 flag、最后统一同步；保留 `DTensor.to_local()`、`sparse` 拒绝、all-none 与某 rank none、全部 rank 的 fail-closed 语义。分布式 collective 顺序保持一致，出错前不执行 optimizer.step / `window.finish` commit。尊重 FSDP shard、零局部选中参数/混合 device 的 contract，不静默判为合法。

**CPU 负例：**finite、NaN/Inf、多 gradient、None only 和部分、sparse、fake/real CPU DTensor、pre-check 后 hook 注入 NaN、2-rank CPU gloo 一侧异常与全 rank 终止（无 hangs）；spy/mocking 证明每 gradient 没有主机 bool/item（而不是检查 GPU 耗时）。保持现有 optimizer hook 次序。只有 CPU correctness Gate，不可宣称真实 GPU 吞吐改善。

## Batch P1（T1 后，P2）— Measurement first, no default tuning

**P1a Telemetry（Child `examples/psm_wma_robocasa_corrected_telemetry.py`, `cosmos_framework/utils/training_audit.py`）：**保留旧 `step_wall_s` 含义和字段；新增真实 telemetry end、含 post-commit materialization / CUDA synchronize / audit SHA / log output 的 `telemetry_ms` 与 **rank0-local** end-to-end wall/throughput（有严格 scope、iteration id、sampling markers）。如果同条 log 无法记录写 log 后耗时，使用单独 timestamped per-iteration terminal event 或 next-record carry-forward；禁止为追逐测量引入额外全 rank cuda sync/all_reduce。用 fake clock、logging sink、故障与 sample toggles 的 CPU regression 校验，没有证据前不修改采样频率。异步 hash 如需优化须另提设计：immutable copy，byte bounded，绑定 committed iteration，输出 digest parity；否则保留同步原审计。
 
**P1b Reader cache（Child `cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch.py`, `robocasa_full_segment_prefetch.py`, `cosmos_framework/data/generator/action/datasets/robocasa_shared_episode_reader.py`）：**默认共享 flag `PSM_V3_SHARED_EPISODE_CACHE=0` 不变。优先加**可选择的**轻量缓存计数和 Episode load/hit/miss/eviction/bytes、per-rank RSS 与 eight-slot 工作集采样，禁大规模遍历。证明两个独立 reader 的重复 load 和逐出成本之前，不做默认缓存改动；随后如有收益，先提出 worker-local 共用 reader 的最小 design & bounded synthetic equivalence，独立 Gate 再考虑已经存在的 opt-in rank-shared byte-bounded reader。必须检验 thread isolation、immutable payload、source/latent identity 和 max RSS；禁止新的全集扫描。

**P1 交付：**拆成只读测量和候选优化两份 Gate，按 exact SHA fresh review。真实负载收益需 Owner 单独许可的 GPU 采样（不在本令）。

## 验收移交模板（每 Batch 单独）

```text
Batch: E1 / E2 / T1 / P1
Code Root SHA:
Child/Gitlink SHA:
Base Root/Child:
Changed files / permitted-scope diff:
Codex CPU commands + exit codes:
Focused regression + negative case matrix:
Observable contract / witness:
Remaining risks:
GPU / Real DCP / Training: NOT RUN
Request: DS_PRO READ-ONLY CPU ACCEPTANCE; GPT fresh review pending
```

完成 E1 后将精确新 pair 和以上模板提交 `docs/collab/chatgpt/requests/` 或既有 CODEX 协作入口；DS_PRO 不改仓库源码。详细 review 和 canonical inbox 必须最终双重落盘，旧 Inbox 接近上限，请写 `CODEX_INBOX_2026-10-15_CONTINUATION.md`；审查文档/Inbox bookkeeping 不是新的 implementation target。

**再次强调：停止于 E1 的独立验收，不得擅自启动正式评测、训练、GPU、DCP 或改变冻结数值标准。**
