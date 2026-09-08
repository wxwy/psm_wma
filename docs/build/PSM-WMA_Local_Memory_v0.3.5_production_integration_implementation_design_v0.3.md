# PSM-WMA Local Memory Production Integration Implementation Design v0.3

**日期**：2026-09-08  
**状态**：docs-only remediation；未授权代码、真实 I/O、GPU 或训练  
**取代**：v0.2 的 whitelist 精确性。

## 1. 唯一允许文件与符号

| 路径 | 状态 | 唯一允许变更 |
|---|---|---|
| `cosmos_framework/model/generator/mot/local_memory_segment.py` | existing/modified | 仅 `SegmentBatch`、`RankLocalSegmentScheduler`、`GAWindowPlan` 的 canonical integration facade |
| `cosmos_framework/model/generator/mot/local_memory_segment_test.py` | existing/modified | 仅相邻 integration fixtures |
| `cosmos_framework/model/generator/mot/c6_runtime_adapter.py` | existing/modified | 新增唯一类 `CanonicalSegmentRuntimeAdapter` |
| `cosmos_framework/model/generator/mot/c6_runtime_adapter_test.py` | existing/modified | 仅 `CanonicalSegmentRuntimeAdapter` fixtures |
| `cosmos_framework/trainer/__init__.py` | existing/modified | 仅 `ImaginaireTrainer._run_local_memory_segment_backward` |
| `cosmos_framework/trainer/trainer_local_memory_integration_test.py` | new | 仅该 seam 的 synthetic tests |

所有其他符号保持行为不变；尤其历史 `C6SyntheticRuntimeAdapter` 不修改、不调用、不删除。不得增加任何其他文件。

## 2. 继承的不可变合同

v0.2 failure taxonomy、primary/auxiliary ABI、raw-native finite 检查、normal/recovery objective、unique scaling owner、CPU fixtures 与所有禁止范围逐字继承。`CanonicalSegmentRuntimeAdapter` 只能适配 opaque payload、`scan_segment_masked_many()` 与 canonical plan；`_run_local_memory_segment_backward` 是唯一 Local primary/aux scaling 和 backward/commit transaction owner。

## 3. Gate

批准仅授权上表的 CPU/static synthetic implementation；新 implementation SHA 仍需三方 closure review。生产 wiring、真实 I/O、GPU/torchrun、训练/评测/推理及 LIBERO4IN1 均未授权。
