# R09-B2 P4-v4 Execution-Preflight Materialization 设计 v0.4

**状态**：draft，替代未批准 v0.3；范围与禁止项完全不变：仅 future CPU-only reservation tooling static implementation，`main()` 永远 hard-stop，不授权真实 request/preflight/materialize/P5/GPU/训练。

## 1. 固定前置

full static closure 为 root=`baf8581`、implementation=`8535a8c`、ChatGPT=`fd00550`、Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。v0.3=`6055ee1` 的 ChatGPT review=`f031dde` 确认其余合同已关闭；本版仅消除 `created_paths` post-mkdir stat-failure 矛盾，不改 closed nested/full validators、P5/P3 authority或 CLI。

## 2. 保持的 admission 与 reservation 合同

唯一 `_admit_execution_request(raw)` 先经既有 `load_execution_request(raw)`，private capability只保存 raw bytes/request SHA和私有 `UNUSED→CONSUMED` latch。helper只从 SHA-bound canonical raw重派生 root/token，拒绝 bare raw/dict/reparse；同一 capability任何尝试只允许一次。

固定 `recurrent→ttt_fast_weight`；每 backend 仅 `<run_root>`、`<run_root>/import_staging`、`<run_root>/import_staging/<token>` 三个无 `parents=True` mkdir。required same-backend ancestor chain是唯一允许 overlap，其他 alias/equality/cross-backend/authority overlap 均拒绝；precheck 全部在任何 mkdir 前。

## 3. 唯一 created_paths 定义

`created_paths` 唯一表示本 helper 已成功执行 mkdir syscall 的 ordered filesystem-mutation footprint，**不**表示 stat-verified set。每一步固定：

1. nofollow mkdir target；
2. mkdir 成功后立即将 target append 到 `created_paths`；
3. 立即对 target 执行 nofollow stat。

若 mkdir FAIL，target 不加入 `created_paths`，返回 `POISONED`，failed path 为 target且 prefix只含此前成功 mkdir。若 post-mkdir stat FAIL，target已在 `created_paths`，返回 `POISONED`，failed path为该 target并保留原始 stat failure类型。任何 `POISONED`（包括首步 mkdir空 prefix）capability均已 CONSUMED，禁止 cleanup/retry/repair/rename/reuse；成功 `RESERVED` 返回六路径 mutation footprint，二者均不代表 materialized/candidate/evidence。

## 4. 实现范围、fixture 与 verdict

若批准仅改 `tools/g0/r09_b2_p4_v4_execution_preflight.py` 与 `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`。fixtures必须逐点验证六 mkdir与六 stat fault的上述精确 prefix、raw-byte admission、latch、ancestor exception、precheck零 mkdir、ambient/subprocess/P5/child零调用及 CLI hard-stop。仅 CPU unittest、py_compile、diff-check；禁止任何真实路径/候选/P5/GPU/训练。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 file:line）。
