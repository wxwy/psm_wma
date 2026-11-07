# PSM-WMA V3 — Issue22 Local-TTT Pipeline Child Candidate Independent Review

- 日期：2026-11-07（Asia/Shanghai）
- 范围：**候选 Child 的静态源码与作者 CPU Evidence 审核**。不是新 matching Root/Child Formal Pair、不是 GPU/性能/生产 Gate closure。
- Child candidate：`5fe2b8def58f4caae8c63581ed3649ac8fb3e0c6`
- Parent / Official V3 Gitlink：`1ca308055fc41fb69efaeb9efaa23808f164a18e`
- 审核时 Official Root V3：`2ff873bde87465a2cc8815eb801d69692f54a396`，Gitlink 保持旧 Child。
- 本记录存放在 `v3-local-ttt-pipeline-issue22-20261107` **隔离文档分支**；不修改 official V3。
- PR：https://github.com/wxwy/cosmos-framework/pull/4（Draft/unmerged）；独立 GitHub review id `5809229710`。

## 1. 结论与边界

**Candidate CPU 静态审查：没有在已审生产代码和已归档 CPU 证据中确认 HIGH 级合同违例。** 实现主线与冻结需求基本相符，但 **real DCP/H100 BF16/FSDP/完整 RoboCasa、真实 P50/P95 和 Ep/h 尚未执行；Hardware / Integration / Performance Gate OPEN**。当前不发出正式 `APPROVE_CODE` 或其他 formal closure literal。作者的 428 CPU PASS 不是 GPT 复跑，不可冒充真实 GPU 结果。

GitHub 作者交接 https://github.com/wxwy/psm_wma/blob/39ba3eb4bf49dbbbe77d4e1bc85407c369820746/docs/collab/codex/reviews/2026-11-07_Issue22_Local_TTT_Pipeline_5fe2b8de_Author_Handoff.md 。原始作者 JUnit `artifacts/local_ttt_pipeline/2026-11-07_issue22_cpu/author-final/junit.xml`、摘要 `final_summary.json`、数值 `numeric_witnesses.json` 已从远端读取。Junit testsuite 元数据：428 tests、failures0、errors0、skipped0、exit0（按作者原始 runner/summary）。保护目录 model/trainer/configs/checkpoint/data/evaluation 相对 parent 树 SHA 未变。候选 Commit parent GitHub compare：ahead1/behind0，20 Python changed files（12 source +8 new tests）。

## 2. 已审核实际链路

1. `robocasa_composite_visual.py:77-254`：实际 Policy Wan T1 Encode1 外层严格抓取裁切前完整 latent，验证 prepared 输入、尺寸、dtype、顺序、参数冻结，输出 `Visual96`。不是添加第二次编码；不匹配 fail-closed。
2. `local_memory_pipeline.py:123-179,236-340`：完成证据按精确 Session/Lease/step 认证，有界 admission；首帧匹配前一 Policy boundary digest 并复用 Visual96，其他15帧独立 Encode1；接单步 `compute_completed_step`，candidate 不发布直到 Replan commit。
3. `local_memory_online.py:160-281`：T1 model-owned scan，`create_graph=False`、fast-state detach carry、telemetry 合并；precomputed candidate 必须匹配已提交锚点。
4. `robocasa_batch_transactions.py:_pump/_execute_completed/_execute_many`：原有 model executor 调度，Replan 在 completed dependencies 未就绪时不能提前封口并阻塞自身；仍以原原子 response/fast/visual commit 为 authority。
5. `local_memory_pipeline_client.py` 与 `eval_v2_transactions.py`：动作完成后复制/上传证据，Sim 继续执行；HTTP admission ACK 不清除 prediction ledger，等待 Replan ACK 后清除。No-TTT 不启用流水线。
6. `robocasa_local_memory_pipeline_test.py`、`robocasa_local_pipeline_transactions_test.py` 等现有测试覆盖 changed replay, out-of-order, capacity, cancellation/close/quarantine, session isolation, no-future frame。测试存在并覆盖这些情形，但本审核不把作者成功计数当成独立硬件验收。

## 3. 数值证据与开放风险

- 作者 `numeric_witnesses.json` 12 组 T16 vs 16×T1：FastState/Prefix max_abs=0，累计 inner telemetry 最大绝对偏差 `3.814697265625e-6`；3 组 online action projection diff0。
- 作者对 generated tiny Wan BF16 CPU 分别比对 Policy pre-crop latent 与独立 Encode1，shape `[1,48,1,H_z,W_z]`、Visual96 bit-exact。**不是**生产真实 DCP / H100/CUDA 检验。
- 代码计数目标单 interval：首帧借用上一 Policy capture + 15 次新的单图 Encode1、16 次合法更新。注意实际的编码调度与 Policy 都在同一模型执行器共享 GPU6/7；尚未测得真实吞吐。
- **Evidence gap（硬件下一 Gate）**：真实 checkpoint/H100 BF16 数值对齐、真实 M16/B8 / 双 Server 完整闭环、No-TTT 防退化、GPU 争用/公平、故障/Deadline canary、P50/P95 分项及 Ep/h before-after。未授权则不得运行。
- **性能风险而非已证实代码 bug**：`RoboCasaLocalMemoryPolicyAdapter._parse` 在 Replan 仍会验证/解码并 hash 全部历史 PNG；其成本与 completed work 共享 model executor 的竞争，需要真实 Profile。不得从“少一次 Encode1”推断 3 秒 Prepare 一定消失。

## 4. 与 L2000 失败的独立关系

L2000 和 L4000 正式运行的现场 root/child 分别 `c447d9f4cc1bb5fe2dd79ca527c5a8e246565ada`/`1ca308055fc41fb69efaeb9efaa23808f164a18e`，与候选 Child `5fe2b8de` 不同。L4000 同旧源码成功900/900；L2000 FAILED_GATE：valid751, invalid32, pending117, unresolved80；`last_failure.json` 记录 `EOFError('actor control socket closed')`。另在 GPU7_S5 模拟日志见 `TimeoutError: original transaction deadline exhausted` 位于 Local Session cleanup/`client.end`，多个 Actor 随后报告控制连接关闭；**未确认最初触发点**。不能把 L2000 失败归责于尚未合并的 PR #4。

## 5. 对 Codex/Owner 的 handoff

- 保持 Child PR Draft/unmerged、V3 Gitlink 不变；不得复用任何旧 run Episode/修改已有 checkpoint。
- 若进入正式实现 Gate，应先以当时最新 official V3 冻结匹配 Root/Child Pair，再申请新的独立 real CPU/GPU 验收；GPU 仅在 owner 明确授权/空闲条件下执行。
- L2000 故障诊断、独立 Fresh900 重测应单独跟踪，不应与候选新 pipeline 性能评测混合。
- 本记录和 PR Review 是 **candidate-level independent feedback，不是 formal approval/rejection**。若要形成 formal verdict，仍必须按审核规范以 precise formal pair 形成详细 review + append-only CODEX_INBOX 并明确 Gate literal。
