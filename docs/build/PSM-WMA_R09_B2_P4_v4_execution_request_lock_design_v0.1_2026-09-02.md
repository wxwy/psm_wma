# R09-B2 P4-v4 Execution-Request Lock 静态设计 v0.1

**状态**：draft，待三方审核。仅申请 root static request-lock tooling 与 stdlib CPU fixture；不授权真实 P4 preflight、materialize/staging、candidate、record/refreeze、P5 export/compose、torchrun、GPU 或训练。

## 1. 前置与范围

本设计只消费已关闭的 static authorities：P4-v4 full request validator=`8535a8c`，P5 full-config static closure=`49e6ccf`，P5 evidence Git authority=`3e3a853`，以及 materialization helper closure=`bda9737`/ChatGPT=`6910a72`；Gitlink 固定为 `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。任一 anchor、Gitlink、Git/current-byte、full-clean 或 lexical identity drift 必 FAIL。

新工具只构造 canonical `r09_b2_p4_v4_execution_request_v1` raw bytes，并调用既有 `load_execution_request(raw)` 复验。它不得调用 `_admit_execution_request()`、`_reserve_staging()`、`main()`、P5 exporter/verifier entry、subprocess child、Git write、torch 或任何 model/data/checkpoint I/O。

## 2. lock 输入与输出

输入必须是 verifier-owned、精确 key-set 的 `lock_spec`，包含：entry/source/interpreter/environment/authorities/backends 的已关闭 identities；两个 backend 的绝对 lexical future run roots、candidate root、attempt id、run token、roster SHA；以及 immutable execution contract。所有 digest 均为 lowercase 64-hex，两个 backend 的 root/token/roster/attempt identity 必 pairwise non-reuse；所有 future root 必不存在，且只允许现有 lexical prefix 做 nofollow/symlink rejection，绝不 mkdir 或 materialize。

输出为单个 canonical request raw 与其 SHA256；写入只能由调用方提供的全新 regular-file target，并以 nofollow create-new 语义完成。输出文件不是 execution authorization，不得位于 run root、candidate root、staging root、P5 evidence root 或 source tree。工具返回 `FROZEN_NOT_EXECUTABLE`，不产生 result、verification、candidate 或 failure payload。

## 3. authority 与一次性边界

lock 工具必须用 single-fd/no-follow read 得到每一外部固定输入的 raw bytes；同一 raw 同时参与 SHA、canonical parse 与 Git/current-byte identity。不得从 `PATH`、cwd、环境变量、caller mutable dict、已存在 candidate或此前 request 推断 authority。任何 lock failure 均零 run-root/staging/candidate 写入，且不得 cleanup、repair、rename、retry或覆盖 lock target。

lock 成功只证明 raw bytes 已冻结；随后实际 preflight 仍必须拿该 exact request raw/SHA、精确 command、source revision、output roots、CPU resource envelope 与停止条件，单独取得 ChatGPT/Kimi/MM 对同一 SHA 的 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY`。该执行批准也不授权 record/refreeze、P5 export/compose、GPU 或训练。

## 4. 永久 CPU fixture

fixtures 必覆盖：完整正例 canonical raw/SHA；每个 top-level与 nested identity drift；entry/source/interpreter/P5/P3/evidence Git authority drift；root/token/roster/attempt reuse；relative/dot/dotdot/double-slash/symlink-prefix/existing-root；target symlink/existing/partial-write；ambient PATH/PYTHONPATH/locale independence；禁用 subprocess/P5 child/torch；以及公开 P4 CLI 仍 hard-stop且不调用 materialization helper。

验收仅 `py_compile`、stdlib CPU unittest、`git diff --check`。本设计请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 file:line）。
