# R09-B2 P4-v4 Execution-Preflight 设计 v0.5

**状态**：draft，待三方审核。本版只申请一次真实 P4-v4 execution preflight；不申请 P4 record/refreeze、P5 export/compose、torchrun、GPU 或训练。

## 1. 前置与唯一授权对象

静态 admission closure 已由 root implementation=`5e4d56a`、ChatGPT review history=`6eca65f`、MM/Kimi 同 SHA关闭；Gitlink 固定为 `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。执行前必须从 clean、可解析 source Git revision 和 frozen P1/P3/P5 authority 重算全部输入；任一 Git/current-byte、Gitlink、untracked 或 symlink drift 立即 FAIL。

本 Gate 唯一允许的副作用是为两个 backend 在一个新且原本不存在的 run root 下 copy-only materialize staging，并写入 candidate PASS/FAIL 文件。不得使用既有 run root、candidate root、staging root 或任何旧 P4/P5 evidence。

## 2. 精确命令与资源边界

经三方批准后，由单一 root stdlib preflight entry 在 CPU 上执行，环境为空白 allowlist，禁止网络、GPU、torch、torchrun、模型/数据/checkpoint I/O：

```text
python -I -S -B tools/g0/<reviewed-p4-v4-preflight-entry>.py --request <reviewed-request.json>
```

实际 entry 名、request SHA、source revision、new run root、candidate root、日志与 JSON 路径必须在批准后的 execution request 中逐项冻结；本设计不预填运行事实。执行者仅可运行该冻结命令一次。

## 3. 原子行为与停止条件

先验证双 backend 的 request、source、lexical interpreter、P5 final grammar、run token 与不存在性，再创建最终 `<run_root>/import_staging/<token>`。每个 staging 只允许一次 copy-only materialize；随后从最终路径重算 manifest、Python/ELF closure 和 readonly roster，并生成 P5-valid PASS payload，或生成唯一 FAIL payload。

任一 FAIL、异常、路径已存在、超出 allowlist 的文件、写入尝试、网络/GPU/torch/torchrun 迹象、pair 不完整或身份复用均立即停止；不得 cleanup、repair、rename、retry、record/refreeze 或发布 evidence。只有两个 backend 均 PASS 时，结果仍停留为 candidate，等待独立 record/refreeze Gate。

## 4. 产物与验收

预期候选根仅含两个 backend 目录。PASS 必为 v0.4 规定的三份最终 P5 payload 加不发布的 `candidate_link.json`；FAIL 必为 `request.json` 与 `failure.json`。验收由已关闭 static contract 的 `stage_atomic_publication()` 和 P5 `load_p4_v4_preflight()` 复验，且不写 Git、不更新 P5 authority。

本版请求 verdict：`APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY` 或 `REQUEST_CHANGES`（附 file:line）。
