# PSM-WMA V3 EvalV2 — DS_PRO Local-TTT iter20000 18×50「Phase A 批量」需求：独立设计审核

**2026-10-31 · Design proposal Verdict：`REQUEST_CHANGES`。** 这是对**本次DS_PRO在会话中提交的八条新改造方案**的技术设计裁决，**不是**对现有V3源码已批准Code Gate的重新审核、也不是新的生产Formal implementation verdict。没有新增Design/Implementation Formal SHA。项目当前已发布代码参照：Root `d7a444036e4497ec9684ccc9bb4b7d497cf68529` / Child+Gitlink `6c83596d6a259e89c4cd3e79424024983426ac3d`；DS工作树旧Root `cee6f53e...` 与这个后续仅日志显示/回执推进的V3不应混同正式新源码设计目标。本轮未运行真实GPU、仿真、模型或DCP。

## 0. 总判定：不批准改造Phase A；推荐直接采用已存在的Phase B `required`

DS正确发现`phase_a`强制`M=B=1`，但由此推导“必须开发Phase A Native Batch才能实现Local-TTT多Sim×批量”**不成立**：现行**`execution_profile=phase_b` + `local_memory_mode="required"`**已经完整接线到事务Session、真正Local-TTT fast-state、`generate_samples_from_batch` Native B1/B2+和原子提交，且此前独立双模式Code Gate已通过对应CPU合成闭环。新设计反而会复制已批路径、引入两套Profile权威，并遗漏Sim/Manifest绑定。保留既有已批代码不动，先让DS只在全新Eval YAML把profile切成`phase_b`，不改Local mode，不借用`off`（会禁掉TTT）。**不能把新的Phase B结果冒称Phase A等价实验**：`execution`和协议身份不同，应冻结新的Run、独立汇报。

## 1. 八条DS提案逐项核定

| 提案项 | 实际源码对照 | 审核裁决 |
| --- | --- | --- |
| 1 放宽Phase A M/B=1 | `scripts/robocasa_eval_v2/config.py:131-146` Phase A现有限制；`phase_b`无此限制，仍有M/B≤8和Episode≤50合同 | **不建议改Phase A**；保留旧Phase A科学口径 |
| 2 改Phase A slots | `resources.py:46-53` Phase A单GPU1 Slot，Phase B已采用`GPU{g}_S{s}` Slot-major并截断task_count | **不需生产改码**；用Phase B已有有界Slots |
| 3 Phase A返回native batch execution block | `config.py:199-209` Phase B已返回`phase_b_native_batch_v1`；Child`evaluation/robocasa_v2/contract.py:103-124`只接受该版本并冻结`resource_architecture` | **复用既有Phase B Profile**，不在Phase A假冒Phase B标识 |
| 4 扩大`batch_profile`布尔 | `runtime.py:65,147-249,441-480,561` Phase B时每GPU一个Server、多Session事务、registered assignment、模型Info严格核验 | 保留`==phase_b`；Phase A仅切一个Boolean不能得到完整事务执行 |
| 5 Required Local与Native共存 | `runtime.py:50-54,168,223,234,461,478`与Child `robocasa_session_transactions.py:409-429`、`robocasa_batch_transactions.py:195-282`已有required路径、Local Prepare/CommitMany | **Code path已存在**；需要**真实GPU LocalTTT canary**闭环验证，不是新架构编码需求 |
| 6 Server N Session×Batch | `action_policy_server_robocasa.py:904-946,1246-1311` Batch生成时每Session prefix；Child`robocasa_local_memory_policy.py:65-87,200-256`fast-state按Session存储；Sim持lease/evidence，fast weight位于Server的Session map而非各Sim各复制模型 | **已实现代码级能力**；只缺该iter20000在GPU上的真实内存与行为证据 |
| 7 8/8资源 | `resources.py:12-42`现有GPU0.85比例、一次性模型启动20GiB预留、Owned RSS总预算；没有真实Local×M/B峰值模型 | **先小规模M2/B2**，OOM/HostRAM/Latency观测后再调整；不建议凭猜测在该文件增加固定每Slot显存值 |
| 8 8 shard DCP | Child`action_policy_server_robocasa.py:738-786`单可见GPU+单rank Model Owner；`utils/generator/model_loader.py`调用 `torch.distributed.checkpoint.load` 读取匹配模型state，支持DCP读取的代码路径；`robocasa_transaction_mode.py:6-35`校验required/Local tensor形状、weight tree | **8个训练Shard不要求8个推理进程**，但不代表已验证singleGPU真实加载；需正式DCP模型加载/模式/容量Gate |

## 2. 当前Blockers：file:line / 根因 / 合同 / 可验收整改

### D-NEW-01 · HIGH · 选择了错误/冗余的执行Profile

- **位置：** Root`scripts/robocasa_eval_v2/config.py:131-146,199-209`、`runtime.py:65,147-249`。
- **根因：** 方案只研究Phase A限制，没有检查新V3已获批的Phase B `required`多Session/LocalTTT/Native Batch能力，把原本已有能力误判为新Framework缺口。
- **违反目标/现有合同：** Owner要的是**真实Local-TTT iter20000、18×50且支持批量**，不是必须复制一个与已有PhaseB等价的新路径；原已批Dual-mode PhaseB与独立source/manifest身份不得误写成新的PhaseA B1口径。
- **验收条件：** 原需求改为使用`execution_profile: phase_b`、`local_memory_mode: "required"`，保留新的独立Run输出；Phase A旧1/1限制不动。若Owner坚持**Phase A字面身份必须改变**，先补充该需求相对Phase B在Local状态、时间语义、结果身份上**实际不同**的场景及严谨versioned新Profile设计，再提交新Design Formal Pair审核；不可只删除guard。

### D-NEW-02 · HIGH（仅坚持扩展PhaseA时适用）· 方案遗漏Simulator和冻结Manifest事务边界

- **位置：** Child`cosmos_framework/simulation/robocasa/eval_v2_adapter.py:90-103`、`eval_v2_worker.py:30-38`；Child`cosmos_framework/evaluation/robocasa_v2/contract.py:91-126`；Root`runtime.py:315-322,559-570`。
- **根因：** Sim `NativeEpisode.execute`与Worker源码见证仍根据`execution_profile==phase_b`选择`PolicyTransport`和transactions模块。即使Root按提案修改为PhaseA batch+多Slot，Sim仍使用旧非事务Client并拒绝传入的`transaction_assignment`。Manifest的`phase_b_native_batch_v1`和`multi_reusable_sim_slots_one_native_model_owner_per_gpu_phase_b`同样不能未经版本化就装进PhaseA。
- **违反合同：** Local TTT每Episode Session是由coordinator注册的真实独立lease、遵守Request Frontier/atomic commit/End/Replay与源码见证身份，不能仅靠Config M/B参数宣称有批量。
- **验收条件：** 优选**不改码而采用既有PhaseB**。若必须做PhaseA新执行语义，设计需要覆盖Coordinator/SimWorker/NativeEpisode/Client/Server/Manifest 的统一真值选择及versioned身份、跨Session failure/reset/replay/End/atomicity，并接受显著更大审查范围；目前8条提案不完整。

### D-NEW-03 · MEDIUM · 8/8并发目标与18Task Slot数量及Resource模型混淆

- **位置：** Root`resources.py:12-42,46-53`、`runtime.py:61-65`；Child`robocasa_batch_transactions.py:126-162`与`robocasa_session_transactions.py:201-209`。
- **根因：** M/B代表**每GPU最多多少Slot/每次最多多少请求**，不是保证每GPU生成B8请求。4GPU×M8物理上可建32个位置，但按`task_count=18`裁剪到**18个实际Slot，分配约5/5/4/4**；单卡最多5个活跃Session，不能在这套18Task配置上实际形成B8。Batch还有20ms等待窗口，不可把设置B8等同真实命中B8。
- **违反合同：** 结果应报告真实`native batch histogram`、峰值显存/HostRSS/吞吐，不可将配置上限冒充测得并发/加速。
- **验收条件：** 先`1GPU M2/B2`或受限真实资源下的小canary，随后可按`M4/B2→M4/B4`等必要级别逐步试；最终4GPU 18Task最多5会话/卡（随调度），B8可保持cap但不能期待有效B8。Resource不需无实测依据的每Slot固定预留；现有maxGPUfraction/RSS监控+实际OOM/latency为前提，发现负载失败再窄修Admission。

### D-NEW-04 · HIGH运行证据缺口（非代码已证bug）· 8-shard真实LocalTTT DCP/单GPU/End与显存未验

- **位置：** Child`action_policy_server_robocasa.py:737-786,904-946,1249-1311`、`robocasa_transaction_mode.py:6-35`；Root`identity.py:116-183`、`runtime.py:147-249,755-766`。
- **根因：** DS已报告`iter_000020000`完整训练DCP，world_size=8，但`complete.v1.json`不是一次真实SingleGPU Server successfully loading该8Shard DCP、完成LocalTTT状态扫描/Native Batch的证据。此前324/84合成CPU与NoTTT OSMesa 4EP不能替代LocalTTT真实Canary。
- **违反合同：** 正式900必须有匹配Checkpoint/config的真实LocalTTT `required` fast prefix（`prefix_present`,`adapted_steps`,`inner_loss_mean`,`fast_state_norm`）、按Session隔离、真实 B1/B2 generation、所有Session End/cleanup、资源与DCP加载稳定性；SR仍由env._check_success、valid/behavioral_failure/invalid分别记录。
- **验收条件：** 首先严格只读验证完整DCP与原训练config匹配以及net/net_ema selected Local inventory、raw15/state15/H16/K4/local32；在Owner另批GPU和确认不干扰现役NoTTT训练后做**最小Local required PhaseB real-GPU canary**，优先单GPU M2/B2、两Task各1–2 EP，记录实际Native Batch histogram、adapted_steps/prefix和Session End/视频/Latency、显存峰值与HostRSS/Process清理。结果PASS再考虑18×1和900，不许自动授权长跑。

## 3. 下一步最小路线/执行权限

1. **DS_PRO无需写生产代码**，把当前准备的`v3_18x50_phase_a.yaml`复制到**新独立输出命名空间**的PhaseB配置，最小修改`execution_profile: phase_b`、保持`local_memory_mode: "required"`、依真实资源先用`M2/B2`。先让Owner亲自执行`dry-run`，核`tasks=18,episodes=50,scope=formal900,profile=phase_b_native_batch_v1,local=required`和实际Slot/GPU计划。dry-run**不是**正式900启动许可。
2. 真GPU资源当前可能被NoTTT训练/外部LIBERO占用；本Review未读取服务器实时占用，不允许DS擅自抢GPU、停止训练或热更共享工作树。训练与评测Checkpoint/Output保持独立，`iter20000`即使另有更晚latest也不得被替代。
3. **如确需改生产源码**：Codex须先拿到Owner与MM/Kimi独立审查后确定的真正新增行为（不能为已有PhaseB能力重复设计），发布隔离formal新Root/Child，再走GPT增量Code Gate。**此次`REQUEST_CHANGES`不批准Codex实施原提出的Phase A 8条改造，也不授权真实GPU/900 Episode**。

## 4. 评审边界

本轮只有会话中DS需求说明作为设计对象（尚未形成项目中新Formal Design SHA），故这里`REQUEST_CHANGES`仅为**提案设计裁决**。原V3代码与既有`APPROVE_CODE`均保持，绝非本轮源码Gate被拒。正式Source Gate仍以其对应的Frozen Pair为准；Code Gate无需在Pair未变时重复进行。