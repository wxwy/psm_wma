# R09-B2 P5 Full Resolved-Config Diff 静态设计 v0.1

**状态**：draft；仅申请后续 root-side 静态 exporter/verifier/tests 实现，尚不执行。

## 目标

P5 冻结同一 P4 v2 D005 recipe 在 recurrent 与 `ttt_fast_weight` 两套显式、净化环境下的
完整 resolved config，输出 machine-readable canonical JSON 与逐 path diff。它证明除实际 backend
控制面以外两侧配置相同；不替代训练，也不读取 checkpoint/数据/VAE。

## 输入与导出

- 固定 recipe、P4 v2 D005 recurrent/TTT record、P1 production manifest、P3 attempt-6 inventory
  与 Gitlink `21d064f`；所有文件 SHA256 记录在 artifact provenance。
- exporter 只解析 structured TOML/config，并以 D005 `environment.set` 作为唯一环境 map；
  `inherit_allowlist=[]`，所有已知 PSM/LIBERO/proxy/key checkpoint/cache 变量显式 unset。
- 不创建 trainer、model、dataloader、optimizer、checkpoint 或 CUDA context；禁止 torchrun、GPU、
  forward/backward、训练/评测/推理。
- 输出 `recurrent_resolved.json`、`ttt_resolved.json`、`diff.json`、`verification.json` 到
  `artifacts/g0/r09/b2/p5_full_config_diff/`，并包含 source/Gitlink、input SHA、canonical JSON SHA。

## Diff 合同

verifier 按 JSON Pointer 比较完整树，拒绝未知/非 JSON-safe/config interpolation 未解析值。允许差异
只能为：`…local_history_backend`、TTT enable switch、由该 switch 推导的 selector keys/optimizer
membership、以及 D005 规定的 backend-specific output root。所有其它路径（precision、seed、data/cache
root、window manifest、world size、microbatch=128、accum=16、100-update override、optimizer/scheduler/
EMA/clip、offline/env controls）必须逐值相等；任一额外 path 立即 FAIL。

## 验收

先做标准库/CPU fixture 回归：canonicalization 稳定、允许差异 PASS、任一未允许配置 mutation FAIL、
环境泄漏 FAIL、P4/P1/P3 provenance mutation FAIL。实现经三方批准后，才在 clean worktree 执行一次
静态 config export 和 verifier；结果再单独 closure review。P5 未关闭前，B2-T 继续禁止。
