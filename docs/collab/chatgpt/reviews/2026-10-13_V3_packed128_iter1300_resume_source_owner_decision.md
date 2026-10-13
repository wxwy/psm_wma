# PSM-WMA V3 — Packed128 接续训练恢复点：Owner 固定 iter1300

Date: 2026-10-13
Decision authority: Owner statement `iter1400保存不成功，还是从iter1300resume.`
Frozen proposed Packed128 implementation Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.
Gate A CPU: APPROVE / CLOSED (151 passed, 2 skipped); Gate B real GPU: NOT YET AUTHORIZED, numerical correctness/performance OPEN.

## Owner 决定与证据等级

- **不使用 iter1400：** Owner明确告知 `iter_000001400` 的保存没有成功。该目录即使存在也不应作为恢复源；不必为了选择恢复点再对它做费时的候选完整性审计。此项是 Owner 告知的运行状态，不冒充GPT已读取所有DCP二进制的独立证明。
- **唯一目标恢复源：** 原 Index8 Formal30k 的 `iter_000001300` 完整DCP（要求实际验证组件完整、来源、8Rank），旧 `latest_checkpoint.txt` 报告已指向 `iter_000001300`。文件指针不能代替全部Rank可恢复性证据。
- **下个 optimizer iteration：** 若从完整iter1300恢复，第一步为iter1301，保留模型/optimizer/scheduler/trainer RNG/Local Fast State/Frontier/8Rank dataloader进度、all source digests、配置及Checkpoint原始字节；绝不从iter0重新训练，也不使用iter1400尝试复活。

## Packed128 与 Index8 的兼容性

- 新 Packed128 `NATIVE_BATCH_LAYOUT=v2_a2_member_packed_slot_major_v1` 已写进 `config_digest`，旧 Index8 DCP 的 `config_digest` 和 Sidecar `SegmentProvenance.config_digest` 与新代码不同，因此**不能直接执行新版 `--phase resume`**。
- 保持严格源数据/权重/Optimizer/RNG/完整 rank状态验证，不能仅为过校验而禁用摘要检查或替换`latest_checkpoint.txt`。
- **推荐顺序**：Gate B 固定真实Consumer/σ/noise/Local梯度数值等价 → GPT实现只允许既有可核验Index8来源的显式一次性`iter1300→Packed128`迁移（不原地修改DCP），并验证全部8Rank/optimizer/scheduler/frontier/sidecar provenance和新命名空间 → Owner手动启动新Packed128从iter1301继续。
- 跨Native布局影响随机数流、packed kernels和浮点归约，因此这种续训是**有边界的算法切换续训**，不是同源码bitwise strict same-job resume。RNG状态可以继承，但后续随机分配可能不同。
- 若Owner选择**继续旧Index8而非Packed128**，才可在旧SHA一致且原DCP可恢复的条件下执行原same-job strict resume。此决策的当前目标仍为通过Gate后Packed128迁移。

## 操作禁令

- 禁止更改现有正式工作树、`iter_000001300`、`iter_000001400`、`latest_checkpoint.txt`和任何原始训练记录；禁止覆盖旧Job命名空间。
- 在Gate B及专门的Checkpoint迁移Gate完成以前，不能直接启动Packed128 Formal30k或宣称旧DCP已兼容。
- DS_PRO现阶段不需要继续检查iter1400作为候选恢复点。针对iter1300只需只读核验4个DCP `.metadata`组件、8个Rank dataloader `.pkl`、最近指针以及原作业来源SHA/epoch、GA边界是否完整；无此证据标为未验证，不能自证已恢复。

Supersedes the optional `iter1400` selection suggestion in `2026-10-13_V3_packed128_native_gateA_CPU_acceptance_closure_c4731bca_c8dabbb3.md` (which was written before Owner confirmed failed save).