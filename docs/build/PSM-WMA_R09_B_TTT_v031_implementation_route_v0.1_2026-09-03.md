# R09-B TTT v0.3.1 当前代码实现路线 v0.1

**日期**：2026-09-03

**状态**：REVIEW；三方对同一 root SHA 批准前不得执行代码实现。

**任务**：`G0-R09-B-TTT-V031-ARCHITECTURE-ROUTE-REVIEW`

**设计 authority**：

- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md`
- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.1.md`
- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.md`
- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.1.md`
- `docs/build/PSM-WMA_R09_B_TTT_CPU_algorithm_implementation_design_v0.1_2026-09-03.md`

**评估基线**：root `4754f5bc25859894e6fc963a9484640ccb5cd082`；
`cosmos-framework` HEAD/Gitlink 均为
`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。

本文只冻结实施顺序和 source-audit 问题，不授权 GPU、训练、评测、推理、P4/P5 真实操作或
B2-T。

---

## 1. Codex 评估结论

v0.3.1 的架构方向可实施，并且比旧 Local-as-GEN-token 路径更严格地隔离历史条件与生成
query。建议接受以下核心合同：

```text
Memory = K/V-only read-only context
AR     = native causal Q/K/V, never reads Memory
DM     = native Q/K/V, reads [Memory, AR, DM]
```

但 v0.3.1 不是可以直接编码的 patch spec。以下四项必须先由 exact source audit 冻结：

1. Memory pre-attention norm 是每 block 独立还是 model-level 共享，以及 exact RMSNorm class/eps；
2. Memory K/V 复用每层 generator `k_proj_moe_gen/v_proj_moe_gen`，还是新增独立 projection；
3. Memory K 与 DM Q 的 position/RoPE 关系；首版 `K_local=1` 仍必须给出明确合同；
4. Memory-present warm start：即使 `K_MEM/V_MEM=0`，新增 softmax key 仍会改变分母，不能把
   zero adapter 自动解释为 function-preserving。必须显式选择“接受初始结构扰动”或另行冻结
   gate/logit-prior；不得在实现时临时决定。

此外，v0.3.1 中“已审核 CPU-core 设计继续有效”仅按“设计未被推翻”解释。CPU-core design
commit `216f1261c81cf6f2bd13053b5e937beeccd335b3` 尚未取得三方同 SHA verdict，当前不能视为
已批准实现。

## 2. 当前代码事实

| seam | 当前事实 | v0.3.1 差距 |
| --- | --- | --- |
| `data/generator/sequence_packing/packers.py:215-260,537-552` | Local 在 text 后被写入同一 sample，长度计入 full split。 | Local 必须退出 native AR/DM query pack；native sample/split/position 不应包含 Memory。 |
| `data/generator/sequence_packing/sequence.py:545-587,765-780,888-928` | Local 具有普通 span、sequence indexes 与 position ids。 | K/V-only context 应使用独立 per-sample token/offset metadata，不创建 native query indexes。 |
| `model/generator/mot/cosmos3_vfm_network.py:946-962` | adapter/embed 后 scatter 回 `packed_sequence`。 | 改为生成独立 Memory Prefix hidden payload，不能 scatter 为普通 token。 |
| `model/generator/mot/unified_mot.py:606-710` | attention 只投影 und/gen 两流并返回同形 query output。 | 每层需额外接收 Memory hidden，生成 K/V；不得生成 Q、output、residual 或 MLP。 |
| `model/generator/mot/unified_mot.py:1175-1178,1207-1256` | block 只有 AR/DM 两套 pre-attention norm 与两条 residual/MLP。 | 新 norm 只服务 Memory K/V；block 输出仍只有 AR/DM 两流。 |
| `model/generator/mot/attention.py:179-318` | `two_way_attention()` 的 AR pass独立；DM pass读取 native `[AR,DM]`。 | 首版应只扩展 DM 的 KV 输入，AR pass完全复用。 |
| `model/generator/mot/attention.py:649-681` | base dispatch 接受同形 packed Q/K/V；无 Memory Prefix 参数。 | 需新增显式 optional Memory K/V+offset metadata，absent 时走原函数原分支。 |

当前 LIBERO recipe 沿用 `model_config.py:220` 的默认 `joint_attn_implementation="two_way"`；
因此首版无需同时解决 `three_way`、NATTEN、FlexAttention 或 CP/Ulysses。

## 3. 推荐的首版最小架构

### 3.1 Memory 不进入 native `PackedSequence`

保留现有 `GenerationDataClean` / Local payload入口，但 packer输出应拆成：

```text
native PackedSequence: [AR, DM] only
MemoryPrefixContext:   per-sample [K_mem_tokens, hidden], offsets, present
```

`MemoryPrefixContext` 只描述 hidden payload与每 sample边界；不含 query indexes、native mRoPE
cursor、loss indexes或 updated hidden state。Global future slot通过同一 context中的顺序
`[Global, Local]` 预留，不创建空 tensor伪 token。

### 3.2 每层只生成 Memory K/V

首选候选是：每个 block 使用与 native block相同 family/eps 的独立 Memory RMSNorm，然后复用该
层 generator K/V projection与 head geometry：

```text
memory_hidden
 -> block.memory_input_layernorm
 -> block.self_attn.k_proj_moe_gen / v_proj_moe_gen
 -> K_MEM / V_MEM
```

不调用 `q_proj_moe_gen`，不构造 Memory output，不进入 `o_proj_moe_gen`、residual、post norm或
MLP。是否最终采用该候选，必须由 source audit核对 checkpoint/FSDP/初始化影响后冻结。

### 3.3 `two_way` DM 联合 softmax

首版建议扩展 dense `two_way_attention()`：

```text
AR pass: 原代码 exact unchanged
DM Q:    原 full_q
DM KV:   per sample concat [K_MEM, K_AR, K_DM]
```

使用一次 varlen `attention()` 完成 DM 联合 softmax，并构造相应 KV cumulative offsets。不要把
Memory作为 query pack，不要把它加入 native `sample_lens`，也不要用两个独立 softmax后直接相加。

不建议首版依赖 `merge_attentions()`：当前实现要求 NATTEN，且三路/反向/data-pointer合同会扩大
依赖与测试面。默认 LIBERO two-way dense路径可直接通过单次 KV concat表达 v0.3.1 数学。

### 3.4 首版兼容边界

- `MemoryPrefixContext is None`：调用现有 dispatch/attention路径，要求 exact parity；
- `joint_attn_implementation != "two_way"`：Memory present时 fail-closed；
- FlexAttention、NATTEN multi-dimensional、multi-control、CP/Ulysses、CUDA graph：Memory
  present时首版均 fail-closed，分别后续 Gate；
- 当前正式 Local 训练先维持 source audit已建议的单 rank / no-CP范围；不得把 CPU contract外推。

## 4. 必须由三方裁决的设计点

三方本轮应明确回答：

1. 是否同意 Memory 完全退出 native query pack，以独立 context进入每层 K/V；
2. 是否同意首版限定 default two-way dense路径，其余 attention/parallel modes fail-closed；
3. 是否同意 DM 采用单次 varlen联合 KV softmax，而不是独立 softmax简单相加；
4. 是否同意先做 exact source audit，再冻结 norm/projection/RoPE/warm-start细节；
5. 是否确认 `216f126` CPU core与 v0.3.1 正交，可在本路线三方批准后先行实现；
6. 是否同意 chronology/loss、Memory Prefix runtime、GPU smoke、inference state、optimizer/config
   authority继续分 Gate。

## 5. 冻结实施顺序

```text
Gate A  v0.3.1 architecture/route review（本 Gate）
  ↓ 三方同 SHA 批准
Gate B  continual-TTT CPU core implementation（只改 local_evidence.py + adjacent tests）
  ↓ CPU closure review
Gate C  v0.3.1 exact Memory Prefix source/ABI audit
  ↓ design review
Gate D  two-way Memory Prefix CPU attention contract implementation
  ↓ CPU closure review
Gate E  chronology + native outer-loss/state-owner integration
  ↓ CPU integration review
Gate F  bounded single-GPU train/validation/checkpoint-reload smoke
  ↓ runtime closure review
Gate G  inference request/state registry + W-only update smoke
  ↓ inference closure review
Gate H  optimizer/checkpoint/config/P3-P5 authority rebuild
  ↓ exact launch review
Gate I  LIBERO 4-in-1 Local Memory formal training
```

任何 Gate 的批准不自动授权后续 Gate。

## 6. 本轮 verdict 请求

请对本文所在 exact root SHA与
`cosmos-framework@21d064f2b7c7aeeb67cfee50ac8d6722a944eddb` 同时返回：

```text
APPROVE_R09_B_TTT_V031_IMPLEMENTATION_ROUTE
APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_CPU_ALGORITHM_CORE
```

或 `REQUEST_CHANGES`，必须带 severity 与 exact `file:line`。

批准只允许先执行 Gate B，并随后编写 Gate C source audit；不授权 Memory Prefix runtime实现、
chronology/loss、GPU、训练、评测、推理、optimizer/config refreeze、P4/P5真实操作或 B2-T。
