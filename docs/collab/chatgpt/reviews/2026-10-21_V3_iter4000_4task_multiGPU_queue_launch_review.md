# PSM-WMA V3 — iter4000 四任务×5 Episode 多 GPU 队列启动申请独立审核

- 日期：2026-10-21
- Scope：静态代码与运行指令审核；**不授权 GPU、仿真、DCP 写入/修改或训练**
- 审核时远端 V3 Root：`1e00a3d978442dbbb2865b08f41535bbd26a4ce7`
- Child/Gitlink：`2d128ed5a07601cdd424974f99b67832eafeeb41`
- 审核对象 Blob：`scripts/eval_robocasa_18task_queue.py` `6833b6ab6d17b85f7a840014ca400bc1dd6424ed`
- 执行服务器本地训练 Root `e0121d...` 与本次远端 Root 的等价性尚未由 GPT 直接验证；DS_PRO 必须现场核对运行脚本 Blob、Root/Child/Gitlink 与洁净状态。

## Verdict

**`REQUEST_CHANGES`**。当前队列脚本存在可静态确认的 HIGH 级死锁和 Server 身份错配窗口。不得按原命令直接运行。此 verdict 只涉及 iter4000 四任务 screening 入口，不重开已关闭的 F0/F1/G0/G1 或离线数据 Gate。

## Findings

### HIGH-01 — 同一不可重入 Lock 嵌套获取，任务完成/异常路径死锁

- File: `scripts/eval_robocasa_18task_queue.py:194,210-232,375-388`。
- Root cause：`result_lock = threading.Lock()`；worker 在 `with result_lock` 内调用 `publish()`，而 `publish()` 再次 `with result_lock`。异常分支同样如此。
- Violated contract：四任务必须产出终态 `screening_summary.json`、完成 worker join，并安全清理 action server；当前第一个 task completion 或 worker-level exception 可永久卡住。
- Acceptance：Codex 仅在 root 队列实现范围消除嵌套加锁，CPU mock worker test 证明 4 tasks×5 results、正常完成、异常分支、无残留线程、summary/RC 正确；不允许靠跳过 publish 掩盖问题。

### HIGH-02 — /info Ready 未校验本次实例的 Checkpoint/Config

- File: `scripts/eval_robocasa_18task_queue.py:64-79,236-280`。
- Root cause：现有 `wait_server` 只检查进程未退出、HTTP `/info` 可读、Local mode=`required`，未绑定目标 `iter_000004000`、config、`raw_action_dim=15`、`requires_state=true`，且没有启动前端口占用拒绝。
- Violated contract：4×5 SR 必须全部来自指定 checkpoint/config/mode；占用8912等端口的旧 action server 可能冒充 Ready，导致错误模型结果混入。
- Acceptance：启动前拒绝非空闲所需端口；Ready 后验证响应中的 `checkpoint`、`config_file`、`raw_action_dim`、`requires_state`、Local required、采样参数，并复核本次 server 进程仍存活；CPU mock 旧server/错模型/端口冲突全部 fail-closed。

### MEDIUM-03 — expected-tasks=4 只校验数量，不校验四个指定 task names

- File: `scripts/eval_robocasa_18task_queue.py:39-61,164`。
- Root cause：基于 `env_args.env_name` 构建映射后只验证 `len(mapping)==4`。
- Violated contract：本申请明确指定 `{CloseFridge,TurnOnSinkFaucet,PickPlaceSinkToCounter,NavigateKitchen}`。
- Acceptance：Codex 在只读执行前检查/运行说明中断言实际 `env_name` 集合精确等于这四项且元数据唯一。无需为此新增通用任务过滤框架。

### MEDIUM-04 — --resume 仅能复用完整 task，不支持中断于 5 Episode 中间

- File: `scripts/eval_robocasa_18task_queue.py:195-206`；`scripts/v3_evaluation_identity.py:129-153`。
- Observed：如某任务 `results.json` 已有1–4条，`--resume` 会被 `expected_trials=5` 校验拒绝；`rollout_evidence.py` 的独占写入防止覆写历史轨迹。
- Boundary：本轮不要求开发 mid-task resume；Codex 必须写明重新运行时对完成 task 的 reuse 规则以及不完整 task 只能在新隔离 namespace 重新执行，保留原始 partial artifacts，不删除/覆盖。不得宣称 5 Episode 中断可无损继续。

## 已确认的兼容部分

- 队列 CLI 支持 `--checkpoint-path --dataset-root --output-dir --server-python --sim-python --gpus --expected-tasks --num-test-episodes --action-horizon --seed --base-port`。
- `--expected-tasks 4`、`--num-test-episodes 5` 对应计划20个 Rollout；单 worker 固定 GPU，一次加载一个 server，依次运行队列任务。
- server/client 默认 raw-action-dim15、fps20、left_wrist、state、base raw、required、success_latch1、image/cam256，`--num-steps`默认30、guidance默认1.0。
- `closed_loop_eval.py:get_env_metadata/make_env` 只从 task dataset_dir 读取 `extras/dataset_meta.json` 构造仿真环境；据此元数据-only 目录在代码读取契约上可行。实际 RoboCasa/Robosuite 依赖由 DS_PRO 在真实环境只读验证。
- `--seed 0` 是每个 task 的环境主种子：每 task 的5次循环 reset；不要把它误称为5个显式独立 seeds。
- 这是一轮 iter4000 4-task screening，不是18-task/多 seed 正式 Benchmark，也不是 Local-TTT 对照实验结果。

## Codex 限定任务（先整改后再申请 GPU release）

1. 只准修改 root `scripts/eval_robocasa_18task_queue.py` 与新增/定向 root CPU 测试。保留当前 `scripts/v3_evaluation_identity.py`、child 仿真/模型/Action ABI、训练/DCP；若发现必须越界改动，STOP 重新提案。
2. 对 HIGH-01 和 HIGH-02 做最小修复。必须测试正常 worker 完成、worker failure、stale server、occupied port、错误 checkpoint/config/mode，验证 summary、RC、server shutdown、无 hang。不得 GPU/torchrun/simulator real run。
3. 以只读元数据预检验证恰好四个 task。给出准确参数的手动运行命令，显式使用 `--server-python`，明确 `--num-steps 30 --guidance 1.0` 与运行 digest/版本身份。
4. 不要求新独立 wrapper；以现有 queue 脚本作为 canonical。不得复制新 orchestration 主逻辑。
5. 完成后先提交新精确 Root SHA + Child/Gitlink、范围 diff、CPU test 结果和 DS_PRO 只读准备指令，再请求 GPT 新 formal pair 增量 review。当前不批准 DS_PRO GPU 启动。

## GPU 后续前置（本轮不授权）

- Owner 明确授权后且 GPU 已释放、现场剩余显存足以同时运行 1 server+1 simulator 时启动；当前 wzy 每卡约72–74GB占用，禁止抢占/共享启动。
- `--gpus` 必须是 DS_PRO 现场确认空闲的 GPU IDs；最多4个，1/2/4卡按可用资源串行/并行队列运行；不得使用默认 `0,1,2,3,4,5,6,7`。
- 验证 iter4000 Checkpoint `complete.v1.json`、Model DCP 与训练配置及存储余量；检查 base-port 对应每个 worker 端口空闲。
- 输出新 namespace，记录 source Root/Child SHA、Checkpoint/Config哈希、task metadata digest、GPU、server_info、随机种子、Episode outcomes、all MP4、异常；任何错模型或缺失Episode不能算有效 SR。
- 完成 4 tasks×5=20 episodes 且无 runtime_error、每任务 `validate_task_results` PASS、每任务5个 nonempty rollout MP4、完整 summary 后才验收。失败任务可保留 failure 轨迹，但不得将 runtime_error 计入任务行为失败。

## Authoritative links

- Queue: `scripts/eval_robocasa_18task_queue.py` at Blob `6833b6ab...`
- Evaluation identity: `scripts/v3_evaluation_identity.py`
- Child: `cosmos_framework/simulation/robocasa/closed_loop_eval.py` and `cosmos_framework/scripts/action_policy_server_robocasa.py`
- Request: DS_PRO owner-pasted 2026-10-21 iter4000 4-task×5 episode application.

**Review provenance：只读 GitHub 源码静态审核；未访问训练服务器、未执行 CPU tests、未启动 GPU/仿真。**
