# PSM-WMA V3 EvalV2 — Replan all-mode durable MP4：独立增量 Code Gate

- 日期：2026-11-02
- **Formal technical verdict：`REQUEST_CHANGES`**
- Root Formal implementation SHA：`d2041e388eda084e42a2d6b0d115db8beedfab44`
- Child/Gitlink Formal SHA：`0dd13d3d952aa7cbab39f966dfab04b23551f0c9`
- 隔离候选：`v3-eval-v2-replan-all-20261102`（后续 review/evidence/Inbox bookkeeping SHA 不能替代 Formal Pair）
- 上次已审已批准 Pair：Root `4b581493db805c92964cb27e740c736db87c0329` / Child `9a8cd6183424bfce245fbca393ca25ed59919ea6`；历史 `APPROVE_CODE` 及媒体/GPU资源已有 Gate **不变**，本轮仅审新增 durable all-mode media delta。
- 冻结 Owner 目标：`save_generated_video=all` 时每次 Replan 完整 MP4，成功诊断须零缺失，故障显式 `MEDIA_INCOMPLETE`；默认每 Server 4 jobs / 512MiB、独立媒体超时300s（可配置）；End 等待保存，写盘完成才 ACK，维持科学 Core/SR、Local ACK 与 GPU/训练边界。900EP 开关由 Owner 手动选择，**不是**本次范围。
- 此审核通过 GitHub 读取了实际 Root/Child commit、target 文件源码、直接相关 tests、原始作者 JUnit/命令、冻结设计和源码绑定；没有在本轮独立运行 pytest 或真实 GPU。

## 1. 当前变更范围与确认正确的行为

增量变动：Root `scripts/robocasa_eval_v2/{config.py,runtime.py,cli.py,generated_media.py}`、相关 tests/docs/gitlink；Child `robocasa_batch_transactions.py`、`action_policy_server_robocasa.py`、`eval_v2_transactions.py`、`eval_v2_adapter.py`、`media.py`、新增 `generated_video.py`、`eval_v2_worker.py`、tests。Frozen model/Local training algorithm、base Session/Core/SR、Scheduler/Store、GPU identity/resource、Vendor/Data/Checkpoint 的 protected blob/tree 未更改。

逐项源审：
1. Root `config.py:34–36,69–71,197–204` 定义可配置默认 **4 jobs、536870912 bytes、300s**，并验证有界输入；`runtime.py:243–251,295–305,374–383,454–455` 传播到 Server argv、真实 `/info` 及 Sim settings，较旧代码有强制运行时配置核对。
2. Child `robocasa_batch_transactions.py:133–181` 先做认证 reservation，满时 429；`eval_v2_transactions.py:190–229` 在 Server executor/model 锁外进行有界重试，避免简单扩容和无限等待。`_pump:253–304` 优先处理已排队的严格媒体解码。
3. Child `media.py:247–305` 严格模式使用 queue 有界提交、等待独立 Encoder datagram；`generated_video.py:80–132` 生成临时 MP4、关闭 FFmpeg writer、验证/发布与收据；`eval_v2_transactions.py:230–332` 要求 VIDEO_SAVED 后才 HTTP media ACK，成功 ACK 才记录完成，失败标 `MEDIA_INCOMPLETE`；Session End/Encoder 清理仍有界。
4. Root `generated_media.py`、CLI `main` 汇总已提交 Core 的 receipt/inventory/hash，媒体失败单独 nonzero，不重标科学 success/failure；`none/first` 旧路径继续可用。
5. Root/Child 真实 Formal Pair 代码身份由 Root gitlink 精确绑定。没有发现需重审历史 H3 900EP、GPU7 EGL 或 B2 的新增理由。

作者 Evidence：`docs/collab/codex/evidence/2026-11-02_eval_v2_replan_all_author_cpu/`。直接读取 **四份原始 JUnit**：58 new +174 related+129 CPU Torch/Local +18 owned CPU runtime = **379 distinct passed /0 failed/0 errors/0 skips**；全部为作者 synthetic CPU。Ruff0.12.7 check、format、Git diff --check exit0；source binding22，artifact checksum73，前后 clean。10条 synthetic 32×32、3帧 MP4 +10回执+10 ACK 可从证据/测试对应；不替代真实 Cosmos/FFmpeg high-load 硬件 Canary 或 DS independent CPU Gate。

## 2. 当前必须修复的 Production blocker

### RM-ALL-R01 — **MEDIUM / Production** — 旧 Replan 的合法 ACK/Reservation 重放在后续 Replan 后失效，并能重新占用 spool

**准确位置：** Child `cosmos_framework/inference/robocasa_batch_transactions.py:94,149–181,559–597`。

**Root cause：** `self._acked_media` 按 `lease.session_id` 只保存**最后一条** `(request_key,payload_sha,receipt_digest,replan)`。第二次 Replan 成功媒体 ACK 会覆盖第一条。随后如果第一条已经完成的 authenticated reservation 因网络延迟、重复递送或请求重试再次到达，`reserve_media()` 的“already_saved”只检查最近一次 ACK，因此既不能识别早期已保存 Key，也**没有对 `frontier` 做已提交进度/过期校验**；它能向 `self._media` 新增一个 `RESERVED` 占槽。旧的 `media_ack()` 重放（携同一合法 receipt）会因 `_acked_media` 已被下一条覆盖而抛 `ValueError("unknown or changed strict media ACK replay")`。

**可直接按真实公开 API 验证的场景：**
- 同一个活跃 Session 内依次完成 Replan0 与 Replan1，各自 `reserve→predict→Encoder VIDEO_SAVED→media_ack`，确认 `media_jobs=0`。
- 在 Session End 前向 `/v2/media/reserve` 重新提交**完全相同**的 Replan0 reservation（`key0, sha0, index0, frontier0`）：当前代码会在内存预算允许时重新建立旧 Key 的 `RESERVED` job；期望应是 `already_saved=true` 且 `media_jobs` 仍为0，不得重复占用资源或触发视频再生成。
- 重发 Replan0 的合法 media ACK 及原收据：当前会 `ValueError`；期望幂等确认而不改变先前保存和确认事实。使用变更过的 hash/receipt/foreign lease 则必须拒绝。
- 多个迟到预留可占满4个 spool 名额，导致本来正常的新 Replan 被 429 backpressure、等待超时和 `MEDIA_INCOMPLETE`；用户要求的“丢媒体不发生”在此重试边界又出现了可避免的失败路径。

**Frozen contract violation：** 原始请求要求 `retry/replay` 不重复生成已保存媒体、ACK 在持久保存后才释放且丢包重试安全；Codex 自己的 implementation r1 §Sequence(1,8) 和 handoff 声称“Replay after completed ACK does not allocate another reservation or encode / lost ACK reuses same receipt”。当前实现只能保证**最近一个** ACK 的即时重试。新 tests `tools/v3/eval_v2_replan_tests/transport_test.py:245–285` 也只在**第一个 Replan 刚 ACK 后**回放这一条，没验证“多次 Replan 后旧 ACK/Reservation 迟到”的情况。

**精确可验收整改条件**：
1. 在保持身份/lease/frontier/receipt绑定与内存上限的前提下，对每个活跃 Episode 维护**有界的已保存媒体重放身份集合或等价不可重复准入 authority**，不能只留最近一次。Session End 可释放状态。旧 `key0` 的完整重放不得新建 reservation/改变另一条媒体；正确旧 ACK 返回幂等确认，任何 changed-key/payload/receipt/foreign-session 不得放行。
2. 新增**真实 `transaction_dispatch` 公开 API** 的确定性 CPU regression：同一个 Session 至少两条不同 Replan 成功→replay 第一条 reserve / media_ack，断言 `media_jobs==0`、`already_saved`、不重做 decode/Encoder、不影响 Replan1 及其它 Session；再测重放 mismatch 拒绝，压力多条旧重放不占4个 spool。保持其它379证据不篡改。
3. 新 Formal Root + Child/Gitlink 独立候选提交、作者 RED/GREEN（如可保留 old production RED）、Ruff/format/pytest Evidence，新的 GPT **增量** Gate。无需重构媒体架构、不批准 GPU 或 V3 merge。

## 3. 非阻断备注（不要扩大整改）

- **性能与额外开销需诚实描述**：Child `generated_video.py:54–75,105–132` 当前在每个严格 MP4 保存路径中对整段视频进行了第二次 CPU FFmpeg 全帧解码与 `fsync`，`read_receipt` 又计算文件 SHA；`generated_media.publish` 再复核文件 SHA。这**不是“只有一条很轻的 ACK”**，与 Owner 此前关心的完成确认开销有关。目前没有真实 Target-Host 耗时证据，不能无证据宣称很小或过大。本轮不要求重写视频校验设计；后续单独的小规模 GPU media Canary 应记录 per-Replan encode/inspect/fsync/drain 时间与整体吞吐，必要时在完成性不降低的前提下做性能优化。
- 合成10个 MP4 均来自同一套3帧 RGB 测试数据，现有测试主要证明数量、写盘/ACK 时序和索引。后续可增加不同 Replan 有不同内容的用例，以增强跨索引媒体内容绑定的 Evidence；仅是建议。
- 只有 `save_generated_video=all` 进入严格路径；900EP 视频策略由 Owner 手动决定。原有 H3 缺失的80个视频不会被此新实现追溯补齐。
- 未独立执行新代码/GPU，不将作者 379 CPU PASS 替代 DS CPU Gate。此前 GPU 分离/试运行的结论不自动转成新媒体修复实测 PASS。

## 4. Gate/授权结论

**`REQUEST_CHANGES`**，唯一当前 blocking production finding 为 **RM-ALL-R01 MEDIUM**。其余实现主线正向，要求一次精准跨 Replan 幂等整改与定向测试，不授权无限缓存或新增任务架构。旧 Pair `4b581493db805c92964cb27e740c736db87c0329` / `9a8cd6183424bfce245fbca393ca25ed59919ea6` 的 `APPROVE_CODE` 保持原样，新 Pair 未获得批准。未授权 DS_PRO GPU、900EP、正式 V3 promotion、修改 out2/NoTTT、Checkpoint/训练或访问 GPU0–3。

原作者交接：`docs/collab/codex/reviews/2026-11-02_V3_EvalV2_Replan_All_Durable_Media_Author_Handoff.md`；
冻结需求：`docs/collab/chatgpt/requests/2026-11-02_V3_EvalV2_Replan_Video_All_Lossless_Media_Fix_Codex.md`。
