# R09-B-TTT v0.3.2 multi-slot CPU algorithm implementation design v0.1

**日期**：2026-09-03  
**状态**：REVIEW；仅在三方针对本文件所在 root SHA 给出同 SHA implementation approval 后才可编码  
**适用分支**：根仓 \`V2\` / 子模块 \`cosmos-framework\` \`v2\`  
**上游 authority**：\`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md\`，root \`ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3\` / Gitlink \`cf52f43dc328d4c8eec51923d66835125664dee5\`  
**现有最小核**：\`ContinualTTTLocalMemoryCore\`（仅 \`K_local=1\` compatibility core）  
**本 Gate**：\`G0-R09-B-TTT-V032-MULTI-SLOT-CPU-DESIGN\`

> 本文件冻结下一步 **CPU-only algorithm-core** 的最小扩展，不是 Cosmos runtime 接入设计。它不授权 attention、Memory Prefix pack、\`local_memory2llm\`、LayerNorm、RoPE、loss/chronology、配置/optimizer/checkpoint migration、GPU、训练、评测、推理或 P4/P5。

---

## 1. 目标、边界与判定

### 1.1 目标

在已有 per-sample continual KVB fast-weight MLP 的基础上，使 \`K_local\` 成为 construction-time 正整数。每个 causal timestep 仍只作一次 K/V write；write 后用同一份 \`W_t\` 对 \`K_local\` 个 query slots 作纯读，得到：

\`\`\`text
e_t                 [B,D_e]
K_t, q_base,t, V_t  [B,D_ttt], [B,D_ttt], [B,D_local]
Q_t                 [B,K_local,D_ttt]
M_t                 [B,K_local,D_local]
\`\`\`

\`M_t\` 是 CPU core 输出，不是生产 attention 的 token pack。后续独立 source/ABI audit 才能冻结：

\`\`\`text
[B,K_local,32] -> local_memory2llm -> [B,K_local,2048]
-> modality embedding -> Memory pre-attention LayerNorm -> K_MEM/V_MEM.
\`\`\`

### 1.2 允许的下一实现变更

仅允许在子模块的下列相邻文件内实现并测试本设计：

\`\`\`text
cosmos_framework/model/generator/mot/local_evidence.py
cosmos_framework/model/generator/mot/local_evidence_test.py
\`\`\`

实现提交必须先在子模块 \`v2\` 推送；之后根仓只能提交 Gitlink、审核证据及状态记录。

### 1.3 明确禁止

- 不改 \`edge_model_config.py:44\` 的 \`joint_attn_implementation="two_way"\`，也不接入任何 attention/runtime；
- 不新建 \`local_memory2llm\`、modality embedding、LayerNorm、K/V projection、position/RoPE/mask；
- 不改训练 sample、loss、TBPTT 调度、optimizer、checkpoint/配置 schema；
- 不执行 torchrun、GPU、训练、评测、推理或真实数据/cache 读取。

PASS 是 C2 CPU implementation 在批准范围内、全部定向 CPU test 通过、静态检查通过、三方同 SHA closure verdict 齐全。任一 runtime/训练 surface 被改动、K/V 按 slot 重复 update、或三方结论不齐均为 FAIL/REVIEW，禁止进入下一 Gate。

---

## 2. 已复用的基线与不变量

### 2.1 既有入口

- \`local_evidence.py:259-265\`：\`ContinualTTTFastState\`，固定为四叶 per-sample fast pytree；本 Gate 不增加 state field。
- \`local_evidence.py:268-315\`：\`ContinualTTTLocalMemoryCore\` 与慢参数 \`key_proj/query_proj/value_proj\`、learned W0。
- \`local_evidence.py:336-389\`：W0 clone、state validation 与两层 fast MLP \`D_ttt -> D_ff -> D_local\`（SiLU）。
- \`local_evidence.py:391\` 起：现有 \`step_projected\` 的逐样本 functional higher-order KVB update；它是一次 write 的复用源。
- \`local_evidence_test.py\` 的 K=1 手工 KVB、inert row、reset/detach、scan、gradient、输入拒绝和 state payload tests。

### 2.2 必须保持的算法不变量

1. fast-weight 结构继续为每个样本独立的二层 MLP：\`64 -> 128 -> 32\`、SiLU、四个 fast tensor；默认数值/行为由现有 \`K_local=1\` core 定义。
2. \`W0\`、\`theta_K\`、\`theta_Q\`、\`theta_V\` 是 slow learned parameter；fast state 是显式携带数据，不进 \`state_dict()\`。
3. 对每个 valid sample/timestep，只有一次 \`torch.autograd.grad(L_inner, W)\` 和一次 \`W_{t-1}->W_t\`。\`L_inner\` 只使用 K/V：\`mean((f_W(K_t)-V_t)^2)\`；Q 与 slot query 不得进入它。
4. 新 read 一律用更新后的 \`W_t\`。read 是纯函数，不变更 W、进度、或任何隐式状态。
5. invalid row 的四叶 state 精确不变；其 multi-slot token 是 \`[K_local,D_local]\` 全零，\`present=False\`。
6. 继续在 ordinary grad mode 做 update；禁止将多槽实现变成 \`no_grad\`/\`inference_mode\` 下的 silently detached update。
7. \`ttt_tbptt_steps\` 仍是正整数、默认 16（与 RoboTTT 对齐），只控制后续 caller 的 detach cadence；本 Gate 不改变其调度语义。

---

## 3. construction/checkpoint contract

### 3.1 新 construction 参数

\`ContinualTTTLocalMemoryCore.__init__\` 新增：

\`\`\`python
k_local: int = 1
\`\`\`

验证规则与其他维度一致：必须为非 \`bool\` 的正整数。\`k_local\` 是 model construction/checkpoint identity 的一部分，不是每个 \`step\`、\`scan\` 或 batch 的可变输入；因此同一实例不得在运行中切换 cardinality。

一个 checkpoint 只对应一个确定的 \`k_local\`。\`k_local=1/4/8\` 分别构造、分别训练、分别保存；不得把 \`K=1\` checkpoint 静默 broadcast 成 \`K>1\`，也不得把多槽 checkpoint 截断加载为单槽。形状不一致必须由标准 state-dict strict loading 报错。这个 Gate 不实现 migration adapter。

### 3.2 query slot 参数

新增慢参数，名称冻结为：

\`\`\`python
slot_queries: nn.Parameter  # [K_local, ttt_dim]
\`\`\`

\`query_proj\` 继续输出 shared evidence-conditioned base：

\`\`\`text
q_base = theta_Q(e)                         [B,D_ttt]
Q = q_base[:, None, :] + slot_queries[None] [B,K_local,D_ttt]
\`\`\`

初始化规则冻结如下：

- \`K_local == 1\`：\`slot_queries\` 精确 zero-init。这让新的 multi API 在相同 parameter values 下与现有单 query read 数值等价。
- \`K_local > 1\`：调用 \`nn.init.normal_(slot_queries, mean=0.0, std=1/sqrt(ttt_dim))\`。不同 row 由随机采样打破 slot permutation symmetry；slot 没有人工命名或固定语义。

新增参数是 deliberate checkpoint schema change；所谓 K=1 compatibility 仅指 step/read 数值与 API adapter，而不承诺旧 \`cf52f43\` state dict 的 strict load。若需要旧 checkpoint 迁移，必须另立 checkpoint Gate。

默认维度下 slow parameter count 从 \`53,568\` 改为：

\`\`\`text
53,568 + K_local * 64
K_local=1: 53,632
K_local=4: 53,824
K_local=8: 54,080
\`\`\`

fast-state 元素数严格保持 \`12,448\`/sample，不随 \`K_local\` 增长。

---

## 4. 冻结 API 与计算顺序

### 4.1 保留的 projection API

现有 \`project_evidence(evidence_t)\` 保持三元返回与形状：

\`\`\`python
(key_t, query_base_t, value_t)  # [B,D_ttt], [B,D_ttt], [B,D_local]
\`\`\`

这里第二项改名仅限局部变量/文档；不改变 tuple arity 或顺序。它不是 \`[B,K,D]\`，避免把 K/V 复制为 slots。

新增纯 projection：

\`\`\`python
project_queries(query_base_t: Tensor) -> Tensor  # [B,K_local,D_ttt], fp32
\`\`\`

它验证 \`[B,D_ttt]\`、\`float32\`、finite、device 与 \`slot_queries\` 相同；只执行 broadcast add，不 update state。

### 4.2 新的 multi-slot public API

新增：

\`\`\`python
read_many(
    query_t: Tensor,                 # [B,K_local,D_ttt], fp32 finite
    state: ContinualTTTFastState,
) -> Tensor                          # [B,K_local,D_local], fp32

step_projected_many(
    *, key_t: Tensor,                # [B,D_ttt]
    query_base_t: Tensor,            # [B,D_ttt]
    value_t: Tensor,                 # [B,D_local]
    state_in: ContinualTTTFastState,
    valid: Tensor,                   # [B]
    create_graph: bool,
) -> tuple[Tensor, ContinualTTTFastState, Tensor]

step_many(
    evidence_t: Tensor, state_in: ContinualTTTFastState, valid: Tensor,
    *, create_graph: bool = True,
) -> tuple[Tensor, ContinualTTTFastState, Tensor]

scan_segment_many(
    evidence: Tensor, valid: Tensor,
    state_in: ContinualTTTFastState | None = None,
    *, create_graph: bool = True,
) -> tuple[Tensor, ContinualTTTFastState, Tensor]
\`\`\`

返回 shapes 分别为 \`[B,K_local,D_local]\`、\`[B,T,K_local,D_local]\` 以及沿用的 present \`[B]\`/\`[B,T]\`。

\`read_many\` 必须逐 sample 复用 \`_fast_mlp\`，允许 query 的 slot 维一次进入线性层；不得 loop slot 并重复 inner update。实现可在一个 sample 内对 \`[K,D]\` 调用 \`F.linear\`，从而输出 \`[K,D_local]\`。

### 4.3 K=1 compatibility wrapper

既有 \`step_projected\`、\`step\`、\`scan_segment\` 名称、参数和返回 rank 均保留，且仅当 \`self.k_local == 1\` 时允许调用：

\`\`\`text
step_projected -> step_projected_many -> token[:, 0:1, :]
step           -> step_many           -> token[:, 0:1, :]
scan_segment   -> scan_segment_many   -> token[:, :, 0, :]
\`\`\`

当 \`k_local != 1\` 调用 legacy API 必须抛出清晰 \`ValueError\`，提示使用 \`*_many\`；不得悄悄只返回第 0 slot。\`K=1\` wrapper 的输出必须精确保持 \`[B,1,D_local]\` / \`[B,T,D_local]\`，且与 direct multi API 的对应 slice allclose。

### 4.4 一次 write、K 次 read 的精确伪代码

\`\`\`python
def step_projected_many(...):
    validate_all_inputs_before_any_update(...)
    queries = project_queries(query_base_t)  # no fast-state mutation
    for b in range(B):
        if not valid[b]:
            state_out[b] = state_in[b]
            tokens[b] = zeros(K_local, D_local)
            continue
        work = make_or_rebuild_grad_leaves(state_in[b])
        inner = mean((fast_mlp(key_t[b], work) - value_t[b]).square())
        grads = autograd.grad(inner, work, create_graph=create_graph)
        updated = work - inner_lr * grads       # exactly once
        state_out[b] = updated
        tokens[b] = fast_mlp(queries[b], updated)  # K reads after update
    return stack(tokens), stack(state_out), valid.bool()
\`\`\`

\`query_base_t\`/\`slot_queries\` 不得传给 \`inner\` 或 \`autograd.grad\` 的 target list。\`create_graph=False\` 仍可用于现有数值 equivalence test；正式 outer meta-gradient contract 在后续 training integration 中必须选 \`True\`。

---

## 5. CPU 定向验证计划（C2）

实现后只运行现成 isolated CPU selector；禁止 GPU/真实数据：

\`\`\`bash
cd /disk/rl/psm_wma/cosmos-framework
/disk/rl/starVLA/.venv/bin/python -B -m pytest \\
  -o addopts='' --confcutdir=cosmos_framework/model/generator/mot \\
  cosmos_framework/model/generator/mot/local_evidence_test.py \\
  -k 'continual_ttt' -q
\`\`\`

资源：CPU-only、无网络、无 checkpoint、无数据集、无 GPU。产物仅 pytest stdout；PASS 为所有既有及新增 \`continual_ttt\` tests 通过；FAIL 为任何 assertion/collection failure。随后只运行：

\`\`\`bash
cd /disk/rl/psm_wma
git -C cosmos-framework diff --check
git diff --check
\`\`\`

新测试最少覆盖：

| ID | 断言 |
| --- | --- |
| MS01 | \`k_local\` 只接受非 bool 正整数；\`1/4/8\` construction 与属性正确。 |
| MS02 | parameter/state_dict registry 精确含 \`slot_queries\`；slow count 为 \`53,568+64K\`，fast payload 恒为 12,448。 |
| MS03 | \`project_evidence\` 仍返回 base Q；\`project_queries\` shape、fp32/finite/device/slot-broadcast validation。 |
| MS04 | 对固定 state，\`read_many\` 与逐 slot 手工 \`f_W(q_base+r_k)\` 相等，且不改变任何 input state。 |
| MS05 | 以 mock/wrapper 计数 \`torch.autograd.grad\`：每个 valid sample 恰一次，与 \`K_local\` 无关；multi 与 K=1 同 K/V 输入的 \`state_out\` 相等。 |
| MS06 | multi read 使用更新后 W：手工 KVB update 后的 K 个 read 与结果相等。 |
| MS07 | invalid row state 精确不变、tokens \`[K,D_local]\` 为零、present false。 |
| MS08 | \`K=1\` 新 API 与 legacy \`step/step_projected/scan_segment\` 对应 slice 数值及 rank 等价；\`K>1\` legacy API fail-closed。 |
| MS09 | 置换 \`slot_queries\` row 时 token slot 同置换；只改变一个 query row 时其余 readout row 不变。 |
| MS10 | outer scalar 覆盖全部 slot 时，\`query_proj\`、\`slot_queries\`、K/V projections、四个 W0 都得到 finite nonzero gradient。 |
| MS11 | \`scan_segment_many\` 与逐 timestep \`step_many\` 一致，输出 \`[B,T,K,D_local]\`；state carry/reset/detach 原语不变。 |
| MS12 | 所有非法 shape/dtype/nonfinite/device/input 在任何 state change 前拒绝。 |
| MS13 | strict state-dict load 拒绝 K 不同的 \`slot_queries\` shape；不写迁移逻辑。 |

\`MS05\` 的 instrumentation 只能在 test 内临时 wrapper/mocking \`torch.autograd.grad\`，不得把 update counter 写进 fast state 或 production API。

---

## 6. Gate 路线与回填

### C1（本文件）

前置资产：v0.3.2 multi-slot architecture 对 root \`ef3ff1a\` 的三方批准。  
输入：本设计、现有 \`cf52f43\` K=1 core。  
输出：本设计所在 root commit 与三方同 SHA \`APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MULTI_SLOT_CPU_CORE\`。  
失败分流：任何 runtime/ABI、checkpoint migration、optimizer、训练需求移入后续 Gate；不扩张本 C1。

### C2（后续、独立申请）

前置资产：C1 三方批准。  
最小改动：仅 §1.2 两个子模块文件。  
输入：synthetic CPU tensors。  
输出：测试 stdout、child SHA、root Gitlink SHA、diff-check。  
PASS：§5 全覆盖与三方同 SHA \`APPROVE_TO_CLOSE_R09_B_TTT_V032_MULTI_SLOT_CPU_CORE\`。  
失败分流：数值/shape/gradient failure 限于同两文件整改并重新审核；任何接入需求转 C3。

### C3（未来 source/ABI audit，未授权）

只读冻结实际 \`local_memory2llm\` owner、\`[B,K,32]->[B,K,2048]\`、pre-attention norm、K/V-only insert、Memory/AR/DM packing、two-way varlen mask、position/RoPE、checkpoint/optimizer ownership；以有效 \`edge_model_config.py:44\` 为配置 anchor。C3 之后才可提出 runtime implementation 设计。

### C4+（未来，均未授权）

CPU runtime contract、chronology/outer-loss contract、配置与 optimizer/checkpoint refreeze、最小 GPU smoke、matched LIBERO latent-cache training 各自是单独 Gate；任一不得由 C1/C2 隐含解锁。

### 回填字段

C2 完成后在 \`SESSION.md\` / \`TODO.md\` 写入：child/root exact SHA、改变文件、selector/通过数、py_compile（如执行）、双仓 \`git diff --check\`、三方 verdict/时间、未执行的运行类验证及原因。不得把尚未获得的运行事实预写为 PASS。

