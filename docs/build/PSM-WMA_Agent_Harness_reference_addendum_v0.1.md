# PSM-WMA Agent Harness 参考增补 v0.1

**日期**：2026-08-13  
**状态**：Reference Addendum / 非 G0 依赖  
**适用阶段**：W10 Planner dynamic modality routing、W11 Cosmos Reasoner Agent thin slice  
**论文**：arXiv:2608.11246（用户指定的后续 Agent 参考；题名、代码开放状态与实现细节在 W10/W11 启动前按 arXiv 一手页面再次复核）  
**链接**：https://arxiv.org/abs/2608.11246

---

## 1. 在 PSM-WMA 中的定位

该工作只作为 **后续 Agent / Planner / Harness 层**的设计参考，不改变当前 G0 Foundation、Edge-Policy-DROID -> LIBERO baseline、Temporal Local Memory 或 Spatial Global Memory 主线。

当前项目仍保持：

```text
Persistent Local / Global Memory
        +
Cosmos3 World-Action Model
        ↓
thin Agent / Harness
```

Agent 层负责低频规划、MemoryRequest、工具/技能编排、执行结果验证与失败恢复；不把项目改造成规则 FSM、纯 scene-graph planner 或外部大 Agent 替代 Cosmos3 WAM。

---

## 2. 后续重点参考点

### 2.1 Harness-first 的闭环执行抽象

后续 Agent 不直接重写底层 policy，而是把已有能力包装成可调用能力：

```text
Goal
→ Reasoner / Planner
→ structured subgoal + MemoryRequest
→ Local / Global retrieval
→ Cosmos3 Generator / Policy
→ Action
→ Environment
→ Evaluator
→ success / continue / failure(reason)
→ continue / replan / retry
```

该抽象适合 PSM-WMA，因为 Memory、World-Action Model、环境执行和 verifier 可以保持解耦，同时由 Agent 统一编排。

### 2.2 Scene / graph context 只作为 Agent-level abstraction

如果论文中的 scene-graph/context 机制在复核后确有价值，PSM-WMA 的优先映射方式是：

```text
Spatial Global Memory
→ query / retrieval
→ compact structured summary
→ Reasoner / Planner context
```

而不是：

```text
Spatial Global Memory
→ 被 scene graph 完全替换
```

连续空间记忆仍服务 Generator 的 world/action prediction；对象、位置、状态、关系等结构化摘要只服务低频 Agent reasoning。这样可以同时保留几何/视觉细节和 Agent 可读的符号级上下文。

### 2.3 Execution Evaluation / Exit-code-style feedback

W11 failure recovery 可把动作/技能执行结果统一成结构化状态，例如：

```text
SUCCESS
CONTINUE
FAILURE(reason, evidence, retryable)
```

必要时再细分：

```text
NOT_FOUND
UNREACHABLE
GRASP_FAILED
STATE_MISMATCH
MEMORY_STALE
NEED_REOBSERVE
```

这些状态不是手写任务 FSM，而是 Agent harness 的执行反馈接口。它们用于决定继续、重新观察、重新检索 Memory、重规划或重试。

---

## 3. 与现有 W10 / W11 的映射

### W10 — Planner dynamic modality routing

参考该类 embodied-agent harness 的思想，Planner 只输出结构化请求，不直接生成连续 memory tokens：

```text
Goal + current summary + memory metadata
→ Reasoner / Planner
→ MemoryRequest
    ├ use_local_memory
    ├ use_global_memory
    ├ query
    └ token_budget
→ SequencePlan
```

Local / Global 的连续 tokens 仍由 Memory 模块检索/编码后送入 Cosmos3 Generator。

### W11 — Cosmos Reasoner Agent thin slice

首版只做最薄闭环：

```text
Goal
→ Cosmos3 Reasoner / Planner
→ MemoryRequest + subgoal
→ Cosmos3 Generator / Policy
→ execute
→ evaluator
→ success / retry / replan
```

E014 重点验证：
- structured request 是否稳定；
- Memory presence 是否随任务需要改变；
- failure feedback 是否能触发合理 replan/retry；
- Agent 层是否带来长程闭环收益，而不是仅增加 prompt/规则工程。

---

## 4. 明确不做

该论文进入参考清单 **不意味着**：

1. R01-R09 提前加入 Agent；
2. 用 scene graph 替代 Spatial Global Memory；
3. 用 hand-written exit code / FSM 完成任务逻辑；
4. 把 Cosmos3 Generator 降级成只执行外部 Agent 指令的低层工具；
5. 引入新的 RL 路线挽救 zero-SR baseline；
6. 在 R06 PASS 前增加 Agent 工程变量。

---

## 5. 启用条件

只有在以下条件满足后才进入具体实现评估：

```text
R06 Edge-Policy-LIBERO PASS
→ Local / Global 机制完成基本归因
→ RoboCasa embodiment 可运行
→ W10/W11 启动
```

W10/W11 启动前重新核验 arXiv:2608.11246 的一手论文页面、项目页/代码（若公开）、实际 scene/context 与 execution-evaluation 接口，避免把当前研究笔记中的二手概括当成冻结事实。

---

## 6. 当前结论

**保留为后续 Agent Harness 高优先级参考，但不改变当前执行顺序。**

最值得 PSM-WMA 吸收的不是另一套 Agent 主体，而是三类接口设计：

```text
persistent context → Agent-readable abstraction
skills/tools        → harness orchestration
execution result    → structured verification / recovery
```

这与 PSM-WMA 当前“Memory + World-Action Model 为主体，Agent 只做薄层 orchestration”的路线兼容。
