# PSM-WMA：Persistent Spatial Memory-Augmented World-Model Agent 研究

**项目立项书**  
**版本**：v1.4-frozen  
**日期**：2026-08-12  
**文档类型**：正式立项书（技术实现解耦冻结版）  
**上游 Source of Truth**：《PSM-WMA 研究准备清单与总体方案 v3.2.2（稳定版）》  
**参考文档方法**：MoWA `docs_zh/mowa/00_project_proposal.md`、`01_technical_survey.md`、`02_detailed_design.md`  
**执行约束**：单人串行；1–8×A100 80GB；单卡 RTX 4090 用于开发/轻量验证；关键训练实验总量 ≤20 组  

---

## 文档治理与冻结说明

本立项书以《PSM-WMA 研究准备清单与总体方案 v3.2.2（稳定版）》为上游 Source of Truth。立项书只冻结**项目价值、研究对象、范围边界、阶段路线、资源约束、成果形态与验收逻辑**；具体模型结构、表示形式、loss、shape、训练配置、实验矩阵与量化阈值由后续 `01_technical_survey.md` 与 `02_detailed_design.md` 冻结。

在不改变 v3.2.2 主线的前提下，本版补充三类项目级信息：

1. 纳入 MemoryVAM、Mem-World、SOMA、HoloAgent-0、MemoryVLA++、DiM-WAM、When Memory Lies 等 2026 年最近邻，用于校准项目差异边界；这些工作首先作为**可复用证据与工程参考**，而不是换题触发器；
2. 明确 PSM-WMA 按**企业研发型系统项目**管理：系统落地与工程完整性是 Hard Requirement，1–2 个方法增量是 Target，论文/专利级独立新颖性是 Stretch；
3. 新增 12 周基线周期作为单人执行规划建议；其硬承诺覆盖 Temporal Local Memory、Spatial Global Memory、PSM→World/Action、RoboCasa365 downstream 收益与最小 Agent vertical slice；**Region/Place 层级化 Regional Global PSM 不进入 LIBERO/RoboCasa 12 周硬交付，仅在进入 BEHAVIOR-1K / 真正多房间 mobile manipulation 后重新专项设计。**

v3.2.2 中将 Persistent Spatial Memory 定位为“项目主要创新”；在本立项书中，该表述统一解释为**项目主要自研与差异化技术主线**，不等同于“文献首次提出”。

> **2026-08-11 Scope Override**：经项目决策，v3.2.2 中“LIBERO/RoboCasa 后即启动 Global PSM prototype”的执行顺序被本版收敛：**LIBERO/RoboCasa 仅做 Local Memory + Goal Memory；Region/Place 与 Regional Global PSM 推迟到 BEHAVIOR-1K / 真正多房间阶段重新决策。** 该调整是明确的阶段范围更新，不是静默改写；后续若继续维护研究准备清单，应在下一版（如 v3.2.3）回灌这一决策。

> **2026-08-11 Depth Route Override**：本项目是研究项目，learned depth 不再以产品化许可证作为首要选型依据。需要 learned depth 时统一采用 **oVDA**：离线数据按时间顺序运行 oVDA 并缓存 depth，在线推理复用同一 causal pipeline。VDA-S 从当前主技术路线删除，仅保留未来必要时的 accuracy upper-bound 对照候选；BEHAVIOR 若仿真环境直接提供 depth，可直接作为机制实验输入。

> **2026-08-12 Memory Topology Override（优先级高于 2026-08-11 Local+Goal-only 收敛）**：当前主线重新明确为两类职责正交、分别构建的 PSM：**Temporal Local Memory** 与 **Spatial Global Memory**。前者压缩时间对齐的近期多模态经历（RGB/视觉表征、depth、相机位姿、机器人状态、可选腕部视觉、已执行动作等），后者从全 episode 的空间化历史中按位置、视角、时间与语义检索关键空间证据。这里的 Spatial Global Memory **不等于** Region/Place 层级化 Regional Global PSM；Region/Place、区域划分、跨房间层级寻址仍推迟到 BEHAVIOR-1K / 真正多房间阶段。

> **2026-08-12 Planner Interface Override**：Local / Global Memory 均定义为**可选信息模态**，与视觉、动作等模态一样按需存在或缺失。当前 Memory 阶段可用训练协议人工控制模态 presence / dropout；后续由更高层 Planner / Reasoner 决定是否请求 Local、是否请求 Global、检索什么以及 token budget，从而为 Agent 留出原生接口。Goal Memory 保留为后续可选 goal-conditioned 扩展，但不再是 Spatial Global Memory 的替代物，也不阻断 Local→Global 主线。

> **2026-08-12 Local Mechanism Candidate Addendum**：RoboTTT（arXiv:2607.15275）提升为 **Temporal Local Memory 的第一优先候选机制**，但**不冻结为最终实现**。其价值在于用持续在线更新的 fast-weight recurrent state 压缩长时 visuomotor history，并以 TBPTT 保持长状态链、短梯度链；这与本项目 Local 的 persistent temporal state 目标高度一致。当前同时保留一个更简单的 recurrent latent / fixed-token compressor 作为 baseline candidate。最终选择必须在 `Cosmos3-Edge-Policy-DROID → LIBERO` 的 R06 closed-loop baseline PASS 后，通过 Local 专项 smoke 比较 future/action sensitivity、训练稳定性、状态 reset/并行环境隔离、显存与延迟后再冻结。首选集成方式是**独立 LocalMemoryEncoder/TTT compressor → Local modality tokens → Cosmos3**，而不是首期直接把 TTT layer 植入 Cosmos3 主干。

v3.2.2 已冻结的 Normal / Zero / Shuffle / Stale / Truncated 五类 Memory Intervention 继续作为基础干预框架。v1.4 起分别扩展为 Local-Zero/Shuffle/Stale/Truncated 与 Global-Zero/Shuffle/Wrong-view/Stale/Top-K-truncation；其中 `modality absent` 必须与 `present + zero content` 区分。Region/Place 层级相关的 Wrong-region retrieval 仍推迟到 BEHAVIOR 阶段。

## 执行摘要

长时序具身任务需要机器人在目标离开视野、历史信息跨时间分布和环境状态变化后，仍能维护“当前世界是什么样”以及“当前目标已经发生过什么”的持续状态，并让这些信息真正影响未来预测和动作。2026 年以来，MemoryVAM、MemoryVLA++、DiM-WAM 等已证明长期/事件记忆能够进入 world/action；Mem-World、SOMA、HoloAgent-0 等又证明 spatial memory 对 world prediction、action 与 Agent 有实际价值。因此 PSM-WMA 不以“首次提出 Memory + World Model/Action”作为立项依据。

本项目定位为 **企业研发型 Persistent Spatial Memory-Augmented World-Model Agent 系统项目**。当前主线采用：

```text
Current / Short-term Observation
        +
Temporal Local Memory      # 近期、多传感器、learned temporal state
        +
Spatial Global Memory     # 长期、空间重组、按需检索的关键空间证据
        ↓
World / Action
        ↓
Planner / Agent thin slice
```

其中：
- **Temporal Local Memory**：任务无关的近期持续世界状态；由时间对齐的 RGB/视觉表征、depth、相机位姿、机器人状态、可选 wrist RGB、已执行动作等压缩得到，内容提取/写入/读取进入优化链路；
- **Spatial Global Memory**：把全 episode 历史按空间位置、相机轨迹、视角、时间和语义重新组织，推理时只检索关键空间 patch / key-view / feature 作为条件；底层表示可由 RGB semantic feature + oVDA depth/局部特征 + pose 等组成，具体存储形式继续专项调研；
- **Goal Memory**：保留为后续可选 goal/subgoal-conditioned 扩展，用于任务进度/目标相关历史，不与 Global Spatial Memory 混为一类；
- **Regional Global PSM / Region-Place hierarchy**：仍不在当前阶段实现。只有进入 BEHAVIOR-1K / 真正多房间 mobile manipulation 后，才重新决定 Region/Place、层级地址、跨区域 revisit 与 stale 策略。

Local / Global 都必须支持 optional presence：没有被 Planner 请求时不应强制补零占位；有请求时通过各自独立的 modality adapter 进入后续 World/Action 主路径。

系统必须支持 Memory 写入/更新、task-conditioned 读取、intervention、World/Action coupling、执行监控与失败恢复接口。项目成功首先看 **能否做成并产生执行收益**：形成稳定 closed-loop、可量化指标、可复现实验、10 分钟级演示和可复用工程资产；其次争取在 recurrent persistent state、Local/Global 分工、independent optional Memory→World/Action conditioning 或模型内部持续状态接入机制中形成 1–2 个方法增量。论文级独立新颖性不作为立项成功的必要条件。

12 周基线周期的 Must-have 调整为：Local Memory 的真实使用与可归因闭环、一个可运行的 Spatial Global Memory prototype 及其检索/注入闭环、action-conditioned world representation、RoboCasa365 downstream 收益，以及一条最小 Planner/Agent vertical slice。**Region/Place 层级化 Regional Global PSM 仍不属于 12 周 Must-have。** Goal Memory 作为可选 Target，不与 Local/Global 主线同时引入。关键训练实验总量 ≤20 组；若 Memory 连续干预不能证明真实使用，则优先回退更简单 history / key-view / Hybrid Memory，而不是提前增加 Region/Agent 复杂度。

# 第一章 项目背景

## 1.1 具身智能正在从反应式策略走向持续世界状态

当前主流 VLA 将视觉、语言和机器人状态映射到动作，已经能够在短时序操作中展现较强的泛化能力。但对真实家庭机器人而言，“看见目标并执行一个 action chunk”只是局部能力。长程任务要求系统在几十秒到数分钟内持续理解环境、更新任务进度、处理遮挡和视角变化，并对自己之前看过但当前不可见的环境状态保持记忆。

这意味着具身系统需要维护一个随时间演化的内部世界状态，而不能把每个时刻都当作近似 Markov 的独立决策问题。对于部分可观测环境，当前图像通常不足以决定正确动作：杯子可能刚刚被放入抽屉，目标物可能在机器人转身后离开视野，门的开合状态可能在前一阶段改变，机器人也可能需要回到之前访问过的区域继续任务。系统若只依赖当前帧或固定短窗口，就会反复搜索、重复操作、误用过期状态，或者在失败后无法判断应重试、重观察还是重新分解任务。

因此，PSM-WMA 的出发点不是“增加上下文长度”，而是把 **持续世界状态（persistent world state）** 作为机器人决策闭环中的一等公民。

## 1.2 长时序具身任务的本质是部分可观测与状态持续变化

PSM-WMA 主要面向 long-horizon household manipulation / mobile manipulation。此类任务具有四个对记忆提出硬要求的特征。

第一，**信息跨时间分布**。完成当前动作所需的信息可能只在几十步之前出现。例如机器人先打开柜门，再拿取其他物体，之后返回时当前视角中并不能直接确认之前的门状态。

第二，**信息具有明确空间归属**。机器人不是只需要知道“以前见过一个杯子”，而是要知道该信息属于哪个房间、区域、视角或可操作位置，并能在重访时恢复相关内容。纯时间顺序的 memory token 很难稳定地区分多个相似区域。

第三，**世界状态会变化**。长期记忆不能只“保存”，还必须支持 update、overwrite 和 stale-state handling。对象移动、抽屉开关、容器内容变化、机器人自身动作导致的场景变化都会使旧记忆失效。

第四，**记忆必须产生行动价值**。如果 Memory 只能在 QA 或 probe 上回答“之前在哪里看到了杯子”，却不改变 world prediction、动作选择、重访效率或任务成功率，那么它仍不是本项目需要的机器人世界状态。

## 1.3 当前 VLA / WAM 的有限历史问题

VLA 的优势在于把多模态理解直接映射到控制，但在长时序任务中，简单扩大视觉历史会增加 token、显存和延迟，也不等价于形成可更新的状态。WAM / World Model 进一步学习 action-conditioned future，但如果其状态仍主要由近期窗口定义，在非 Markov 任务中仍会缺失决定当前动作的早期事件。

2026 年 MemoryWAM、MemoryVAM、MemoryVLA++ 等已经证明：机器人策略需要超越固定 recent window 的持久记忆，并让记忆进入 world/action。本项目因此不把“增加历史”当创新，而研究**受控容量的持续状态如何被更新、读取，并产生动作价值**。

## 1.4 当前阶段采用 Temporal Local + Spatial Global，而不是 Local + Goal 替代 Global

当前问题不再把“Global”与“Region/Place 层级地图”绑定。PSM-WMA 当前明确两类互补 Memory：

```text
Temporal Local Memory
= 最近一段时间的多模态经历经过学习式压缩后的 temporal world state

Spatial Global Memory
= 全 episode 历史按空间/视角/时间结构化后，按需检索出的关键空间证据
```

Local 回答“刚才发生了什么、状态如何演化到当前”；Global 回答“之前在什么位置、什么视角、什么时间观察到过哪些与当前决策相关的内容”。二者分别建模，不共用一个 Memory mapper。Goal-conditioned task progress 可后续单独增加，但不再代替 Global。

## 1.5 Spatial Global Memory 进入当前主线，Regional/Place hierarchy 仍后置

当前 Global Memory 不要求先完成房间分区、Place ID 或导航算法。第一版重点是：把历史 RGB/视觉语义、oVDA depth/局部几何、相机 pose/trajectory、timestamp/view direction 等组织成 persistent spatial store，并通过 current pose / semantic query / task context 检索少量关键 patch / key-view / feature。

进入 BEHAVIOR 多房间阶段后，若单一全局空间 store 出现容量、aliasing 或检索冲突，再引入 Region/Place 层级地址。

## 1.6 Planner / Agent 负责按需调用 Memory，而不是代替 Memory

Local / Global 是可选模态。Planner / Reasoner 的职责不是重新生成低层世界状态，而是决定：
- 当前是否需要 Local；
- 当前是否需要 Global；
- Global 要查询什么空间/语义/时间证据；
- 每类 Memory 的 token / retrieval budget。

Memory 系统负责存储、更新、压缩、检索和转成模型可消费的表示；World/Action 模型负责基于这些条件预测未来并输出动作。这样当前阶段可以先用人工/随机 modality routing 训练，后续无缝替换成 Agent 动态 routing。

## 1.7 最近邻工作与项目差异边界

截至 2026 年 8 月：
- MemoryVAM / MemoryVLA++ / DiM-WAM 已证明 memory 可影响 future/world 与 action；
- Mem-World / Mirage 证明 persistent spatial state 可进入 world modeling；
- SOMA / SERF 证明 spatial state 可改善 action；
- HoloAgent-0 证明 spatial memory 可被 Agent/skills 使用；
- When Memory Lies 说明 stale memory 是现实风险。

因此，本项目不把“有记忆”“空间记忆”“层级记忆”“stale handling”“memory intervention”单独作为首次贡献。

当前更实际的研究抓手是：

1. **Temporal Local persistent state**：固定/受控容量地压缩近期时间对齐的多源经历，学习内容提取、更新与读取；
2. **Spatial Global persistent state**：把全 episode 历史按空间位置、相机轨迹、视角、时间与语义结构化，并按需检索关键空间证据；
3. **Independent optional modality interfaces**：Local / Global 分别适配到统一 World/Action 主干，允许按需存在或缺失；
4. **Shared Memory → World / Action interface**：两类 Memory 都必须真实影响 action-conditioned world representation 与在线 action；
5. **可归因系统闭环**：通过 Local/Global intervention、future/action sensitivity 与 closed-loop 结果证明真实作用。

Regional Global PSM / Place Memory 仍是未来可能的方法空间，但只在 BEHAVIOR 阶段重新评审。

## 1.8 PSM-WMA 的企业研发机会

当前统一闭环是：

```text
Continuous Observation
        ↓
Temporal Local Memory (optional)
        +
Spatial Global Memory (optional)
        ↓
Action-conditioned World State
        ↓
Action Policy
        ↓
Agent Monitor / Retry
        ↓
New Observation → Local update / Global store update
```

如果该闭环能够在 LIBERO / RoboCasa365 上稳定运行，并通过干预证明 Temporal Local Memory、Spatial Global Memory、WAM 与 Agent 各自提供可重复收益，就已经构成有价值的企业研发成果。

BEHAVIOR 阶段如出现真实跨区域需求，再增加：

```text
Regional Global PSM / Place Memory
```

而不是为了架构“完整”提前实现。

# 第二章 项目定位

## 2.1 项目研究对象

PSM-WMA 研究的是：

> **在长时序、部分可观测且环境状态持续变化的具身任务中，如何构建固定/受控容量、可递归更新、可跨时间保持、具有空间可寻址性并可按任务查询的 Persistent Spatial Memory；如何使该 Memory 真正进入 action-conditioned World Model 与 Action path；以及如何在此基础上形成具备长程任务分解、监控、恢复和后续持续演进能力的 World-Model Agent。**

项目核心研究主体为：

**Persistent Spatial Memory + action-conditioned World Model**

Agent 是完整系统闭环，但不是前期首要算法创新。

## 2.2 PSM-WMA 不是什么

PSM-WMA 不等同于以下任一方向：

| 方向 | 已有主要能力 | PSM-WMA 的工程/研究侧重点 |
|---|---|---|
| 普通 VLA | 当前观测/语言 → 动作 | 增加可跨时间更新的空间世界状态，并验证其进入 world/action path |
| VLA + 多帧历史 | 扩大短时上下文 | 解决长期空间寻址、稀疏保存、状态覆盖和跨区域 retrieval |
| MemoryVAM / MemoryVLA++ / DiM-WAM | episodic/event memory → world/action | 优先复用其 memory-to-world/action 经验，进一步研究 spatial state 与 Local/Global 空间层级 |
| Mem-World | spatial/temporal memory → action-conditioned world model | 参考其 persistent world modeling；本项目更强调 online action、层级 PSM 与后续 Agent 的统一系统接口 |
| SOMA | persistent spatial memory → VLA action | 参考其动态 refinement/retrieval；本项目同时要求 world prediction 与更大空间 Global PSM |
| HoloAgent-0 | 3D spatial memory → Agent/skills | 参考 Agent/世界状态职责切分；本项目不以 explicit 3D scene graph 为既定表示，并保留 learned WAM/action coupling |
| 视频 Spatial Memory | 保持生成世界长期空间一致性 | 只采用能转化为机器人 future/action/closed-loop 收益的能力 |
| SLAM / 3D Reconstruction | 几何建图与定位 | 本项目不以完整 3D 重建质量为目标；空间表示服务 world/action/agent |
| 文本 RAG / Agent Memory | 语义历史、经验、规则检索 | PSM 保存环境空间状态；Experience Memory 另管执行经验 |
| Navigation / VLN | 路径规划、导航策略 | 导航只作为 Global PSM 和移动操作基础设施，不研究新导航算法 |

## 2.3 项目与前序工作的关系

前序 VLA / MoWA 相关工作提供了成熟策略、训练评测工程和 World Model / Action 接口经验。PSM-WMA 不重复优化 VLA action head，也不把旧失败架构继续扩复杂；它继承的是可运行策略、工程框架和“future 必须进入 action path”的研究原则。

PSM-WMA 的增量在于：从“预测未来”继续向前推进到“维护持续世界状态，并利用该状态预测未来和组织行动”。

## 2.4 项目核心研究问题与扩展问题

12 周基线首先回答 Q1–Q4；Q5 只要求最小 Planner/Agent vertical slice；Q6 为后置 Region/Place hierarchy。

### Q1：多源 Observation 是否能形成可靠的时间/空间 evidence？

当前 RGB / visual feature、depth、camera pose、robot state、可选 wrist view 与 executed action 能否在统一 source timeline 上正确对齐，并在不引入 future leakage 的情况下形成 Local/Global 的输入证据？

### Q2：Temporal Local Memory 如何学习近期持续世界状态？

在固定/受控容量下，Local 如何压缩多模态近期经历、跨 policy query 持续更新，并通过 native World/Action loss 学会保留对后续动作真正有用的状态？训练时如何在 TBPTT / detached recurrent state / stable update 之间取得稳定性与长期保持能力？

### Q3：Spatial Global Memory 如何保存并检索长期空间证据？

如何把历史视觉/语义、depth/geometry、camera pose/trajectory、view direction、timestamp 等按空间关系组织成 persistent store，并在当前 pose / task / semantic query 下只检索少量关键 patch / key-view / feature，回答“之前在什么位置、什么视角、什么时候观察到了什么”？

### Q4：Local + Global 是否真的改善 World / Action / Closed-loop？

Local/Global 是否分别和组合改善 action-conditioned future、action、重访/out-of-view 情境和 closed-loop SR？模型是否绕开某一模态？如何用 Local/Global 分别的 intervention、longer-history/key-view control 与 matched baseline 证明收益来自正确的 temporal/spatial evidence？

### Q5（系统集成）：Planner / Agent 如何按需调用 Memory？

在稳定的 Local+Global + WAM 基础上，Planner 如何通过统一 `MemoryRequest` 决定 `use_local/use_global`、query 与 token budget，并用于 subgoal、verifier、retry/re-observe，而不是让 Agent 自己重新实现记忆或靠大量规则掩盖底层失败？

### Q6（BEHAVIOR 后置）：什么时候需要 Region/Place hierarchy？

只有真正多房间任务出现容量、aliasing 或跨区域检索冲突后，才引入 Region/Place、层级地址、跨区域 revisit/stale 等机制；该问题不阻断当前 Spatial Global Memory。

## 2.5 项目价值优先级

PSM-WMA 按企业研发项目而非纯论文项目管理，价值优先级冻结如下：

### 第一优先级：系统落地（Hard Requirement）

必须形成可运行、可评测、可复现的 PSM → World Model → Action 闭环，并保留 Agent 接入接口。项目不能以“有想法但系统没跑通”作为成功。

### 第二优先级：工程完整性与可复用资产（Hard Requirement）

形成统一数据 contract、Memory I/O、intervention framework、benchmark adapter、日志/评测、checkpoint 与 demo，使结果可由其他研发人员复现和扩展。系统集成本身属于正式项目成果。

### 第三优先级：1–2 个方法增量（Target）

从 Temporal Local learned compression/update、Spatial Global store/retrieval、Local/Global optional-modality injection、stale-aware update 等候选点中，只选择最有价值且最可验证的 1–2 个做深入优化；Region/Place hierarchy 的方法增量推迟到 BEHAVIOR 阶段。

### 第四优先级：论文级新颖性（Stretch）

只有当 `01` 的最近邻核验和后续实验同时支持独立贡献时，才形成明确 独立新颖性表述。新的论文出现只影响贡献表述和复用策略，不自动触发项目换题。

因此，项目评审首先问“**系统是否做成并产生业务/任务收益**”，其次问“**哪里做得比已有方案更好**”，最后才问“**是否构成学术首次**”。


---

## 2.6 2026-08-12 当前主研究对象口径

当前 PSM 的两条主线为：
1. **Temporal Local Memory**：learned、时间对齐、固定/受控容量，保持近期多模态世界状态；
2. **Spatial Global Memory**：explicit/semi-explicit、空间结构化、长期 persistent、按需检索关键历史空间证据。

两类 Memory 均必须进入 World/Action 路径，并支持 presence/absence；后续 Planner/Reasoner 只负责 routing/query，不改变其底层信息职责。Goal-conditioned Memory 作为可选扩展保留；Regional/Place hierarchy 仅在真正多房间阶段启动。

# 第三章 项目目标

## 3.1 总体目标

构建并验证一个 **Persistent Spatial Memory-Augmented World-Model Agent** 原型，使机器人能够：

1. 维护一份 task-agnostic **Temporal Local Memory**，压缩时间对齐的近期 RGB/视觉、depth、pose、robot state、可选 wrist 与 executed action；
2. 建立一份 **Spatial Global Memory**，把全 episode 历史按空间/视角/时间结构化，并按需检索关键证据；
3. Local / Global 分别通过独立可选模态接口进入 World/Action 主路径；
4. 在 Memory 不提供时保持可运行，在提供时能真实改变 future/action；
5. 通过 Local/Global intervention、future/action sensitivity 与 closed-loop 结果证明任务价值；
6. 后期由 Planner / Reasoner 决定是否请求 Local/Global、检索什么和 token budget；
7. Goal Memory 若需要作为独立 Target 增加，不与 Global 混淆；
8. Region/Place hierarchy 只在真正多房间阶段评估。

## 3.2 技术研究目标

- 研究 fixed-budget Temporal Local Memory：多源时间对齐、学习式压缩、稳定跨步更新与读取；
- 研究 Spatial Global Memory：RGB/语义 + depth/几何 + pose/trajectory/time 的空间重组、persistent store 与关键证据检索；
- 研究 Local 与 Global 的职责分离、互补与 optional presence；
- 研究 Local / Global 分别通过独立模态适配器进入 World / Action 的共享主干；
- 研究 action-conditioned future supervision 是否能塑造 action-facing world state；
- 建立 Local/Global intervention 与 no-regression / memory-dependent benchmark 体系；
- 保留 Regional Global PSM 的未来接口，但当前不设计 Region/Writer/Reader。

## 3.3 工程目标

- 建立独立的 PSM-WMA 工程 namespace 与可替换的 World-Action/Reasoner 接口，不在立项阶段绑定具体 基础模型、checkpoint 或训练框架；
- 建立 `PSMSequenceAdapter`、Temporal Alignment、receding-horizon runtime；
- 建立 Local / Global Memory 独立 store/update/read/retrieval 与 intervention；
- 建立 Local / Global 两套独立 Persistent Modality Interface，使二者能按需存在/缺失并进入 world/action 主路径，而不是只进入 auxiliary probe；
- 建立 Planner-facing `MemoryRequest` / modality routing 接口，为后续 Agent 决定 Local/Global presence、query 与 token budget 留出稳定边界；
- 支持 LIBERO / RoboCasa365 train/eval，并为 BEHAVIOR-1K 的多 embodiment / mobile-manipulation 接入保留接口；
- 建立 Agent thin-slice 接口与 verifier / retry / re-observe 运行合同；
- 关键训练实验 ≤20。

## 3.4 评测目标

**Temporal Local Memory**：retention、update、stale/truncated、Local-Zero/Shuffle、近期多模态时间状态 usefulness。  
**Spatial Global Memory**：spatial retrieval hit-rate、key-view/patch relevance、Global-Zero/Shuffle/Wrong-view/Stale、out-of-view / revisit usefulness。  
**Goal Memory（Target）**：goal-relevant retention、task progress、Goal-Zero/Shuffle。  
**World/Action**：future latent、action error、memory-conditioned action difference、shared world-state sensitivity。  
**Task-level**：SR、任务推进、重复/无效动作、失败恢复、步骤数/时间、推理成本。

Regional retrieval/revisit/region Recall@K 等指标不进入当前阶段，留到 BEHAVIOR Regional PSM 后。

## 3.5 分层成功口径

### 最低成功（Must-have，12 周硬验收）

- R01–R06 证明无 Memory foundation 可用且 closed-loop SR > 0 可重复；
- Temporal Local 完成 function-preserving 接入，时间对齐/causality 可审计，Local intervention 证明模型真实使用；
- Spatial Global prototype 可构建 persistent store、检索 Top-K 关键空间证据并通过独立 Global modality 进入 World/Action；
- Global-Zero / Shuffle / Wrong-view / Stale 等产生可解释差异，或形成可复现负结论；
- Local-only / Global-only / Both / Neither 的 matched 对照能够解释二者职责与互补性；
- 在 RoboCasa365 受控任务中，Local/Global 至少一项对 action / task progress / closed-loop / failure-recovery 产生可重复正向收益；future-only auxiliary 提升不能单独视为成功；
- 跑通稳定 `MemoryRequest` 接口和至少一条 Planner/Agent vertical slice；
- 形成可复现的数据、Memory modality、intervention、训练/推理和 demo 资产；
- **不要求** 12 周内实现 Region/Place hierarchy。

### 推荐成功（Target）

- Local 相比 longer raw history 显示 fixed-budget temporal-state 优势；
- Global 相比简单 keyframe history / location-only retrieval 显示空间结构化优势；
- Local+Global 组合显示互补收益或清晰边界；
- Goal Memory 只在确有 task-progress 缺口时作为额外 Target；
- 条件允许时进入 BEHAVIOR 小子集验证多房间需求。

### 扩展成功（Stretch）

- 形成 1–2 个可独立表述的方法增量；
- BEHAVIOR 阶段实现 Region/Place hierarchy；
- 稳定 base policy 下做 continual/post-training 或 proactive-agent 扩展。

# 第四章 研究范围与非目标

## 4.1 In Scope

当前 12 周 / LIBERO / RoboCasa365：
- current/short-term observation；
- Temporal Local Memory：multi-sensor temporal alignment + learned compression/update/read；
- Spatial Global Memory：persistent spatial store + retrieval/compression；
- Local / Global optional modality interface；
- action-conditioned World/Future + Action；
- Local/Global intervention 与 matched baseline；
- oVDA 作为 conditional geometry source 与 offline cache；
- Planner-facing `MemoryRequest` + Reasoner thin slice；
- Goal Memory only if needed；
- Region/Place hierarchy 仅保留未来接口。

## 4.2 Out of Scope

本项目明确不做：

- 从零训练大型视频世界模型或通用基础模型；
- 以纯像素长视频生成质量为主要目标；
- 以 point cloud / 3DGS 重建精度为主要科研目标；
- 纯 Spatial QA / Memory QA / 文本 RAG；
- 大量人工规则 FSM / Scene Graph planner；
- 新的 VLN / path-planning / navigation policy；
- 从全量 BEHAVIOR-1K 1000 tasks 起步；
- 在 0-SR 或高度不稳定 baseline 上用 RL/RECAP“救模型”；
- 把 Done Head 作为项目主线；
- 一次同时切换基础模型、Memory、Agent 与 Environment，导致无法归因。

## 4.3 项目原则

1. **执行任务优先**：Memory benchmark 只做内部诊断。
2. **功能保持优先**：新增条件接口优先 zero-init/gated/function-preserving。
3. **一次一个变量**：关键实验总量 ≤20。
4. **先 Foundation，再 Local，再 Global，再 Planner/Agent**：R01–R06 未通过前不归因 Memory。
5. **Local/Global 分责**：Local 压缩近期时间状态；Global 组织长期空间证据；不把 Global 简化成“更长的 Local”。
6. **Optional modality**：Local/Global 可存在或缺失；训练时人工 routing，Agent 阶段 Planner routing。
7. **Memory 必须进入任务路径**：不能只在 auxiliary probe 上有效。
8. **状态更新与参数学习分离**：推理在线更新 Memory state/store，但模型参数不逐步反向传播；慢循环训练另行进行。
9. **Region/Place 不提前造系统**：只有多房间瓶颈真实出现后再引入层级地址。
10. **证据成熟度治理**：极新模型/论文区分事实存在与工程可依赖。

# 第五章 总体技术路线

## 5.1 概念闭环

```text
Task / Goal
    ↓
Current Observation
    ├──→ Temporal Local Evidence → learned Local Memory ─────┐
    │                                                        │
    └──→ Spatial Global Store update / query → Global Memory ├→ World / Action
                                                             │
Planner/Reasoner ── MemoryRequest(use/query/budget) ─────────┘
    ↓
Robot Action → New Observation → Local/Global update
```

Local/Global 可选；Planner 不请求时对应模态不进入模型。

## 5.2 Temporal Local Memory

Local 是受控容量的 learned temporal world state。核心要求：RGB/depth/pose/state/wrist/action 先按 source timestamp 对齐，再压缩；write/read/compression 可被 world/action loss 优化；完整 episode 不要求全程 BPTT。

## 5.3 Spatial Global Memory

Global 是长期 persistent spatial store + retrieval，不要求 Region/Place。底层候选由 RGB semantic、oVDA depth/geometry、camera pose/trajectory、view direction、timestamp 等构成；当前决策只把检索后的少量关键 patch/key-view/feature 送入 World/Action。

## Stage 1：LIBERO — Temporal Local Memory 最小闭环

目标：
- 使用成熟成功策略；
- 添加 Local learned temporal memory path；
- 证明接入不破坏 baseline；
- 在 memory-dependent task 上证明近期/中期历史被真实使用；
- 完成 Local Zero/Shuffle/Stale/Truncated 与 longer-history control。

普通 LIBERO 主要承担 no-regression；LIBERO-Mem / RoboMME 或等价受控任务承担 memory-dependent 收益验证。

## Stage 2：Spatial Global Memory — Store / Retrieval / Modality

目标：
- 基于 historical semantic/visual + depth/geometry + camera pose/trajectory/time 构建 persistent spatial store；
- 通过 current pose / semantic query / task context 检索 Top-K key patch/key-view/feature；
- 通过独立 Global modality 进入 World/Action；
- 做 Global Zero/Shuffle/Wrong-view/Stale/Top-K 与 simple keyframe control；
- 做 Local-only / Global-only / Both。

当前 **不要求 Region/Place 分区**，但 Spatial Global Store 本身已经进入主线。

## Stage 3：RoboCasa365 — Local / Global transfer

先建立无 Memory baseline，再分别 +Local、+Global、+Both。重点验证 state change、out-of-view、multi-stage manipulation、空间重访/参考与 downstream execution gain。RoboCasa action/domain adaptation 与 Memory 变量分开。

## Stage 4：Planner / Agent-ready Memory Interface

通过稳定 `MemoryRequest` 决定：
- 是否请求 Local；
- 是否请求 Global；
- Local horizon/token budget；
- Global semantic/spatial/time query 与 Top-K。

Goal Memory only if task-progress 缺口明确；随后跑通最小 subgoal→MemoryRequest→policy→verifier/re-observe vertical slice。

## Stage 5：BEHAVIOR-1K 小子集 — Region/Place hierarchy 决策 Gate（Target）

只有 Stage 1–4 达到 Go 条件后进入。若单一 Spatial Global Store 在真正多房间任务中出现容量、aliasing 或跨区域检索冲突，再研究 Region/Place hierarchy、层级 addressing、revisit/stale；不研究新的导航算法。

# 第八章 预期成果、技术贡献与创新层级

PSM-WMA 的成果按“系统成果 → 工程贡献 → 方法增量 → 条件性学术创新”分层管理。任何一层都不得为了追求下一层而牺牲前一层的可运行性。

## 8.1 系统成果：当前 PSM-WMA 闭环

```text
Observation
├→ Temporal Local Memory
├→ Spatial Global Store / Retrieval
└→ Planner MemoryRequest (optional routing)
        ↓
Local / Global optional conditions
        ↓
action-conditioned World State → Action
        ↓
Environment feedback → Memory update
```

## 8.2 工程贡献：可复用 Persistent Memory 平台

形成统一的：
- multi-sensor temporal alignment / history replay；
- Temporal Local store/update/read；
- Spatial Global store/retrieval/provenance；
- Local/Global independent modality adapters；
- optional-modality `SequencePlan` / `MemoryRequest`；
- Local/Global intervention；
- LIBERO / RoboCasa / future BEHAVIOR adapters；
- cache、logging、profile、checkpoint、reproducibility。

## 8.3 候选方法增量：只选 1–2 个做深

候选包括：
1. 多源时间对齐的 fixed-budget Temporal Local compression/update；
2. explicit/semi-explicit Spatial Global store + action-relevant retrieval/compression；
3. Local / Global 独立 optional-modality injection；
4. Local/Global complementary routing；
5. stale-aware temporal/spatial state update。

Region/Place hierarchy 不占当前实验预算。

## 8.4 评测贡献：Action Utility First

明确区分：

- Memory 中是否有信息；
- 模型是否读取了 Local / Global Memory；
- Memory 是否改变 future/world state；
- Memory 是否改变 action；
- 是否最终改善 task execution。

当前使用 Local Zero/Shuffle/Stale/Truncated 与 Global Zero/Shuffle/Wrong-view/Stale/Top-K 等；Region/Place 层级 Wrong-region 延后。

## 8.5 系统架构贡献：Temporal State / Spatial State / Planner-Experience 分责

- Temporal Local Memory：近期多模态 temporal world state；
- Spatial Global Memory：长期空间结构化 store + retrieval；
- Goal Memory：仅在 task-progress 缺口明确时作为 Target；
- Experience Memory：Agent success/failure / skill-level trace；
- Region/Place hierarchy：BEHAVIOR 后按需增加。

该分责避免构建一个不可解释的“万能 Memory”。

## 8.6 后续扩展：Continual / Proactive

在线 PSM state update、批次 Policy/World Model post-training、以及更慢的 Planner/Skill evolution 分离。只有主闭环稳定后，才探索 real + imagined experience 的持续演进和 Proactive Agent。

## 8.7 学术创新声明原则

立项阶段不写“首次提出”“首个”等强 novelty 语句。最终论文级贡献必须同时满足：

1. `01_technical_survey.md` 未发现直接覆盖的最近邻；
2. `02` 中有清晰可控的对照实验；
3. 方法变量在至少一个 downstream / closed-loop 指标上有可重复增益；
4. 增益不能简单归因于更多参数、更多历史帧或额外数据。

若未达到上述条件，项目仍可按系统研发成果验收，不影响项目成立。


---

# 第九章 实验与评测原则

## 9.1 实验预算治理

关键训练实验总量 ≤20 组。立项阶段只冻结预算与优先级，不预分配具体 E 编号；完整实验矩阵由 `02_detailed_design.md` 冻结。预算按四个层级使用：

1. **Baseline / Temporal Local / Intervention**：先证明 learned temporal state“会压缩、会更新、会用”；
2. **Spatial Global / Retrieval / Intervention**：验证结构化空间历史与关键视角检索是否形成额外 world/action 收益；
3. **RoboCasa365 Local/Global + WAM**：验证双模态 memory-conditioned world/action 的 downstream 执行价值；
4. **Planner/Agent / Goal Memory Target / BEHAVIOR Regional / Continual**：只在前序 Go 条件满足后使用剩余预算。

不得为了补结果无限增加组合实验，也不得让条件触发阶段反向挤占 Must-have 的复跑与消融预算。

## 9.2 一次只验证一个核心假设

禁止同时：

- 换基础模型；
- 换数据集；
- 新增 PSM；
- 新增 Agent；
- 修改 action head；
- 加 RL。

每次实验必须能回答一个明确问题。

## 9.3 Memory Intervention 必须成为主评测

**Local**：Normal / Zero / Shuffle / Stale / Truncated。  
**Global**：Normal / Zero / Shuffle / Wrong-view / Stale / Top-K truncation。  
**组合**：Local-only / Global-only / Both / Neither。

所有 content intervention 保持相同 tensor shape/index/计算路径；`modality absent` 通过 presence flag 单独验证，与 zero content 区分。Region/Place 的 Wrong-region 只在后续层级 Global 阶段定义。

## 9.4 Function-preserving 接入

新增 PSM/WAM branch 优先采用 gated/residual/zero-init，使初始行为可恢复 baseline。旧失败经验表明，不应让尚未验证的未来分支一开始完全接管动作输出。

## 9.5 成本指标

除 SR 外，记录：

- latency；
- GPU memory；
- memory footprint；
- retrieval time；
- token budget；
- throughput；
- storage/cache cost。

PSM 的价值必须包含“长期信息能力 / 成本”的权衡。

---

# 第十章 项目资源与周期

## 10.1 资源约束

按 v3.2.2 固定：

- 研究者：单人串行；
- 训练资源：1–8×A100 80GB；
- 开发：单卡 RTX 4090；
- 关键实验：≤20 组；
- 一次只验证一个核心假设。

不设置多人 FTE、招聘计划或虚构预算。

## 10.2 建议项目周期

建议采用 **12 周基线周期**，主线顺序固定为 Foundation → Local → Global → RoboCasa → Planner/Agent；Goal Memory 为条件 Target，Region/Place hierarchy 后置。

### 第 1–3 周：G0 Foundation
R01–R06：官方 checkpoint、Action contract、LIBERO forward/tiny-overfit/closed-loop baseline。

### 第 4–5 周：Temporal Local
R07–R09 + E002–E004：多传感器时间对齐、learned compression、Local intervention、longer-history control。

### 第 6–7 周：Spatial Global
R12/R13 + E005–E007：oVDA/geometry source、persistent spatial store、Top-K retrieval、Global modality、Local/Global complementarity。

### 第 8–9 周：RoboCasa
建立无 Memory baseline，再分别 +Local、+Global、+Both。

### 第 10 周：Planner routing
把人工 `has_local/has_global` 替换成 `MemoryRequest`；Goal Memory only if task-progress 缺口明确。

### 第 11 周：Reasoner Agent thin slice
subgoal → MemoryRequest → policy → verifier/reobserve/retry。

### 第 12 周：复跑与交付
完成 intervention、成本、负结果、demo、文档冻结；不强行进入 BEHAVIOR / Region hierarchy。

# 第十一章 主要交付物

## 11.1 文档

1. `00_project_proposal.md` — 项目立项书；
2. `01_technical_survey.md` — 技术调研报告；
3. `02_detailed_design.md` — 详细设计说明书；
4. 实验日志与结果报告；
5. 风险/负面结果记录；
6. 最终项目总结；
7. 系统架构与关键数据流说明；
8. 可用于内部评审/技术展示的 10 分钟级 demo 脚本与结果说明。

## 11.2 工程

- PSM-WMA 独立 module/framework namespace；
- Temporal Local Memory；
- Spatial Global Memory store/retrieval；
- Local / Global optional modality adapters；
- Planner-facing MemoryRequest interface；
- sequence adapter / temporal alignment / receding-horizon runtime；
- intervention framework；
- benchmark / embodiment adapters；
- Agent harness（条件达到后）；
- cache / logging / evaluation tools；
- BEHAVIOR Regional PSM 仅保留 deferred interface，不在当前实现清单。

## 11.3 模型与实验资产

- baseline checkpoint manifest；
- PSM checkpoints；
- latent/depth caches；
- experiment configs；
- evaluation results；
- reproducibility scripts。

## 11.4 展示

至少形成一个可重复演示：

- 机器人先观察环境；
- 目标/状态离开视野；
- Memory 保留并在重访/后续操作时被检索；
- 环境变化后旧状态被更新；
- 使用 Memory 的策略与 Zero/Stale Memory 出现可观察差异。

---

# 第十二章 风险与降级路径

## 12.1 基础模型 / 工程框架风险

**风险**：候选统一 World-Action / Reasoner 模型可能在推理、后训练、closed-loop、资源成本或 embodiment 适配上不稳定。  
**处理**：技术调研必须先做多路线比较；最终选定方案仍需通过官方推理、action/state contract、短训练 smoke、closed-loop 非零且可重复等 Runtime Gate。失败时回退到调研报告中已登记的成熟方案，不允许把 PSM 与某个极新模型绑定为单点依赖。

## 12.2 Spatial Observation 风险

**风险**：输入空间表征本身不稳定，导致 Memory 学不到几何/对应关系。  
**处理**：Spatial probe 区分“看错”与“记错”；必要时比较 depth cue / geometry encoder / StreamVGGT 等对照，但不把几何模块扩展成独立大项目。

## 12.3 隐式 PSM 被模型绕过

**风险**：主干容量足够大，Memory 只成为无效旁路。  
**处理**：强制 intervention；检查梯度、readout、attention/gate；两轮 read/write/loss/injection 修正后仍无法证明使用，则优先回退更简单 Local history / Global key-view-hybrid 或 zero-gated injection；不提前引入 Region/Place hierarchy。

## 12.4 Local / Global 职责或检索混叠

风险：Local 退化成长窗口缓存；Global 退化成无结构 keyframe dump；两个模态保存重复信息；Global retrieval 被相似视角/旧状态误导。

治理：
- Local-only / Global-only / Both / Neither；
- Local longer-history control；Global keyframe/location-only control；
- Local Zero/Shuffle/Stale/Truncated；Global Zero/Shuffle/Wrong-view/Stale/Top-K；
- Global 保存 source pose/time/view/provenance；
- Planner routing 与 Memory 内容构建分离。

Goal Memory 若后续启用，必须证明它解决 task-progress，而不是复制 Local/Global。

## 12.5 Dynamic State 更新错误

**风险**：旧状态长期保留，反而误导 action。  
**处理**：stale-memory intervention、environment-change update、same-region overwrite；必要时保留 recency/confidence/pose 等轻量 meta key，但不发展复杂人工 version FSM。

## 12.6 World Model 提升预测但不提升任务

**风险**：future loss 下降，但 SR/action 不变。  
**处理**：降低 auxiliary future 的主导地位，优先验证 memory-conditioned action / candidate evaluation / verifier；若长期无 downstream gain，不把该 World Model 作为主贡献。

## 12.7 Agent 掩盖底层失败

**风险**：依靠 Prompt/retry 堆叠掩盖不稳定 policy/PSM。  
**处理**：Agent 进入条件是底层已有稳定非零 closed-loop；失败必须优先定位 world state / policy / execution，而不是继续加 Prompt。

## 12.8 BEHAVIOR 工程复杂度

**风险**：仿真、任务 reset、导航、技能本身占用过多时间。  
**处理**：只选 small subset；导航栈固定；若底层执行未稳定，BEHAVIOR 降为集成验证而非硬性算法增益来源。

## 12.9 Continual / RL 风险

**风险**：reward 不可靠、WM hallucination、0-SR base 使后训练无意义。  
**处理**：主闭环前不进入 RL；imagined rollout 需要 reliability gate；持续演进不挤占 ≤20 组主实验预算。

## 12.10 License / 开源成熟度风险

**风险**：极新工作代码未放出、许可证不适合内部/商业使用。  
**处理**：建立证据成熟度与 license ledger；候选技术进入工程前逐项核验，论文存在不等于可直接依赖。

---

# 第十三章 Go / No-Go 与验收标准

本章在立项阶段冻结 **验收维度与 Go/No-Go 逻辑**，不冻结“提升多少百分点”“干预差异多少”等具体数值阈值。量化门槛必须在 baseline、数据规模、rollout 数与统计方差完成核验后，由 `02_detailed_design.md` 统一冻结；不得在立项书中以未经实测的数字形成虚假承诺。

## 13.1 Stage 1 — Local PSM Go

**Go：**

- baseline 功能保持；
- Local PSM 能稳定 update/read；
- intervention 对 future/action 有可解释影响；
- 至少一个 memory-dependent 情境优于 short-history baseline。

**No-Go：**

- memory zero/shuffle 几乎无影响；
- 增益只来自更多参数/更多帧；
- policy 被新分支显著破坏且无法恢复。

## 13.2 Stage 2 — Spatial Global Go

**Go：**
- Global store 可持续构建且 source/provenance 可追踪；
- retrieval Top-K 有界、与当前 pose/query 有解释性；
- Global intervention 对 future/action 有可解释影响；
- 至少一个 out-of-view / revisit / spatial reference 情境优于 no-memory 或简单 keyframe control。

**No-Go：**
- 只能改善 map/probe，action/world 不使用；
- retrieval 与 current decision 无关；
- 增益来自更多视觉帧而非空间结构。

## 13.3 Stage 3 — RoboCasa Local/Global Go

**Go：**
- 无 Memory baseline 稳定非零；
- Local 或 Global 至少一类产生可重复 execution gain；
- Both 的结果能解释互补/冲突；
- stale memory 不系统性误导策略。

**No-Go：**
- 只提高 auxiliary future/probe；
- downstream 无收益；
- 依赖 Agent/RL 才能从 zero-SR 工作。

## 13.4 Planner / Agent Go

**Go：**
- `MemoryRequest` 稳定控制 Local/Global presence/query；
- 至少一条 subgoal→memory routing→policy→verifier/reobserve 跑通；
- Planner 不直接重写 Memory store 或低层 action。

Region/Place hierarchy 只在 BEHAVIOR 后重新 Gate。

## 13.5 最终项目验收

项目完成验收至少应满足：

- 一条可运行、可重复执行的 PSM-WMA closed-loop；
- 一套可复现的数据、模型、Memory 与评测 contract；
- 一组完整的基础 Memory Intervention 结果；
- **至少一个执行相关场景中出现可重复正向收益**，收益应落在 action、任务推进、失败恢复、长期历史利用或 closed-loop SR 等指标之一，不能只来自 auxiliary probe / future reconstruction；
- Temporal Local + Spatial Global 两个 optional modality 与最小 Planner/Agent vertical slice 跑通，并有明确接口和日志；Region/Place hierarchy 不属于当前硬验收；
- 资源、延迟、显存、memory footprint 与主要工程成本分析；
- 完整 `00/01/02` 文档链、复跑脚本和关键失败路径诊断。

如果经过规定的两轮修正和 fallback 后仍没有执行相关正向收益，则该阶段可以形成高质量负面技术结论与资产交付，但应标记为 **Partial / No-Go**，不等同于完整项目成功。具体量化阈值、rollout 数量与统计判定方式由 `02_detailed_design.md` 在 baseline 方差核验后冻结。

---

# 第十四章 后续技术调研报告必须解决的问题

立项书只冻结“做什么、为什么做、做到什么算成功”，以下问题必须留给 `01_technical_survey.md` 研究后再冻结。

## 14.0 最近邻差异与可复用资产（强制项）

`01` 的首要任务不是证明 PSM-WMA “没人做过”，而是建立 **Build / Reuse / Adapt / Compare** 决策表。至少逐点比较以下最近邻：

**Temporal / episodic memory + WAM/VLA**
- MemoryVAM；
- MemoryWAM；
- MemoryVLA / MemoryVLA++；
- DiM-WAM；
- HiMem-WAM；
- LIBERO-Mem / Embodied-SlotSSM。

**Spatial memory → World / Action / Agent**
- Mem-World；
- SOMA；
- HoloAgent-0；
- Video World Models with Long-term Spatial Memory；
- Mirage；
- MosaicMem。

**Dynamic / stale memory**
- When Memory Lies；
- 其他具有 overwrite / conflict reconciliation / memory invalidation 的方案。

**Diagnostic / benchmark**
- LIBERO-Mem；
- RoboMME；
- RMBench；
- SpaMEM；
- LMEE-Bench；
- 3DMem-Bench。

每项至少核对：

- memory content：frame / event / object / latent / 3D / spatial state；
- addressing：time/event vs pose/place/region/spatial key；
- hierarchy：temporal hierarchy 还是 spatial hierarchy；
- update：append/compress/merge/overwrite/invalidate；
- injection：world model / online action / agent；
- closed-loop：是否真正用于执行，还是只做 generation / evaluation；
- attribution：zero/shuffle/stale/wrong-region 等已有证据；
- code/data/license/资源成本；
- 可直接复用资产与本项目仍需自研的最小部分。

重点回答三个工程问题：

1. **Mem-World** 的 spatial memory + action-conditioned world model 能否直接作为 Global/World 分支参考或 baseline，而不是重复设计；
2. **SOMA / HoloAgent-0** 的 spatial refinement、retrieval 与 Agent integration 哪些可以直接借鉴；
3. **MemoryVAM / MemoryVLA++ / DiM-WAM** 的 memory→world/action 接口是否可复用到 Cosmos 系或当前稳定 policy 上。

`01` 完成后，应把所有候选能力归类为：**直接复用 / 轻量适配 / 需要自研 / 暂不做**。只有“需要自研”且确有 downstream 价值的部分才进入项目方法创新清单。

**流程门禁**：`01_technical_survey.md` 必须提供 Detailed Design 启动 Gate。承重的模型/数据/接口/许可证/资源项若未核验，不得在 `02_detailed_design.md` 中冻结为硬依赖；无法核验时必须先给出 fallback，再允许进入对应阶段详细设计。

## 14.1 World-Action / Reasoner 技术路线

技术调研报告必须比较至少以下路线，而不是在立项阶段预设答案：
- 成熟 VLA + 模块化 latent World Model；
- 视频世界模型 + 独立 Action module；
- feature/latent dynamics world model；
- 原生统一 World-Action Model；
- 同时具备 Reasoner 与 World-Action generation 的统一模型。

必须回答：
- 哪条路线最少引入与 PSM 无关的结构变量；
- world representation 是否真实进入 action path；
- action 是否是原生 modality 还是外挂 head；
- 是否支持多 embodiment/action contract；
- Reasoner 能否承担低频 Agent / verifier；
- 训练、推理、许可证与 1–8×A100 80GB 资源是否可控；
- 主方案与 fallback 分别是什么。

最终具体模型、checkpoint、代码母体与 adaptation plan 由 `01_technical_survey.md` 冻结，再由 `02_detailed_design.md` 落到接口、shape、loss 和 Runtime Gate。

## 14.2 Spatial Observation

- RGB vs RGB+Depth；
- depth map vs depth feature；
- learned depth 统一 oVDA；
- StreamVGGT / D4RT 的实际价值；
- pose/camera metadata 的最低需求。

## 14.3 Temporal Local Memory

- main/wrist RGB、depth、pose、state、executed action 的时间对齐；
- evidence encoder / temporal compressor / recurrent state 的 shape 与 token budget；
- update frequency / TBPTT / detach / stable update；
- stale / overwrite；
- Local intervention 与 longer-history control。

## 14.4 Spatial Global Memory

- Global raw store 保存 RGB semantic、oVDA depth/intermediate、pose/trajectory/time 中哪些字段；
- spatial organization/fusion 的最小形式；
- retrieval query、Top-K、provenance 与 freshness；
- GlobalSpatialEncoder / mapper；
- keyframe-only / geometry-only / semantic-only 对照；
- Global intervention。

## 14.5 Memory Injection / World-Action Coupling

- Local / Global 为什么分别建模为独立 optional modalities；
- 两类 mapper、modality embedding、position semantics；
- shared backbone 中如何同时影响 future/action；
- Native Modality vs Global→Vision Control vs zero-gated residual 的实现/成本比较；
- 如何防止模型绕开 Memory。

## 14.6 Planner / Goal / Agent Interface

- `MemoryRequest` 如何决定 Local/Global presence、query、token budget；
- Reasoner 如何只在事件级调用；
- Goal Memory 是否真的需要独立 persistent state，还是 goal-conditioned retrieval 已足够；
- Region/Place hierarchy 只在 BEHAVIOR 阶段重新决策。

## 14.7 Memory 监督与 Intervention

- action loss / future latent loss；
- Local Zero/Shuffle/Stale/Truncated；
- Goal Zero/Shuffle；
- future decodability intervention；
- 防止额外参数/更长历史造成伪增益。

## 14.8 Agent

- Harness VLA 等方案的可复用边界；
- frozen policy as primitive；
- planner/actor/verifier；
- Agent Experience Memory 与 Spatial State 的 joint retrieval；
- done/completion 判断；
- failure recovery。

## 14.9 Continual Evolution

- RECAP/LWD/RISE/WoVR/FPO 等适配条件；
- memory-conditioned critic；
- real vs imagined experience；
- world model reliability；
- co-evolution；
- replay 和 catastrophic forgetting。

## 14.10 Proactive Agent

- need/goal discovery；
- obligation/utility；
- Ask-or-Act；
- system/user principle；
- persistent world state 触发；
- 安全与误触发控制。

---

# 第十五章 立项结论

PSM-WMA 建议作为 **企业研发型完整系统项目** 推进。最新研究已经证明 temporal/episodic memory、spatial memory、world-model imagination、online action 与 Agent 的多种组合具有价值，因此当前重点不是继续扩大模块，而是把一条最小、可归因、可交付的 Memory→World→Action 闭环做稳。

当前 12 周主线正式收敛为：

```text
LIBERO:
Temporal Local Memory
→ Spatial Global Memory
→ Local/Global matched attribution

        ↓

RoboCasa365:
Temporal Local + Spatial Global
+ action-conditioned World/Action

        ↓

Planner/Agent thin slice
(+ Goal Memory only if task-progress gap is proven)
```

**Region/Place 划分与 Regional Global PSM 不属于当前阶段。** 只有进入 BEHAVIOR-1K / 真正多房间 mobile manipulation 后，才根据实际任务需求重新调研和设计 Place/Region、Spatial Address、Writer/Reader、revisit/stale。

项目硬成功条件是：
- stable baseline；
- Local Memory 真使用；
- world-model-trained / memory-conditioned representation 进入 inference action path；
- RoboCasa 下游执行收益；
- Spatial Global Memory 的长期空间任务价值与 Local/Global 职责可解释；
- Agent thin slice；
- 可复现工程资产、干预/消融与 demo。

方法层面只选择 1–2 个当前真正相关的增量做深，例如 Local temporal compression/update、Global spatial retrieval/compression、Local/Global 分责、optional-modality injection 或 stale-aware update。Region/Place hierarchy 的方法创新推迟到 BEHAVIOR 阶段。

路线纪律更新为：**先 Foundation、再 Local、再 Global、再 Planner/Agent；Goal Memory 条件触发；只有多房间层级需求真实出现后再 Region/Place hierarchy。** 不因未来模块“看起来完整”而提前增加系统复杂度。

基于问题价值、已有工程基础和明确降级路径，建议继续执行。

# 参考资料（立项阶段关键一手来源）

1. **PSM-WMA 研究准备清单与总体方案 v3.2.2（稳定版）**，2026-08-10，项目 Source of Truth。
2. Jiang et al., **MemoryVAM: Integrating Memory into Video Action Model for Robot Manipulation**, arXiv:2606.20679, 2026. https://arxiv.org/abs/2606.20679
3. Yang et al., **MemoryWAM: Efficient World Action Modeling with Persistent Memory**, arXiv:2606.20562, 2026. https://arxiv.org/abs/2606.20562
4. Chung et al., **Rethinking Progression of Memory State in Robotic Manipulation: An Object-Centric Perspective**（introducing LIBERO-Mem）, arXiv:2511.11478, AAAI 2026. https://arxiv.org/abs/2511.11478
5. **Video World Models with Long-term Spatial Memory**, arXiv:2506.05284, 2025. https://arxiv.org/abs/2506.05284
6. **Latent Spatial Memory for Video World Models (Mirage)**, arXiv:2606.09828, 2026. https://arxiv.org/abs/2606.09828
7. **MosaicMem: Hybrid Spatial Memory for Controllable Video World Models**, arXiv:2603.17117, 2026. https://arxiv.org/abs/2603.17117
8. **Harness VLA**, arXiv:2607.08448, 2026. https://arxiv.org/abs/2607.08448
9. Dai et al., **RoboMME: Benchmarking and Understanding Memory for Robotic Generalist Policies**, arXiv:2603.04639, 2026. https://arxiv.org/abs/2603.04639
10. Chen et al., **RMBench: Memory-Dependent Robotic Manipulation Benchmark with Insights into Policy Design**, arXiv:2603.01229, 2026. https://arxiv.org/abs/2603.01229
11. Liao et al., **SpaMEM: Benchmarking Dynamic Spatial Reasoning via Perception-Memory Integration in Embodied Environments**, arXiv:2604.22409, 2026. https://arxiv.org/abs/2604.22409
12. Wang et al., **Explore with Long-term Memory: A Benchmark and Multimodal LLM-based Reinforcement Learning Framework for Embodied Exploration**（LMEE / LMEE-Bench）, arXiv:2601.10744, 2026. https://arxiv.org/abs/2601.10744
13. Hu et al., **3DLLM-Mem: Long-Term Spatial-Temporal Memory for Embodied 3D Large Language Model**（introducing 3DMem-Bench）, arXiv:2505.22657, 2025. https://arxiv.org/abs/2505.22657
14. **LIBERO official project / benchmark**。https://libero-project.github.io/main.html
15. **RoboCasa365 official project / documentation / GitHub**, ICLR 2026；官方 2026-07-07 更新加入逐帧 subtask annotations。https://robocasa.ai/
16. **BEHAVIOR-1K official repository / benchmark**。https://behavior.stanford.edu/
18. Zheng et al., **Mem-World: Memory-Augmented Action-Conditioned World Models for Persistent Robot Manipulation**, arXiv:2606.18960, 2026. https://arxiv.org/abs/2606.18960
19. Li et al., **Spatial Memory for Out-of-Vision Manipulation in Vision-Language-Action (SOMA)**, arXiv:2605.22283, 2026. https://arxiv.org/abs/2605.22283
20. Zhou et al., **HoloAgent-0: A Unified Embodied Agent Framework with 3D Spatial Memory**, arXiv:2606.23565, 2026. https://arxiv.org/abs/2606.23565
21. Shi et al., **MemoryVLA++: Temporal Modeling via Memory and Imagination in Vision-Language-Action Models**, arXiv:2606.09827, 2026. https://arxiv.org/abs/2606.09827
22. Wang et al., **DiM-WAM: World-Action Modeling with Diverse Historical Event Memory**, arXiv:2606.27677, 2026. https://arxiv.org/abs/2606.27677
23. Sun & Zhang, **When Memory Lies: An Empirical Study of Spatial Memory Staleness in VLM Agents**, arXiv:2608.04574, 2026. https://arxiv.org/abs/2608.04574
24. Sun et al., **HiMem-WAM: Hierarchical Memory-Gated World Action Models for Robotic Manipulation**, arXiv:2606.10363, 2026. https://arxiv.org/abs/2606.10363
25. Shi et al., **MemoryVLA: Perceptual-Cognitive Memory in Vision-Language-Action Models for Robotic Manipulation**, arXiv:2508.19236, 2025. https://arxiv.org/abs/2508.19236


