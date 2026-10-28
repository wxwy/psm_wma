# PSM-WMA V3 — Compact Cached Video CPU Evidence Gate 增量关闭审查

- 日期：2026-10-28
- **Disposition：E1 CLOSED；E2 CLOSED；E3 CLOSED。Compact 0/1 CPU parity Evidence Gate CLOSED（仅 CPU Evidence 范围）。**
- 审核对象：本轮用户上传合并文件所含完整 Python 源代码与 JSON 结果；非产线复测，非新实现 Gate。
- 对应 Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`；No-TTT 相关原始 Root 代码基线 `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`。新产生 Root Git commits **仅归档证据/Review/Inbox**，不授予新 production implementation/design verdict。
- 前序 Evidence-only `REQUEST_CHANGES`：`docs/collab/chatgpt/reviews/2026-10-28_V3_Compact_Segment_NoTTT_Full_CPU_Parity_Evidence_Review.md`，唯一待关闭 E3 = Python/JSON 原始可检查 Evidence 未在远端。
- 已有 DS 原始摘要：`docs/collab/chatgpt/DS_PRO_2026-10-27_V3_Compact_Segment_Full_NoTTT_CPU_Loader_Parity.md`。
- 本轮新证据由用户的单个合并附件直接提取、审核并上传，路径：
  - `docs/collab/chatgpt/evidence/compact_segment_parity.py`
  - `docs/collab/chatgpt/evidence/compact_segment_parity_results.json`
  - `docs/collab/chatgpt/evidence/compact_segment_parity_README.md`
- **Source provenance 注意**：附件在 Markdown 源中用 U+00A0 占位缩进；提取时仅将 non-breaking spaces 转为 ASCII spaces、末尾添加 newline，脚本 Python 语法验证和 JSON 解析通过。不能据此证明与 DS 训练服务器`/tmp`目录的原始字节级文件完全相同；脚本/值本身可直接审查。

## 1. E1 — Terminal partial Segment：CLOSED

`compact_segment_parity.py:149-232` 从真实 `ExactWindowLocalCatalog` 选择 `window_count % 16 != 0` 的 3个 Episode，通过 `cursor=segment_count-1` 和 `valid_count=window_count-cursor*16` 创建 `training_stream_end=True` 的真实 Catalog-capability Requests。

| Episode | window_count | segment_count | terminal cursor | valid_count | 结果 |
|---|---:|---:|---:|---:|---|
| CloseBlenderLid/episode_000000 |345|22|21|9|PASS|
| CloseBlenderLid/episode_000001 |396|25|24|12|PASS|
| CloseBlenderLid/episode_000002 |365|23|22|13|PASS|

- GPT 独立读取 JSON 中各 Episode `tensor_fields_eq`、`meta_eq`、`payload_eq_all_consumers`、`rng_before_eq`、`rng_after_eq` 全 True；遍历所有 **34 个有效 Consumer** 的 per-field map，除预期的 `video_proxy0=False/video_proxy1=True` 之外，没有 False 或 missing。
- 对照生产 `ExactWindowRankPlanner` 的 Terminal/valid_count 规则（Child `robocasa_exact_window_local.py:269-295`），覆盖真实 partial，关闭 E1。
- Video 为相同形状/全零逻辑像素；未要求/宣称物理 stride、storage 相同。

## 2. E2 — 完整 No-TTT CPU Worker→Segment→Native Collate：CLOSED

- `compact_segment_parity.py:234-348`：创建两个相同冻结 Planner（rank0/world4/B8/GA4/T16），构造 `NoTTTCpuLoader` 双路 `workers=1/prefetch=1/persistent=True`，分别 `begin(plan)`、每 Member 依序 `materialize`、`MatchedNoTTTWindow.pack`、`collate_grouped_native_batch`。
- JSON `frozen_plan_eq=True`、`member_counts=[128,128,128,128]`；4个 Member 均 `payload_count=128`，合计512 Consumer，`positions_eq=True`、`rng_consumed_eq=True`、`batch_all=True`、`batch_video_eq=True`，全部非 proxy 字段 `payloads_eq/collated_batch_eq` 为True；`video_proxy0=False`、`video_proxy1=True`，均符合预期。
- `NoTTTCpuLoader` 真正 RAW Worker 与 Parent materialize 链路被执行（而非只测 `sft[idx]` helper）。测试仅限 CPU 的`workers=1`配置：不是证明正式`workers=8`端到端训练加速、FSDP等价或GPU传输。
- 测试脚本在每 Member 的 Dense 消费前 snapshot Python+PyTorch CPU RNG，比较其 after-state，恢复相同起点后执行 Compact 并比较 after-state（`compact_segment_parity.py:262-275`）。四轮 `rng_consumed_eq=True` 实际约束 CFG dropout 的可见 Python/Torch 流；下一 Member 从匹配的 Compact after-state 继续，连贯性成立。

## 3. 审核发现与风险边界

**LOW / nonblocking: 不得引用 Task2 的最终 `rng_after_eq` 作为独立结论**

- `compact_segment_parity.py:332-335` 中 `after0=snap_rng()` 与 `after1=snap_rng()` 连续读取同一全局状态，中间无不同模式操作，故`rng_after_eq=True` 为恒真的假见证；同理 `rng_before_eq` 只是重复Seed的自检。
- **为何不是 Gate blocker**：E2 的真正时序验证在 `:262-275` 的逐 Member `mem_state→Dense end→restore→Compact end→compare`，且 JSON 4个 Member 的 `rng_consumed_eq` 全True，覆盖本 Gate Python/Torch可见 RNG。`snap_rng` 未记录 NumPy RNG，但现有 NoTTT RAW Worker/Parent `_require_same_rng` 自行监视 Python/NumPy/Torch RAW路径；此 CPU Gate 约束的 CFG dropout 调用 `transform_draw(random.random)`，不构成当前阻断。
- **INFO**：脚本主要把等价结果写 JSON，并非每个 False 都立即 raise（除几何前置 assert）；GPT 已另外完整解析 JSON、逐字段强制核验 True。建议未来测试加强 fail-fast，但不为已关闭 Evidence 重做大实验。
- **INFO**：从用户合并 Markdown 提取证据，不等于独立比对 DS 服务器原始 `/tmp` 文件内容，也不是 GPT 本地重执行；判据是提交的可检查代码与报告完整机器结果互相一致。
- **Performance**：隔离 CPU-only 单Worker功能测试中 `transform_host_ms` Dense3541.1ms vs Compact348.6ms（约10.2×）；前序4样本固定8线程 Transform20.6–28.7×属于微基准。`step_window_host_wall_ms` 32905ms vs20145ms **不等于真实 NoTTT GPU训练Step**，不能据此外推得到10秒/Step或承诺任何系统收益。

## 4. Gate 范围与下一步

- **E1/E2/E3：CLOSED，当前 Compact Cached Video 0/1 CPU Evidence Gate CLOSED。**
- 生产源码仍基于旧的 Child/Gitlink，无需重新做 Implementation/design full review；此次提交是 Evidence / Review / Inbox bookkeeping。
- **GPU Native Forward/Loss/Gradient parity：NOT_RUN、未授权。**
- GPU H2D、真实 No-TTT DCP/Resume、在已有 Job 的 checkpoint 边界从 Compact0 切 Compact1、正式训练性能收益：**NOT_RUN、未授权**。
- 下一 Gate 若 Owner 独立授权：相同冻结 Batch / Seeds / 权重下隔离 GPU 验证 Native Forward/Loss/Gradient 和模型输入 ABI；不覆盖正式训练切换与已有 DCP，后者再独立 Gate。
- 不要停止、重启、环境切换正在运行的 `no_ttt_packed128_droid_fresh_30k_world4_ga4`，也不为此改代码。

**正式落盘条件：本 Detailed Review 与 Canonical CODEX_INBOX 同时更新后才形成持久 Gate disposition。**
