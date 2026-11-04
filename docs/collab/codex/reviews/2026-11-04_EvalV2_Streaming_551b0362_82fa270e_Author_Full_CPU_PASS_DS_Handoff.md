# Issue #17 — 新 Formal Pair 完整作者 CPU PASS / DS 交接

日期：2026-11-04（Asia/Shanghai）。结论：**AUTHOR_FULL_CPU_PASS，869/869；DS_INDEPENDENT_CPU_PENDING**。

| 对象 | 精确版本 |
|---|---|
| Formal Root（实现权威） | `551b03621507dde52303f54290d4fea89d66e8da` |
| Child / Root Gitlink | `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e` |
| GPT Code Gate | `APPROVE_CODE`，NEW-F01 CLOSED |
| 正式审核所在 V3 | `9635cefe3208ab6320ba5fa70b0e0d68fd444790` |
| 隔离归档分支 | `v3-evalv2-streaming-newf01-20261104` |

依据：[GPT 正式复审](../../chatgpt/reviews/2026-11-04_EvalV2_Streaming_NEW_F01_551b0362_82fa270e_APPROVE_CODE.md)。本轮实际执行了一次新Pair的完整统一作者CPU Gate，没有复用旧00e119cc的846项，也没有把定向35项追加到旧结果充当完整验收。**实现及测试入口均未修改，后续归档/账本提交不是新Formal Root，不申请重复源码审核。**

## 完整运行结果

| 测试组 | 实际唯一用例 | FAIL / ERROR / SKIP | Gate step秒数 |
|---|---:|---|---:|
| inference | 182 | 0 / 0 / 0 | 32.01 |
| Phase A regression | 278 | 0 / 0 / 0 | 391.46 |
| Phase B runtime | 234 | 0 / 0 / 0 | 157.86 |
| media / replans | 89 | 0 / 0 / 0 | 68.01 |
| streaming（原63 + 新23） | 86 | 0 / 0 / 0 | 479.68 |
| **合计** | **869 / 869 PASS** | **0 / 0 / 0** | |

Shell exit **0**；`gate.status=PASS`；`source_unchanged=true`。90项受监控源码前后SHA256一致；外部只读后核验再次逐文件复算一致，保存`source_sha256_after.json`。66个静态文件的Ruff0.12.7、format、AST通过；导入来源确认来自精确Child工作树。Root/Child的HEAD、Gitlink及干净状态前后均一致，合并JUnit具有869个唯一`classname/name`。

[最终机器摘要](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_full_cpu/final_summary.json) · [原Gate JSON](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_full_cpu/gate.json) · [原始合并JUnit](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_full_cpu/junit.xml) · [Shell退出码](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_full_cpu/author-full-after-code-review.shell.exit)。各组原始XML/log、环境、命令、前后指纹均可直接浏览；完整测试临时Store/进程/OS证明在证据包中。

## 行为证据与解释范围

- 原Phase A合成900用例完成900有效Core、450 success/450 failure、0pending、`clean_execution=true`，不是实际模型SR结论。
- M32/B8及M32/B16两组均为18Task、64个物理Slot状态机、900个唯一Core、900个唯一Session及2个Policy owner。逐Core sealed哈希/身份、Task/EP唯一性、64Slot覆盖、请求总量及Batch cap均经后核验；另一Agent只读核对了7200个Core inventory文件哈希和同Task多EP重叠。CPU模型/物理/进程边界使用fixture doubles，真实OS小场景独立验证启动与回收。
- 两组流水线实际最大Native Batch分别为3和2，主要B1/B2；这是受控CPU到达过程的观察，**不证明B8/B16饱和、真实64OS Sim或H100吞吐**。配置cap、独立M/B容量、Session隔离及B32 carrier契约由统一Gate相应用例覆盖。
- NEW-F01的off/required两个真实OS用例均在双Slot活跃时触发`BLOCKED_RESOURCE: startup RSS reservation`，不提交有效Core；预约/jobs归零，1Server+2Sim三个owned进程关闭/收据对应，outsider在Runtime清理时存活。原Server exit23、双Slot并发、外部进程隔离及双模式并行启动用例继续通过。故障清理中的SIGTERM/BrokenPipe原诊断保留，不能称所有fixture均无runtime故障。
- CPU测试确有微型DCP API调用，例如Child `robocasa_dual_mode_test.py:268,300,353`使用临时目录、单元素权重/2×3小线性层生成DCP以验证checkpoint-mode身份。**未读取真实训练checkpoint或数据集，未启动GPU/训练/真实RoboCasa评测。** 原Gate粗粒度字段`gpu_native_model_simulation_dcp_training=NOT_RUN`原样保留，不能将其解释为完全没有调用DCP库；[范围说明](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_full_cpu/evidence_scope.md)明确区分。

按AGENTS要求，另一Agent `review_requirements`进行了只读作者Evidence核对，没有重跑测试、修改文件或充当DS：[核查记录](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_full_cpu/peer_evidence_audit.md)。

## 执行与归档

执行环境：既有CPU venv，Python3.12.14 / Torch2.10.0+cpu / pytest9.0.2 / Ruff0.12.7；约5vCPU/17GiB RAM，单线程BLAS，OSMesa、离线cache全部在外部证据目录。执行工作树是单独新建、干净detached的精确Pair；bookkeeping工作树分离。完整命令：

```bash
cd /workspace/work/psm-wma-streaming-newf01-formal
CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 \
  /workspace/.venvs/psm-wma-cpu/bin/python \
  tools/v3/run_eval_v2_streaming_cpu_gate.py \
  --root-worktree /workspace/work/psm-wma-streaming-newf01-formal \
  --expected-root 551b03621507dde52303f54290d4fea89d66e8da \
  --expected-child 82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e \
  --evidence-dir /workspace/work/eval-streaming-newf01-evidence/author-full-after-code-review
```

外层Shell的完整重定向及退出码保存命令在`author-full-launch-command.txt`；未包装Runtime或改变断言。原统一入口使用`-x`遇首错停止，并拒绝已有/位于工作树内的证据目录。

Evidence：`artifacts/eval_v2_streaming_newf01/2026-11-04_author_full_cpu`。
[完整原始证据包](../../../../artifacts/eval_v2_streaming_newf01/2026-11-04_author_full_cpu/cpu_evidence.tar.gz)：**13,664,718 bytes，107,474 entries**；SHA256 **`763f6e9105ae3ea5358edff2d7f90ab99b24517467c6750caa41672fce080b4a`**。压缩包校验及目录回读通过；含全部本次原始日志/JUnit/Store/OS证明、后核验脚本及命令。只排除依赖cache、bytecode和临时Server capability token文件，原始断言/错误诊断/日志空白不归一化。没有读取、复制或传输远程服务器文件；全部来自本地生成的CPU fixture。

## DS 下一步（交接命令，未由Codex执行）

DS应准备自己的独立干净CPU工作树及新证据目录。**checkout精确551b0362 / Child82fa，不能直接使用证据分支HEAD作为expected-root。** 使用匹配CPU环境（Ruff必须0.12.7），执行同一入口：

```bash
cd /workspace/work/ds-streaming-newf01-formal
CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 \
  /workspace/.venvs/psm-wma-cpu/bin/python \
  tools/v3/run_eval_v2_streaming_cpu_gate.py \
  --root-worktree /workspace/work/ds-streaming-newf01-formal \
  --expected-root 551b03621507dde52303f54290d4fea89d66e8da \
  --expected-child 82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e \
  --evidence-dir /workspace/work/ds-streaming-newf01-evidence/full-01
```

路径为独立执行建议，DS须使用未存在的目录并自行核验环境；不得复用作者cache、工作树或作者PASS代替独立执行。预期约869项，以实际JUnit为准，要求零fail/error/skip、shell0、gatePASS、源码不变、完整原始证据；失败保留首错后停止，不能由DS改生产代码或断言。

当前仅完成作者完整CPU阶段，**DS独立CPU仍PENDING**；通过其对应验收后再由Owner决定真实GPU Canary。M/B Resume和资源Manifest冻结全部保持；未合并V3、未整合G2、未操作R04或其他活动运行，未启动GPU/真实模型/训练/正式900Episode。
