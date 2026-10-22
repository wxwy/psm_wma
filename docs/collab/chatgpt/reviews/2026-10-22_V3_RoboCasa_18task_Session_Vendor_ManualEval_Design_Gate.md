# V3 RoboCasa 18-task × 5 Rollout — 新运行证据 Design / Integration Gate

日期：2026-10-22
Gate：18任务首轮运行缺陷审计 + Owner未来统一手动启动评测 Frozen Contract。
**原已审正式 Implementation Pair 没变，不重做代码/旧CPU Gate：Root ba91ebb7de2555cd1ff2a290d0af5ee43a8a3ee6；Child/Gitlink 35b0ea1ccee9ee26653ed6589c484f0997d1c586；Queue Blob 72ad7e2b94b31cbfd7a8af0a1eaff92127ffa7ae。**
本次首次远端 V3 docs HEAD 1fc28effe9e33a2e6522f6ffe60c55c68f8b367c，冻结新需求/Review docs产生的新HEAD不代表Implementation。
DS_PRO 2026-10-22 报告是真实目标机执行摘要，GPT无法从目标设备直接读取原始完整log；有关 worker07 138次session限额、4Task×5 SR 0.05、18Task×5 85/90结果都按 DS-attested 记录，不冒充独立复现。

## Verdict 与 scope

**Design Gate = APPROVE（仅批准所附 Frozen Design Contract 的范围与验收设计）。**
**真实18-task正式执行/当前依赖基准 Gate = REQUEST_CHANGES（尚有生产/依赖/可重现性 Blocker）。**
此前代码Gate的正式 APPROVE 不等于本轮真实评测依赖或会话生命周期准入。本审查不是旧 formal pair 的重复代码审核。
实现规范：docs/collab/chatgpt/requests/2026-10-22_V3_RoboCasa_Owner_Manual_Eval_Framework_Frozen_Contract.md；Codex必须分批交源码和行为Evidence，随后新 Pair fresh review，Owner再决定正式GPU。

## HIGH-09 (production lifecycle) — task异常中断后 persistent Server 的Local-TTT session被后续Task复用

- Severity：HIGH；file:line Root scripts/eval_robocasa_18task_queue.py:343–523、特别是:353–404 Server在每worker生命周期启动、:407–505 重复处理多个任务以及:460 subprocess.run无真实Task wall timeout；Child cosmos_framework/inference/local_memory_online.py:135–160 max_sessions gate、:266–270 reset_session；Child cosmos_framework/simulation/robocasa/closed_loop_eval.py:237–350/484–509；Child simulation/robocasa/local_memory_client.py:44–58/127–134。
- Root cause：每worker仅1 Server+max_sessions=1，异常退出/HTTP断联/reset失败不能保证服务端释放该session，下一Task的新session注册会被拒。DS报告worker07 task首个Episode无results后138次limit error，与这一失效模式一致。
- **DS root cause 需纠正**：Child run_policy 已有finally，普通异常尝试调用end/reset，非“仅正常结束才清理”；进程被SIGTERM/SIGKILL、卡死、video encode失败或reset HTTP错误会跳过/破坏正常确认，因此单纯添加finally并不完整。
- Violated new frozen contract：不同底层Task与Episode不得共享残留 OnlineLocalMemory state；任务失败不得毒化同worker后续Task或将runtime_error计入完成。
- Acceptance：默认Server per_task、每任务完成/异常终止回收自有Server，严格新会话；若复用必须证明 /info sessions=0/pending=0；Queue需真正受管task+episode monotonic超时/自有PGID终止；session/heartbeat/failure evidence；模拟SIGKILL/HTTP400/timeout/media-reset-failure后后一Task隔离不受污染。不要扩大max_sessions或无界TTL隐瞒泄漏。

## HIGH-10 (dependency physics contract) — robosuite 4处脏editable兼容patch不是正式可重现/行为等价依赖

- Severity：HIGH；file:line DS仓外 robosuite/controllers/parts/controller_factory.py:173、robosuite/environments/base.py:740、robosuite/environments/manipulation/manipulation_env.py:147、robosuite/models/tasks/task.py:63–64；Child fixed cosmos_framework/simulation/robocasa/closed_loop_eval.py:186–213 创建官方Kitchen、:280–321 消费base raw15。
- Root cause：DS为使RoboCasa运行而直接修改仓外editable，没有正式 Git/patched SHA和安装合约。经独立核对上游官方robosuite v1.5.2 tag Git SHA 824ac14cefcfb7ec125fe5eb2e0bad7364466154 与后续 master：
  - DS将JOINT_VELOCITY_LEGACY指向普通MobileBaseJointVelocityController，但后续官方明确使用独立LegacyMobileBaseJointVelocityController，对 forward joint axis/reorder有不同逻辑，不能只看 ENV RESET成功；
  - DS加load_model_on_init形参但 v1.5.2 RobotEnv/MujocoEnv未完整传递/实现延迟初始化；
  - DS给Task多加两个物理开关形参，但未传入MujocoWorldBase，无法证实CCD/sleeping flags生效；
  - _destroy_sim getattr安全性需测重复调用。
- Violated contract：eval与官方目标场景和动作控制/碰撞物理必须可复现，且准确绑定实际安装依赖；临时忽略参数或非Legacy映射可能影响SR和任务时长。现DS 4Task×5 1/20 与18Task×5 1/85不能作为 verified-physics benchmark 对照，只是diagnostic。
- Acceptance：pinned fork or reproducible patch series（SHA、clean tree、安装和import origin），逐个接口要求下沉至真实运行语义并针对 PandaOmron forward/lateral/yaw raw action、load initialization、multiccd/sleep flags、env create/reset/step+seed parity做测试；不能把不确定的新版master随意pip最新替代。所有真实Sim结果 identity 都必须包含vendor依赖pin和patch版本。

## HIGH-11 (execution reliability) — 无硬任务deadline及隔离输出/来源

- Severity：HIGH；file:line Root Queue scripts/eval_robocasa_18task_queue.py:217–263 CLI仍按整个dataset元数据集合计数，:460 subprocess.run无限Task process wall时间，:183–214及:298–308 只保证Task级完整记录；Child closed_loop_eval.py:360–425有 --save-gen-video、:484–501会生成 MP4，但Root Queue未透传，现每预测gen_frames.extend并非只保存first。
- Root cause：每次需要DS手动再发现CLI参数/组织数据子树；无法可靠从18任务根选择任务子集；--timeout当前含request或server等待语义，没有Queue的task/episode deadline；generated video选项丢失在Queue。
- Violated new Owner contract：独立手动单入口配置GPU/Task/episodes/MP4/prediction/timeouts/dry-run/output manifest；任何错误不能强行构成Complete成功率。
- Acceptance：统一可执行launcher+YAML/schema/CLI overrides、--list-tasks/--dry-run、元数据唯一Task枚举、1/4/18任务且每Task N集、1/2/8 GPU对独立Local session槽映射、视频none/first/all按真实含义、超时和task-only resume、完整输出与evidence、无任意overwrite；必须保留off-line no-guardrails、chunk16、Local required/raw15/state/left_wrist、精确Root/Child/checkpoint身份和Owner GPU控制。具体字段、例子及负例见Frozen Contract。

## Implementation Gate steps

1. Batch A (P0) 会话与进程生命周期/timeout；CPU fault injection: SIGKILL, no-result, request timeout, reset失败, media失败及 Task2 无session污染。
2. Batch B (P0) robosuite依赖pin和物理行为等价：不允许继续在脏editable上声称正式有效benchmark。
3. Batch C (Owner使用) 单入口配置+严格identity/task selection/episodes/GPU slots/videos/文档，遵守批次A/B边界。
4. 每次新Root或Child formal implementation SHA变化必须独立增量审核及测试证据；正式 verdict须同时落盘review与canonical CODEX_INBOX；DS执行限定CPU/static/受授权smoke；Owner本人负责实际GPU启动。

**Design APPROVE不代表三项Production已完成。当前不放行新的18Task正式Benchmark结论；不动G1训练、DCP、Config/Identity、GPU或DS仓外临时补丁。**
