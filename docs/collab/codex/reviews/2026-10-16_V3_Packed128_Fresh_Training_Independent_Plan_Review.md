# V3 Packed128 DROID Fresh 分段训练路线——Codex 独立技术审核

日期：2026-10-16（Asia/Shanghai）  
审核者：Codex，独立于 GPT 路线提案的技术审核。  
**最终建议：`REQUEST_CHANGES`。支持另立 Packed128 DROID Fresh 路线、解除其对 iter1300 迁移/旧 B1 严格数值等价的依赖；不批准按当前提案直接执行训练。**

本轮只读检查设计、当前及历史 Git 源码、仓库内审核/Evidence 摘要。**没有修改生产实现、冻结版本、配置、Checkpoint 或历史 Evidence；没有运行项目测试、真实数据检查、DCP load、GPU、仿真或训练。**本报告新增的结论属于设计/静态审核，不是实施验收或执行授权；文中 CPU/GPU 矩阵均为后续建议，不能引用为已通过。

## 1. 版本锁定、审核范围与证据边界

| 对象 | 完整 SHA / 核验结果 |
|---|---|
| 重新读取的 `origin/V3` | `6d41a2dcbabebf5bc4f7ae4d81c7101f07415c6c` |
| Owner 指定生产源码快照 Root | `2f4dec43eb6b1e35b33a99d844d67813df5922a6` |
| 当前生产 Child / Gitlink | `1d56320c08c56b0f8dd248919d152d81ae12ea7b`；实际 Child HEAD、Root tree 一致，工作树干净 |
| 冻结 Packed128 Target Root / Child | `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`；已核对 Root tree |
| V2 Root / Child | `b13024456e313b545871a0d5de07f5495848f4e3` / `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92`；远端 V2 ref、Root tree 已核对 |
| 独立 B1 诊断（仅参考已有审核） | `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`；不是生产训练实现 |

`git diff 2f4dec43..origin/V3 -- scripts tools cosmos-framework` 为空；此次 V3 增量为文档，不能用新的文档 HEAD 声称新的训练实现已验收。当前 Child 比冻结 Packed128 Target 多 **13 commits、17 个文件变化**。核心 grouped window / Local core / DCP 文件在这两个 Child 之间没有变化，但数据初始化、变换 RNG、预取、Trainer 接线和遥测有变化，不能继承旧 Pair 的整体 PASS。

读取了两份指定文档：

- `docs/collab/chatgpt/designs/2026-10-16_V3_Packed128_DROID_Fresh_staged_training_route_PROPOSAL.md`。
- `docs/collab/chatgpt/reviews/2026-10-16_V2_A2_Packed128_training_reference_for_V3_Fresh_training.md`。

另读取 B1 完整 GPU r2 失败审核及其交接。其“8/8 jobs RC0、跨实现及同路径 repeat 数值失败、约595GB Evidence、约47GB 剩余空间”是 **DS 报告/仓库审核记录中的事实层级**；本环境没有访问那些原始 PT、168MB comparator JSON 或训练服务器，不能独立确认原因、实际磁盘余量或可用 GPU。

以下位置均指 **生产 Child `1d56320c…`**，除非标为 Root 或 V2。行号取自该精确源码。

## 2. Packed128 默认行为：实际满足什么、还缺什么

### 2.1 实际训练链路确实是 Packed128，不只是名称

1. `examples/psm_wma_robocasa_corrected_phase5.py:57` 固定 `NATIVE_BATCH_LAYOUT="v2_a2_member_packed_slot_major_v1"`；`:571–581` 默认 T16/B8/GA2/K4/world8。
2. `overlay_config():267–280` 设置 FSDP8、GroupedLocalMemoryTrainer、GA2；没有通过 config/environment 选择 Index8 的分支。
3. `cosmos_framework/trainer/local_memory_grouped.py:257–310` 的 native callback collate 全部有效 payload，调用一次 `model_ddp.training_step(..., _local_memory_prefixes=prefixes)`。
4. `cosmos_framework/model/generator/mot/local_memory_grouped_window.py:191–208` 每个 GA member 只调用一次 native loss 和一次 backward。完整成员为 B8×T16=128；两个成员每 rank/update 共256 Consumer，8 rank 完整更新最多2048。**Terminal Partial 必须用实际 N，不得硬报2048。**
5. `pack_native_member():69–95` 按 slot-major、slot 内时间递增收集；同时验证 payload/prefix/identity 数量、绝对时间、S0 恰好没有 prefix、坐标唯一性。`:205–207` 使用真实成员 Consumer 数加权，未塞入 PAD Consumer 凑128。
6. `omni_mot_model.py:1384–1400` 拒绝 dataset 提供 Local authority，再将 prefix 逐样本注入已物化的 native carriers；`memory_prefix.py:59–69` 保持 SequencePlan 和 prefix 对齐、不 detach；`unified_mot.py:811–833`、`attention.py:346–357` 将 Local K/V 接入 generation attention。源码层面存在通向 Action 的连接，而非仅旁路日志。

**结论：当前 corrected Phase5 默认 Packed128、Full/Terminal 的结构契约成立；没有发现 OOM/异常后自动缩小 batch 或回退 Index8 的逻辑。无需再增加第二个 Packed128 开关来“修默认值”。**

### 2.2 尚不满足“Index8 保留且可显式选择”

当前 Phase5 parser 没有 native-layout 参数，GroupedWindow.run_member 只有 packed 路径。`robocasa_exact_window_local.py:457–472` 虽保留 `gather_exact_window_same_index`，搜索结果显示调用者只是测试，不能把保留 helper 或 Git 历史当作保留了可运行的兼容训练入口。

因此 Owner 新要求 **Packed128 默认 + Index8 显式独立选择** 目前只完成前半项。应在一个新的 Child 候选中恢复显式 Index8 dispatch；Packed128 保持默认。不能用改变常量/换旧 Child/失败后 fallback 代替真实选择。

Layout 必须从解析后的同一个值进入 Trainer/Window、配置身份和遥测。当前遥测 `corrected_telemetry.py:549` 也写死 packed；恢复 Index8 后必须同步修正，而不是两条路径都报告 packed。

### 2.3 Launcher 不能混用

- Root `scripts/train.sh` → `train_local_memory_ttt.sh:6–7` 已拒绝未移植的 V2/LIBERO 路径，这是正确保护。
- Child `examples/launch_sft_action_policy_robocasa_edge_all_target_atomic.sh:101–112` 实际调用 **`psm_wma_robocasa_h3f.py`**，后者引入 H100/Stage-A 旧配置；不是当前 corrected Phase5。不能因名字有 target_atomic 就把它当本路线 Launcher，也不在此声称该旧入口一定能运行 Index8。
- 新路线须冻结一个明确调用 corrected Phase5 的 canonical 命令/薄 Launcher，并固定正式几何、精确 Pair、Fresh/Resume phase、已验收 Index 和独立 Job。可以用经审核的明确命令完成这一点，不要求为命名好看重构全部 Launcher；旧入口不能成为正式默认入口。

### 2.4 同 Job Layout 身份已有基础保护

`corrected_phase5.py:202–237` 的 config_digest 已包含当前 Layout、B/GA、Local 几何、World/Shard、模型/数据 witnesses 和完整 schedule；`local_memory_grouped_resume.py:118–124` 严格匹配 digest/profile。换 Layout 应 fail closed，不做旧 Index8→Packed128 同 Job Resume。新增选择应绑定**真实执行值**，继续保留该保护。

注意 digest 不是全量 resolved config 的哈希：当前未覆盖所有 RF loss/normalization、precision、seed、deterministic/GradScaler、optimizer skip-pattern 等语义字段。S0 应冻结完整 resolved 配置及这些字段；不能把旧 `70e9867f…` Index8 摘要直接指定给新的 Packed128 Fresh。

完整resolved配置应每次启动留档；训练身份应使用规范化的语义字段，允许phase、实际load_path/load_training_state、执行预算等Fresh/Resume的合法启动差异。不能要求Fresh与Resume两个配置文件逐字节相同，也不能借“规范化”排除Layout、Loss、precision、随机策略等真正影响训练的字段。

## 3. V2 → V3 继承与差异矩阵

| 契约 | V2 源码/经验 | V3 实际源码 | 独立判断与剩余见证 |
|---|---|---|---|
| Stable Slot / Episode 顺序 | `grouped_active_driver.py:83–160` 每组一段/slot，slot 顺序固定，terminal 后重绑定 | `robocasa_exact_window_local.py:154–295` rank 分区、确定性任务队列、frontier/cursor/segment_id、terminal清空后重绑定 | 核心契约继承；不要求逐 Episode 顺序与 V2 相同。需见证 fresh/continuation/mixed/terminal-rebind；恢复的第一个 request 必须精确续接 |
| Batched Fast Update | `grouped_active_runtime.py:131–195` batched scan、dependency waves | `local_memory_segment_adapter.py:216–273` 拼接状态/valid、逐 row gather；`local_evidence.py:231–236` per-row inner MSE 后求和，不除B | 不是将128个 Consumer 当128独立 Fast Slot；Fast batch是B8，Native batch才是128。旧 V2 支持该架构，仍需真实分片功能验证 |
| Slow Gradient / create_graph | V2 runtime `:172–179` 使用 create_graph=True | model-owned `cosmos3_vfm_network.py:362–414`、core `local_evidence.py:227–243,274–287` 保留高阶图、index_copy、prefix；跨段 state detach | 源码没有发现整体 detach 掉 Local outer 链。应检查 action-only outer→encoder/core/projector 的梯度/实际 FP32更新，不能只验 inner loss 能下降 |
| 原生 Packed Forward | V2 `omni_mot_model.py:1428–1476` 一次 native forward、逐 Consumer prefix | V3 Window `:191–208` + Trainer native callback + MoT attach/prefix attention | 思路继承，调用生命周期不同；不应复制旧 V2 特殊 forward/ownership 类覆盖 V3 |
| Loss / Aux | V2 native total 拆 primary+aux；`local_memory_segment.py:137–140` 为 n/N*primary + aux/GA | V3 Window `:200–207` 将整个 native total 乘n/N | Full128/128 时可相符；Partial 或跨rank Consumer数不同必须明确新目标。Dense 无 aux 的前提须由真实输出证明，不凭名字认定 |
| commit / rollback | V2 owner candidate records，成功边界后提交 | V3 adapter只改candidate；Window `:230–246` 仅真实optimizer成功后切换live引用 | 结构可排除普通 scan/backward 失败发布FastState。若 optimizer已部分写入后自身抛错，不能声称回滚了 Slow/Optimizer；必须终止整个Job并从完整Checkpoint恢复，不能同进程重试 |
| FSDP Local 参数 | V2 `active_local_memory_launch.py:327–339` 明确拒绝DTensor，复制参数并broadcast | V3 `parallelize_vfm_network.py:144–177` root fully_shard并注册scan；Window `:122–129` 强制model-owned FSDP scan | **重大实现差异**。V2成功不能证明V3高阶梯度、unshard/reshard及跨rank参数更新正确；不要为方便直接恢复V2复制态实现 |
| W0 fresh / continuation | V2 fresh state与detach prior混合 | V3 `cosmos3_vfm_network.py:381–405` all-continuation仍接入零梯度W0，mixed只对fresh行用W0 | 全continuation W0梯度可以是数值0；零长本地shard也合法。不能要求每rank每FQN每step非零；也不能把非空shard的全Local断梯度当合法 |
| Save / Resume | V2历史3→4和长训checkpoint记录 | V3 per-rank Local callback/profile/Sidecar，5组件DCP，RNG单独rank key | 格式设计完整，**当前保存发布/RNG/分段控制有下文缺口**；必须验新Fresh自己的Save→Resume |
| 任务效果 | V2 Owner归档LIBERO 358/400，required/init/off为358/350/280 | V3 RoboCasa raw15/State15、cached VAE、不同Simulator ABI | V2是架构实证，非V3 SR证据；online update相对init仅+2pp的历史差值也不能直接移植为V3预期 |

V2证据来自 `artifacts/g0/localmem_ttt_a2_training_full_record_iter3288_2026-09-22.md` 的 Owner 归档摘要，不是本轮独立访问原训练日志。V3 现有 `local_memory_fsdp_scan_test.py`、grouped window/resume 测试包含有价值的合成正/负例，但本轮只阅读测试源码，没有重跑；其中 mock FSDP 注册的 PASS 不能当真实8卡高阶图验收。

## 4. 新 Fresh 路线本身合理，但要补齐哪些初始化/恢复条件

### 4.1 可以放弃 iter1300 迁移作为这条新路线的前置条件

认可新算法路线：**直接从官方 DROID 初始化、独立 Job/Optimizer/Scheduler/Planner/Local 状态，学习有效性+自身可恢复性+真实任务结果为目标。**无须先证明与旧 Index8 梯度逐 FQN/元素相等。

旧 B1 r2 仍为 REQUEST_CHANGES/NUMERIC_FAIL；同路径 repeat 也 FAIL，不能武断归因于“只是布局改变”或“正常GPU误差”。已有 CPU first-divergence addendum 若证明是输入、初始化、Optimizer状态、模型调用上的实际缺陷，仍须评估并修复其对新 Fresh 的影响；但不要求把整套旧 B1 数值门重新通过，才允许设计新实验。不得放宽旧 r2、改写结果、删除旧Evidence或把新Fresh成绩追认为旧Gate PASS。Gate M 不再是新Fresh依赖，旧iter1300仍只读保留。

### 4.2 源码能够支持的 Fresh 初始化

- `corrected_phase5.py:310–312,279–283`：Fresh只选择base DCP，load_training_state=False，skip仅net_ema和Local；没有要求读取iter1300。
- `checkpoint/dcp.py:783–810`：新Job没有latest时是model-only warm-start；不存在“Fresh必须恢复旧optimizer”的依赖。
- `omni_mot_model.py:598–617`：materialize后初始化；`cosmos3_vfm_network.py:416–426` 显式初始化Local encoder/core/projector/embed，之后DROID load跳过这些Local键。**当前Local projector是随机初始化，不是零投影。**
- `corrected_phase5.py:38–53,117–151`：generation/action/Local exact allowlist与requires_grad、optimizer参数对象集合检查已存在。LR基础5e-5、Action倍率5；wd期望0.05，投影的skip-pattern须从resolved配置核实，不能误读为所有参数都wd0.05。
- 新 planner/live sidecar 从空状态创建，Fresh第一次没有pending Local恢复。不能把随机初始化Slow State与应为空的历史Fast Sidecar混为一谈。

以上是源码逻辑成立，尚不是实际模型权重正确加载/更新的GPU Evidence。新启动须见证只load model、起始iteration0、新optimizer step/moments、scheduler warmup、8 rank空frontier，以及实际模型selected FQN inventory。

### 4.3 不存在“显式load_path必然破坏same-job恢复”的结论

`dcp.py:771–806` **优先读取本Job latest，再考虑load_path warm-start**。`local_memory_grouped_resume.py:231–253` 拒绝same-job缺失训练组件、拒绝warm-start携带旧训练状态。这部分已有正确保护；不建议为修路线把它替换成旧B1临时load-source shim。

但“full strict resume”仍有下列实际缺口，不能用该正确分支逻辑一笔带过。

## 5. P0/P1/P2 风险、阻塞与最小修复建议

### P0-01：可选 Index8 不存在；正式 Launcher 身份未闭合【确认的需求缺口】

**位置：**`corrected_phase5.py:57,537–593`；`local_memory_grouped_window.py:162–208`；`corrected_telemetry.py:549`；旧 target_atomic Launcher `:101–112`。

**最小方案：**一个解析后的native-layout枚举，默认packed128，显式index8走自己的真实native callback/权重路径，共用现有scan/事务；拒绝未知值、任何异常/OOM不得fallback。配置摘要和DCP恢复匹配真实选择，遥测报告真实选择。canonical正式命令固定corrected Phase5及B8/T16/GA2；旧H3F入口不作为默认。保留现有Packed实现，不另建一套架构。

**CPU负例：**未指定必须packed、显式index8确有forward次数/Consumer数差别、Full/Partial对齐、错序prefix拒绝、错误layout拒绝、跨layout恢复拒绝、修改环境不能触发fallback。**GPU：**新Packed至少一次真实native检查；Index8可先做独立兼容验收，不要求二者梯度数值相等。**身份影响：**新Child/Root；Layout必须参与digest；可保持Packed字符串和DCP格式，但新实验语义字段必须冻结。旧B1/旧Job不变。

### P0-02：提案中的正式100/101分段，当前CLI没有安全可表达的执行预算【确认的可执行性缺口】

**位置：**`corrected_phase5.py:393–416,619–620,664–670`；`trainer/__init__.py:292–300,350–352,428–435`。

现有stop-after只允许**fresh、bounded_前缀、固定30000/500/100 schedule**，bounded不能formal Resume。直接设max_iter=100会改变scheduler cycle和config_digest，后面30000恢复被拒绝；Resume时也不能用现有stop-after=101。进程手动kill不是可靠的“完成save后安全停止”接口。

**最小方案：**增加与训练schedule分离的正式execution boundary，支持new-job fresh到100和同Job resume到101/后续目标；保持max_iter30000/warmup500/save100、digest不因执行预算变化；只在完整optimizer window及已完成save/finalize后退出。保留bounded诊断不能冒充formal的隔离规则。优先复用已经存在的 `_execution_max_iter`，不要改掉LR目标来凑运行步数。

**CPU负例：**100→101/500预算、已恢复iteration≥预算、GA中间不许停、bounded复用拒绝、schedule/digest前后不变、save失败不得正常退出。**GPU：**一次正式100保存与恢复续步。**身份影响：**新实现SHA；单纯execution预算不应改变训练config_digest或Checkpoint schema；不能以此放行旧Index8→Packed恢复。

**重要写盘事实：**当前trainer结束时若iteration不是save_iter整数倍，会在`:428–429`保存完整DCP。因此3-step诊断会写iter3，单步恢复停101也会写iter101，不能当作“无保存的小探针”。可以接受这些独立诊断DCP并提前配足空间；若要NoSave，必须另行冻结明确的诊断机制，不能静默patch正式save。

### P0-03：同步保存的latest发布早于所有rank Sidecar完成确认，且本地发布非原子【确认的保存协议缺口，未声称已发生损坏】

**位置：**`checkpoint/dcp.py:1165–1199,1231–1257`；`checkpoint/base.py:231–243`；`utils/easy_io/backends/local_backend.py:111–112,133–134`。

配方继承`action_policy_robocasa_nano.py:128`的dcp_async_mode_enabled=False。同步保存最后各rank独立写dataloader/rank_N.pkl，rank0写完自身后就更新latest，**没有该次所有rank pkl写完的确认**。`easy_io.dump`经本地backend直接wb/w写目标，latest也不是tmp+原子replace。rank0先完成、rank7写得慢/失败时，latest可能先指向缺失或截断的Local组件；“latest出现就kill”会放大这个窗口。组件存在性检查不是完整性见证。

**最小方案：**同步路径中每rank Local文件durable/原子发布，所有rank成功确认后才发布完整Checkpoint标记和latest；任一rank写失败不推进latest。latest使用同文件系统原子更新，保留上一个完整指针。不要改变数据内容/schema或重写旧DCP。改动优先局限DCP保存/该profile，不全局更改easy_io所有用途。

**CPU负例：**延迟rank7、rank7写失败、半写pkl/半写latest、中断前后latest保持旧完整版本、失败所有rank有界退出、同步/异步分支不回归。**GPU：**新Job真实8 rank保存及严格加载；用完成事件/全rank退出确认，不能只看rank0日志。**身份影响：**新Child/Root；可不改变旧DCP内容格式；新的提交协议/标记如新增须版本化，不追认旧DCP已满足该协议。

即使暂用“正式run-limit100后等全部rank clean exit”的操作方案规避停机窗口，也不能把当前latest语义表述成全rank原子完成；长训中断恢复的协议风险仍需关闭。

### P0-04：strict resume对整份rank RNG缺失是fail-open；deterministic分支可覆盖恢复后的RNG【确认源码行为，后者为条件风险】

**位置：**`checkpoint/dcp.py:932–955`；`trainer/__init__.py:327–331`；`utils/generator/rand_state.py:11–38`。

当某rank整个rng_state_N不存在时，loader不会将它加入待load字典，因此即使strict_resume=True也继续而不恢复该rank的Python/NumPy/Torch/CUDA RNG。若启用torch deterministic algorithms，父Trainer又在load和callback之后重新按seed+rank设种子，覆盖已恢复状态。Loss仍可正常下降，却不再是所要求的严格续接。

**最小方案：**对本新profile的same-job strict恢复，强制每rank完整RNG字段存在；只允许明确的外部model-only warm-start没有训练RNG。成功恢复后不能再重置其RNG；fresh初始化的seed策略独立保留。若暂不修改通用Trainer，必须用已审核的profile机制保证此分支不会启用，并在strict恢复入口强制RNG完整；不能仅写“默认应该没开”。

**CPU负例：**整rank RNG缺失、单叶缺失、恢复后Python/NumPy/Torch后续抽样与未中断状态相同、deterministic=True时resume不reseed、Fresh仍正确seed。**GPU：**100保存前和101第一个随机消费前的每rank状态/Consumer/CFG绑定见证；不要求重新跑旧r2跨布局比较。**身份影响：**新SHA；Checkpoint格式可不改，仅收紧验证；若改随机策略/deterministic语义，应作为新Fresh配置身份字段。

### P0-05：正式Fresh缺少前置新namespace保护，误用已有Job可先覆盖配置【确认的防护缺口】

**位置：**`corrected_phase5.py:398–415,310–312,618`；`trainer/__init__.py:138–144`；grouped trainer `:155`。

namespace exists检查只在bounded分支；普通Fresh直接返回max_iter。后续Trainer构造会exist_ok创建目录并覆盖config.pkl/config.yaml，之后才在GroupedTrainer.train检查same-job与load_training_state冲突。已有latest通常会**拒绝**Fresh，而非静默继承旧optimizer；但拒绝前可能已经覆盖原Job配置。不要把“最终报错”当作“不会改旧Job”。

**最小方案：**正式Fresh在任何Trainer/日志/config写入前独占申请新Job；已有非空目录、符号链接别名、旧Formal/旧DCP路径均拒绝，绝不自动清理。Resume需先对冻结身份做校验，保留canonical配置，新增启动记录采用独立文件而非先覆盖再报错。

**CPU负例：**已有latest、仅已有config、已有Evidence、并发申请、路径别名、错layout/digest Resume，全部不得改变原文件字节。**GPU：**不需要为目录防护单独花GPU；纳入实际Fresh/Resume的preflight。**身份影响：**新SHA，可不改DCP格式；新增/完善配置身份则新Fresh digest需冻结。旧Formal数据不能被此候选触碰。

### P0-06：FSDP/Action功能与存储仍是执行前证据门，不是Loss监控的替代项【未闭合风险，不是已证实算法bug】

- V3 model-owned scan/高阶图/Action attention路径源码存在，但V2复制态Local和旧B1某组RC0不能证明当前Fresh初始化后正确更新。现有finite guard只要求整体存在梯度，不要求每个Local子组的非空shard都真正连上Action；inventory只证明被选中，不证明更新发生。
- 检查要在**pre-optimizer**捕获真实梯度、结合非空shard/当前fresh与continuation角色；step结束后zero_grad导致None是正常现象。全continuation W0数值0、合法空shard不能误报；非空eligible Local组全None、Action-only目标对Local无梯度/干预无影响，则阻止长训。
- Slot queries在rank4–7的空shard是旧B1记录中的合法情况。当前finite(empty).all为真，不会仅因此抛非有限；missing-gradient审计虽记录local_numel，但聚合缺失计数不等于全局算法失败。不得沿用numel=0的余弦/relL2判定作为训练门。
- 剩余空间/配额未独立核实。**存储门要在S1a之前，不只是S1b之前**，因为3-step也会写完整Checkpoint。旧595GB Evidence和原iter1300/DROID/data不可自动删移。

### P1：目标函数与配置身份必须更明确【需要冻结，不宜无证据重写Loss】

设rank r的成员数n_rg，总数N_r；当前原生成员total为L_rg，Window实际目标为 `sum_g n_rg/N_r * L_rg`，FSDP按其既定跨rank梯度归约。不要把这无条件称为全局Consumer均值。若各rank N_r不同，等权rank均值与 `sum n*loss / sum n` 不同；若开启native sample_level_loss_averaging，还存在其额外每member跨rank系数，不能再盲目叠加全局权重。

V3将aux也乘n/N。部分成员[122,128]对应0.488/0.512；V2 aux/GA则0.5/0.5。**这可以是新算法的明确选择，而不是必须回到V2公式；但要确认真实Dense模型aux absent/zero，或者冻结非零aux的预期公式。**`omni_mot_model.py:2015–2039`与`:1750–1783`是实际计算权威。普通Edge期望vision10/action10、normalize_by_active=False；不能只拿日志的未加权action/vision相加推导outer。`algorithm/loss/flow_matching.py:95–118,156–166`表明conditioned帧、有效通道、active-only设置会影响分母。

最小要求：冻结resolved loss/precision/optimizer/seed字段及其身份；CPU用Full/Partial、不同rank counts、有/无aux、conditioned/action-valid-mask负例验证公式。若接受当前目标，无须修改算法；如另选全局Consumer目标，再立实施Gate并改变新配置身份，不能冒充原实现等价。

### P1：真实任务验证太晚；init模式当前未实现

当前训练适配为raw15/state15/H16/17帧，`robocasa_exact_window_policy.py:61–102,218–220`、`cached_sft.py:97–127`作源/行身份检查。`transforms.py:329–407`的wam原则为vision首帧clean、action的state行clean；应从真实物化SequencePlan/Mask验证“其余16动作确实监督、64维无效通道不参与”，不能只验shape。

在线侧`closed_loop_eval.py:113–136,283–322`构造零base+state10，raw15→env12并将**实际提交命令**重编码给Local evidence；`eval_utils.py:89–130`有decoder/canonical roundtrip保护。源码契约一致，仍不能替代对真实controller坐标/单位、rot6d、gripper/base模式、视觉预处理及Local两次replan的验证。

建议把小型功能闭环移到S1、完整Checkpoint100后（若已有绑定当前ABI的有效证据，可复用），不要等500–2000再第一次发现动作ABI错误。可只用1–2任务、固定scene/seed、48–128 steps验证调用和动作执行；低SR本身不作FAIL。正式18-task summary仍必须等E1等评测可靠性Gate；E1候选不能未经独立验收就并入训练Pair。

`action_policy_server_robocasa.py:518`只支持off|required，**没有init**。当前可做同输入/同Seed的Local on/off功能干预，不能把off改名init来填三组消融。真正init/no-online-update消融需另立语义、实现、配置身份与Gate；不作为开始Fresh的必要开发前置。

### P2：性能和工程优化可分开，不应阻塞必要的正确性工作

逐参数finite同步、rank0遥测成本、缓存重复加载等保留原分批Gate。先用已有journal timestamp/外部整段wall测量包括audit与save的实际吞吐；不要为新路线先堆预取/缓存/异步哈希优化。最初选择num_workers0、full_segment_prefetch=False、明确冻结transform RNG策略合理；训练中不能静默切换keyed RNG或Layout。正确性前置不等于必须合入所有性能补丁。

## 6. 最小必须修改清单与影响边界

所有内容只是**待Owner/GPT确认的修改建议**，本轮未实施。

| 最小改动 | 建议位置 | CPU验收 | GPU是否必要 | Checkpoint / Config影响 |
|---|---|---|---|---|
| 显式Index8兼容选择，Packed默认不变，布局身份一致 | Phase5 parser/overlay/digest；Window dispatch；Trainer/telemetry必要接线及聚焦测试；canonical Launcher/命令 | 默认/显式/未知值、Full/Partial对齐、无fallback、跨layout恢复拒绝 | 新Packed真实native；Index8兼容另验，不做旧r2等价 | 新Pair；Layout digest真实绑定，尽量保留DCP schema；旧Frozen Source/Target不动 |
| 正式execution budget与schedule分离 | Phase5运行预算/完成检查；复用Trainer execution_max_iter | Fresh100、Resume101/500、已越界、GA边界、save/finalize失败、schedule不变 | 实际100→101续接 | 执行预算不改schedule/digest；不能借此重用bounded诊断 |
| 8rank完成确认+原子latest/Local发布 | DCP save_state_dict_worker/_save_as_pkl、latest发布（局部封装，不泛改easy_io） | 延迟/失败rank、半写/旧latest、全rank终止、sync/async | 新Job一次8rank Save→Resume | 内容schema可保持；新完成协议需版本说明，禁止修改旧DCP |
| strict RNG与Resume不reseed | DCP trainer-RNG读取；Trainer确定性分支，profile限定策略 | 整rank/单叶缺失、后续抽样连续、Fresh/Resume区别 | 首个恢复消费前8rank RNG见证 | 可仅收紧验证；随机策略须绑定新Fresh配置 |
| Fresh独占namespace、Resume先验身份与配置保护 | Phase5 preflight + Job创建/配置保存边界 | 旧目录/别名/并发/错身份保持字节不变 | 不需单独GPU实验 | 不改旧文件或DCP，新增启动记录/完整配置witness |

Loss/Aux实现改动、Global Consumer归一化、Local复制态重构、init消融、缓存默认打开、性能补丁**不自动纳入必须修改清单**。先冻结/验证需求；出现真实缺陷再单独修。每个新实施Pair独立CPU证据、DS验收、Fresh Review；不把本设计审核当批准去编码。

## 7. 最小 CPU/GPU 验收矩阵与监控

| Gate | 最小验证内容 | 可复用证据 / 不能替代什么 |
|---|---|---|
| C0 / CPU 版本与默认 | 新Pair、默认Packed/显式Index8、正式几何、完整resolved配置/摘要、源Index receipt、输出真实路径/独占性；8rank planner只用已有Index元数据预测Full/Partial/重绑定位置 | 不全量重扫/重hash451GB；旧Index验收不重开 |
| C1 / CPU Native/Local契约 | Full/Partial/PAD/S0、slot/prefix/action/mask严格对齐、fresh/continuation/mixed/terminal；有/无aux和不同rank counts的显式公式 | 复用现有合成测试并补缺口；不是GPU高阶图证据 |
| C2 / CPU 失败及恢复 | 错Layout/digest、缺组件/RNG/rank state、写失败/半写/迟到rank、正式预算不改schedule、旧namespace不改、全rank失败不挂死 | 不要求跑旧B1全量比较；不执行实际旧DCP迁移 |
| G0 / 一个新Fresh native健康门 | 精确新Pair+DROID+既定BF16/FSDP8；2–3真实optimizer更新；每GA一次packed forward/backward；实际N/Mask/Prefix；8rank非空eligible Slow/Action/Generation梯度与正确dtype的master更新、moment/step变化；fresh/continuation及Partial覆盖计划 | 旧B1 GPU执行可复用“这类架构能启动”的证据，不能代替新Local初始化/新Pair；CPU高阶导测试不能代替FSDP8。无旧Index8逐参比较，无128份大张量全捕获 |
| G1 / 同Job100 Save→Resume | 100保存后所有rank完成且最新指针稳定；5组件+8rank Local/RNG完整；恢复第一个pre-step时model/master/Adam/scheduler/GradScaler/frontier/sidecar与保存状态一致；第101步Consumer/CFG/随机状态与预期续接一致，之后真实更新 | **恢复前状态本应一致**，这不是要求两次CUDA训练trajectory或Index8/Packed梯度相等。只记录需要的FQN/状态摘要，不重复所有32 shard全量哈希 |
| G2 / 小闭环 | 新模型Checkpoint只读；真实raw15/state15→env12、两次以上replan、S0无prefix→后续prefix存在、completed-action evidence连续；同输入Seed Local on/off干预 | 无需early高SR；不得拿Local core单测冒充完整Policy+Online+Simulator |
| G3 / 学习效果 | 500时18-task×1仅screening；后续相同tasks/scenes/seeds、required/off，必要时独立实现init；视频/失败/error和置信度 | 低早期SR允许观察；错误ABI/断Local/系统性运行错误必须停止；不能把18单样本称统计结论 |

**每步适合保留：**iteration与真实optimizer成功、Layout、每member实际N/forward-backward计数、loss各分量/有效覆盖、LR与optimizer step、rank-local数据等待及端到端wall、NaN/Inf/运行错误。硬门失败须全Job停止，不能跳过样本或自动换路径。

**低频/门点采样即可：**每rank FQN分片角色、Local/Action/Generation梯度与FP32 master/Adam更新、W0 fresh/continuation参与、Fast State摘要、slot终端重绑定抽样、显存峰值、审计耗时、配置身份和Checkpoint完整性。无需每step全参数复制/哈希、大PT保存、全rank全量state范数或所有数据文件检查。

应检查优化器实际dtype/FP32 master归属（`utils/generator/optimizer.py:65–79,149–174`），不能强行要求存在一个特定名字的master字段。warmup500的最初几步更新很小；BF16前向权重未翻位不必等于没学习，需结合实际FP32 master/moment/梯度。W0全continuation为零、合法空shard不作FAIL；非空eligible组一直断梯度则必须FAIL。

**立即停止：**错误Pair/Layout/配置身份；非有限有效tensor/gradient；非空eligible Local全部断链；错误Consumer/Mask/ActionABI；跨Episode状态污染；保存不完整却宣称成功；恢复任一核心状态/RNG/下一Consumer不连续；容量低于下一次安全保存所需且无已授权解决方案；OOM后自动降batch/换Index8；严重运行基础设施错误。

**允许继续观察：**Warmup期loss不单调、Full/Partial间幅度变化、单个任务早期失败、合法零梯度/空shard、有限且受控的梯度尖峰。判断依据是冻结健康范围和直接功能见证，不能事后改阈值合理化NaN或历史B1失败。

## 8. 认可的执行顺序、GPU最省方案与磁盘处理

### 8.1 修订后的顺序

1. **S0：关闭明确接口/保存/RNG/namespace缺口，锁定新Pair和新完整配置，先解决存储。**冻结Index8保留/Packed默认；预先选择loss目标；只使用已验收Index，不重建/重扫。审核现有B1少量first-divergence摘要以排除已知可迁移的真实缺陷，不能自行将repeat FAIL解释为正常。
2. **保留一个新Fresh初始native健康门，但不坚持必须额外开一个完整3-step Job。**旧B1两步从iter1300模型/状态出发、不同Pair，V2也不是FSDP Local；不能完全替代。最省方案是在新正式Fresh-to100的前2–3步设置经审核的自动硬门和定向采样，同一进程通过后继续100；需新的正式budget/audit接口先实现验收，**当前CLI不能这么用**。若坚持独立bounded_3step，则接受它会写独立C3、提前配空间，不可拿该C3当formal Resume源。
3. **正式Fresh至100**，schedule始终30000/500/save100，已批准输出新路径；到完整optimizer边界干净保存、finalize、全rank成功退出。不要以latest出现/grep一行rank0日志就kill。
4. **100→101恢复健康门**必须保留。恢复前比对状态，101验证下一Consumer/RNG/LR/optimizer与Local续接。可以将101硬门与后续至500放在一个另获授权的Resume预算中，通过硬门后继续，避免为“只到101”额外写C101、再重载一次；若授权确实只到101，就应真的停并预留C101，不能默认继续。
5. **把小型真实功能闭环提前至100后**，复用此处暂停/Checkpoint；与恢复门可按资源安排先后，二者都要在长训前通过。正式18-task批量评测只使用独立验收过的E1评测Pair；训练Pair不因合并评测补丁而滚动变化，记录train/eval两个身份。init消融可以后置。
6. **S2至500**观察学习健康及真实耗时；**S3至2000**固定协议任务评测，兼顾18-task×1筛查与少量多seed分析。S2/S3可作为同一持续Job的决策点，不必每点kill/restart；若无进展且功能链有缺陷立即停，不能等2000才查ABI。
7. **S4长训与最终验收**以真实任务趋势和剩余时间决定；30k是预算上限，不是无效长训必须完成的仪式。旧B1、Gate M、Formal原Job和数据Evidence保持原身份和结论；任何新执行另行Owner批准。

### 8.2 存储不能只解决“眼前能存两份”

S0先由DS只读报告目标持久卷实际free/quota、原DCP/595GB Evidence位置、新Job真实路径、baseline占用。**本报告没有独立测量这些数值。**优先新持久卷/扩容/另一个已授权输出位置；未经Owner授权不移动或删除旧Evidence、旧Job/DCP，也不自动压缩重写原始PT。

设新完整DCP实际大小为C，至少预算保留的完整副本、正在写的副本/CPU staging、日志/视频、失败空间及余量；若保留2完整+1在写，应按约`3C + 日志/评测 + 余量`核算，不能把“2份”同时当在写空间。C只能由可复用的同结构清单/首个真实保存测得，不用595GB GPU捕获大小猜测C。

当前每100步保存、到30000约**300个完整保存点**；所查DCP保存路径没有这一路线的自动保留/淘汰策略，Phase5还清空通用callbacks。若全保留，需预算约300C；若仅保留少量，则在启动前由Owner明确批准**新Job**的保留/归档规则（latest及前一完整版本、选定里程碑、验收源不删；正在写/被评测读取的不动；移出须先校验新副本）。不在训练中把save100改成save500来“省空间”，因为它已进入digest/schedule；更不以此清理历史B1。没有空间方案则该执行阶段BLOCKED，设计审核仍可完成。

### 8.3 最少额外GPU与时间预算

可把“独立3步烟测 + Fresh100 + 单步Resume101 + 再Resume到500”压缩为**Fresh-to100含前3步硬门 + 一次Resume含101硬门至500**，加Checkpoint100上的小功能闭环；前提是上述接口和采样先验收、Owner按这个预算明确授权。否则保留独立3步也可以，不能跳过新的Fresh高阶图/分片验证。无需再跑旧B1八个对比Job、全量PT捕获或重复451GB离线验收。

ETA应使用包括遥测、checkpoint、共享GPU干扰和评测的实际端到端wall/p50/p95，计入后续保存次数、评测和失败余量。不能把rank0 pre-telemetry消费者吞吐直接外推到11月30日，更不能把V2 A100的LIBERO步时等同于V3 H100的RoboCasa步时。

## 9. 最终建议与关闭条件

**`REQUEST_CHANGES`，不是否定Fresh路线，也不是旧B1阈值申诉。**

认可：Packed128独立Fresh、保留Index8对照、保持旧失败结论、以自身Save/Resume和真实RoboCasa效果为门的方向。

变成`APPROVE_PLAN`至少需要：

1. 将“当前已Packed”与“尚缺显式Index8兼容路径/正式Launcher”分别写清，并冻结最小补齐范围。
2. 为正式100/101分段提供可执行且不改schedule的边界，明确3步/101都会保存的磁盘后果。
3. 关闭Checkpoint全rank发布及严格RNG/Resume重置问题，正式Fresh前保护独占namespace与原配置；实现另获批准并经独立验收。
4. 提前真实Action/Local功能见证，明确非空shard、W0角色及Loss/Aux/跨rank归一化口径，不用普通Loss下降替代这些见证。
5. 给出实际输出卷容量及新Job长期Checkpoint保留/归档方案；E1等评测Gate保持独立，不盲目合并。

即使后续`APPROVE_PLAN`，仍只批准设计；**不会自动授权任何GPU、Fresh/Resume、正式Checkpoint写入、旧Formal Job恢复或Gate M。**当前报告只提交审核结论，等待GPT/Owner确定实施范围。
