# PSM-WMA V3 EvalV2 Phase B — Author Full CPU435 Evidence Gate

**Date:** 2026-10-30

**正式作者 CPU Evidence verdict：`PASS`（仅作者完整合成CPU Gate）。** 本轮独立审核原始执行证据，未重新审核上一轮已经批准、且正式技术 Pair 未变的源码。**DS_PRO independent CPU Evidence Gate 仍为 `PENDING / OPEN`，不能继承作者 PASS。**

| Identity | Exact SHA |
| --- | --- |
| Formal Root | `a139b5a35877a79e0a56c2208f3002f731972b11` |
| Formal Child / Gitlink | `0ae313e329d290fc6b8a50fda1112820fb7ac485` |
| 既有 F4-P1 incremental Code Gate | `APPROVE_CODE`，Review 位于 V3 `docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_F4P1_InFlight_Snapshot_a139b5a3_0ae313e3_APPROVE_CODE.md` |
| 作者 Evidence bookkeeping commit | `2c2f590093ae7d1f8d97b828bb6113487960b1fc`，仅后续Evidence/交接记录，不是新 Formal Root |
| 上次 V3 docs-only HEAD | `8944539165b297ba426cfa203a5d0a95b02d5d38`（本轮文档追加不代表候选生产合并） |

## 1. Gate原始执行内容 — independently reviewed raw artifacts

直接通过 GitHub connector 读取 `2c2f590093ae7d1f8d97b828bb6113487960b1fc` 下 `raw/gate.json`、`raw/{inference,phase_a_regression,phase_b_runtime,junit}.xml`、各自原始 log、`raw/{import_origin,ruff_check,ruff_format}.log`、`raw/shell-exit.txt`、`raw/source_sha256.json`、`source_after_independent.json`、`source_gitblob_bindings.json`、OS事件与ledger/receipt/Server日志原件、`original_to_published.json` 和 `artifact_sha256.json`。

| Group | Real JUnit collected | Passed | Failures | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| inference | 145 | 145 | 0 | 0 | 0 |
| Phase A regression | 256 | 256 | 0 | 0 | 0 |
| Phase B runtime | 34 | 34 | 0 | 0 | 0 |
| **Total** | **435** | **435** | **0** | **0** | **0** |

`raw/junit.xml` 中435个**互不重复**的 testcase 身份与三套原始 XML 拼接在**顺序和成员上完全一致**。此处为源文件XML逐个读取核验，而非只引用作者汇总。六个既定 Gate Steps（import origin、Ruff check、Ruff format、inference、Phase A、Phase B）`exit_code=0`；`raw/shell-exit.txt=0`；`raw/gate.json.status=PASS`，`source_unchanged=true`，`syntax_files=30`。`import_origin.log`真实指向 Formal Root 隔离工作树的 Child package，不是外部pip或V3的另一个版本。

**科学边界：**其中 `test_900_exact_episode_major_dispatch_real_store_path_and_index_no_model_per_episode` 是 **synthetic900 CPU regression**，不是 18任务×50真实RoboCasa Episode 评测；没有真实Cosmos/WAN GPU、EGL、DCP或训练。

## 2. Identity与原始归档完整性

- Gate三项身份精确等于冻结Root/Child/Gitlink；`raw/source_sha256.json` 原始54项哈希与 `source_after_independent.json` **54/54 完全一致**，两worktree前后均 clean。
- `source_gitblob_bindings.json` 中 **62/62 GitBlob**（54 frozen watched +8重要补充）逐一对照了 GitHub 对应 Root `a139b5a35877a79e0a56c2208f3002f731972b11` 与 Child `0ae313e329d290fc6b8a50fda1112820fb7ac485` **非截断完整Git树**；无错误SHA、错仓、错版本或缺失对象。
- 证据提交中的 `original_to_published.json` 201项原件映射与 `artifact_sha256.json` 的记录一致，`artifact_sha256.json` 为209件文件建立manifest，归档210件（含清单自身）；没有manifest缺失或映射指向不存在的文件。它们提供来源/逐文件hash链；除已单独读取的关键原件外，不冒称GPT重新计算了所有归档字节的SHA256。
- 此次是一份**作者运行**；GPT做了独立GitHub静态回读、哈希/绑定/行为证据核验，**并没有在同环境独立运行CPU pytest**。DS自主CPU运行未开始。

## 3. Contract → behavior → real OS evidence

**F4-P1 / Phase A**：原始 `phase_a_regression.xml` 确认本轮同时执行并通过 F4 同锁快照、上次READY脆弱性测试和完整synthetic900。原日志 `V2_PROGRESS_SNAPSHOT_WITNESS` 记录 `copy_held_writer_lock=[true]`，`GPU0/GPU1` 在进度读取期间完成、`valid=2/error=None`；synthetic900 witness 报 900次DISPATCH、50次ROUND_BARRIER、450成功/450失败、3个physical_slots与3个mock模型载入。由于旧作者434失败只存了`repr(error)`，本次作者435 PASS不能反过来证明历史错误的内部抛错栈。

**Native B>1 / 多 Sim**：原始CPU fixture实际Server日志而非人工假想时间:
- `G1_N2_E2`：**一个Server/两个Sim**，`CPU_NATIVE_BATCH` 调用5次，真实大小分布 B1×2+B2×3（共8个成员请求），4个有效Core，二者执行时间重叠。全部3个owned进程关闭回执显示`live_group=false`；`summary.results_qualified=true`。
- `G2_N3_E1`：两个不同Server PID，B1×4+B2×1（6成员请求），3个有效Core；三个Sim的真实时间区间可重叠。
- `G1_N3_E1`：一个Server、两个Sim，B1×4+B2×1，3个有效Core；时间区间重叠。测试仍按每Server有界窗口动态收集，不假定每个GPU拓扑必B2。
- JUnit 正式通过的原用例还验证每成员Session/Prefix/Prediction、D5 Round Barrier、完成后Resume不再次启动模型或Sim、原Core结果字节不变；独立RAW文件亦归档了可公开的prediction/ledger片段。**Resume byte parity和foreign-process survival没有额外单独原始比较工件，证据为原测试断言；不伪造独立证明。**

**F3故障 / Store**：原始 `F3_server_death/logs/GPU0_server.log` 记录真实`CPU_SERVER_FAULT`，同一Owner的两个独立Slot Ticket分别处于`GENERATING`和`QUEUED`，`native_size=1`；真正Server进程关闭回执 `returncode=23`、3个owned清理回执全部 `live_group=false`且`remaining_pids=[]`。失败任务 `valid=0/results_qualified=false`，两个Task均留下`core_invalid/coordinator_stop/process_cleanup`故障记录，不把失败解释成合法成功。单独Store并发受控测试留下两条不同UUID记录，`core_invalid`与`coordinator_stop`对应的`core_committed_at_fault=false`。

**其他：**已有 F1 端口不同loopback拒绝负例2项及F2 三拓扑测试在 Phase B 正式 JUnit 中；作者此次使用的Gate Ruff/format冻结30文件检查通过，新F4 regression此前的focused Code Gate已单独检查Ruff、AST与Hash，本轮完整Gate也执行了该case，不将30文件静态列表冒充已包含新regression文件。

## 4. Gate Closure 与唯一下一步

**结论：`PASS` — 作者完整 CPU435 Evidence Gate 可以关闭；此PASS仅覆盖合成CPU完整candidate，**不是 **DS_PRO独立CPU**、真实模型GPU、真实RoboCasa以及正式900的准入证明。

**下一步下发DS_PRO一次独立完整CPU replay**。在其训练服务器创建全新隔离的干净detached Root `a139b5a35877a79e0a56c2208f3002f731972b11` + 完全一致Child `0ae313e329d290fc6b8a50fda1112820fb7ac485` worktree，使用已验证的CPU环境、外部从未存在的Evidence路径执行同一现有入口：

```bash
python tools/v3/run_eval_v2_batch_b2_cpu_gate.py \
  --root-worktree '<DS_NEW_EXACT_CLEAN_ROOT_WORKTREE>' \
  --expected-root a139b5a35877a79e0a56c2208f3002f731972b11 \
  --expected-child 0ae313e329d290fc6b8a50fda1112820fb7ac485 \
  --evidence-dir '<DS_NEW_EXTERNAL_EVIDENCE_DIR>'
```

**DS标准：**一次完整 **145+256+34=435/435**、0失败/错误/跳过、shell0、Gate `PASS`、`source_unchanged=true`、完整真实CPU OS B2/G1、G2多GPU模拟、F3 Server exit23与全部owned清理、D5/Resume及F4 快照证据；DS独立原始JUnit/log/Gate/source前后哈希和非复用证据目录。不得在运行训练worktree checkout/reset/clean；不能改production/fixtures、降低断言、反复重跑来抹除首次失败。若DS出现新首错，保留原始FAIL并报告第一个error，不自动归因于环境。

**后续只有**：DS结果→GPT证据审核→由Owner另行决定受控V3/Child生产合并、1GPU M2/B2真实Cosmos/RoboCasa Canary→再独立授权正式18×50。此次未执行或授权任何真实GPU、训练、checkpoint、DCP、Canary/900或V3生产合并；无新架构阶段、无重复Code Gate。

## 5. 相关ref

- [作者完整归档](https://github.com/wxwy/psm_wma/tree/2c2f590093ae7d1f8d97b828bb6113487960b1fc/docs/collab/codex/evidence/2026-10-30_eval_v2_author435_after_F4_PASS)
- [上一完整源代码Approval](https://github.com/wxwy/psm_wma/blob/8944539165b297ba426cfa203a5d0a95b02d5d38/docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_F4P1_InFlight_Snapshot_a139b5a3_0ae313e3_APPROVE_CODE.md)
