# GPT 独立增量 Code Gate — Issue #17 NEW-F01 修复复审

**日期：2026-11-04**  
**正式技术 Verdict：`APPROVE_CODE`（仅 NEW-F01 窄增量代码闭环）**  
**历史状态：`HIGH NEW-F01 → CLOSED`**  
**仍需后续 Gate：新 Formal Pair 完整 CPU Gate / DS 独立 CPU 验收 / 经 Owner 另行授权的真实 GPU Canary。**

## 1. 精确 Formal Pair 与审核范围

| 对象 | SHA |
|---|---|
| 新 Root formal implementation | `551b03621507dde52303f54290d4fea89d66e8da` |
| Child / Root Gitlink（完全不变） | `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e` |
| 上一 Root formal implementation | `00e119cc20cabe082974bd3495474b589c4b46b6` |
| Codex 新证据/交接 bookkeeping | `ebaec6452cb62dd96bae3dcbc313f305ea14c79c`（不替代 formal SHA） |
| 受检隔离分支 | `v3-evalv2-streaming-newf01-20261104` |

GitHub 实际读取了新 commit、完整旧→新 compare、Root Tree Gitlink、新`startup.py`、新增`startup_completion_test.py`、作者`summary.json`/`static.json`和交接文档、上一轮 GPT `REQUEST_CHANGES`。确认 Root 所含 Child Gitlink 与冻结 Child SHA 精确一致。Root 为新的技术 target；证据提交是账本，不得继承技术 verdict。

增量比较显示有历史 V3 文档审查和合并账本提交，但**实际被修改/新增的生产与测试文件仅两项**：

- `scripts/robocasa_eval_v2/startup.py`（生产，`+40/-18`）；
- `tools/v3/eval_v2_streaming_tests/startup_completion_test.py`（新增测试，327行）。

没有 Child / `runtime.py` / `config.py` / `identity.py` / `store.py` / `scheduler.py` / Local-TTT / Media / G2 / 模型 / 训练改动。本轮不是重做上一 Formal Pair 的全量 Code Gate。

## 2. OLD HIGH NEW-F01 — CLOSED

**上一轮阻断点**：[NEW-F01 `REQUEST_CHANGES`](https://github.com/wxwy/psm_wma/blob/470577f33db9a106d19cc3e477394f4ba278e538/docs/collab/chatgpt/reviews/2026-11-04_EvalV2_Streaming_M32_B32_00e119cc_82fa270e_REQUEST_CHANGES.md)。

### 2.1 实际 production 修复

[新源码 `startup.py`](https://github.com/wxwy/psm_wma/blob/551b03621507dde52303f54290d4fea89d66e8da/scripts/robocasa_eval_v2/startup.py)：

1. `reserve()` 入场和成功完成都通过同一 `_reconcile(key,reservation,complete=...)`。入场校验 `owned_actual + 全部existing reservations + new reservation`；完成校验 `owned_actual + 除本次reservation以外的全部outstanding reservations`，**不是只看实际RSS或GPU**。RSS是总量，GPU按物理设备分别对账，测量GPU覆盖本次及其他device。
2. `measure()` 在metadata锁外；锁内检查 `version` 是否与测量前相符。若其他预约insert/pop改变version，则重新取真实测量，成功的预算检查与本次insert/pop及version递增在同一短锁内完成。
3. 完成时不重复加计本Owner已兑现的预约；仍保留其他Owner的预约。超预算、缺失计量或版本持续争用均fail-closed，最大128轮重试，没有无限等待或静默上限放宽。
4. `finally` 只删除 `pending.get(key) is reservation` 的同一Owner条目；成功完成时无多余删除，出错时释放自身预约，不会删除另一Owner/复用key的占位。Runtime既有`stop`、owned进程关闭和单次Core权威不变。

### 2.2 冻结失败交错已被针对性验证

作者证据：[NEW-F01 handoff](https://github.com/wxwy/psm_wma/blob/ebaec6452cb62dd96bae3dcbc313f305ea14c79c/docs/collab/codex/reviews/2026-11-04_EvalV2_Streaming_NEW_F01_Author_Handoff.md)、
[`summary.json`](https://github.com/wxwy/psm_wma/blob/ebaec6452cb62dd96bae3dcbc313f305ea14c79c/artifacts/eval_v2_streaming_newf01/2026-11-04_author_cpu/summary.json)、
[`static.json`](https://github.com/wxwy/psm_wma/blob/ebaec6452cb62dd96bae3dcbc313f305ea14c79c/artifacts/eval_v2_streaming_newf01/2026-11-04_author_cpu/static.json)。

- **RED**：同一测试文件下，旧 production 字节指纹与上一正式 `startup.py` 一致；RSS/GPU × A先完成/B先完成 四项均按预期 FAIL（测试进程的Root因 docs/测试在建，未冒充旧完整干净Formal工作树）。
- **GREEN**：新 Formal Root `551b0362`／精确Child，`35 passed / 0 failed / 0 errors / 0 skipped`，运行命令退出0；新增23项+已有12项，`source_unchanged=true`。两项早期OS测试路径依赖异常属于开发历史，正式干净精确Pair的35项均通过且无deselect。
- 新测试覆盖：`70 actual + 40 other reserved > 100`（RSS/GPU、A/B顺序）必须拒绝；另一预约变化触发version重测；边界等于100通过；独立GPU预算；双并发完成；128次争用停止；缺失/抛错测量；both `off|required` 模式实际OS 1Server+2Sim的过预算fail-closed、无有效Core、owned退出/收据完整、外部进程不被杀。
- Ruff、format、AST、diff-check通过；作者报1239源码条目字节指纹在测试前后一致，Child/M/B/Manifest未改。

**审查者的独立结论：** 源码中已能直接对应旧 finding 的并发完成/释放反例，逻辑与定向证据吻合，现有 NEW-F01 的根因与验收条件达到关闭标准。**`CLOSED`，不是依赖作者“35 PASS”一项独断。**

## 3. 新 finding / 限制

本增量未发现新增 HIGH/MED 生产代码阻断项。该预算模型是**有界、基于owned进程实际测量的启动准入**，不是Linux cgroup硬内存隔离；真实进程占用可能在相邻计量之间增长，因此不能对外承诺永不出现瞬时OOM或超预算。128轮version重试在极高争用下可保守失败，这是有意fail-closed，需要硬件Gate观察。

重要冻结约束：

- **M/B Resume严格一致性未修改、未放宽。** 新增代码完全没有动 Manifest构造、execution配置或Resume比较；不能因本Gate改变Run的`sims_per_gpu`/`max_infer_batch_size`。
- 新streaming目前还将RSS/Startup预算冻结进Manifest；本轮未授权更改。后续如需沿R04模式仅增RSS并Resume，需Owner另行指定新科学/部署语义，不可暗中放宽。

作者35项是本增量的**定向作者CPU Gate**；GPT独立阅读了真实源码及证据清单，但没有独立在干净工作树复跑完整846+新增项，未运行H100/真实64OS Sim/实际RoboCasa物理环境。不应将此`APPROVE_CODE`当作全功能与实机吞吐认证。

## 4. Verdict/下一权限

**`APPROVE_CODE` — Issue#17 NEW-F01 narrow remediation; HIGH NEW-F01 CLOSED。**

这只关闭当前精确 Formal Root/Child 的 startup reservation 增量源码 blocker。下一阶段应由 Codex 对**新精确Pair**运行完整统一作者CPU Gate（旧846项 + 新23项的收集总数以真实JUnit为准），然后提交 DS 对同Pair的独立CPU验收。两项均不应挪用旧Formal的846项作为新Pair的完整验收。

**明确不授权**：V3 candidate promotion、G2合并/覆盖、修改R04或其他活跃服务器运行、启动GPU/H100、正式900EP、模型/数据/训练或自动扩大资源预算。后续真实硬件Canary单独申请Owner授权。若Formal pair后续没有代码变更而只新增账本，不重复技术审核。

正式 verdict 的持久化条件为本`docs/collab/chatgpt/reviews/`文件 + 向canonical `CODEX_INBOX.md`追加同一精确Pair和决定。
