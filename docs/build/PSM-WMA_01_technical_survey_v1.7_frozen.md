# PSM-WMA：Persistent Spatial Memory-Augmented World-Model Agent
# 技术调研报告 v1.7（Local/Global Memory Modality 专项收敛版）

> **文档类型**：正式技术调研报告  
> **版本**：v1.7-frozen  
> **日期**：2026-08-12  
> **项目名称**：PSM-WMA（Persistent Spatial Memory-Augmented World-Model Agent）  
> **上游 Source of Truth**：《PSM-WMA 研究准备清单与总体方案 v3.2.2（稳定版）》  
> **上游立项书**：《PSM-WMA 项目立项书 v1.4-frozen》  
> **参考文档方法**：MoWA `docs_zh/mowa/01_technical_survey.md` v2.11  
> **执行约束**：单人串行；1–8×A100 80GB；RTX 4090 用于开发/轻量验证；关键训练实验总量 ≤20  
> **报告目标**：把“研究准备阶段的候选清单”收敛为可直接进入 `02_detailed_design.md` 的技术决策输入，而不是重复堆论文。
> **Scope Override（2026-08-12）**：当前主线 Memory 拓扑更新为 **Temporal Local Memory + Spatial Global Memory**。Spatial Global Memory 是全 episode 历史的空间结构化存储与按需检索，不等于 Region/Place 层级化 Regional Global PSM；后者仍为 BEHAVIOR-only。Goal Memory 保留为后续可选扩展。Local / Global 均按 Cosmos-style optional modality 设计，后续由 Planner / Reasoner 决定 presence、query 与 token budget。

---

## 修订记录

- **v1.7（2026-08-12）**：在 v1.6 Cosmos-native 路线基础上完成 Memory Injection / Representation 专项收敛。当前主 PSM 拆为两个独立可选模态：Temporal Local Memory（时间对齐的 RGB/视觉、depth、pose、robot state、可选 wrist RGB、executed action 经学习式压缩形成）与 Spatial Global Memory（历史视觉/几何/pose/trajectory/time 经过空间结构化重组与 retrieval，提取关键 patch/key-view/feature）。两者分别使用独立 mapper / modality embedding 接入 Cosmos3 shared MoT；第一版均作为 clean condition，无 decoder、无 memory reconstruction loss。新增 Planner-facing optional-modality interface；评审 Native Memory Modality、Global→Vision Control、zero-gated residual/ControlNet-lite、KV MemoryState 四种注入范式，Native Memory Modality 为当前第一候选，Global→Vision Control 为强备选，Full ControlNet 不优先。补充 LaMem-VLA、ReMem-VLA、μVLA、SERF、VistaVLA、MosaicMem、ControlNet、OminiControl 证据链。
- **v1.7 Local Candidate Addendum（2026-08-12）**：新增 RoboTTT（arXiv:2607.15275）作为 Temporal Local Memory 的第一优先候选机制。RoboTTT 将 fast weights 作为 recurrent state，在训练与推理时通过 TTT-KVB 更新，并用 sequence action forcing + TBPTT 把训练上下文扩展到 8K timesteps（官方约 5 分钟）；这直接支持“固定/受控状态容量 + 长状态链 + 短梯度链”的 Local 方向。但 RoboTTT 原版把 TTT layer 集成进 VLA policy，本项目首选改造成独立 Local temporal compressor/readout，再通过 Local optional modality 接入 Cosmos3。**该选择仍是 Candidate，不是 Frozen**；simple recurrent latent/fixed-token compressor 保留为 baseline，R06 PASS 后再通过 R09-A/B 工程 smoke 决策。

- **v1.6（2026-08-11）**：按“先比较、后选型”原则重做 World-Action/Reasoner 路线评审；将 Cosmos3 从条件候选提升为主工程路线，代码母体改为 NVIDIA `cosmos-framework`，基础 checkpoint 采用 `Cosmos3-Edge-Policy-DROID`；StarVLA/LayerwiseFM 降为历史 baseline / fallback 参考。明确 Reasoner 与 Generator 是同一 checkpoint 的两条 inference pathway，PSM 第一版作为 clean persistent conditioning modality 接入 Generator，并通过 compact readout 接入 Reasoner。

| 版本 | 日期 | 主要修改 |
|---|---|---|
| v1.0 | 2026-08-10 | 首版正式技术调研候选。继承 v3.2.2 与立项书边界，重新独立核验 Backbone、Spatial Observation、Local/Global PSM、Writer/Reader、World/Action coupling、Benchmark、Agent、Continual/Proactive；新增 RoboMemArena、DREAM、RetrieveVGGT、MobileWAM、LiLa-WAM、SelfWAM、Mind-VLA 等未完全依赖研究清单的新近工作；给出 Build / Reuse / Adapt / Compare 决策、证据成熟度、许可证约束、主路线、fallback 与详细设计输入。 |
| v1.1 | 2026-08-10 | 冻结前承重审查：新增 μVLA / ReMem-VLA 对 recurrent latent memory 的直接证据并明确其能力边界；将 `gated update/read` 从文献结论降级为默认实现候选；将 Global `latent content + semi-explicit address` 明确标注为本项目综合式自研组合；将 geometry-first Reader 限定为 V0 prefilter 而非最终最优；补充“测试时可不生成未来视频，但 World-Model-derived representation 必须仍进入 action path”的硬边界；发现 oVDA 官方代码主许可证禁止商业使用，研究主线改为 oVDA，oVDA 作为研究主候选；许可证限制单独记录；同步更新许可证表、Build/Reuse 矩阵和详细设计冻结输入。 |
| v1.2 | 2026-08-10 | 外部独立评审后正式冻结：补齐 RISE / WoVR / FPO 参考资料；补充 [36] Efficient-WAM 以消除编号缺口并纳入轻量 WAM 对照；将 RoboCasa365 改为官网给出的正式 ICLR 2026 引用；确认 EventVLA / τ0-WM / Mind-VLA 均可由 arXiv 一手页面核验；确认 RoboCasa365 2026-07-07 per-frame subtask 更新来自官网；确认 μVLA 的 0.42→0.84 与 LIBERO 96.2% 可由论文正文直接复核；保留 D4RT“CVPR 2026 Best Paper”并增加 CVPR 官方奖项来源；StarVLA/WM4A 能力声明统一加“以仓库 smoke test 为准”；所有许可证字段统一加“最终以实际使用代码、权重和依赖的 LICENSE 为准”。 |
| v1.3 | 2026-08-11 | 范围收敛修订：LIBERO 与 RoboCasa365 阶段不再引入 Region/Place 划分、Global Spatial Store、Spatial Writer/Reader；当前主线记忆拓扑简化为 **Short-term Video State + 单一 Local Memory + 单一 Goal Memory**。Local Memory 保存任务无关的持续场景状态；Goal Memory 保存当前 goal/subgoal 条件下的任务相关长期历史/进度摘要，goal/subgoal 变化时可重置或重建。真正的区域化 Global PSM 仅在进入 BEHAVIOR-1K / 多房间 mobile manipulation 后重新专项调研与设计；原 Global PSM 文献调研保留为未来阶段技术储备，不作为当前 LIBERO/RoboCasa 设计约束。 |
| v1.4 | 2026-08-11 | 与立项书 v1.1、详细设计 v1.2、G0 Static/Runtime v0.3 全面对齐：LIBERO/RoboCasa 当前拓扑固定为 Short-term + Local Memory + Goal Memory；Regional Global PSM 仅作为 BEHAVIOR-only 技术储备；清理当前阶段的 Wrong-region、pose/region Gate、Global Writer/Reader 硬约束；补充 Memory Injection Topology 的阶段性结论——Must-have 采用 post-backbone shared WorldState + Action path，true backbone-side memory injection 仅作为 Target 候选，不阻断当前实现。 |

---

# 引用、核验与证据等级说明

本报告以 **2026-08-11** 为核验截点。技术结论采用以下证据纪律：

1. **A 级：工程可依赖**：一手论文/官方项目页 + 官方代码/权重或 benchmark + 开放状态与许可证可核验。可直接作为详细设计依赖，但仍需本地 smoke test。
2. **B 级：方法可信、工程需验证**：一手论文真实，官方代码/权重部分开放、刚发布、接口尚未在本项目环境验证，或许可证依赖需要进一步确认。可作为候选或对照，不可默认为“已能直接集成”。
3. **C 级：研究参考**：论文/项目存在，但代码未开放、实现不完整、依赖重或目标与 PSM-WMA 距离较远。只用于方法设计，不进入首期硬依赖。
4. **D 级：线索**：二手材料、未能核验的实现细节。本报告不使用 D 级证据冻结设计。

研究清单中的结论被视为**内部研究输入**，不是外部事实的替代物。本报告对承重选择重新核验，并允许新增上游清单未覆盖的工作。

---

# 快速参考索引：本报告最终收敛结论

| 模块 | 本报告推荐路线 | 状态 | 主要理由 | 关键 fallback |
|---|---|---|---|---|
| 基础执行策略 | **Cosmos3-Edge-Policy-DROID warm start → 先建立 Edge-Policy-LIBERO 无 PSM baseline** | **Primary** | 已具 robot world-action post-training，减少“先学会控制”这一额外变量 | Cosmos Policy Predict2-2B；再降级 stable VLA |
| World/Action/Reasoner Host | **NVIDIA cosmos-framework + Cosmos3-Edge-Policy-DROID** | **Frozen Primary** | 4B；原生 Vision/Action；SequencePlan/PackedSequence；multi-domain action；同 checkpoint Reasoner | Cosmos Policy Predict2-2B；stable VLA + modular WM |
| 深度 | **oVDA（唯一 learned-depth provider）** | **Conditional / 推荐** | causal online + offline sequential cache 统一；论文报告 A100 42 FPS / Jetson 20 FPS；许可证仅记录，不作为本研究首要 Gate | RGB-only baseline / simulator depth；VDA-S 仅 future accuracy upper-bound |
| 强几何对照 | StreamVGGT / commercial-cleared VGGT 仅在 Q1 几何瓶颈时触发 | **对照** | 几何能力强，但不等于 Memory；StreamVGGT 依赖/许可证需审计 | oVDA + pose metadata |
| 4D Query 参考 | D4RT / RetrieveVGGT | **BEHAVIOR 技术储备** | query readout、固定预算 spatial retrieval 未来可用于 Regional Reader | 当前不实现 |
| Local PSM | **固定容量 recurrent latent/query memory**；gated update/read 为默认实现候选 | **主路线** | μVLA、ReMem-VLA 直接支持 recurrent memory，但也表明单层 recurrence 并非万能长程记忆 | frame/key memory；dual-scale/Hybrid fallback |
| Spatial Global Memory | **persistent spatial store + query/compress + independent global adapter** | **Stage 2 主路线** | 全 episode 历史按空间/视角/时间重组，按需提取关键 patch/key-view/feature；不要求 Region/Place | key-view memory / Global→Vision Control |
| Goal Memory | **goal-conditioned memory / progress（可选）** | **Stage 3 Target** | 作为 Planner/Agent 的目标历史扩展，不替代 Global Spatial Memory | planner summary / longer history |
| Regional/Place Global hierarchy | **BEHAVIOR-1K 前不实现** | **Deferred** | 只有进入真正多房间/大空间后才解决 place/region hierarchy、跨区域 addressing/revisit | 到 BEHAVIOR 阶段重新专项调研 |
| Regional Writer/Reader | 暂不冻结 | **Deferred** | 当前环境没有必要提前设计 region create/match 与 spatial Top-K | BEHAVIOR 阶段再定 |
| PSM→World/Action | 尽可能用**同一 Readout**同时供 future/world 与 action | **目标路线** | 系统价值强，MemoryVAM/MemoryVLA++证明共享记忆进入 world/action 可行 | 先 Memory→Action，再接 WM |
| Future inference | **不要求测试时生成未来视频，但 WM-derived hidden/world state 必须继续进入 action path** | **硬边界** | Fast-WAM、MobileWAM、SelfWAM 支持去掉 future generation；但 PSM-WMA 不能退化成普通 VLA + 训练期 auxiliary loss | diagnostic-only future decode |
| Memory 主监督 | action loss + action-conditioned future latent/feature；depth/geometry 为轻辅助 | **推荐** | Memory 必须被任务梯度塑造，避免独立“建图模块” | action-only + probe |
| Intervention | Local: Zero/Shuffle/Stale/Truncated；Global: Zero/Shuffle/Wrong-view/Stale/Top-K truncation；`absent` 与 `present+zero` 分离 | **必须** | 防止强 backbone 绕过 Memory，并区分 Temporal Local / Spatial Global 职责 | 无 |
| Stage-1 诊断 | LIBERO/已有稳定策略 + LIBERO-Mem + RoboMME | **推荐** | 低成本证明 Memory 真使用 | RMBench / RoboMemArena |
| Stage-2 主环境 | RoboCasa365 | **推荐** | 365 tasks、2,500+ scenes、2,200+ h demos、分帧 subtask 标注 | RoboCasa 原版子集 |
| Goal Memory 诊断 | LIBERO-Mem / RoboMME / RoboMemArena（条件） | **辅助** | 当前重点验证长期任务历史与 goal-conditioned recall，不做 region-revisit | 普通 longer-history control |
| 最终环境 | BEHAVIOR-1K 小子集 | **后置** | house-scale long-horizon mobile manipulation | 不做全量起步 |
| Agent | Harness VLA / HoloAgent 的角色划分；最小 planner-actor-verifier | **后置但首期做 thin slice** | 项目名含 Agent，但不允许 Agent 吞掉 PSM 主线 | rule-light verifier |
| Continual / Proactive | 只保留接口与进入条件，不占首期实验 | **Deferred** | 首先把 PSM→WM→Action 闭环做稳 | 无 |

---

# 冻结前承重审查结论

本轮对四个承重选择进行独立核验，结论如下。

| 决策 | 审查结论 | 证据与边界 |
|---|---|---|
| Local recurrent latent | **保留主路线** | μVLA 用少量 learnable recurrent memory tokens 在部分可观测操作上显著提升；ReMem-VLA 用双层 recurrent queries 获得短/长程能力。与此同时，两者都提示“简单 recurrence”存在任务结构与 TBPTT 边界，因此它适合作为 **Local PSM**，不能直接扩张成 Global PSM。[62][63] |
| Spatial Global Memory（LIBERO/RoboCasa） | **提升为当前主线** | 当前不要求 Region/Place 层级化，但可以验证全 episode 历史按空间/视角/时间重组后的关键证据检索，以及 Global→World/Action 的独立收益；Goal Memory 降为 task-progress gap 明确时才启用的 Target。 |
| Regional Global PSM（BEHAVIOR） | **保留为未来方向，但不在当前阶段冻结实现** | Mirage、Mem-World、SERF、HoloAgent、RetrieveVGGT 等仍提供有效技术储备；真正到多房间/大空间任务时再根据 BEHAVIOR 数据与导航定位条件重新决定 place/region 表示、Writer/Reader 和 stale 策略。 |
| Training-time future + fast inference | **保留，但增加硬约束** | Fast-WAM、MobileWAM、SelfWAM 支持推理时不生成未来视频；但本项目必须确保 action 在推理时仍消费 **world-model-trained / PSM-conditioned hidden representation**。若把 World branch 全部拿掉，仅剩普通 VLA + auxiliary future loss，则不满足 PSM-WMA 项目定义。[34][38][40] |

此外，oVDA 的技术能力与许可证必须分开处理：论文/项目的 causal online depth 能力成立，但官方仓库采用 mixed licensing，部分代码受 NC-SA-UHDV1.0 约束，产品化前需要单独做许可审查。[8] 当前项目是研究项目，因此 **oVDA 仍作为唯一 learned-depth provider**；许可证记录不作为本轮算法研究的首要 PASS/FAIL 条件。


---

# 第一章 调研范围、立项遗留问题与方法

## 1.1 技术调研报告的职责

立项书已经回答“为什么做、做什么、什么不做、做到什么算成功”。本报告不重新论证项目价值，而要把立项书留下的技术问题收敛为：主方案、备选方案、淘汰/后置方案、可直接复用的工程资产、必须本地验证的未知项，以及进入 `02_detailed_design.md` 时可以冻结的设计边界。

因此，本报告**不**提前给出最终 tensor shape、token 数、LoRA rank、loss 数值权重、exact training step、E001–E020 的具体实验编号、代码类名和每层插入点。这些属于详细设计。

## 1.2 上游冻结边界

以下口径不得在本报告中静默改变：

- 研究主体：Persistent Spatial Memory + action-conditioned World Model；
- Agent 为最终闭环，不是前期主创新；
- 当前主线使用 **Current/Short-term Observation + Temporal Local Memory + Spatial Global Memory**；Region/Place 层级化 Global 只有进入真正多房间任务时才扩展；Goal Memory 为条件 Target；
- 内容以 latent/token 为主，不默认显式 point cloud/3DGS；
- LIBERO → RoboCasa365 → BEHAVIOR-1K；
- Memory benchmark 是 diagnostic，不替代真实机器人执行指标；
- World-Action/Reasoner 主路线已由多路线比较收敛到 Cosmos3-Edge-Policy-DROID；仍需 Runtime Gate 验证 Edge→目标 embodiment 的可执行性；
- 隐式 latent PSM 若连续两轮无法通过 intervention 证明被使用，则允许 Hybrid PSM fallback；
- Region/Place Writer/Reader **不在 LIBERO/RoboCasa 阶段实现或冻结**；进入 BEHAVIOR-1K 后再重新做专项技术决策；
- 不研究新的 VLN/path planning 算法；
- 关键训练实验 ≤20。

## 1.3 本轮独立调研相对研究清单的新增

本报告没有只复述 v3.2.2。独立搜索新增了若干会影响决策的 2026 工作：

1. **RoboMemArena**：26 个超长程 memory manipulation tasks，平均轨迹 >1000 steps，且提供 keyframe/subtask annotations；说明 RoboMME 之外还有更贴近长程复杂操作的诊断资源。[44]
2. **DREAM**：动态 mobile manipulation 中维护在线 spatio-semantic voxel memory，并处理 pose correction 与 stale observation；它是 Global PSM 动态更新与企业落地风险的重要显式对照。[29]
3. **RetrieveVGGT**：把 streaming geometry 的 context 构造变成固定预算 retrieval，使用 pose-aware spatial memory 与 query-key similarity；强化本项目 Global Reader 的“geometry-first”路线。[12]
4. **MobileWAM**：把 WAM 推到 mobile manipulation，并在部署时丢弃 future chain、保留 policy-level cost；进一步支持“future supervision 不必变成 test-time video rollout”的路线。[38]
5. **LiLa-WAM**：用紧凑 latent reasoning space 在单 24GB GPU 上做 world-action joint learning，说明小型 latent future branch 可作为 Cosmos 失败后的低成本 WM fallback。[39]
6. **SelfWAM**：action-conditioned future RGB/self-mask 只服务 joint training，在线保持 fast action-only inference；进一步强调 future target 应尽量 action-sensitive。[40]
7. **Mind-VLA**：instruction-aware 3D representation alignment 可显著改善空间操作，但它仍是 spatial feature/alignment 而非 persistent memory；用于防止把“空间编码强”误判为“会记忆”。[41]
8. **μVLA**：用少量 recurrent memory tokens 隔离验证 recurrence 本身，在 MIKASA-Robo 上将最强设置的平均 SR 从 0.42 提升到 0.84，同时在 LIBERO 保持 96.2%；但对“需要不同 memory structure”的任务接近 baseline，直接说明 recurrence 有明确能力边界。[62]
9. **ReMem-VLA**：用 frame-level + chunk-level recurrent queries 建立双时间尺度记忆，并指出简单 frame-level recurrence / 短 TBPTT 对真正长程依赖可能不足；它强化了“Local recurrent state 可做，但 Global memory 需要另外的空间生命周期”的项目分层。[63]

这些新增项不会改变项目主线，但会影响 fallback、对照和 Reader/WM 设计。

---

# 第二章 最近邻谱系与 PSM-WMA 的真实技术边界

## 2.1 2026 年的 Memory + WAM/VLA 已经非常拥挤

如果仍把 PSM-WMA 描述成“给 WAM 增加记忆”，将无法解释项目差异。最近邻至少形成五类。

### A. Temporal / Episodic Memory → World/Action
MemoryVAM、MemoryWAM、MemoryVLA/MemoryVLA++、DiM-WAM、HiMem-WAM、EventVLA、KEMO、HALO 等擅长“过去发生了什么、哪个事件重要”，但未必天然回答“这个状态属于哪个空间区域”。

### B. Persistent Spatial Memory → Action
SOMA、SERF、DREAM、HoloAgent-0 已经证明**空间记忆对动作/Agent 有价值**。因此 PSM-WMA 不应主张“首次把空间记忆用于机器人动作”。

### C. Persistent Spatial Memory → World Model
Video World Models with Long-term Spatial Memory、Mirage、MosaicMem、Mem-World、WorldKV 证明**空间记忆能提升 world consistency/future modeling**。其中 Mem-World 是最直接的 PSM-WMA 近邻。

### D. Addressable World State
OA-WAM 把 scene 分成 persistent address + dynamic content 的 object slots，并做 slot-level intervention。它说明“addressability”本身也不是空白。本项目若采用 region/place addressing，应强调**空间尺度与长期状态生命周期**。

### E. Spatially Strong VLA
Mind-VLA、Spatial-Forcing 等说明空间表示增强能改善 action，但这类方法不维护跨时间 persistent state。它们是 Q1 Spatial Observation / Representation 的对照，不是 Q2 Memory 的替代。

## 2.2 最近邻对比矩阵

| 工作 | Memory 内容 | Address | Update | 进入 World | 进入 Action | 层级类型 | 对 PSM-WMA 最有价值部分 |
|---|---|---|---|---|---|---|---|
| MemoryVAM | episodic history | time/event | recall | ✅ | ✅ | temporal | shared memory→world/action |
| MemoryWAM | recent+anchor+gist | time/event | compress | ✅ | ✅ | temporal | efficient persistent temporal memory |
| MemoryVLA++ | perceptual/cognitive bank | semantic/history | consolidation | imagination | ✅ | working/long-term | memory+imagination+action |
| DiM-WAM | event banks | event | bounded banks | ✅ | ✅ | temporal banks | bounded memory + dual conditioning |
| HiMem-WAM | skill/motion | boundary | boundary-triggered | latent WAM | ✅ | skill hierarchy | stage-aware write |
| EventVLA | selected visual events | keyframe/event | event write | optional/probe | ✅ | recent+events | learned writer reference |
| Mem-World | 4D surfel-linked history | geometry+action | persistent | ✅ | indirect/policy eval | spatial | **closest spatial-memory→WM** |
| SOMA | spatial-semantic scene memory | object/spatial | dynamic refinement | ❌ | ✅ | scene | spatial update/retrieval |
| SERF | environment+robot neural points | 3D frame | online | ❌ | ✅ | local/global map | **local/global spatial state→policy** |
| DREAM | spatio-semantic voxel memory | map/semantic | prune/reconcile | ❌ | system action | global | stale/pose correction |
| HoloAgent-0 | 3D spatial/scene graph | floor/room/view/object | dynamic | ❌ | skill/Agent | spatial hierarchy | Agent/world state interface |
| Mirage | diffusion latent 3D cache | geometry/view | read/write | ✅ | ❌ | spatial | **latent content in 3D** |
| MosaicMem | aligned patches | geometry/view | compose | ✅ | ❌ | spatial | hybrid fallback |
| WorldKV | evicted WM KV chunks | camera/action | store/compress | ✅ | ❌ | long-term | native WM retrieval |
| OA-WAM | robot/object slots | object address | dynamic content | ✅ | ✅ | object | address/content separation |

## 2.3 企业项目不需要证明“组合首创”

合理定位是：

> 把 **持续空间状态 → action-conditioned world representation → online action → Agent monitor/recovery** 做成稳定、可诊断、可扩展的闭环；优先复用近邻能力，再在真正有收益的接口上做 1–2 个方法增量。

因此 persistent memory、spatial memory、hierarchical memory、stale handling、keyframe memory、memory intervention、WAM joint action/future 均不单独称为创新。

---

# 第三章 World-Action / Reasoner 技术路线比较与主方案筛选

## 3.1 选型问题不是“哪个模型分数最高”

PSM-WMA 的研究变量是 Temporal Local Memory + Spatial Global Memory，以及二者如何作为独立可选条件进入统一 World/Action 主干，而不是重新发明 Action Head 或从零训练世界模型。因此主工程路线必须尽量减少与 Memory 无关的结构变量，并满足：

1. world representation 必须真实进入 action path；
2. 能同时表达“已知 condition”和“待生成 target”，便于 Forward Dynamics / Policy / Inverse Dynamics 统一；
3. Action 最好是原生 modality，而不是再外挂一套深 Action Transformer；
4. 支持多 embodiment / 可变 action dimension；
5. 最好同一 checkpoint 还保留视觉语言 Reasoner，可承担低频 Agent / verifier；
6. 有公开 checkpoint、SFT/后训练代码、inference/serving 路径；
7. 4B 左右规模优先，单人 1–8×A100 80GB 可操作；
8. 能以最少改动加入 PSM clean condition，并通过 intervention 做因果归因。

因此本章比较的是“PSM-WMA 的工程宿主范式”，而不是单独比较视频质量或 LIBERO SR。

## 3.2 路线 A：成熟 VLA + 模块化 latent World Model

代表形态：稳定 VLA policy（如 StarVLA/Qwen+Flow Matching）外接 feature/latent future predictor。

优点：
- baseline 成熟，LIBERO/RoboCasa 工程资产多；
- action closed-loop 风险最低；
- future branch 可以很小，便于快速验证 Memory→Future。

缺点：
- World Model 与 Action Policy 天然分裂；
- 需要额外设计 `Memory→World`、`World→Action`、`Memory→Action` 接口；
- 很容易退化为“普通 VLA + auxiliary future loss”，无法证明 world model 在 inference action path 中发挥作用；
- PSM 实验会被 ActionBridge / WorldStateAdapter / head topology 等额外变量污染。

**结论**：保留为低风险 fallback / 对照，不再作为主工程母体。

## 3.3 路线 B：视频世界模型 + 独立 Action module

代表形态：Wan/Predict 系视频 DiT + Action DiT/Action expert，Faster-WAM/X-WAM/类似统一训练路线。

优点：
- world representation 强；
- action-conditioned future 与 action joint training 已有充分证据；
- Faster-WAM 说明 Action module 可以很浅，不必成为主要研究变量。

缺点：
- 即使 Action module 很浅，仍要维护 video/action 两条结构和接口；
- Memory 注入点仍需在 video backbone、action module、cross-modal bridge 之间选择；
- Reasoner/Agent 通常仍需额外 VLM/LLM。

**结论**：重要论文对照，尤其用于证明“World+Action joint representation”价值，但不是本项目最简主线。

## 3.4 路线 C：Cosmos Policy Predict2-2B（上一代 Cosmos Policy）

Cosmos Policy 基于上一代 Cosmos-Predict2 视频模型，把机器人 action / proprio / value 等包装进视频 diffusion latent 训练，使视频模型直接成为 visuomotor policy。官方公开 `Cosmos-Policy-LIBERO-Predict2-2B`，并在 LIBERO 四套任务上给出强闭环结果。

优点：
- 2B，资源友好；
- LIBERO 已有直接执行证据；
- 证明“视频世界模型直接做 action policy”路线可行。

局限：
- 属于 Cosmos3 之前的上一代范式；
- Action 更接近“编码成视频 latent frame”，不是 Cosmos3 的原生 action modality；
- Reasoner / 多模态任务路由 / multi-embodiment abstraction 不如 Cosmos3 原生统一。

**结论**：作为 P1 fallback 很有价值，但不作为首选主架构。

## 3.5 路线 D：Cosmos3-Nano Action Policy

官方 `cosmos-framework` 已公开 DROID 与 LIBERO Action-Policy SFT recipe；LIBERO recipe 使用 `frame_wise_relative` + rot6d 10D action、chunk 16，并有 `libero_10` / `libero_all` launcher。

优点：
- Cosmos3 原生 Action modality；
- 官方 LIBERO SFT 路径最完整；
- SequencePlan / PackedSequence / multi-domain action abstraction 已开源。

局限：
- Nano 为 16B，对本项目单人快速迭代偏重；
- 研究重点是 PSM，不应把大部分资源花在 16B policy adaptation 上。

**结论**：作为“官方 LIBERO 数据/action contract”的最佳工程参考，但不作为主模型尺寸。

## 3.6 路线 E：裸 Cosmos3-Edge 4B

Cosmos3-Edge 是 4B 统一 omnimodal 模型。Generator 原生支持 Vision / Action / Sound 等连续模态；Reasoner 支持 text/image/video understanding。源码中 Action 通过 `action2llm / llm2action + action_modality_embed` 进入共享 MoT，而不是外挂深 Action DiT。

优点：
- 4B，规模合适；
- 原生支持 Policy / Forward Dynamics / Inverse Dynamics 的 condition/target 组合；
- `SequencePlan` 显式描述 modality presence 与 clean/noisy target；
- multi-embodiment 通过 `domain_id / raw_action_dim / DomainAwareLinear` 支持；
- PSM 可自然扩展为 clean conditioning modality。

局限：
- 裸 Edge 虽有 Action modeling 能力，但不是一个针对 DROID/LIBERO 闭环控制后训练好的 policy checkpoint；
- 若从裸 Edge 开始，项目首先要花时间重新建立 robot policy ability，归因不利。

**结论**：World/Reasoner foundation reference，不作为 PSM-WMA policy warm start 首选。

## 3.7 路线 F：Cosmos3-Edge-Policy-DROID 4B

`Cosmos3-Edge-Policy-DROID` 是 Cosmos3-Edge 经过 DROID robot action-policy post-training 的 4B checkpoint。公开模型保持 Cosmos3 Reasoner 能力，同时 Generator 已学习机器人视觉/世界/action coupling。DROID policy action 为 8D absolute joint position（7 joints + gripper），典型 action chunk `[16,8]`。

其关键价值不是“8D head 可以直接迁所有机器人”，而是：
- shared generation pathway 已经经过 robot policy post-training；
- Action 仍是 Cosmos3 原生 modality；
- Reasoner 与 Generator 共存在同一 checkpoint；
- action-specific projection 是 embodiment-aware，可为 LIBERO/RoboCasa/BEHAVIOR 建立新 domain；
- 官方 `cosmos-framework` 同时提供 Action SFT、Reasoner、Generator、serving 和 checkpoint 工具。

风险：
- 官方公开的 exact LIBERO action-policy recipe 当前是 Nano，而不是 Edge；
- Edge-Policy-DROID 不能零样本直接跑 LIBERO/RoboCasa/BEHAVIOR，必须做 embodiment/action-contract adaptation；
- Reasoner 与 Generator 当前是两条 inference loop：Reasoner 为 autoregressive text，Generator 为 flow-matching continuous generation，并非一次 decoding 同时输出 text+action。

**结论：主方案。**

## 3.8 路线 G：DINO-WM / feature-space dynamics

优点：轻量、训练快、适合检查 Memory 是否能改善未来 feature prediction。  
缺点：不天然提供 robot Action policy、Reasoner 或统一多 embodiment abstraction。

**结论**：若 Cosmos 主线工程 Gate 失败，用作最低成本 World Model fallback；不能替代最终 World-Action 主路径。

## 3.9 路线对比矩阵

| 路线 | World→Action 原生耦合 | Action 原生 modality | Reasoner | Multi-embodiment | LIBERO 直接证据 | 规模/工程成本 | PSM 接入变量数 | 决策 |
|---|---|---|---|---|---|---|---|---|
| Stable VLA + modular WM | 中 | 否 | 外挂 | 依赖 policy | 强 | 低 | 高 | fallback |
| Video WM + Action module | 强 | 部分 | 外挂 | 需适配 | 强（视工作而定） | 中 | 中 | compare |
| Cosmos Policy Predict2-2B | 强 | 非原生（latent packaging） | 弱/外部 | 中 | **有** | 低 | 中 | P1 fallback |
| Cosmos3-Nano Policy | **强** | **是** | **是** | **是** | **官方 SFT recipe** | **高（16B）** | 低 | recipe reference |
| Cosmos3-Edge | 强 | 是 | 是 | 是 | 未见公开 Edge-LIBERO closed-loop | 中（4B） | 低 | foundation reference |
| **Cosmos3-Edge-Policy-DROID** | **强** | **是** | **是** | **是** | DROID/RoboLab 有；LIBERO需适配 | **中（4B）** | **最低** | **Primary** |
| DINO-WM/feature dynamics | world only | 否 | 否 | N/A | N/A | 最低 | 中 | WM fallback |

## 3.10 最终冻结决策

本项目从 v1.6 起冻结：

```text
Primary engineering framework:
NVIDIA cosmos-framework

Primary initialization checkpoint:
Cosmos3-Edge-Policy-DROID (4B)

Reference foundation:
Cosmos3-Edge (4B)

Official action-contract reference:
Cosmos3-Nano DROID/LIBERO SFT recipes

Fallback 1:
Cosmos Policy Predict2-2B

Fallback 2:
Stable VLA + modular latent/feature WM
```

理由不是“Cosmos3 最新”，而是它最直接满足 PSM-WMA 的结构要求：**World、Action、Reasoner 与多 embodiment 已经在同一开源框架中，PSM 可以被收敛成一个新的 persistent condition，而不是重新研究 Memory→Backbone / Memory→Action Head / Memory→World Head 的组合。**

## 3.11 Cosmos3 的任务路由机制与 PSM 的直接关系

Cosmos3 不是根据输入内容自动猜“该输出什么”。`SequencePlan` 明确声明：
- 某个 modality 是否存在：`has_vision / has_action / has_sound`；
- 某 modality 哪些 frame/step 是 clean condition；
- 哪些是 noised target，由 `mse_loss_indexes / noisy_frame_indexes` 解码。

因此：

```text
Policy:
Current Vision = clean
Future Vision  = noisy
Action         = noisy

Forward Dynamics:
Current Vision = clean
Action         = clean
Future Vision  = noisy

Inverse Dynamics:
Vision         = clean
Action         = noisy
```

缺失 modality 就不进入 PackedSequence；不是所有输出 head 每次都产生有效结果。

这直接给当前 Memory 第一版设计结论：

> **Temporal Local Memory 与 Spatial Global Memory 分别作为始终 clean、无 diffusion target 的 optional conditioning modalities；SequencePlan 同时负责 Memory presence 与本次 Future Vision / Action target 路由。**

## 3.12 Reasoner 与 Generator 的冻结关系

同一 Cosmos3 checkpoint 内：
- **Reasoner pathway**：autoregressive text，负责低频 task/subgoal/verifier；
- **Generator pathway**：flow-matching continuous generation，负责高频 Future World + Action。

当前官方实现不是一次 forward 同时输出 reasoning text 和 action。因此 PSM-WMA 首期采用：

```text
PSM summary + Observation + Goal
          ↓
Cosmos3 Reasoner（事件级）
          ↓
structured subgoal / verifier result
          ↓
PSM continuous condition + Observation + subgoal
          ↓
Cosmos3 Generator（控制级）
          ↓
Future World + Action
```

不在首期研究 joint text/action sampler，也不把长 CoT 设为控制依赖。

# 第四章 Spatial Observation：RGB、Depth、Geometry 与空间能力边界

## 4.0 当前结论

Depth 不是 Temporal Local baseline 的硬依赖；但 Spatial Global 若选择 geometry-aware store，则 oVDA/simulator depth 是条件数据源。默认先保留 RGB semantic + pose 路线可独立运行。

需要 learned depth 时，当前统一采用：

> **oVDA = 唯一 learned-depth provider**

不再同时维护 VDA-S 与 oVDA 两套正式 pipeline。

## 4.1 RGB-only baseline

RGB-only 用于回答：
- 强 backbone 是否已有足够隐式几何；
- depth 是否真带来 downstream 收益；
- Memory 增益是否被 depth 变量混淆。

因此 E-001–E-013 不因为 oVDA 未运行而阻断。

## 4.2 VDA 的位置

Video Depth Anything（VDA）是 oVDA 的基础来源之一。[7]

当前不把 VDA-S 放入主 Build/Reuse 路线。只有未来怀疑 oVDA causal context 形成 accuracy ceiling、需要 full-context/offline upper bound 时，才把 VDA-S 临时恢复为 diagnostic comparator。

## 4.3 oVDA：统一 offline / online learned depth

oVDA 通过缓存 latent features 与训练时 masking，把 VDA 改造成 causal online video depth。[8]

官方项目/论文报告：
- A100 42 FPS；
- Jetson 20 FPS；
- c8 / c16 两种 temporal cache 版本；
- 2026-03-09 已发布官方代码和权重。[8]

官方仓库支持视频推理，`run.py --lazy_forward` 可对排序图像目录逐帧 forward。[8]

因此 PSM-WMA 采用同一模型覆盖：

### Offline dataset preprocessing
```text
episode RGB_1 ... RGB_T
按真实时间顺序运行 oVDA
→ Depth_1 ... Depth_T
→ depth sidecar/cache
```

### Online inference
```text
previous oVDA latent cache
+
current RGB_t
→ Depth_t
```

这样 train / inference 使用同一 causal temporal semantics，避免“训练由 full-context VDA 生成、在线由 oVDA 生成”的额外 depth-distribution mismatch。

## 4.4 BEHAVIOR / Simulator Depth

若 BEHAVIOR / OmniGibson 等仿真环境直接提供可靠 depth，机制实验可以使用 simulator depth，以隔离 Memory 机制与单目深度误差。

需要 learned monocular depth / sim-to-real robustness 时再切 oVDA。

统一 depth source：
```text
none | ovda | simulator
```

## 4.5 许可证

oVDA 官方仓库采用 mixed licensing：VDA-derived 部分与其来源许可证一致，其余主要组件使用 NC-SA-UHDV1.0，商业使用需书面许可。[8]

当前是研究项目，因此：
- 许可证继续登记；
- 不把商业产品化许可作为技术主选型第一判据；
- 若未来进入产品化，再单独建立许可 Gate。

## 4.6 Depth map vs feature

v0 优先缓存 depth map，便于 debug、probe，并避免绑定 oVDA 中间层接口。只有 depth 已证明有价值、但带宽/表示成为瓶颈时，才研究 intermediate feature。

## 4.7 StreamVGGT / VGGT

StreamVGGT 仍是强 geometry control，但不进入首版 Local/Global critical path。只有 RGB/oVDA + pose 的 Global store 在 correspondence/geometry 上成为瓶颈时才触发。[9][10]

## 4.8 D4RT / RetrieveVGGT

D4RT 的 query-based 4D readout、RetrieveVGGT 的 pose-aware fixed-budget retrieval 继续作为未来 BEHAVIOR Regional PSM 技术储备。[11][12]

## 4.9 最终路线

当前：
```text
RGB / existing latent
→ Temporal Local + Spatial Global Memory
```

条件增强：
```text
RGB + oVDA depth
→ Spatial Observation Adapter
```

BEHAVIOR mechanism：
```text
RGB + simulator depth
```

原则：
- depth 是 observation cue，不是 Memory body；
- learned depth 统一 oVDA；
- 当前不为 PSM 从零做 3D reconstruction；
- Q1 失败后才升级 geometry complexity。

# 第五章 Local Persistent Spatial Memory

## 5.1 Local PSM 的能力

Local PSM 面向当前房间/操作区的分钟级状态，需要：
- 固定/受控容量；
- 在线 recursive update；
- out-of-view retention；
- 新状态覆盖旧状态；
- task/recent query；
- 向 future/world 与 action 提供 readout；
- 可关闭退化回 baseline。

## 5.2 四类候选表示

### A. Sliding history / frame buffer
工程稳，但不是真正 state compression，成本随历史增长或必须截断。

### B. Keyframe / event memory
EventVLA、KEMO、HALO 说明稀疏 keyframe 有效，但 writer 本身变成新变量。

### C. Recurrent latent tokens
固定 K 个 memory tokens，持续 `Update(M_{t-1}, O_t)`。容量固定、端到端、最符合隐式 PSM 定义；风险是信息混叠和模型绕过。

### D. Object / slot state
OA-WAM 等提供 address/content 分离，可解释，但依赖 object/slot tracking，对 background geometry 与跨区域 state 不完整。

## 5.3 主路线为什么仍是 recurrent latent

推荐的**结构族**是：
> **fixed-budget recurrent latent/query memory**

冻结审查后，不再把“gated update + query/read cross-attention”写成文献已经证明的唯一正确机制，而把它们降级为详细设计的默认实现候选。

直接证据比 v1.0 更强：
- μVLA 只增加少量 learnable memory tokens，并跨时间携带、通过 attention 更新；论文正文直接报告 MIKASA-Robo 五个训练任务平均 SR 从 0.42 提升到 0.84，最强 recurrent variant 在 LIBERO 达到 96.2%，同时指出需要不同 memory structure 的任务仍接近 baseline。[62]
- ReMem-VLA 进一步使用 frame-level + chunk-level recurrent queries，并指出简单 recurrence/短 TBPTT 对真正长程依赖可能不足。[63]

这两项证据刚好支持本项目的分层判断：
- **Local PSM**：recurrent latent/query memory 合理；
- **Global PSM**：不能只是把同一个 recurrent state 做得更大，仍需要 spatial address、sparse storage 与 retrieval。

理由：
1. 与 Cosmos/WM4A hidden representation 最自然；
2. 不引入 detector/symbolic schema；
3. 可由 action/future loss 端到端塑造；
4. 能直接检验“纯隐式 Local state 是否足够”；
5. 能力边界清楚，失败后可升级 dual-scale recurrence / Hybrid PSM。

## 5.4 Update 与 Read

Update 优先：
- gated cross-attention / gated residual update；
- 只有容量或表达不足才升级 recurrent Transformer；
- Mamba/state-space 不作为首期架构切换。

Read 优先：
- task/recent-conditioned compact readout；
- gated cross-attention 注入 World/Action；
- 不把完整 M_local 无筛选拼进所有 token。

## 5.5 Short-term 与 Local PSM 并存

- recent raw/latent frames：细粒度 motion、即时变化；
- Local PSM：超出 recent window 的状态。

避免一个 recurrent memory 同时承担短期 motion 和长期 state。

## 5.6 基础对照

详细设计应保留：
- current/recent-only；
- longer raw history；
- keyframe memory；
- recurrent latent PSM；
- Hybrid/object-centric fallback（条件触发）。

**Local PSM 收敛**：fixed latent tokens + gated update + compact readout。learned writer、symbolic table、scene graph、point map 均不默认进入第一版。



---

# 第六章 当前记忆拓扑：Temporal Local + Spatial Global 两个独立可选模态

## 6.1 Temporal Local Memory：learned temporal state

Local 不再定义成单一视觉 latent 的递归缓存，而是最近一段时间多源状态经过**时间对齐 + 学习式压缩**得到的 task-agnostic temporal world state。候选证据包括：

```text
main RGB / visual feature
+ depth feature（与 RGB 同时间戳）
+ camera pose
+ robot state / proprio
+ optional wrist RGB feature
+ executed action interval
→ Temporal Alignment
→ Local Memory Encoder / recurrent compression
→ K_local latent tokens
```

关键边界：
- RGB、depth、pose、state、wrist 必须先在统一时间轴对齐，再做 temporal compression；
- write/read/compression 参数应被 native future/action loss 优化；
- 跨长 episode 的 recurrent state 不默认做全程 BPTT。μVLA 显式比较 cross-step gradient 与 detached EMA；ReMem-VLA / μVLA 都说明 recurrence 需要受控训练边界，因此项目把 detached state / truncated BPTT / stable update 作为待 Runtime 冻结项，而不是先写死某一种公式；
- Local 重点回答“刚才发生了什么、当前状态如何演化到这里”。

LaMem-VLA 将短/长期历史重构成 latent memory tokens 并与当前多模态 token 组成同一连续 embedding sequence，支持“memory native latent”方向；ReMem-VLA 与 μVLA 为 recurrent learned memory 提供直接证据。[69][70][71]

RoboTTT 进一步提供了更强的长上下文工程证据：它把一个小模型的 **fast weights** 作为 recurrent state，在每个输入 token 到来时用 TTT-KVB 自监督 key-value binding loss 做在线梯度更新；状态大小不随历史长度线性增长。训练时使用 sequence action forcing 与 TBPTT，在 segment 边界携带但 detach fast-weight state，从而形成“长状态链、短梯度链”。官方报告训练到 8K timesteps（约 5 分钟 @ 30 Hz），并在真实机器人上完成 5 分钟、10-stage assembly。[76]

对 PSM-WMA 的直接启发不是“照搬 RoboTTT 主干改造”，而是把 Temporal Local 的候选实现收敛为两类：

```text
A. Recurrent Latent / Fixed-token Baseline
aligned multimodal evidence
→ recurrent query/gated compressor
→ K_local tokens
→ Local modality

B. TTT Fast-weight Local (Primary Candidate)
aligned multimodal evidence
→ per-step summary tokens
→ TTT fast-weight recurrent state W_t
→ Local readout
→ K_local tokens
→ Local modality
```

B 当前优先级更高，但只有在 R06 Edge-LIBERO baseline PASS 后，比较 future/action sensitivity、训练稳定性、fast-weight reset/并行环境隔离、FSDP/episode batching、显存与延迟，才允许冻结。首期不把 TTT layer 直接插入 Cosmos3 28 层主干，以避免把 Local 研究变量与 backbone surgery 绑定。

## 6.2 Spatial Global Memory：explicit / semi-explicit persistent spatial state

Global 的核心不是“更大的 Local recurrent latent”，而是把整个 episode 的历史观测按空间关系重新组织，使系统能够回答：**什么时候、在哪里、从什么视角观察到了什么相关内容。**

候选 raw store：

```text
RGB semantic / visual feature
+ oVDA depth / local geometry representation
+ camera pose / trajectory
+ view direction
+ timestamp
+ confidence / freshness
→ spatial lifting / organization / fusion
→ persistent spatial store
```

推理时不把整张 map 全部塞入主干，而是：

```text
current pose + current visual + planner/task query
→ spatial/semantic/temporal retrieval
→ Top-K key patches / key views / spatial features
→ Global Spatial Encoder / Compressor
→ K_global tokens
```

SERF 证明从时空 feature map 提取 local/global map tokens 能进入 VLA；VistaVLA 说明仅低层 depth/point cloud 不足，geometry 与 semantic grounding 应结合，并用 query/compression 把密集 3D 表征压成 compact tokens；MosaicMem 说明 explicit 3D 定位与 model-native conditioning 可形成 hybrid spatial memory。[20][72][73]

因此 oVDA 在 Global 路线中首先是 geometry/depth source；是否直接复用 oVDA 中间 feature、是否加入独立 RGB semantic feature、底层 store 采用 patch/point/Gaussian/key-view hybrid，继续作为专项实现变量，不在本版伪冻结。

## 6.3 Local 与 Global 必须独立构建、独立适配

```text
Temporal Local Memory  → local_memory2llm  → Local modality embedding  ┐
                                                                    ├→ shared World-Action backbone
Spatial Global Memory → global_spatial2llm → Global modality embedding ┘
```

二者不共用一个 `memory2llm`：Local adapter 需要建模 time order / sensor alignment / robot dynamics；Global adapter 需要建模 spatial address / camera pose / view direction / timestamp / retrieval provenance。

## 6.4 Optional-modality / Planner interface

Local / Global 与 Vision / Action 等模态一样允许存在或缺失。训练阶段可人工构造 presence、modality dropout 与 matched controls；Agent 阶段由 Planner / Reasoner 输出：

```text
MemoryRequest
├─ local: enabled, horizon/budget/query
└─ global: enabled, semantic_query, spatial_region, temporal_range, top_k
```

Planner 只决定“要不要、取什么、取多少”，Memory 系统负责 store/update/retrieval/tokenization，World-Action 模型负责消费后预测 future/action。

## 6.5 Goal Memory 的新位置

Goal Memory 仍可用于 goal/subgoal progress，但它不再承担 Global Spatial Memory 的职责，也不阻断 Local→Global 主线。首期优先让 goal/task 作为 Global retrieval query / Planner routing 条件；若任务进度仍需要独立 persistent state，再单独做 Goal Memory Target。

## 6.6 Regional/Place hierarchy 仍是 BEHAVIOR-only

Spatial Global Memory 当前可以是单一全局 store；只有多房间任务出现容量、aliasing、跨区域检索冲突后，才增加 Region/Place hierarchy、分层 Writer/Reader 与 place-level stale/revisit 机制。

# 第六A章 BEHAVIOR 阶段的 Region/Place 层级化 Global 技术储备（Deferred）

> **Scope Guard**：从本章开始直到 Regional Writer/Reader 章节结束，内容只为 BEHAVIOR/多房间阶段保留，不进入当前 LIBERO/RoboCasa 的 Build/Implement/Experiment 清单。

> 本章为未来阶段参考，不属于当前 Stage 1–2 的实现冻结项。



## 6.1 为什么 Global PSM 不能只是更大的 Local PSM

多房间长期任务包含多个相似区域、大量当前无关内容、重访、状态覆盖与严格容量约束。若把全部压进单个 recurrent \(M_t\)，空间 aliasing 与不可控遗忘会随环境规模快速加重。

因此 Global PSM 应被定义为：

> **多个 sparse region/place memory entries，而不是一个巨大 recurrent state。**

## 6.2 候选表示对比

### A. Explicit point cloud / voxel / scene graph

代表：DREAM、HoloAgent、传统 3D semantic map。

优点：
- address 清晰；
- debugging 简单；
- stale/conflict 可显式处理；
- Agent 易消费。

缺点：
- 重建/SLAM 工程重；
- semantic schema 容易变成另一个项目；
- learned WAM 还需重新编码为 tokens。

**结论**：fallback / 对照，不是默认 memory content。

### B. 4D surfel-indexed memory

Mem-World 把“何时/何地看到什么”绑定到动态 surface element，再按 future action 检索历史观测。[23]

价值：
- geometry/action conditioned retrieval 很强；
- 为“先结构筛选，再把相关历史交给 world model”提供直接证据。

限制：
- 更接近可检索历史观测索引，而不是直接给 online policy 的统一 latent spatial state。

### C. Latent 3D cache

Mirage 将 diffusion latent 通过 depth-guided back-projection 写入 persistent 3D cache，并在新 view 下直接 query/warp latent；官方代码 MIT。[26]

优点：
- content 与 world backbone latent 对齐；
- 避免 RGB render→VAE encode 往返；
- 最接近 PSM-WMA 的 implicit content。

风险：
- depth/pose 误差会污染 cache；
- dynamic object 处理更难；
- 原目标主要是视频 world consistency，不是 action。

**结论**：Global latent content 的第一参考。

### D. Hybrid spatial patches

MosaicMem 将可定位 patch lift 到 3D，以 geometry 保定位姿一致性，再利用生成模型补动态内容。[27]

优点：
- 比纯 implicit 更可定位；
- 比完整 point cloud 更贴近 backbone token。

**结论**：纯 latent Global PSM 失败后的高优先级 fallback。

### E. Neural point feature map

SERF 在线维护 environment + robot neural points，从多个 reference frame / scale 提取 local/global map tokens 给 VLA。[28]

它对本项目特别重要，因为已经证明：
- feature map 可 online update；
- local/global spatial tokens 能直接 condition action；
- BEHAVIOR-1K 上改善 long-horizon reasoning、direct trajectory 和 failure recovery。

**结论**：Global PSM action-side 强对照。

### F. Dynamic spatio-semantic voxel memory

DREAM 在真实 mobile manipulation 中做 bounded online memory、pose-graph correction、redundancy pruning 和 target reacquisition。[29]

**结论**：stale/pose correction 与工程鲁棒性参考；不作为 latent 主表示。

## 6.3 推荐 Global PSM 结构

为兼顾上游“latent content 优先”与大空间可控寻址，本报告推荐一个**本项目综合式自研组合**：

> **latent content + semi-explicit spatial address**

它不是某篇论文已经验证完毕的标准架构：Mirage 提供 latent spatial content 证据，OA-WAM 提供 persistent address / dynamic content 分离证据，SERF/HoloAgent 提供 local/global spatial hierarchy 与 action/Agent 使用证据。详细设计必须把这一组合当成可证伪假设，而不是既定事实。

具体只冻结结构原则：
- content：latent chunk / compact spatial tokens；
- key：place / region / pose / frustum / coverage metadata；
- optional metadata：timestamp、confidence、visibility、version/state-change cue；
- 不预设 object table；
- 不要求完整 mesh/3DGS。

这不是“放弃隐式 PSM”。**address 可以半显式，content 仍然是 learned latent。**

## 6.4 Local→Global Consolidation

Consolidation 需要回答“什么时候把 Local PSM 固化为 Global entry”。

候选触发：
- 离开 region；
- coverage/pose 显著改变；
- Local memory 接近容量上限；
- task/subtask boundary；
- 状态长时间稳定；
- 环境状态真实变化后生成新版本。

本报告只冻结“需要 consolidation”和候选触发集合，不冻结阈值、region segmentation 和版本结构。

## 6.5 重访流程

原则流程：

1. current geometry/pose 推断候选 region；
2. Global Reader 返回 Top-K entries；
3. task/recent query re-rank；
4. selected Global entry 恢复/增强 Local PSM；
5. 新 observation 与旧 memory reconcile；
6. stale 内容 update / invalidate / 降权。

## 6.6 Global PSM 收敛

- **主 content**：latent；
- **主 address**：semi-explicit spatial key；
- **主参考**：Mirage + Mem-World + SERF；
- **fallback**：MosaicMem / DREAM-like explicit structure；
- **不做**：从零构建完整 SLAM/3DGS/scene graph 主系统。

---

# 第七章 Regional Global Writer / Reader 技术储备（BEHAVIOR-only，Deferred）

## 7.1 Writer 的风险

写太多：
- memory 膨胀；
- retrieval latency 增加；
- 重复内容挤占容量。

写太少：
- 错过状态变化；
- revisit 时没有有效证据。

最危险的是**过早 task-aware write**：当前任务认为“不重要”的信息，后续任务可能需要。

如果未来进入 BEHAVIOR 多区域阶段，v3.2.2 的 task-agnostic writer 起步仍是合理候选；**当前 LIBERO/RoboCasa 不实现本章 Writer/Reader。**

## 7.2 Writer V0：规则/几何

候选 cue：
- spatial novelty；
- new frustum / coverage；
- pose displacement；
- depth / appearance / latent change；
- task-agnostic state-change indicator；
- minimum interval / cooldown。

Create vs Update：
- 新空间 → create；
- 同 region + 状态变化 → update / new version；
- 高重复 → skip。

阈值全部下沉 02。

## 7.3 V1/V2 的顺序

V1 先固定 Writer，只增强 Reader。

原因：如果 memory 已经写入正确内容，但 action 无收益，优先验证“读错了”比继续改 writer 更容易归因。

只有 Reader 已证明 retrieval 有价值，才考虑：
- EventVLA-style future utility；
- KEMO-style event candidate；
- boundary-aware writer；
- learned novelty / value scorer。

## 7.4 Reader 的证据链

不同方向都趋向“先结构筛，再任务相关性”：

- Mem-World：geometry/action-guided retrieval；
- WorldKV：camera/action correspondence；
- RetrieveVGGT：pose-aware memory + query-key similarity；
- Mirage：target-view geometry query；
- HoloAgent/DREAM：spatial hierarchy / semantic retrieval；
- SOMA：instruction-conditioned contextual retrieval，说明几何正确后仍需要 task relevance。[24]

因此推荐两级 Reader：

### Stage A：Geometric / Structural Prefilter
候选依据：
- region/place；
- camera pose/frustum；
- EE neighborhood；
- potential action trajectory；
- coverage overlap。

### Stage B：Task / Recent Relevance
输入：
- instruction；
- current/recent latent；
- robot state；
- candidate memory summary。

输出：
- Top-K；
- optional confidence / relevance。

## 7.5 为什么不一开始全 learned retrieval

纯 learned retrieval 初期风险：
- training signal 稀疏；
- shortcut；
- pose/relevance 错误难区分；
- 多一个核心实验变量。

企业项目优先：
> **V0 geometry-first prefilter → V1 task/recent-aware rerank**

这里的 `geometry-first` 只冻结为**第一阶段候选集构造**，不主张几何相似度就是最终相关性函数。

## 7.6 Readout

候选：
- cross-attention；
- query-token readout；
- pooled memory embedding；
- geometry-aligned latent warp（只适合特定 WM 分支）。

推荐：
- policy/world 尽量共享 compact memory readout；
- Global entries 不直接全量拼进 backbone。

## 7.7 Writer/Reader 决策

- **V0**：rule writer + geometry reader；
- **V1**：fixed writer + task/recent-aware reader；
- **V2**：learned/event writer，条件触发；
- 禁止一开始 writer + reader 同时学习。

---

# 第七A章 Memory Injection Topology：两个独立 Cosmos3-style optional clean modalities

## 7A.1 设计出发点

Cosmos3 原生结构将 Vision / Action / Sound 通过各自 mapper 投影到统一 hidden space，再由 `SequencePlan/PackedSequence` 决定本 sample 中哪些模态存在、哪些是 clean condition、哪些是 noised target。源码中缺失 modality 不 pack，而不是固定零占位。该抽象天然适合 Local / Global 的 optional presence。

LaMem-VLA 与 OminiControl 进一步支持“将新条件表示成 compact tokens，直接进入共享 Transformer sequence”这一范式。[69][75]

## 7A.2 Primary：Native Local / Global Memory Modality

建议新增两个 first-class condition field，而不是统一 `psm`：

```text
SequencePlan.has_local_memory
SequencePlan.has_global_memory

PackedSequence.local_memory
PackedSequence.global_memory

local_memory2llm
local_memory_modality_embed

global_spatial2llm
global_memory_modality_embed
```

第一版两者均为：
- always clean；
- no diffusion / flow timestep；
- no `mse_loss_indexes`；
- no `llm2local_memory` / `llm2global_memory` decoder；
- 通过 shared MoT 同时影响 Future Vision 与 Action；
- presence/absence 由 `SequencePlan` 明确声明。

这不是“把两个 memory token concat 后统一投影”：两类 token 的生成器、position semantics、type embedding 与 retrieval provenance 保持独立，只有进入 `D_cosmos` 后共享 backbone。

## 7A.3 Local / Global position semantics 必须分开

Local：relative temporal position、sensor/view type、可选 camera motion；重点保持 RGB-depth-pose-state-wrist 的同时间轴。  
Global：world/robot-relative position、camera pose、view direction、historical timestamp、spatial region/provenance。Metric XYZ 不直接硬塞进现有 vision H/W mRoPE，第一版可作为 content embedding / Fourier pose embedding，并通过 R07/R13 审计 attention/position。

## 7A.4 强备选：Global Map → aligned Vision Control

Cosmos3 当前 transfer 路径已支持多个 control vision item 与 target 共享 temporal positions，并通过 control→target attention 影响生成。因此 Global store 可以按当前 pose/query 重投影或组合成 camera-aligned depth/semantic reference，再作为 control-vision 条件。该路线复用更多现有 packing/attention，但需要把 Global map 转成当前视角 reference；适合作为 Global modality 的强对照/工程 fallback，而非默认替代。

## 7A.5 ControlNet-lite / zero-gated residual

原始 ControlNet 的关键经验是 frozen pretrained backbone + zero-initialized residual condition branch，可在初始时近似保持 baseline function。[74] 对 PSM 若 Native Modality 侵入 packing 过大，可采用轻量 cross-attention/residual adapter，并以 zero gate 初始化。Full ControlNet 复制大块 Generator 会增加参数、activation 与通信，不符合当前吞吐优先原则，不作为首选。

## 7A.6 KV / MemoryState

Cosmos3 内部已有 memory-aware attention/KV state，但其语义主要服务 causal cache。把 external PSM 映射成逐层 K/V 需要重新定义 position、梯度与 cache ownership，作为后续高级候选，不阻断 W4/W5。

## 7A.7 当前排序

```text
Primary:    Local/Global Native Optional Modalities
Strong Alt: Global Spatial Store → Vision Control
Fallback:   Zero-gated CrossAttn / residual adapter
Deferred:   external PSM → per-layer KV MemoryState
Avoid:      Full ControlNet branch as first implementation
```

注入 topology 在 R07/R13 做源码级 shape/attention/throughput audit；如果 Native Modality 证明工程成本不可接受，才切 Strong Alt / Fallback。

# 第八章 Memory → World / Action：Cosmos3 原生耦合、监督与归因

## 8.1 主耦合方式

v1.6 只冻结一条主路径：

```text
PSM clean condition
      ↓
shared Cosmos3 Generator
      ├─ noisy Future Vision → vision flow target
      └─ noisy Action        → action flow target
```

PSM 不拥有独立 FutureHead；World prediction 与 Action 都使用 Cosmos3 原生 decoder/flow objective。

## 8.2 主监督

主损失复用 Cosmos3 原生目标，Local/Global 本身第一版不增加 reconstruction target：

```text
L = λ_vision L_vision_flow + λ_action L_action_flow + optional L_text
```

第一版不增加 PSM reconstruction loss。Memory 是否有效由 downstream world/action 与 intervention 证明，而不是靠额外 memory probe loss 自证。

## 8.3 Action-sensitive future

Policy / Forward Dynamics 使用相同 SequencePlan/condition机制，使 future target 与 action 时间覆盖显式对齐。禁止用不依赖 executed/candidate action 的“未来先验”冒充 action-conditioned World Model。

## 8.4 推理期是否必须 decode future video

不要求每个 control step 都把 future video decode 成 RGB。允许只完成 latent/hidden denoising或在 serving 中关闭昂贵展示分支，但必须保证 Action 是从同一 PSM-conditioned shared generation state 得到，不能退化为与 World pathway 完全脱钩的普通 VLA。

## 8.5 Memory Intervention

必须分别支持：
- Local Zero / Shuffle / Stale / Truncated；
- Global Zero / Shuffle / Wrong-view / Stale / Top-K truncation；
- Local-only / Global-only / Both / Neither；
- `modality absent` vs `present+zero content`；
- future/action output sensitivity；
- closed-loop SR / step / retry / revisit sensitivity。

所有 content intervention 保持 token 数、shape、action domain、target plan 不变，只改变 Memory content。

## 8.6 防止模型绕过 Memory

按顺序排查：
1. memory-dependent task 是否真的需要历史；
2. PSM condition 是否进入正确 packed indexes；
3. attention visibility 是否允许 noisy Action/Vision 读取 PSM；
4. PSM readout/gate 是否有梯度；
5. Zero/Shuffle 是否改变 Action/Future；
6. 再决定是否需要更深 injection。

不允许因一次无效就直接增加 Region/Agent/RL。

# 第九章 数据集与 Benchmark

## 9.1 Execution 与 Diagnostic 必须分开

### Execution Track
回答“机器人是否做得更好”：
- LIBERO / LIBERO-Mem；
- RoboCasa365；
- BEHAVIOR-1K subset。

### Diagnostic Track
回答“哪层坏了”：
- Spatial Probe；
- RoboMME；
- RMBench / RoboMemArena；
- SpaMEM；
- LMEE / 3DMem。

Diagnostic 不替代 SR/task progress。

## 9.2 LIBERO / LIBERO-Mem

普通 LIBERO：
- 工程成熟；
- 用户已有 stable policy/weights；
- 适合 regression；
- 但很多任务并不强依赖长期 memory。

LIBERO-Mem：
- 专门形成 non-Markov / memory-dependent manipulation；
- 更适合 Local Memory stress test。

**决策**：
LIBERO = baseline/regression；LIBERO-Mem = memory stress。

## 9.3 RoboMME：Stage-1 首选标准诊断

RoboMME 是 ICML 2026 Oral，官方有 16 tasks：
- temporal；
- spatial/permanence；
- object/reference；
- procedural/imitation。

代码 Apache-2.0，并系统比较 14 种 memory-augmented policy variants。[42]

**定位**：Local PSM 主 diagnostic benchmark。

## 9.4 RMBench

RMBench 提供 memory-dependent manipulation，并被多篇 2026 Memory/WAM 工作采用。

**定位**：cross-paper comparison / secondary diagnostic。

## 9.5 RoboMemArena：独立调研新增的长程 stress test

RoboMemArena：
- 26 tasks；
- 平均轨迹 >1000 steps；
- full trajectory HDF5；
- subtask/keyframe annotations；
- LIBERO-compatible evaluation；
- TSR/CSR；
- paired real-world memory tasks。[44]

它比 RoboMME 更长更复杂，但成本也更高。

**建议**：
- 不进首批硬预算；
- RoboMME 成立后再做长跨度 stress；
- keyframe annotation 可用于 learned writer 后续研究。

## 9.6 SpaMEM

SpaMEM 主要检查 dynamic spatial belief maintenance / perception-memory integration。

**定位**：
- Q1/Q2 diagnostic；
- 验证 Build/Update/Maintain；
- 不作为主策略 benchmark。

## 9.7 RoboCasa365：中期主环境

官方 RoboCasa365：
- 365 tasks；
- 2,500+ kitchen scenes；
- 3,200+ 3D objects；
- 600+ h human demos；
- 1,600+ h synthetic demos；
- code MIT，assets/datasets CC BY 4.0；
- RoboCasa 官网 Updates 明确记录：2026-07-07 target composite task datasets 新增 per-frame subtask index、atomic-skill name、stage（pick/place/navigate）和 natural-language instruction。[46]

这些标注特别适合：
- Local PSM + WAM；
- stage-aware analysis；
- Agent thin slice；
- keyframe/event diagnostics。

**决策**：RoboCasa365 是 PSM+WAM 的第一主环境。

## 9.8 LMEE / 3DMem

LMEE：
- long-term exploration / active memory query；
- 偏 exploration/nav/QA。

3DMem：
- long-term spatial-temporal memory；
- working↔episodic / multi-room 参考。

**边界**：只做 Global retrieval diagnostic，不把项目变成导航/QA。

## 9.9 BEHAVIOR-1K

官方 BEHAVIOR：
- 1,000 full-length household activities；
- 50 interactive scenes；
- 2026 Challenge：100 full-length tasks / 7 scenes；
- 同时考验 reasoning、navigation、manipulation。[49]

**决策**：
- 首期 small subset；
- 使用成熟 navigation stack；
- 测 Global+Local PSM + WAM + Agent；
- 不追 full leaderboard。

## 9.10 数据字段最低要求

进入 02 前 profile：
- RGB views；
- timestamp / Hz；
- camera intrinsics/extrinsics 或可恢复 pose；
- robot state/proprio；
- action；
- language；
- episode boundary；
- optional depth；
- optional subtask/stage；
- object/state GT 只做 diagnostic。

完整 episode 是采样容器，不等于一次性输入完整 episode。

---

# 第十章 Agent：优先复用 Cosmos3 Reasoner，而不是外挂第二个大模型

## 10.1 Agent 职责

Agent 只承担低频：
- task / subgoal selection；
- completion verification；
- failure classification；
- retry / re-observe；
- 必要时 semantic re-grounding。

不承担高频 contact control，也不替代 Local/Goal persistent state。

## 10.2 Primary：Cosmos3 Reasoner

`Cosmos3-Edge-Policy-DROID` 同一 checkpoint 保留 Reasoner 与 Generator。Reasoner 是 autoregressive text pathway；Generator 是 flow-matching world/action pathway。首期采用事件触发：episode start、subgoal complete、failure、unexpected state、memory conflict 时运行 Reasoner。

## 10.3 Reasoner→Generator 数据合同

Reasoner 不输出长 CoT 作为硬依赖，而输出紧凑结构化结果，例如：

```text
subgoal: open_drawer
target: drawer_handle
status: need_manipulation
```

Generator 再结合 current observation + continuous PSM condition 生成 Action。这样 Reasoning 真正进入 Action 因果路径，但不会把每个控制 step 的 latency 变成 LLM latency。

## 10.4 Memory 与 Agent

- Local Memory：task-agnostic world state；
- Goal Memory：goal/subgoal-related history/progress；
- ReasonerMemoryReadout：从上述状态生成 compact context；
- Experience Memory：若后续需要，保存 skill success/failure trace，不能和 PSM 混成一份。

## 10.5 External Agent fallback

只有 Cosmos3 Reasoner 在目标 task/subgoal/verifier 上明显不足时，才接外部 VLM/LLM Agent。它是 fallback，不是首期 Must-have。

# 第十一章 Continual Evolution 与 Proactive Agent

## 11.1 只调研进入条件

Continual / Proactive 决定系统未来能否“越用越强”，但在 PSM 未成立时引入 RL/self-improvement 会破坏归因。

因此首期只冻结 entry gate。

## 11.2 Continual Evolution 候选

参考：
- RECAP / π*0.6；
- LWD；
- RISE[54]；
- WoVR[55]；
- FPO[56]；
- Batch Online RL；
- HiRoC；
- SARL。

潜在 PSM 结合：
- `V(o, M, goal)` memory-conditioned critic；
- PSM-conditioned imagined rollout；
- stale/error-aware replay；
- WM-policy co-evolution；
- failure cluster → Agent/skill update。

进入条件：
- base policy 非零且稳定；
- PSM intervention 有效；
- World Model reliability 可测；
- reward/reset/replay infrastructure 稳定。

## 11.3 Proactive Agent

WorldLines 等说明长期 world/user/task state 可让 Agent 从“执行给定任务”走向主动 task discovery。[51]

后期可研究：
`system/user principles + persistent world state → need/goal discovery → task queue`

但首期不做。



---

# 第十二章 工程成熟度、代码、许可证与可复用性

## 12.1 主工程母体：NVIDIA cosmos-framework

主工程直接基于 `cosmos-framework`，原因是当前需要的能力已经在同一代码体系内：
- Cosmos3 Generator / Reasoner；
- Vision/Action multimodal packing；
- `SequencePlan` / `PackedSequence`；
- ActionProcessor / multi-domain action；
- flow-matching training；
- DROID/LIBERO Action SFT recipes（当前公开 exact recipe 为 Nano）；
- checkpoint conversion/export；
- policy/inference server。

因此 PSM-WMA 不再把 Cosmos3 包装进 StarVLA，也不再维护一套独立 LayerwiseFM action path。

## 12.2 StarVLA 的保留价值

StarVLA 降级为：
- 已有 LIBERO/RoboCasa baseline 结果参考；
- dataset/eval 语义核对参考；
- 若 Cosmos runtime Gate 失败时的 stable-policy fallback。

不再作为 PSM-WMA 主代码母体。

## 12.3 Edge-Policy-DROID 的复现边界

公开 `cosmos-framework` 已有完整 DROID Action SFT stack，但当前仓库显式注册的一键 recipe 主要是 Nano。项目不需要先复现 Edge→DROID；直接从官方发布 `Cosmos3-Edge-Policy-DROID` warm start，做 LIBERO/RoboCasa embodiment adaptation。

## 12.4 许可证原则（研究阶段）

- 记录 Cosmos3/OpenMDW、oVDA mixed license、benchmark/data license；
- 当前研究阶段先做技术可行性；
- 若进入产品化，再单独建立 commercial-license Gate。

# 第十三章 Build / Reuse / Adapt / Compare 决策矩阵

| 能力 | 决策 | 说明 |
|---|---|---|
| Cosmos3 Generator / Reasoner | **Reuse** | 直接基于 cosmos-framework |
| Edge-Policy-DROID checkpoint | **Reuse** | robot world-action warm start |
| LIBERO Nano SFT data/action contract | **Reuse/Adapt** | 将 Nano recipe 迁到 Edge-Policy-DROID |
| LIBERO action domain | **Adapt** | 10D frame-wise-relative rot6d |
| RoboCasa action domain | **Build/Adapt** | 保留数据/controller 原始语义，不硬转 DROID 8D |
| BEHAVIOR action domain | **Build later** | 进入 BEHAVIOR 后按 robot/controller 定义 |
| Temporal Local Memory | **Build** | 项目核心自研：多源时间对齐 + learned compression/update/read |
| Spatial Global Memory | **Build** | 项目核心自研：persistent spatial store + retrieval/compression |
| Local Memory optional modality adapter | **Build** | 独立 `local_memory2llm` / position/type semantics |
| Global Memory optional modality adapter | **Build** | 独立 `global_spatial2llm` / spatial provenance semantics |
| Goal Memory | **Build / Target** | 后续 goal-progress 扩展，不阻断 Local/Global |
| ReasonerMemoryReadout | **Build** | compact readout，不复制 Memory |
| oVDA depth | **Reuse** | conditional spatial cue |
| StarVLA/LayerwiseFM | **Compare/Fallback** | 不再是主工程 |
| Cosmos Policy Predict2-2B | **Fallback** | 小模型且有 LIBERO 执行证据 |
| DINO-WM | **Fallback/Compare** | feature future diagnostic |
| Region/Place hierarchical Global | **Deferred** | BEHAVIOR-only；不等于当前 Spatial Global Memory |
| External Agent LLM | **Fallback** | Cosmos Reasoner 不够用才启用 |

# 第十四章 推荐总体技术路线

## 14.1 不采用“大爆炸集成”

执行顺序固定：Foundation → Temporal Local → Spatial Global → RoboCasa → Planner/Agent。禁止同时做 Edge adaptation + Local + Global + Goal + Agent + BEHAVIOR。

## 14.2 Stage 0：Cosmos3 原生能力与 LIBERO baseline

R01–R06：Reasoner/Policy/World smoke、Action contract、LIBERO forward/loss、tiny-overfit、closed-loop non-zero baseline。失败不归因 Memory。

## 14.3 Stage 1：Temporal Local Memory

```text
aligned RGB/depth/pose/state/wrist/executed-action history
→ learned Local compression/update/read
→ Local clean optional modality
→ shared Cosmos3 Generator
→ Future + Action
```

普通 LIBERO 做 no-regression，memory-dependent task 做 attribution。

## 14.4 Stage 2：Spatial Global Memory

```text
historical semantic/visual + depth/geometry + pose/trajectory/time
→ persistent spatial store
→ current-query Top-K retrieval
→ Global clean optional modality
→ shared Cosmos3 Generator
```

先 Global-only，再 Local+Global。Region/Place 不在本阶段。

## 14.5 Stage 3：RoboCasa365 embodiment transfer

先无 Memory baseline，再 +Local、+Global、+Both；action/domain adaptation 与 Memory 分开。

## 14.6 Stage 4：Planner / Reasoner routing

Planner 通过 `MemoryRequest` 动态决定 Local/Global presence/query/budget。Goal Memory only if task-progress 缺口明确。

## 14.7 Stage 5：Agent thin slice

subgoal → MemoryRequest → policy → verifier → retry/re-observe；External Agent 仅 fallback。

## 14.8 Stage 6：BEHAVIOR small subset + Region/Place Gate

只有单一 Spatial Global store 在多房间出现容量/aliasing/跨区域检索冲突时才层级化。

## 14.9 12 周节奏

```text
W1–W3  Foundation / Edge-LIBERO baseline (R01–R06)
W4     Temporal Local modality + learned compression
W5     Local formal attribution
W6     Spatial Global store/retrieval + Global modality
W7     Local + Global complementarity / intervention
W8–W9 RoboCasa transfer
W10    Planner dynamic routing / optional Goal
W11    Cosmos Reasoner Agent thin slice
W12    rerun / demo / documentation
```

# 第十五章 风险、触发条件与降级路径

## R1 Edge-Policy-DROID → LIBERO adaptation 失败
先检查 action/state/camera/normalization/SequencePlan，不允许直接归因模型能力。tiny-overfit 都失败则停止主线适配，切 Cosmos Policy Predict2-2B；仍失败再回 stable VLA fallback。

## R2 Cosmos3 规模/吞吐不满足单人迭代
优先冻结大部分 shared weights、训练 action domain/PSM adapter；必要时降低分辨率/序列长度。仍不可控则切 2B fallback。

## R3 PSM condition 被 Generator 绕过
使用 memory-dependent task + Zero/Shuffle/Stale + output sensitivity；两轮仍无效才进入更深 injection，不先加 Global/Agent。

## R4 Reasoner 能力保留但 task-level agent 不够用
先用结构化 prompt/readout和事件触发；仍不足才外挂外部 VLM/LLM Agent。

## R5 Depth/Pose 噪声污染 Spatial PSM
RGB-only 为默认；oVDA conditional；BEHAVIOR simulator depth 用于机制隔离。

## R6 RoboCasa/BEHAVIOR embodiment action 复杂
不强行映射为 DROID 8D，建立独立 domain + ActionProcessor；先 schema/tiny-overfit 再闭环。

## R7 World 指标提升但 Action 不提升
只把同时进入 shared generator/action path 且能通过 closed-loop/intervention 证明价值的结果算成功。

## R8 Agent 工程吞掉算法时间
Reasoner 事件级、Agent thin slice 后置；Stage1/2 不达标则不进入 Agent/BEHAVIOR。

## R9 Benchmark 太多
执行主线只保留 LIBERO→RoboCasa→BEHAVIOR small；其他 benchmark 仅 diagnostic。

# 第十六章 面向详细设计的冻结输入

## 16.1 进入 `02_detailed_design.md` 的硬结论

1. 主工程母体：`cosmos-framework`；
2. 主初始化 checkpoint：`Cosmos3-Edge-Policy-DROID` 4B；
3. `Cosmos3-Edge` 作为 foundation/reference；
4. `Cosmos3-Nano` DROID/LIBERO recipe 作为官方 Action SFT contract 参考；
5. Action 是原生 modality，使用 `domain_id / raw_action_dim / DomainAwareLinear`；
6. Temporal Local 与 Spatial Global 是两个独立 **clean optional conditioning modalities**，不设自身 flow target；
7. Local 负责多源时间对齐后的 learned temporal state；Global 负责 persistent spatial store + retrieval/compression；
8. World/Action supervision 使用 Cosmos3 原生 Vision/Action flow loss；
9. Reasoner 作为低频 Planner/Agent primary，Generator 作为高频 World-Action primary；
10. Planner 通过 `MemoryRequest` 决定 Local/Global presence、query 与 token budget；
11. Goal Memory only if task-progress gap 明确；Region/Place hierarchy 只在 BEHAVIOR 后重新设计；
12. learned depth 统一 oVDA；Local baseline 可 RGB-only，Global geometry path 按 R12/R13 选择；
13. External Agent、StarVLA/LayerwiseFM、Predict2-2B 都是 fallback/reference，不是主线。

## 16.2 仍由 G0 / 详细设计决定

- Edge-Policy-DROID 本地推理 VRAM/latency；
- Edge→LIBERO 最小 config diff；
- `K_local/K_global`、两类独立 adapter 与各自 position semantics；
- shared weights 的 freeze/LoRA/full-SFT 范围；
- LIBERO/RoboCasa action execution horizon；
- RoboCasa exact action/state schema；
- BEHAVIOR robot/controller exact action dimension；
- Reasoner structured schema；
- λ_action/λ_vision calibration。

## 16.3 详细设计必须明确的数据流

```text
Dataset episode
→ ActionProcessor / Observation preprocessing
→ history replay / Local & Goal update
→ local_memory2llm / global_spatial2llm
→ SequencePlan + PackedSequence
→ Cosmos3 Generator
→ native Future Vision / Action prediction
→ execute action
→ new observation
→ update Memory

事件触发：
observation + goal + compact memory metadata/summary
→ Cosmos3 Reasoner
→ structured MemoryRequest / subgoal / verifier
→ Local/Global routing & retrieval
→ feed next Generator query
```

必须给出训练/推理、condition/target、multi-embodiment action、intervention 与 checkpoint 继承的准确合同。

# 第十七章 技术调研结论

本轮调研没有从“想用 Cosmos3”出发，而是比较了成熟 VLA+模块化 WM、视频 WM+Action module、上一代 Cosmos Policy Predict2-2B、Cosmos3-Nano、裸 Cosmos3-Edge、Cosmos3-Edge-Policy-DROID 与 feature-space dynamics 等路径。

筛选结果是：**PSM-WMA 主线冻结到 NVIDIA `cosmos-framework` + `Cosmos3-Edge-Policy-DROID`。** 选择理由是结构而不是新旧：它以 4B 规模同时提供 Reasoner、原生 Vision/Action Generator、多 embodiment Action abstraction、SequencePlan/PackedSequence 任务路由与公开 Action SFT 体系，最少引入与 PSM 无关的桥接模块。

当前 12 周路线因此收敛为：

```text
Stage 0:
Edge-Policy-DROID official smoke
→ LIBERO embodiment/action adaptation
→ Edge-Policy-LIBERO baseline

Stage 1:
+ Local PSM clean condition

Stage 2:
RoboCasa embodiment
+ Local PSM

Stage 3:
+ Spatial Global Memory
+ Planner/MemoryRequest
+ Cosmos3 Reasoner

Stage 4:
Agent thin slice

Stage 5 (Target):
BEHAVIOR small subset
→ only then decide Region/Place hierarchical Global
```

PSM-WMA 的研究核心不再是“Memory 应注入 backbone 还是 Action Head”，而是：

> **Persistent Spatial/Goal State 作为共享 clean condition，能否改善统一 World-Action Generator 的未来世界建模和机器人动作，并能否通过同一 checkpoint 的 Reasoner 被用于低频任务决策与验证。**

若 Edge adaptation Gate 失败，先降级到 Cosmos Policy Predict2-2B；只有 Cosmos family 路线仍不可用时，才回到 stable VLA + modular latent WM。

# 参考资料与一手来源

> 核验截点：2026-08-10。极新工作的代码/许可证仍需在 G0 clone 后再次确认。

## A. 项目内部与工程

[1] 《PSM-WMA 研究准备清单与总体方案 v3.2.2（稳定版）》，2026-08-10。  
[2] 《PSM-WMA 项目立项书 v1.0-freeze-candidate》，2026-08-10。  
[6] StarVLA, **WM4A: World Model for Action**, `wxwy/starVLA`, branch `merge-official-starvla-dev`, `docs/WM4A.md`.

## B. Backbone / World Model / WAM

[3] NVIDIA, **Cosmos3-Edge**, official model card, 2026. https://huggingface.co/nvidia/Cosmos3-Edge  
[4] NVIDIA, **Cosmos official repository**. https://github.com/NVIDIA/cosmos  
[5] NVIDIA Cosmos Framework, **Cosmos3 DROID Action-Policy Post-Training**. https://github.com/NVIDIA/cosmos-framework/blob/main/docs/action_policy_droid_posttrain.md  
[64] NVIDIA, **Cosmos3-Edge-Policy-DROID**, official model card. https://huggingface.co/nvidia/Cosmos3-Edge-Policy-DROID  
[65] NVIDIA Research, **Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning**, arXiv:2601.16163; official code: https://github.com/NVlabs/cosmos-policy  
[31] Liu et al., **OA-WAM: Object-Addressable World Action Model for Robust Robot Manipulation**, arXiv:2605.06481. https://arxiv.org/abs/2605.06481  
[32] Zhou et al., **DINO-WM: World Models on Pre-trained Visual Features**, ICML 2025. https://arxiv.org/abs/2411.04983  
[33] Guo et al., **X-WAM: Unified 4D World Action Modeling from Video Priors with Asynchronous Denoising**, arXiv:2604.26694. https://github.com/sharinka0715/X-WAM  
[34] Yuan et al., **Fast-WAM: Do World Action Models Need Test-time Future Imagination?**, arXiv:2603.16666. https://arxiv.org/abs/2603.16666  
[35] Ma et al., **Faster-WAM: Do World Action Models Need Deep Action Modules?**, arXiv:2608.02365. https://arxiv.org/abs/2608.02365  
[36] Li et al., **Efficient-WAM: A 1B-Parameter World-Action Model with Low-Cost Future Imagination**, arXiv:2606.10040. https://arxiv.org/abs/2606.10040  
[37] Zhou et al., **τ0-WM: A Unified Video-Action World Model for Robotic Manipulation**, arXiv:2606.01027. https://arxiv.org/abs/2606.01027  
[38] Fan et al., **MobileWAM: Bridging World Action Models to Mobile Manipulation with Chain-of-Foresight**, arXiv:2608.04657. https://arxiv.org/abs/2608.04657  
[39] Yang et al., **LiLa-WAM: Lightweight Latent Reasoning World-Action Model for Robotic Manipulation**, arXiv:2608.03701. https://arxiv.org/abs/2608.03701  
[40] Pan et al., **SelfWAM: A Self-Grounded Unified World Action Model for Fast Robot Control**, arXiv:2608.00725. https://arxiv.org/abs/2608.00725  
[41] Ding et al., **Mind-VLA: Instruction-Aware Spatial Representation Alignment for Vision-Language-Action Models**, arXiv:2608.04633. https://arxiv.org/abs/2608.04633

## C. Spatial Observation / 4D Geometry

[7] Chen et al., **Video Depth Anything**, CVPR 2025 Highlight, arXiv:2501.12375. https://github.com/DepthAnything/Video-Depth-Anything  
[8] Feiden et al., **Online Video Depth Anything**, 3DV 2026, arXiv:2510.09182. Project: https://friedfeid.github.io/oVDA-website/ ; official code/license: https://github.com/FriedFeid/OnlineVideoDepthAnything  
[9] Wang et al., **VGGT**, CVPR 2025. https://github.com/facebookresearch/vggt  
[10] Zhuo et al., **StreamVGGT: Streaming 4D Visual Geometry Transformer**, ICLR 2026, arXiv:2507.11539. https://github.com/wzzheng/StreamVGGT  
[11] Zhang et al., **Efficiently Reconstructing Dynamic Scenes One D4RT at a Time (D4RT)**, **CVPR 2026 Best Paper**, arXiv:2512.08924. Paper: https://arxiv.org/abs/2512.08924 ; CVPR proceedings: https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_Efficiently_Reconstructing_Dynamic_Scenes_One_D4RT_at_a_Time_CVPR_2026_paper.html ; official award: https://cvpr.thecvf.com/Conferences/2026/News/Best_Papers  
[12] Zou et al., **RetrieveVGGT: Training-Free Long Context Streaming 3D Reconstruction via Query-Key Similarity Retrieval**, arXiv:2605.09644. https://github.com/zzctmd/RetrieveVGGT

## D. Memory / Persistent Spatial State

[13] Jiang et al., **MemoryVAM: Integrating Memory into Video Action Model for Robot Manipulation**, arXiv:2606.20679. https://arxiv.org/abs/2606.20679  
[14] Yang et al., **MemoryWAM: Efficient World Action Modeling with Persistent Memory**, arXiv:2606.20562. https://arxiv.org/abs/2606.20562  
[15] **MemoryVLA**, arXiv:2508.19236. https://arxiv.org/abs/2508.19236  
[16] **MemoryVLA++**, arXiv:2606.09827. https://arxiv.org/abs/2606.09827  
[17] **DiM-WAM**, arXiv:2606.27677. https://arxiv.org/abs/2606.27677  
[18] Sun et al., **HiMem-WAM: Hierarchical Memory-Gated World Action Models**, arXiv:2606.10363. https://arxiv.org/abs/2606.10363  
[19] Yang et al., **EventVLA: Event-Driven Visual Evidence Memory for Long-Horizon Vision-Language-Action Policies**, arXiv:2606.20092. https://arxiv.org/abs/2606.20092  
[20] **KEMO**, arXiv:2606.23589. https://arxiv.org/abs/2606.23589  
[21] **HALO**, arXiv:2606.25136, RSS 2026. https://arxiv.org/abs/2606.25136  
[22] Yi et al., **WorldKV: Efficient World Memory with World Retrieval and Compression**, arXiv:2605.22718. https://github.com/cvlab-kaist/WorldKV  
[23] Zheng et al., **Mem-World: Memory-Augmented Action-Conditioned World Models for Persistent Robot Manipulation**, arXiv:2606.18960. https://arxiv.org/abs/2606.18960  
[24] Li et al., **Spatial Memory for Out-of-Vision Manipulation in Vision-Language-Action (SOMA)**, arXiv:2605.22283. https://arxiv.org/abs/2605.22283  
[25] Zhou et al., **HoloAgent-0: A Unified Embodied Agent Framework with 3D Spatial Memory**, arXiv:2606.23565. https://horizonrobotics.github.io/robot_lab/holoagent/  
[26] Wang et al., **Latent Spatial Memory for Video World Models (Mirage)**, arXiv:2606.09828. https://github.com/microsoft/LatentSpatialMemory  
[27] Yu et al., **MosaicMem: Hybrid Spatial Memory for Controllable Video World Models**, arXiv:2603.17117. https://mosaicmem.github.io/mosaicmem/  
[28] Kim et al., **SERF: Spatiotemporal Environment and Robot Feature Map for Long-Horizon Mobile Manipulation**, arXiv:2606.12956. https://arxiv.org/abs/2606.12956  
[29] Yan et al., **Dynamic Resilient Spatio-Semantic Memory with Hybrid Localization for Mobile Manipulation (DREAM)**, arXiv:2606.00576. https://arxiv.org/abs/2606.00576  
[30] **Video World Models with Long-term Spatial Memory**, arXiv:2506.05284. https://arxiv.org/abs/2506.05284  
[60] **When Memory Lies**, arXiv:2608.04574. https://arxiv.org/abs/2608.04574

## E. Benchmarks / Data

[42] Dai et al., **RoboMME**, ICML 2026 Oral, arXiv:2603.04639. https://github.com/RoboMME/robomme_benchmark  
[43] Chen et al., **RMBench**, arXiv:2603.01229. https://arxiv.org/abs/2603.01229  
[44] Lei et al., **RoboMemArena**, arXiv:2605.10921. https://github.com/OpenHelix-Team/RoboMemArena  
[45] Liao et al., **SpaMEM**, arXiv:2604.22409. https://arxiv.org/abs/2604.22409  
[46] Soroush Nasiriany, Sepehr Nasiriany, Abhiram Maddukuri, Yuke Zhu, **RoboCasa365: A Large-Scale Simulation Framework for Training and Benchmarking Generalist Robots**, International Conference on Learning Representations (ICLR), 2026. Official project/citation: https://robocasa.ai/  
[47] Wang et al., **LMEE / LMEE-Bench**, arXiv:2601.10744. https://arxiv.org/abs/2601.10744  
[48] Hu et al., **3DLLM-Mem / 3DMem-Bench**, arXiv:2505.22657. https://arxiv.org/abs/2505.22657  
[49] Li et al., **BEHAVIOR-1K**, official benchmark. https://behavior.stanford.edu/  
[61] Chung et al., **LIBERO-Mem**, arXiv:2511.11478. https://arxiv.org/abs/2511.11478
[62] Cherepanov et al., **μVLA: On Recurrent Memory for Partially Observable Manipulation in VLA Models**, arXiv:2606.12497. https://arxiv.org/abs/2606.12497  
[63] Li et al., **ReMem-VLA: Empowering Vision-Language-Action Model with Memory via Dual-Level Recurrent Queries**, arXiv:2603.12942. https://arxiv.org/abs/2603.12942

## F. Agent / Continual / Proactive

[50] Zhang et al., **Harness VLA**, arXiv:2607.08448. https://arxiv.org/abs/2607.08448  
[51] **WorldLines**, arXiv:2606.18847. https://arxiv.org/abs/2606.18847  
[52] **RECAP / π*0.6**, arXiv:2511.14759. https://arxiv.org/abs/2511.14759  
[53] **Learning while Deploying (LWD)**, arXiv:2605.00416. https://arxiv.org/abs/2605.00416  
[54] Yang et al., **RISE: Self-Improving Robot Policy with Compositional World Model**, arXiv:2602.11075. https://arxiv.org/abs/2602.11075  
[55] Jiang et al., **WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL**, arXiv:2602.13977. https://arxiv.org/abs/2602.13977  
[56] Lyu et al., **Reinforcement Fine-Tuning of Flow-Matching Policies for Vision-Language-Action Models (FPO)**, accepted to ICRA 2026, arXiv:2510.09976. https://arxiv.org/abs/2510.09976  
[57] **Batch Online RL**, arXiv:2505.08078. https://arxiv.org/abs/2505.08078  
[58] **HiRoC**, arXiv:2608.05999. https://arxiv.org/abs/2608.05999  
[59] **SARL**, arXiv:2606.31958. https://arxiv.org/abs/2606.31958

> Continual/Proactive 文献只作为后续路线输入。RISE、WoVR、FPO 的论文身份与核心方法已由 arXiv 一手来源核验；但在真正进入实施前，仍必须重新核验届时代码、许可证、checkpoint、数据和环境要求，它们不构成当前详细设计硬依赖。

---

# 附录 A：关键选择的一句话理由

- **为什么不是纯 RGB？** 保留 RGB baseline，但 Global addressing 需要更稳定 geometry cue。
- **为什么研究默认 oVDA？** 它提供 causal online depth，并可用同一模型覆盖 offline sequential cache 与 online inference，减少 train/inference depth semantics mismatch。
- **许可证怎么处理？** mixed license 单独登记；当前研究阶段不把产品化许可作为算法主选型第一判据，进入商业化再设独立 Gate。
- **为什么不直接 StreamVGGT？** geometry 强但更重，而且 geometry memory ≠ task memory。
- **为什么 Local recurrent latent？** 最小、fixed-budget、端到端，最能检验“隐式长期 state”。
- **为什么当前不做 Region/Place hierarchy？** Spatial Global 可以先用单一 persistent store + retrieval 验证长期空间证据，无需先引入房间分区/Place ID；只有多房间 aliasing/容量瓶颈出现后再层级化。
- **为什么保留 Regional 技术储备？** BEHAVIOR 多房间任务真正出现跨区域重访后再根据实际定位/导航条件做专项选择。
- **为什么不在线生成未来视频？** latency 高，2026 多个 WAM 工作支持训练期 future supervision + fast action inference。
- **为什么 Agent 后置？** PSM 若还未被 action 使用，Agent 只会掩盖根因。
- **为什么不追 full BEHAVIOR？** 单人项目先证明机制，再扩系统。

# 附录 B：Detailed Design 启动 Gate

> **强制流程 Gate**：下列承重项未完成核验时，不冻结 `02_detailed_design.md` 中与该项相关的实现参数、实验编号和资源预算；若某项无法完成，应先写明 fallback，再启动对应阶段的详细设计。

- [ ] `Cosmos3-Edge-Policy-DROID` Reasoner + Policy + World/Generator official smoke；
- [ ] Edge vs Edge-Policy-DROID checkpoint/config/parameter audit；
- [ ] DROID ActionProcessor/domain 数据流核对；
- [ ] Edge-Policy-DROID × LIBERO 10D forward/loss + tiny-overfit；
- [ ] LIBERO closed-loop non-zero usable baseline；
- [ ] PSM clean condition packing/attention smoke；
- [ ] LIBERO/LIBERO-Mem/RoboMME 最小 data contract；
- [ ] RoboCasa365 episode/action/state schema profile；
- [ ] oVDA inference/streaming profile（仅条件路径）；
- [ ] Local PSM 最小训练接口确认；
- [ ] RoboCasa pose/intrinsics / camera trajectory 对 Spatial Global 是正式 schema 字段；若缺失需明确替代定位来源；Region/Place hierarchy 仍后置；
- [ ] license table 完成；
- [ ] ≤20 实验预算初版；
- [ ] 12 周 Hard Requirement 与 Target 边界再次确认。

## v1.7 新增参考


[69] Qu et al., **Dual Latent Memory in Vision-Language-Action Models for Robotic Manipulation (LaMem-VLA)**, arXiv:2607.07608. https://arxiv.org/abs/2607.07608  
[70] Li et al., **ReMem-VLA: Empowering Vision-Language-Action Model with Memory via Dual-Level Recurrent Queries**, arXiv:2603.12942. https://arxiv.org/abs/2603.12942  
[71] Cherepanov et al., **μVLA: On Recurrent Memory for Partially Observable Manipulation in VLA Models**, arXiv:2606.12497. https://arxiv.org/abs/2606.12497  
[72] Liu et al., **VistaVLA: Geometry- and Semantic-Aware 3D Gaussian-Grounded VLA for Robotic Manipulation**, arXiv:2607.12356. https://arxiv.org/abs/2607.12356  
[73] Yu et al., **MosaicMem: Hybrid Spatial Memory for Controllable Video World Models**, arXiv:2603.17117. https://arxiv.org/abs/2603.17117  
[74] Zhang et al., **Adding Conditional Control to Text-to-Image Diffusion Models (ControlNet)**, arXiv:2302.05543. https://arxiv.org/abs/2302.05543  
[75] Tan et al., **OminiControl: Minimal and Universal Control for Diffusion Transformer**, arXiv:2411.15098. https://arxiv.org/abs/2411.15098  
[76] Jiang et al., **RoboTTT: Context Scaling for Robot Policies**, arXiv:2607.15275. NVIDIA project: https://research.nvidia.com/labs/gear/robottt/ ; paper: https://arxiv.org/abs/2607.15275  
