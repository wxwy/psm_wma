# PSM-WMA Local Memory Production Integration Implementation Design v0.1

**日期**：2026-09-08  
**状态**：CPU/static design only；未授权 production、真实 I/O、GPU 或训练  
**Gate**：`G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION-DESIGN`

## 1. 唯一语义源与范围

唯一语义源是 canonical v0.3.6--v0.3.9、已关闭 CPU/static core（child `0fddc27f`）及 production migration v0.2。旧逐行 lifecycle、`scan_segment_many()`、closing replay/materialize 均禁止。

未来 CPU/static implementation 的精确白名单只可为：`cosmos_framework/model/.../local_memory_segment.py`、相邻 `local_memory_segment_test.py`、`production_runtime_adapter.py`、其相邻 test、`trainer/__init__.py` 的 synthetic seam，以及相邻 trainer test；实现前必须逐个冻结实际路径与现存入口。不得改 recipe/defaults/registry/model forward、checkpoint I/O 或任何真实 data/cache 接口。

## 2. 强制调用合同

adapter 只接收 canonical `SegmentBatch`；opaque `consumer_payload` 不检查/重算。调用顺序固定：scheduler 先形成 immutable `GAWindowPlan` → `scan_segment_masked_many()` invalid-first → stream-major gather payload/local/identity → synthetic consumer spy 返回 native mean → `planned_N_valid/N_window` 唯一缩放 → outer backward → identity 校验 → detached fast cursor/exposure commit。任何 `actual!=planned`、load/identity、inner、forward/native-loss/backward 异常均 abort 当前 member、保留已提交 fast chronology、丢弃本 window 全部 slow grad、跳过剩余成员并 deterministic suffix-only redelivery；不得 rebind/resample。

`GradScaler` skip 仅阻止 slow optimizer/LR step，已提交 fast chronology 保持。state/dt/age 由 construction-time inventory 真关闭；不能创建或传入伪零 tensor。

## 3. CPU/static 验收

必须以 synthetic payload/consumer spy 覆盖：S0/PAD 不读不写不损失；valid flat identity/local/payload 同步 gather；全成功 weighted objective；planned/actual mismatch；首/后 member exception 的 partial fast-commit 与 slow-grad 丢弃；suffix retry identity 不变；GradScaler skip；disabled parity。不得执行真实 I/O、GPU、训练。通过后仅允许该 CPU/static 实现，implementation 新 SHA 必须再次三方审核。

## 4. 明确禁止

本设计不授权真实 adapter 接入模型、registry/defaults、checkpoint/data/cache、CUDA/GPU/torchrun、训练/评测/推理、P4/P5、B2-T 或 LIBERO4IN1。GPU smoke、matched smoke 与正式训练继续各自独立 Gate。
