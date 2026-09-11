# PSM-WMA Local Memory v0.3.5 Canonical Native Consumer Runtime Source-Audit 设计 v0.1

**日期**：2026-09-11
**状态**：P0 docs-only source-audit design；须本文件 formal root/child pair 三方同 SHA 批准后，才可进行定义的只读审计
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-SOURCE-AUDIT-DESIGN`

## 1. 目的与边界

v0.3.5 §20.2 明确保留了首次 canonical GPU smoke 以前不能猜测的六项源码问题。本设计只冻结一次**只读**审计，形成下一份 native implementation design 的事实输入；它不把已经关闭的 synthetic CPU/static contracts 当作 production runtime 已接通。

上游 authority：

- `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §3--§20；
- `PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.3.md`；
- formal `e1a0c53ee91d7f1ac1dae34f785db2a88ec30e6d` / child `08775da2e73e352ebb1497548de5909baab8c2dc` 已关闭的 production-ABI CPU/static Gate。

本 P0 仅允许阅读 root/child 源码、文档与既有测试；禁止修改 child、执行 Python/pytest、真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、native real forward/loss/backward、optimizer/scheduler step、runtime sidecar、训练、评测、推理及 LIBERO4IN1。

## 2. 已知入口（只作审计起点，不预设结论）

| 审计对象 | 现有入口 | 必答事实 |
| --- | --- | --- |
| canonical diversion 与 safe prefix | `model/generator/omni_mot_model.py::_canonical_production_segment_forward`、`_prepare_canonical_production_inputs`、`training_step` | 现有 hard-stop 前的 request/carrier/scan/preparation object identity、何处可插入真实 native continuation、何处会重新进入 ordinary Local 路径。 |
| native pack/noise/forward/loss | `omni_mot_model.py::_pack_input_sequence`、`training_step` ordinary native chain、`_compute_losses`、`algorithm/loss/flow_matching.py` | 每个 consumer 的 sample identity 在 pack、noising、network output 与 modality reduction 中怎样保留；是否存在可验证的 variable-length gather seam。 |
| trainer backward/GA boundary | `trainer/__init__.py::training_step` 与 canonical dispatch helpers | exact one-backward、loss scaling、DDP sync、optimizer boundary及异常/skip语义可由哪个 production seam继承或必须新建。 |
| segment scheduler/frontier | `model/generator/mot/local_memory_segment.py`、`canonical_segment_adapter_scheduler.py`、`canonical_segment_production_adapter.py` | planned/actual valid-count 的 authority、tail/PAD 的不重绑约束、weighted category exposure 与 commit/abort provenance。 |
| prefix/sequence packing | `model/generator/mot/attention.py`、`model/generator/mot/unified_mot.py`、`utils/data_and_condition.py` 与 Local-prefix tests | `K_local=1` 的 `[N_valid,1,32] -> [N_valid,1,2048]` prefix 是否能与 gathered consumers exact 对齐，及 Native packer 对 variable population 的硬约束。 |
| legacy supersession | active-wiring/runtime owner/segment producer 的现存接口与相邻 tests | 哪些只可保留为 scheduler/transaction/provenance authority，哪些 row-wise materialization/replay/marker path 必须在 canonical real route 旁路或删除。 |

## 3. 审计问题与不可静默替代的分流

1. **Variable-valid consumer ABI**：证明或否证 native packer 能接收 `N_valid_micro < B_stream*T` 的已 gather 逻辑 consumer。若不能，报告 exact fail point，并给出两种互斥后续设计候选：真 gather 适配，或有 native-loss mask 的等价 ABI；不得用可训练 zero-PAD 替代。
2. **Loss/reduction 与 GA**：从 native modality loss 到 trainer backward 逐段标明 reduction、auxiliary loss、sample axis、`grad_accum_iter` scaling。仅当 source 证明可定义 `N_valid` 加权且 full batch 退化为 `1/GA`，后续才可设计 valid-exposure weighting；否则必须先单独设计 loss adapter。
3. **planned count 与 scheduler**：指出 normal/recovery plan 在不读取尚未 materialize tensor 的条件下，如何冻结每 member/window `planned_n_valid`、row provenance、queue/seed/epoch 和 category exposure；若当前 objects 无法承担，必须标为新 scheduler/data-side Gate。
4. **首轮 feature disable**：核实 `LocalEvidenceEncoder` 的 state/dt/age 分支是否可从实际 module construction 与 forward path移除；不能接受“常数零输入”作为关闭证明。若现有 config/owner 不能表达 disabled branch，后续 implementation design 必须显式列入 config/module migration。
5. **supersession boundary**：以 `file:line` 给出 canonical `[B_stream,T]` route 与旧 active row-wise marker/arming/replay/transaction 路径的每一处交汇。任何共享 mutation authority 必须按 object identity、one-shot commit 与 abort/terminal semantics 标注；无法证明隔离即 fail closed，不进入 native implementation。
6. **single-GPU smoke feasibility contract**：仅做静态 resource/accounting 追踪：fp32 `W_fast` 存储位置、higher-order graph 生命周期、CP/DDP prohibitions、single-device config admission。不得估报吞吐、分配 GPU 或执行 smoke。

## 4. 审计产物与验收

唯一产物为后续新增的 `...canonical_native_consumer_runtime_source_audit_v0.1.md`，至少含：

- 对第 3 节每项的 source `file:line` 证据、输入/输出 identity 与明确 PASS/FAIL；
- `[B_stream,T] -> stream-major valid gather -> [N_valid,K_local,2048]` 的逐阶段 ownership 表；
- native loss/reduction/GA 的具体 scalar 公式及不可证明项；
- 保留/旁路/删除三栏的旧 active-wiring components 表；
- 只读审计范围内可证明的 first GPU smoke prerequisites 与必须另起 Gate 的项目。

若任一事项要求 dataset/collate/packer/production model/trainer 代码改动、真实 I/O 或 GPU 才能回答，审计必须记录为 `REQUEST_CHANGES`/后续 Gate，不得执行或假定答案。

## 5. 审核请求

请对本 docs-only P0 设计回复唯一 verdict：

`APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_SOURCE` 或 `REQUEST_CHANGES(file:line)`。

即使批准，也只授权上述只读 source audit；不授权 child 代码、真实 I/O、GPU/CUDA、torchrun、native forward/loss/backward、optimizer/scheduler step、runtime sidecar、训练、评测、推理或 LIBERO4IN1。
