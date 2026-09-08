# PSM-WMA Local Memory v0.3.9 CPU/static implementation design v0.3

**日期**：2026-09-08
**状态**：docs-only remediation；待三方同 SHA 审核；未授权代码、GPU、真实 I/O 或训练
**前置批准**：canonical contract v0.3.9，formal root `e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9` / Gitlink `80aec090688e3c710c41e1dfd86b6500773db2c7`
**取代范围**：本文件 supersede v0.2 对 feature-disable owner 的 §1/§3；v0.2 的 invalid-first scan、opaque `consumer_payload` common gather、scheduler/transaction 与禁止范围均原样继承。v0.1/v0.2 只保留审核历史，不构成实现授权。

## 1. 唯一 owner、literal 与白名单

唯一 canonical-route evidence encoder 仍是既有 `LocalEvidenceEncoder`；不得新增或保留
`SegmentEvidenceEncoder`。实现授权的唯一 literal 是
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC`，仅在三方对同一 formal root/Gitlink
给出该 verdict 后生效。前置 `CANONICAL_CPU_DESIGN` 只授权创建 implementation design。

允许文件精确为：

```text
cosmos_framework/model/generator/mot/local_memory_segment.py       # 新：SegmentBatch、scheduler、GA helper
cosmos_framework/model/generator/mot/local_evidence.py             # EvidenceFeatureConfig、LocalEvidenceEncoder config、masked scan
cosmos_framework/model/generator/mot/local_memory_segment_test.py  # 新：synthetic CPU tests
cosmos_framework/model/generator/mot/local_evidence_test.py        # encoder/masked-scan tests
```

除 `EvidenceFeatureConfig` 与 `LocalEvidenceEncoder` 的精确变更外，`local_evidence.py` 只可新增
`scan_segment_masked_many()` 与它的私有 row select/scatter helpers。不得改变旧
`scan_segment_many()`/`step_many()`、`LocalHistoryRuntime` 或旧 runtime 路径。不得修改 dataset、trainer、
production adapter、model forward、`local_memory2llm`、config、optimizer、checkpoint、manifest 或
`ttt_lifecycle.py`；禁止真实 I/O、CUDA、torchrun、训练、评测和推理。

## 2. `EvidenceFeatureConfig` 与 `LocalEvidenceEncoder` 的双模式合同

`EvidenceFeatureConfig` 定义在 `local_evidence.py`，为不可变 construction-time config：

```python
EvidenceFeatureConfig(state: bool, dt: bool, age: bool)
LEGACY_EVIDENCE_FEATURE_CONFIG = EvidenceFeatureConfig(state=True, dt=True, age=True)
CANONICAL_EVIDENCE_FEATURE_CONFIG = EvidenceFeatureConfig(state=False, dt=False, age=False)
```

`LocalEvidenceEncoder(..., feature_config=LEGACY_EVIDENCE_FEATURE_CONFIG)` 是默认值，必须保持当前无参、
单参及明确 legacy construction 的模块树、forward signature、参数/缓冲区、数值和错误行为逐字兼容；现有
old-route tests 是该不回归证据。`state_mean/state_std` 只能在 `state=True` 时接受，保持其现有配对校验。

`LocalEvidenceEncoder(..., feature_config=CANONICAL_EVIDENCE_FEATURE_CONFIG)` 是唯一的新 Local-Memory
route 构造方式。在 construction 时它只注册：`visual_proj`、`action_proj`、`norm`、不可变 dims/config
metadata；它**不得**注册 `state_proj`、`state_mean`、`state_std`、`dt_proj`、`age_embedding`，也不得注册
这些名称的参数、buffer 或 placeholder。该 canonical module 的准确 trainable inventory 因而是
`visual_proj.weight/bias`、`action_proj.weight/bias`、`norm.weight/bias`；后续 config/optimizer/checkpoint Gate
必须以此 inventory 及 feature-config identity 为唯一绑定点，旧 strict checkpoint 默认 fail closed。

为保持 legacy public signature，forward 的 history keyword 仍可出现在 Python 签名；但 canonical config
的专用 `encode_segment(visual_summary, executed_action)` 调用路径只能接受这两个 tensor，且在调用
`LocalEvidenceEncoder` 前不得构造、传递、有限性检查或读取 state/dt/age。若有人经 legacy `forward` 向
canonical instance 传入任何 `history_state`、`history_dt_s` 或 `history_age_steps`，必须 fail closed，且在
任何读取、shape check 或 projection 前失败；canonical path 不允许 zero/None dummy feature。legacy config
则保持现有 history forward 行为不变。

CPU acceptance 必须同时证明：(a) legacy default 的 `state_dict` keys、数值 output 与现有 tests 一致；
(b) canonical inventory 完全没有上述五类 disabled 名称；(c) canonical `encode_segment` 的 spy 证明
state/dt/age tensor 没有创建、传递或读取；(d) 向 canonical legacy-forward 入口提供任一 disabled tensor
会在读前 fail closed。

## 3. 继续继承的 v0.2 必需合同

新 route 不得调用旧 `scan_segment_many()`：`scan_segment_masked_many()` 在每 timestep 先取得 valid row，
all-invalid 时不访问 evidence、不 finite-check、不 encoder/K/Q/V project/read/write，仅原样 carry state；
mixed batch 只在紧凑 valid sub-batch 操作并 scatter。invalid state bytes 必须不变，Local 为 absent 而非零 token。

`SegmentBatch` 保留 v0.3.6 的 opaque `consumer_payload`，并使用同一 stream-major valid index 同时 gather
payload、Local（S0=`None`）和 identity，PAD 全部排除。`RankLocalSegmentScheduler`/`GAWindowPlan` 仍在
`local_memory_segment.py`，保持 v0.2 的 target-distribution/exposure snapshot、suffix retry 和 episode vs
slow-LR scheduler 语义。Prefix 仍只允许注入 synthetic projector，不得触碰 production `local_memory2llm`。

所需 synthetic CPU matrix = v0.2 §5 全集，外加 §2 的四项 legacy/canonical encoder dual-mode evidence；
`py_compile`、相关 pytest、child/root `git diff --check` 必须 PASS。即使通过也仅授权白名单 CPU/static
实现，不授权生产接线、真实 I/O、GPU 或 LIBERO4IN1。
