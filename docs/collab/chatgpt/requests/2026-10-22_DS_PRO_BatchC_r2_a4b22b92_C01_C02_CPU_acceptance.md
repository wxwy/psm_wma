# DS_PRO — Batch C r2 C01/C02 定向独立 CPU 验收

日期：2026-10-22
来源：GPT 已完成该候选 C01/C02 增量技术审核，技术结论 APPROVE，详见 `docs/collab/chatgpt/reviews/2026-10-22_V3_RoboCasa_BatchC_r2_a4b22b92_c9f21040_incremental_review.md`。本文是验收范围，不是启动真实模型或仿真的指令。

## 精确对象

- Root：`a4b22b929175e462b6a8db57ad2abee7e220dd37`
- Child/Gitlink：`c9f21040f462a114d597fc83773cb9b6a9e96214`
- Vendor：`1ac174585293ed998ffc9cf73e47439798cf6f6c`，此轮未变，无需因此重建/安装运行中的Vendor。
- 使用新的隔离 clean worktree，不以 docs HEAD 代替 Formal Root；不 pull/checkout/update 正在训练的 G1 工作树。

## 边界

仅 CPU-only + 新外置证据；不修改生产源码、测试、Config、DCP、JobIdentity或vendor；不加载GPU模型、不启动真实Action Server/Kitchen；不要求GPU库存检查，不操作G1训练。慢动作分析为另一独立任务，不据此调整动作scale/normalization或control_mode。

## 最小执行集

用已有CPU解释器，设置 CUDA_VISIBLE_DEVICES=''、HF_HUB_OFFLINE=1、TRANSFORMERS_OFFLINE=1；pycache/HF/MPL/Numba日志放在源码外新目录。实际路径由现场填写，不能照抄作者 /workspace 路径。

先核验 Root HEAD、Child HEAD、Root Gitlink 和两个工作树 clean。然后在 Root 下运行：

```bash
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tools/v3/robocasa_eval_results_test.py \
  tools/v3/robocasa_processes_test.py \
  --junitxml="$EVIDENCE/results_process.xml" > "$EVIDENCE/results_process.log" 2>&1

"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q -s \
  tools/v3/eval_robocasa_queue_identity_test.py \
  --junitxml="$EVIDENCE/queue.xml" > "$EVIDENCE/queue.log" 2>&1
```

按作者最终测试清单，第一组125+23=148项，第二组35项+72subtests，合计183项+72subtests。以现场实际收集数和退出码为准；不能拿作者334项报告冒充这次只跑的183项。缺依赖/任何fail/error都STOP并保留记录，不修改断言或跳过。

Ruff0.12.7 check 和 format --check 使用 `--config cosmos-framework/.ruff.toml`，检查本轮六个变化Python文件：上述三个测试对应的 `scripts/robocasa_eval_results.py`、`scripts/robocasa_processes.py`、`scripts/eval_robocasa_18task_queue.py` 及三个测试文件。语法检查输出pycache应外置。无需重跑训练G1或全仓历史测试。

## 必须返回的行为证据

1. 完成与Resume两阶段：缺失/截断/错误Task或Attempt/顺序不完整进度，Local reset失败、缺失session或错误slot均拒绝；旧文件bytes不变。
2. 真实 Queue synthetic Resume：先COMPLETE，再损坏进度/Attempt/cleanup，第二次返回非零，Server/Simulator启动次数不增加，不跳过伪完整任务。
3. 在线错误Attempt进度：任务FAILED/INCOMPLETE；正常流程仍通过。
4. 环境视频关闭、generated first/all开启：每任务及总summary中 rollout_mp4s=[]，generated_mp4s正确；失败片段保留且不计为完整结果。
5. 测试结束不遗留自有进程/线程；原有wrong checkpoint/config/chunk、foreign listener、超时与cleanup错误不被吞掉。

归档 exact Pair、命令/解释器/RC、原始stdout/stderr/JUnit、Ruff结果和前后clean状态。无需再证明已关闭的旧设计，也无需把本地Evidence先push成功才报告；沿用Owner接受DS现场报告的方式，明确实际执行范围。

## 完成后

回传GPT进行同Pair Evidence closure，未变SHA不重新做代码审核。作者完整四组334+72的复现记录在 `docs/collab/codex/evidence/2026-10-22_RoboCasa_Batch_C_r2_evidence_integrity_author_cpu/commands.json`，需要扩展时可参考，但不要与本定向验收数量混算。

成功不自动授权真实仿真。后续实际sim环境的 --dry-run、vendor import/物理验收、模型加载和Owner手动canary→4×5→18×5仍按独立执行边界处理。