# V3 RoboCasa 手动评测统一入口 — Frozen Design Contract

日期：2026-10-22
Owner负责手动启动与GPU分配；Codex负责生产实现；DS_PRO只做验收与证据；GPT独立设计/代码/Evidence Gate审核。
本文件是待实现的设计与验收契约，不代表下列CLI已经可运行，不批准GPU执行。

## 目标及版本

Owner每次只需修改一个YAML或覆盖几个CLI参数，运行同一脚本，即可选择CUDA GPU、并行仿真slot、任务子集、每任务episodes、Checkpoint、保存环境MP4和预测视频/JSONL、timeout、输出namespace、task-only resume。
此轮起点：已审实施Root ba91ebb7de2555cd1ff2a290d0af5ee43a8a3ee6，Child/Gitlink 35b0ea1ccee9ee26653ed6589c484f0997d1c586，Queue Blob 72ad7e2b94b31cbfd7a8af0a1eaff92127ffa7ae。当前远端V3 docs头可能变化，不可代替Implementation SHA。
DS报告iter8900：4-task×5真实结果COMPLETE SR=1/20；18-task×5八卡首轮INCOMPLETE，85/90 trials；worker07 Local-TTT session limit reached 138次；四处非提交第三方robosuite临时补丁。上述为DS提供的现场线索，并非GPT读取原始服务器日志的实测结果。

## A. P0 — Local-TTT session生命周期及任务硬超时

Finding HIGH-09：Root Queue scripts/eval_robocasa_18task_queue.py 中每个GPU启动一个Action Server并跨不同Task复用，Simulator通过无总wall deadline的subprocess.run执行。一次异常终止造成Server仍占有session(max_sessions=1)时，后续task依次失败。DS的worker07时间线与此机制一致。
重要源事实：固定Child closed_loop_eval.py的run_policy() 已经在finally中调用LocalMemoryClient.end(0)和reset_local_memory()，普通异常会尝试清理；仅重复加finally不解决SIGTERM/SIGKILL、进程卡死、保存MP4期间失败、网络reset失败或未进入完整生命周期的情况。

实现合同：
1. 正式模式默认 server_lifecycle=per_task。每个Task有全新ActionServer/Local-TTT状态；任务完成/基础设施失败/视频失败/timeout后停止自身服务，再运行下个Task。可以提供reuse_server_if_clean优化，但只有前一Task完整、/info的sessions=0及pending=0、清理成功且服务仍为自有进程时才允许跨Task复用；否则关闭并重启。禁止用Local mode off或max_sessions扩大掩盖泄漏。
2. 清理保留客户端现有finally，并对普通异常、HTTP400、环境reset、视频保存、reset失败等路径测试。原始错误不被cleanup错误覆盖，保存独立cleanup witness；异常任务结果必须INCOMPLETE。
3. 将Task Simulator改成受管Popen(process group)+monotonic deadline：server_start_timeout_s、predict_request_timeout_s、episode_wall_timeout_s、task_wall_timeout_s、terminate_grace_s。Episode开始/结束要有可观察的进度事件；当阻塞于模型请求、环境step或视频写入时，Queue仍能根据episode/task wall deadline杀死**仅本次创建的**PID/PGID，先SIGTERM再在grace后SIGKILL；永不执行全局pkill、抢占训练或杀foreign listener。CLI旧 --timeout 600 不是Task wall-clock保护，不能混同。
4. Task一旦 infra error 默认fail_fast，不污染别的Task。Screening允许continue_with_new_server，但worker_errors/失败task必须留在最终summary，整个Run不得标COMPLETE或提供误导性正式SR。超时可保留部分mp4/actions/预测和错误，需明确不等于合法完整episode。
5. 首轮不引入无界TTL自动回收共享Local-TTT fast-state；若设计TTL，另开pending/commit/abort race Gate。

Acceptance CPU：模拟第一个Task被SIGTERM/SIGKILL、request超时、无results、reset失败、视频encoder崩溃，验证下一Task绝不出现旧session contamination；Task/episode超时真实杀自有进程组而不误杀其他任务；不残留PID；no runtime_error->COMPLETE；正常1/2/8worker仍可复现结果。

## B. P0 — RoboCasa/robosuite兼容依赖必须版本化且行为正确

Finding HIGH-10：DS在仓外editable robosuite_repo直接修改controller_factory.py、base.py、manipulation_env.py、task.py；变更未提交/未pin。虽然ENV CREATED/RESET与MP4输出成功，不能证明与目标数据对应的模拟物理行为相同。

GPT已核对上游ARISE-Initiative/robosuite tag v1.5.2基准Commit 824ac14cefcfb7ec125fe5eb2e0bad7364466154 和后续上游源码/RoboCasa Kitchen：
- 兼容1 JOINT_VELOCITY_LEGACY不能直接别名为普通MobileBaseJointVelocityController。后续上游单独有LegacyMobileBaseJointVelocityController，根据mobile-base的forward axis处理输入映射；不一致可能改变行为。
- 兼容2 _destroy_sim应在sim尚未创建、已销毁、重复close时幂等。
- 兼容3 load_model_on_init=False必须从ManipulationEnv经过RobotEnv传入MujocoEnv并在reset时真正延迟初始化，不能只在外层签名加形参。
- 兼容4 enable_multiccd与enable_sleeping_islands需通过Task/ManipulationTask到MujocoWorldBase/模型选项实际生效，不得只接受关键字后丢弃。
RoboCasa Kitchen实际使用上述Legacy、deferred init和物理flags。不可把现有临时4行patch复制后立刻视为正式有效。

优选由Codex维护一个可复现的受控robosuite fork commit，或repo内third_party版本化patchset+基准SHA+验证安装脚本（针对隔离checkout）。不要自动修改用户已有dirty editable仓，不安装漂移的master，不含未跟踪.bak。
正式sim启动前必须核验robosuite/robocasa/mujoco版本、实际import origin、两repo SHA/dirty、补丁版本与运行时物理模型/控制器行为，写入evaluation identity；如不符fail-closed。
可在合法约束内选择同一Python venv同时运行Server/Simulator或两个venv，脚本不得强制不同，但需要各自imports和ABI验证。
Acceptance：真实PandaOmron Kitchen env create/reset/step、多方向移动底座动作、LEGACY controller class与forward-axis映射、load_model_on_init=False首次reset时模型初始化、multiccd/sleeping flags实值检查、seed和场景一致性；任何语义漂移会使此前SR=0.05只能作为diagnostic_unverified_physics，不得当正式benchmark值。实机robocasa版本仅DS自述1.0.1，实际repo SHA须只读核对，不造版本。

## C. P1 — 一个可参数化、用户亲自手动执行的统一入口

Codex需提交：
- scripts/run_robocasa_eval.sh (或等价稳定命令)；
- scripts/eval_robocasa_18task_queue.py 兼容 --config YAML、--list-tasks、--dry-run 和必要CLI overrides；
- configs/eval/robocasa_g1_iter8900.example.yaml；
- docs/eval/robocasa_manual_runbook.md；
- 严格参数/流程CPU测试与schema版本冻结。

CLI接口（待实现，不能现在直接执行）：
    bash scripts/run_robocasa_eval.sh --config configs/eval/robocasa_g1_iter8900.example.yaml --gpus 2,3 --tasks CloseFridge,TurnOnSinkFaucet --episodes 5 --run-name iter8900_demo --save-generated-video first
    bash scripts/run_robocasa_eval.sh --config ... --list-tasks
    bash scripts/run_robocasa_eval.sh --config ... --dry-run

配置示例（候选字段名，Codex实现时不得静默改语义）：
    schema: psm_wma_robocasa_eval_v1
    checkpoint: /mnt/data1/data_v2_0617/psm_wma_v3_packed128_runs_fresh_g1_20261019/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019/checkpoints/iter_000008900
    config_file: /mnt/data1/data_v2_0617/psm_wma_v3_packed128_runs_fresh_g1_20261019/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019/config.yaml
    dataset_root: /mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic
    tasks: [CloseFridge, TurnOnSinkFaucet]
    episodes_per_task: 5
    gpu_ids: [2]
    slots_per_gpu: 1
    base_port: 8900
    server_python: /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
    sim_python: /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
    output_root: /mnt/data1/data_v2_0617/robocasa_eval_runs
    run_name: iter8900_example_g2
    seed: 0
    prediction_steps: 30
    guidance: 1.0
    fps: 20
    action_horizon: 16
    local_memory_mode: required
    server_lifecycle: per_task
    on_infrastructure_error: stop
    save_rollout_mp4: true
    save_generated_video: first
    save_init_png: true
    save_action_jsonl: true
    save_prediction_jsonl: true
    timeouts:
      server_start_s: 900
      predict_request_s: 600
      episode_wall_s: 1800
      task_wall_s: 10800
      terminate_grace_s: 20
    resume: false

配置和CLI的优先级为CLI > YAML >版本化defaults；未知键、空/重复GPU、重复/不存在Task、无效timeout、不可执行Python、dirty vendor、复用已有namespace等都fail-closed。
gpu_ids列表决定GPU→独立Worker/Server/Simulator的最大并行Task数，每GPU在线Local-TTT session slot固定为1；不是训练B_stream=8。要求更高slots_per_gpu另开并发设计Gate。
task发现须扫描dataset_meta.json中的env_args.env_name，tasks: all表示全部18 underlying task class，不把语言paraphrases当任务。允许1/4/18任务及任意合法指定子集；同名元数据多源则fail-closed。全评测固定Local-TTT required/raw15/state15/left_wrist/base raw/H_pred16/20fps/chunk16/seed与split，若有人更改冻结模型ABI必须拒绝或明确另一个协议。
video模式：none不保存预测视频；first每episode仅第一次模型生成的视频；all各次replan可追溯地保存，不允许将现有closed_loop_eval.py中每次预测都append到gen_frames的行为误标为first。Child当前已有 --save-gen-video，但Queue没有透传；需对三种模式实施与显式测试。环境rolloutXX.mp4按save_rollout_mp4控制；actions.jsonl、predictions.jsonl须保留作可审计证据，和模型生成视频不是同一文件。启用的MP4要验证非空、可解码；可中断时保留partial并标记failed，不覆写。
任务级resume：仅同Root+Child+依赖commit+Checkpoint+Config+selected tasks+episode次数+视频/timeout/seed/protocol identity、且整个Task结果/必要媒体完整，才能跳过。不能拼接中途完成1–4条的episodes；必须保留原历史并用新attempt namespace重跑整个Task。
运行开始前 --dry-run CPU-only 只读解析配置，打印设备映射、Task、模型/依赖身份、输出目录和完整有效启动参数，不启GPU或修改训练。正式执行写 resolved-config、evaluation_manifest、每Task results/rollout/action/predictions和真MP4、server_info/进程/日志、summary/status/真实SR/错误类型及各SHA。

## D. 分批实现与独立 Gate

Batch A (P0): Local-TTT任务隔离 + per-episode/per-task真实进程超时，CPU故障注入红绿测试。
Batch B (P0): pinned正式robosuite/RoboCasa兼容依赖 + 行为等价测试与版本/脏树阻断。
Batch C (P1): Owner manual launcher + YAML/CLI严格解析 +任务选择/次数/GPU映射/视频+task-only resume+文档。
三个Batch可在隔离分支分别完成但必须最终组合验收；每一新exact Root Implementation/Child Gitlink/vendor pin提交须由GPT独立增量审查。DS做CPU只读复验，Owner自己决定停训练/释放GPU/最终手动执行。真实GPU E2E必须按1Task×1Episode canary→4Task×5→18Task×5；遇infra错误停止并报告，不能靠吞报错证明完成。禁止修改G1训练Checkpoint/Optimizer/DCP/冻结Config/Job Identity、强制启动GPU或运行时patch现有editable依赖。

## 交付成功定义

Owner以后只用这一条稳定命令+配置即可改变任务、次数、GPU及预测/环境视频，不需要DS每轮回忆旧参数。无跨Task session污染、依赖可复现、超时严格、输出不可覆盖、identity可追溯、SR与故障区分清楚。
