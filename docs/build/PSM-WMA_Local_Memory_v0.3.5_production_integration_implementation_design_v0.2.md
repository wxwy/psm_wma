# PSM-WMA Local Memory Production Integration Implementation Design v0.2

**日期**：2026-09-08  
**状态**：docs-only remediation；未授权代码、真实 I/O、GPU 或训练  
**取代**：v0.1 的 failure/loss/whitelist 定义。

## 1. 精确白名单

未来 CPU/static implementation 仅可修改既有 `cosmos_framework/model/generator/mot/local_memory_segment.py`（`SegmentBatch`、`RankLocalSegmentScheduler`、`GAWindowPlan` 的 integration facade）、既有 `cosmos_framework/model/generator/mot/c6_runtime_adapter.py`（仅新增 canonical adapter facade）、既有 `cosmos_framework/trainer/__init__.py`（唯一 Local loss/backward seam），以及新建相邻 `local_memory_segment_test.py`、`c6_runtime_adapter_test.py`、`trainer_local_memory_integration_test.py`。历史 C6 adapter 不删除、不重写；旧 lifecycle 不调用。除此以外任何路径禁止。

## 2. failure taxonomy

仅 same-digest `LOAD_DECODE_TRANSIENT` 且 `attempt=0` 可创建唯一 suffix recovery plan；`attempt=1` 必须 `LOCAL_MEM_RETRY_EXHAUSTED`。identity 或 planned/actual mismatch 是 `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE`；inner/native-loss nonfinite 是 `LOCAL_MEM_NUMERICAL_FAILURE`；forward/backward exception 是 `LOCAL_MEM_OUTER_FAILURE`。所有 terminal failure 清空 partial slow grad、保留已提交 fast chronology、抑制余 member 和 optimizer/LR，**绝不 redeliver**。只 transient attempt0 进入 suffix-only recovery。

## 3. 唯一 loss owner

consumer spy/adapter 返回结构化 `(primary_consumer_mean, auxiliary_loss)`；先检查两项 raw native finite。normal objective 仅由 trainer Local seam 计算：`(N_valid_mu/N_window)*primary + (1/GA)*auxiliary`；recovery 使用 frozen `GA_effective`。不得按 valid ratio 缩放 total loss，不得第二次 `/grad_accum_iter`。

## 4. 验收与禁止

CPU fixtures 必须分别覆盖 transient attempt0/retry exhaustion、identity/planned mismatch、numerical、outer exception、prior fast retention/zero slow grads/remaining suppression/optimizer-LR 不动及 terminal evidence；另覆盖 unequal valid counts、nonzero aux、full-window equivalence、无二次 GA 缩放。无真实 I/O、GPU、训练。
