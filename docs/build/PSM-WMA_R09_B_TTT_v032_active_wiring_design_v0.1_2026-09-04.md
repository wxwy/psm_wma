# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.1

**状态**：待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：production runtime contract design v0.3（root `bc6ff9e`）与 implementation（root `78bb329`/Gitlink `4f857ea`）、config/optimizer/checkpoint design v0.2（root `93c9974`）与 implementation（root `994887d`/Gitlink `dce279a`）均已三方同 SHA 关闭。

## 1. 目标与总边界

把已关闭的 CPU contract 接入 active Cosmos 训练路径：唯一 production authority（`cosmos_framework/model/generator/mot/runtime_authority.py::ProductionRuntimeAuthority`）驱动物理 episode owner 的 `begin → admit → materialize → backward → commit/reset` 生命周期，输出经已存在的 active Memory Prefix 路径（`unified_mot.py:643`、`attention.py:276` None-bypass）进入 DM attention。默认关闭：`local_ttt_enabled=False` 时 composed config、参数集合、forward 行为与 No-Memory 逐位一致。本 Gate 只冻结**训练侧**接线；推理（inference-mode 前 W-only update）与 sequence-resume fast-state persistence 另起独立 Gate。

## 2. Config identity（继承 config design v0.2 §1）

`OmniMoTModelConfig`（attrs，`configs/base/defaults/model_config.py:298` 之后）新增字段：`local_ttt_enabled: bool = False`、`ttt_tbptt_steps: int = 16`、`ttt_inner_lr: float = 0.1`、`k_local: int = 1`、`runtime_evidence_steps: int = 1`。校验规则与 frozen `LocalMemoryConfig` 完全一致（正整数/有限正标量/`k_local∈{1,4,8}`/`runtime_evidence_steps` 固定 1、bool 拒绝）。`local_ttt_enabled=True` 必须同时满足 `local_history_enabled=True` 且 `local_history_backend="ttt_fast_weight"`，否则 fail-closed。experiment 经 env `PSM_R09_B_TTT_ENABLED` 注入，与 `PSM_R09_A1_ENABLED`/`PSM_R09_B1_TTT_ENABLED` 互斥（`action_policy_libero_edge_all.py:70-77` 模式）；TOML schema（`configs/toml_config/sft_config.py:28` `extra="forbid"`）不新增字段。上述值全部进入 config identity，漂移必须 strict-load 失败。

## 3. 唯一 owner 与对象 identity（继承 config design v0.2 §2）

`net.local_history_runtime`（`omni_mot_model.py:323`）保持唯一注册 owner。启用本 wiring 时其 `recurrent_backend` 属性必须就是 `ContinualTTTLocalMemoryCore` 实例（`local_evidence.py:268`；key/query/value projection、`slot_queries`、`w0_fast_*` 四件均为 nn.Parameter），`encoder` 为 `LocalEvidenceEncoder`；dormant stateless readout 不进入 selector。`ProductionRuntimeAuthority`（及 `ProductionLocalMemoryRuntime` seam）必须引用同一批 Python 对象，禁止从 config 重新实例化第二套 trainable Local module。authority 对象本身**不得**注册到 module tree（持有 fast `W_t`/pending/epoch/replay，按 v0.2 §3 不进 checkpoint）。`local_memory2llm`/`local_memory_modality_embed` 沿用 `cosmos3_vfm_network.py:227-229,284-291` 的现有注册。验收：`named_parameters()` exact inventory 与 `config_checkpoint_contract.SELECTORS` 四组一致、runtime 引用与注册对象 `is` 同一、无重复 trainable Local module。

## 4. 训练时序与 TBPTT 映射（继承 production design v0.3 §2/§3）

- owner identity 取自 `data_batch` 的 episode provenance key；同一 episode 跨 window 连续，episode 边界 `finish(terminal=True) → reset`（owner epoch+1）。
- 训练为 one-step evidence：每个 native window 经 `_inject_local_history` seam（`omni_mot_model.py:962-1019`）admit 一行 `R08_COMPLETED_CAUSAL` evidence（graph-free raw payload）。
- pending 行数达到 `ttt_tbptt_steps`（默认 16）或 terminal remainder 时 `materialize`（`create_graph=True` 一次性 scan 全 segment），当前 window 的 Memory Prefix token 取该 materialize 的 post-update read；中间 window 使用 detached state 的 K/V-only read，不建图。
- segment outer loss 严格按 v0.3 §2：`L_segment = sum(t∈I_s, L_task[t]) / max(N_valid_window, 1)`；trainer 每 micro-batch 单次 `loss.backward()`（`trainer/__init__.py:497`）即该 segment 唯一 backward；`commit` 在 `on_after_backward` callback 执行；跨 window 只 carry detached fast state；`N_valid_window=0` 禁止 backward/commit/optimizer step。
- evidence admission 不得改变 native packing/attention 语义：prefix payload 仍走 `packers.py:246-254` → `sequence.py` `pack_local_memory_prefix_payload` 现有 active 路径；`PackedSequence.local_memory_prefix is None` 时零开销旁路不变。

## 5. Optimizer exact membership（继承 config design v0.2 §2）

`PSM_R09_B_TTT_ENABLED` 时 `keys_to_select` 精确替换为冻结四组 selector（`local_history_runtime.encoder`、`local_history_runtime.recurrent_backend`、`local_memory2llm`、`local_memory_modality_embed`），取代 B1 列表（`action_policy_libero_edge_all.py:222-226`）。注意现有机制为子串匹配且非空时冻结未匹配参数（`utils/generator/optimizer.py:205-216`），该行为不变。验收必须对真实 composed model 用 `canonical_slow_inventory()` + `validate_exact_optimizer_membership()` 逐项证明 exact key set、对象 identity、无重复对象。

## 6. Checkpoint（继承 config design v0.2 §3）

slow 参数经 `net.state_dict(prefix="net.")` 自动进入 DCP（`omni_mot_model.py:4519-4564`、`checkpoint/dcp.py:85-96`），零额外收集代码；fast `W_t`/pending/epoch/replay 因 §3 的注册边界天然排除。strict-load 缺失/额外键 raise（`dcp.py:853-858`）与 config identity 漂移失败保持不变；恢复路径语义对齐 `strict_restore_into()` 的 same-object round-trip。真实 checkpoint I/O 的执行验证属于后续 GPU Gate，不在本设计授权范围。

## 7. Disabled parity 与验收（implementation Gate，CPU/static）

- `PSM_R09_B_TTT_ENABLED` 未设置时：composed config 与现状 diff 为空、`keys_to_select` 不变、不注册任何新 submodule、forward 无新分支（默认参数 `None`/False 旁路）。
- 实现验收（全部 CPU/static，无 GPU/真实 I/O/训练）：新 config 字段类型/范围/互斥校验矩阵；meta/CPU 构建 composed model 的 owner identity 与 exact inventory/selector membership；fake `data_batch` 生命周期 wiring（admit→materialize→backward→commit→reset、terminal remainder、零分母拒绝）；disabled parity 静态测试；py_compile 与双仓 `git diff --check`。

## 8. 允许范围与后续 Gate

设计批准后 implementation Gate 仅允许修改：`configs/base/defaults/model_config.py`、`configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py`、`model/generator/omni_mot_model.py`、`model/generator/mot/local_evidence.py`、`model/generator/mot/production_runtime_adapter.py`、`model/generator/mot/runtime_authority.py`，可新增一个 lifecycle callback 模块与相邻 `*_test.py`。禁止：TOML schema 变更、真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1。后续 GPU smoke、LIBERO4IN1 matched smoke、正式训练/评测各自独立三方同 SHA 审核。

完整继承条款：production runtime contract design v0.3、config/optimizer/checkpoint design v0.2 及各自 v0.1 起的历史版本；冲突时以本 v0.1 与上述最新冻结版本为准。
