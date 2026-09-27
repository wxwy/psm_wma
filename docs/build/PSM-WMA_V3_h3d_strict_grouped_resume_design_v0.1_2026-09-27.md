# PSM-WMA V3 H3-D — strict grouped resume CPU/static 设计 v0.1

- 日期：2026-09-27；责任：cx 技术 owner 与 CPU 实现，ds 后续 8×H100 恢复验证。
- 前置：H3-C CPU/static closure pair root `a8eccf0bbaf32581e714baf8c41790ea1083caf8` / child `0dca391d2cb6e4a62b0fca0c39ebf0640e678dd9`。本 Gate 不启动 GPU/训练。

## 权威持久化入口

沿用 upstream `DistributedCheckpointer` 的 `model`、`optim`、`scheduler`、`trainer` 组件；`trainer` 已保存 GradScaler、iteration 与每 rank Python/NumPy/Torch RNG。Local 不复写这些组件、不注册 fast state 为参数或 optimizer state。通过现有 `_DataloaderWrapper` 的首个 `checkpoint_component="dataloader"` 回调，保存每 rank 独立的 committed Local 状态到 `dataloader/rank_<rank>.pkl`。该文件与模型 DCP 同属 `iter_<iteration>`，只在 checkpoint marker 成功发布后作为恢复源。

## Local state schema 与严格验证

版本化 schema 包含：iteration、rank/world8、seed、catalog manifest digest、Stage-A/config digest、冻结 T16/K4/raw15/local32/evidence256/ttt64/fast256/lr0.1/GA2、`CatalogFrontier` 的 epoch/assigned/8 slots、每 slot scheduler identity、非 terminal slot 的 provenance 与四个 fp32 fast tensors。保存时 fast tensor detach+CPU clone；加载前逐字段检查类型、形状、finite、UID/rank、slot→episode/cursor/segment 连续性、manifest/config/source digest 与 planner 当前值；加载时再搬到 model Local core 设备并验证。任何失败不得部分改 live state。

同 job 恢复时，若 `dataloader` 组件被过滤、rank-pkl 缺失、schema 不匹配或 iteration 不一致，必须在首个 grouped window 前硬失败；Stage-A Edge DCP warm-start 只加载模型权重且没有 Local runtime state，允许从初始 frontier 启动。零步 checkpoint 在 Local state 建立前不得发布。恢复回调必须在 DCP load 前绑定，加载时可暂存状态，首个 `training_step` 创建 model-owned window 后一次性验证并应用；不可使用未验证的 pickle 对象直接替换 live。

## CPU 验收

中断前保存成功窗口后的 slow model、optimizer、scheduler、GradScaler、DCP RNG 与 Local schema，重建对象后恢复：下一窗口的 `(epoch, UID, slot, cursor, segment_id)` 完全一致，fast state fp32 数值一致，后继相同输入的 outer loss/梯度在 CPU 容差内一致；无重复/跳过。缺失/损坏/异 rank/异 manifest/异 config/异几何/异 iteration/sidecar 造假均 fail closed，live 零变化。验证现有 DCP 的 rank-pkl 回调真实被选中且保存/加载顺序正确；Ruff/format、合并 CPU 回归、双仓 diff-check PASS。H3-E 由 ds 执行真实 H100 DCP save/reload 短跑与跨 rank 一致性证据。
