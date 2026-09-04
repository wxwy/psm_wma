# PSM-WMA R09-B TTT v0.3.2 C6 runtime integration design v0.4

**状态**：v0.3 superseded；仅修正 chronology 坐标，其他条款逐字继承 v0.3/v0.2。待三方同 SHA 设计审核；不授权实现、生产接线、GPU 或训练。

## 唯一修正：owner-epoch 全局 chronology

`source_timestep` 不再是 segment-relative。它是 **owner epoch 内全局、从 0 开始且严格连续的 causal timestep**，由被委托的 C5A `AdmissionAuthority`/owner ledger 唯一维护：同一 owner epoch 的后续 segment 首行必须等于上一段最后 timestep 加一。`segment_id` 与 segment-local row index 仅用于分组和日志，不得重新定义或重置 `source_timestep`，adapter 不得维护第二 chronology。

`reset(owner)`/`done(owner)` 的 v0.3 规则保持：pending 任意 phase 时立即拒绝且不变更快照或 epoch；显式 abort 后才可 reset；成功 reset 开启新 epoch，C5A 清理 owner chronology 后允许新 epoch 从 timestep 0 重新 admission，旧 capability fail-before-C5。

## 新增验收

在 C6 synthetic adapter seam 直接委托 C5A fixture：

1. 同一 owner epoch 连续提交两个非 terminal segments（例如 N=1 后 N=3），第二段 source_timestep 从前一段末尾连续递增，segment-local row index 仍从 0 独立计数；
2. reset 后新 epoch 同 owner/identity/timestep=0 可重新 admission，旧 epoch capability 拒绝；
3. 跨 owner、skip、duplicate、changed-byte、permutation/row-mismatch 仍 fail-closed，且不发生第二 chronology 分配。

v0.3 继承的 test-only adapter 直接委托、整段 materialize/backward/commit、terminal/N 矩阵、segment outer-loss、Memory Prefix 形状与全部禁止范围不变。C6 implementation 仍须另行三方同 SHA closure；未授权 active Cosmos runtime、config/optimizer/checkpoint、GPU、训练、评测、推理、P4/P5、B2-T 或 LIBERO4IN1。
