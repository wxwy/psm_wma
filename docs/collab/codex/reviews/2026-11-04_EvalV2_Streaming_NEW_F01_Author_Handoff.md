# Issue #17 NEW-F01 — 窄整改交接与增量审核申请

日期：2026-11-04（Asia/Shanghai）。状态：**作者窄 CPU/static PASS；请求 GPT 增量 Code Gate**。不是新的完整作者 Gate、DS 验收或 GPU 性能结论。

| 对象 | 精确版本 |
|---|---|
| 新 Formal Root（唯一实现审核目标） | `551b03621507dde52303f54290d4fea89d66e8da` |
| Child / Root Gitlink（未改变） | `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e` |
| 上一 Formal Root | `00e119cc20cabe082974bd3495474b589c4b46b6` |
| 最近核对 official V3 | `470577f33db9a106d19cc3e477394f4ba278e538` |
| official V3 Gitlink | `1069fe78841228cadbbfbe6afbd767eaed6225da` |
| 隔离候选分支 | `v3-evalv2-streaming-newf01-20261104` |

后续包含本交接和 Evidence 的提交仅为 bookkeeping，不替代 Formal Root551b0362。原候选1c6f66ab及历史846/846证据保留，不改写、不重跑，也不将其计为新Pair验收。

## 1. 修复范围及行为

依据 [GPT NEW-F01 Review](../../chatgpt/reviews/2026-11-04_EvalV2_Streaming_M32_B32_00e119cc_82fa270e_REQUEST_CHANGES.md)。相对00e119cc，生产/测试路径仅两项：

- `scripts/robocasa_eval_v2/startup.py`：入场和完成共用 `_reconcile()`。锁外读取 owned RSS/GPU；锁内核验预约版本，不匹配则重测。完成时仅排除当前owner的预约，检查 **actual + 其他全部pending**；RSS全局计算，GPU逐卡计算。当前GPU没有其他pending时仍校验真实用量及测量存在性。预算校验和成功的预约insert/pop/版本更新处于同一短锁内。`finally`只清理仍指向本次reservation对象的条目，不会误删复用key。重试上限128次，持续争用以`BLOCKED_RESOURCE`失败，无新增等待或配置项。
- `tools/v3/eval_v2_streaming_tests/startup_completion_test.py`：新增23项确定性回归；旧测试/断言不改动。

Child完全不变；Runtime/调度/Store/Batch/Session/Local-TTT/媒体不改。**M/B Resume严格一致性、冻结Manifest及资源预算全部保持**。原V3审核文档通过普通合并保留（merge8bf312fb），没有覆盖官方历史，也没有把候选合入V3或G2。

该机制保证测量时的预算对账和预约元数据原子转移，仍依赖既有owned probe和Runtime故障清理；它不是操作系统内存硬限额，也未证明真实H100吞吐/显存。

## 2. 作者定向证据

[机器摘要](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_cpu/summary.json)；[完整原始证据包](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_cpu/cpu_evidence.tar.gz)；[窄增量补丁](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_cpu/incremental.patch)。

| 运行 | 实际结果 | 源码身份/说明 |
|---|---|---|
| old-red | **预期4 FAIL**；无error/skip | RSS/GPU × A/B先完成；旧代码均错误返回成功。旧production与00e119cc逐字节相等，Child82fa未变；执行HEAD为docs-only merge/claim e44feeba，新增测试untracked及外部副本，不能冒称旧Formal工作树完全干净。1235指纹前后一致。 |
| new-green（首次） | **33 PASS / 2 FAIL** | 21新预算unit及12原有回归通过。两新OS case的外部测试副本缺少按相邻路径引用的os_fixture.py，Server raw stderr为ENOENT/code2，未进入预算故障目标。原JUnit/log全部保留，不计为35PASS。 |
| os-green | **2/2 PASS** | 不改任何源码/断言，仅从工作树原路径运行这2项。off/required双模式；54.39s，exit0，source unchanged。冻结前working delta，与Formal源文件字节相同。 |
| **formal-targeted（最终）** | **35/35 PASS**；0failure/error/skip，exit0 | 干净Root551b0362/Child82fa；100.68s（pytest96.10s），**1239项源码指纹前后一致**。全部23新回归+12原有回归一次通过，没有deselect。 |

23新项覆盖：RSS/GPU×两种完成次序的70+40>100拒绝及回收后恢复；测量后C准入的版本交错；同时完成的旧样本重测；自身预约排除/恰好上限；逐卡隔离；持续预约争用有界失败；缺失/异常测量；双模式真实OS两Slot已活跃时的超限收束。测试资源计数为合成单位；OS进程/控制通道/Session/Store/Registry为真实CPU链路，不是实际分配70GiB内存的实验。

OS两新case均：真实1Server+2Sim，两个不同Episode/Slot活跃；原始错误`BLOCKED_RESOURCE: startup RSS reservation`；0有效Core、结果未合格、故障未假解除；pending0、activeJobs0；三owned进程身份和关闭收据对应，外部进程不在owned集合并存活。原始SIGTERM/BrokenPipe诊断保留，这是故障后的安全收束，不能称零故障/优雅退出。原有两模式并行4Sim及Server exit23/双Slot/外部隔离测试也通过。

静态检查Ruff/format/AST/diff-check全部PASS；[static.json](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_cpu/static.json)核验增量恰为上述两Python文件、其他生产路径与Child不变。AGENTS要求的另一Agent `review_requirements`只读审查未发现新HIGH/MED，核对了原始OS及失败证据；[记录](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_cpu/peer_review.md)。不代表GPT或DS批准。

测试文件同字节SHA256（RED外部副本/全部GREEN/Formal）：`eac4f96e774a66b2a691c0bdd9a48385dfa63c7ecdf0d071f69611e5e7c44b59`。旧startup：`1bdcc2a7313864ed2eac72aa1480b22fe74f2a43ffaa46f9a3331e8745ae2c8a`；新startup：`1c6e242f7299663aba22d1769df895e21c7523fc4823dbcc1a5591b7b1958de1`。

证据包545616 bytes、292 entries，SHA256：`a73c700396c4771ee61604acfbf3d0c6c692b6dd8c7a589d0203286598de32c5`。包含原始JUnit、log、命令/白名单环境、前后指纹、实际OS process/error/cleanup证明、静态补丁、透明外部记录脚本及同字节RED测试。未读取或复制远程服务器文件；不打包临时capability token文件。所有产物来自本地合成CPU fixture。

## 3. 可复核命令及后续边界

工作树`/workspace/work/psm-wma-streaming-newf01`；Python3.12.14、pytest9.0.2、Ruff0.12.7、Torch2.10.0+cpu。完整argv/env在每次[command.json](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_cpu/formal-targeted/command.json)中，外部脚本在证据包内。最终执行：

```bash
cd /workspace/work/psm-wma-streaming-newf01
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/eval-streaming-newf01-evidence/run_cpu.py \
  /workspace/work/psm-wma-streaming-newf01 \
  /workspace/work/eval-streaming-newf01-evidence/formal-targeted \
  tools/v3/eval_v2_streaming_tests/startup_completion_test.py \
  tools/v3/eval_v2_streaming_tests/resource_test.py \
  tools/v3/eval_v2_streaming_tests/startup_race_test.py \
  tools/v3/eval_v2_streaming_tests/startup_test.py
```

记录器固定CPU/OSMesa/offline/单线程BLAS环境，拒绝覆写证据目录，不包装项目函数、不改断言。记录器实际pytest命令含`--noconftest -c /dev/null -p no:cacheprovider --junitxml ... --basetemp ...`。

**请求GPT仅审核00e119cc→551b0362的NEW-F01增量与上述证据**，给出是否关闭源码blocker的正式结论。当前旧REQUEST_CHANGES未被作者自测撤销。新Pair完整作者CPU/DS Evidence Gate仍未执行；原统一入口会自动收集新增23项，预计总数869、以实际收集数为准。GPT增量复审通过并取得对应后续授权后再继续；本轮不运行完整Gate、不派DS、不跑GPU/真实模型/Canary/训练、不改R04、不合并V3或G2、不放宽Resume。
