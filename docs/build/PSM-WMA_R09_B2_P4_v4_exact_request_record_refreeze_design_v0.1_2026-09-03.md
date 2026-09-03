# R09-B2 P4-v4 Exact Request / Record-Refreeze 设计 v0.1

**状态**：draft。仅冻结未来一次 P4-v4 CPU preflight 的 exact-request 与后续 record/refreeze 审计合同；本设计不创建 request、run-root、staging、candidate 或 evidence，不调用 lock/preflight/P5 export/compose、child、torch、torchrun、GPU 或训练。

## 1. 前置与目标

前置 closure：P4 request static=`8535a8c`、planned-lock=`4108eb6`、P4 materialization=`bda9737`、P5 evidence authority static=`3e3a853`、P4/P5 handoff migration=`28b8592`（ChatGPT=`90cb466`、Kimi/MM 同 SHA）；Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。这些均不授予真实副作用。

唯一目标是在独立、可审计的后续 Gate 中生成一个 immutable exact request，并在其一次 CPU preflight PASS 后将两 backend 六份 canonical payload 原字节以 commit-or-none 方式 record/refreeze。实际路径、source revision、request raw/SHA、attempt、token、输出根、命令和资源在本设计中均为未填占位，禁止用历史 artifact 或文本代替。

## 2. Exact-request freeze

冻结对象必须包含 ordered backend set `["recurrent","ttt_fast_weight"]`、每侧 canonical source/Gitlink/current-byte bindings、lexical interpreter/loader、environment、P3 contract、v2 planned roster、互异且原本不存在的 run/candidate roots、attempt-id、run token、以及完整 canonical raw bytes 与 SHA256。所有值只可由 verifier-owned lock/spec/source authority 独立读取并交叉验证；caller、环境变量、历史 P4 v2/D005 artifacts 均不是 authority。

freeze 前任何 source/HEAD/tree/Gitlink/blob/current-byte/cleanliness/symlink drift，重复 identity/token/root，或 output 已存在均 FAIL-before-create。成功的 request raw/SHA 仅可供一次后续 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY` 审核；不得由本 Gate 执行该命令。

## 3. 一次 preflight 与候选边界

获得独立三方同 SHA execution verdict后，唯一允许命令须在请求中逐字冻结为 CPU-only stdlib entry及 `--request` raw/SHA；环境 allowlist、cwd、日志路径、candidate root、资源上限和停止条件不得由运行时补全。任何网络/GPU/torch/torchrun/模型数据 checkpoint I/O、路径存在、异常、identity reuse、额外文件或 pair 不完整立即停止，禁止 cleanup/retry/repair。

PASS candidate 每侧仅 `{request.json,result.json,verification.json,candidate_link.json}`；FAIL 仅 `{request.json,failure.json}`。`stage_atomic_publication()` 必先验证 exact dual PASS candidate；candidate link 永不发布。

## 4. Record/refreeze 与 P5 authority 分离

record/refreeze 只能在 preflight 双 PASS 后另获三方批准：逐侧复验 candidate link、三 payload raw bytes、P4 schema/source/staging/closure/v2 roster，及 pair shared-source/cross-backend invariants。只可将六份 payload 原字节同时写入固定 P5 evidence paths并以一个 Git commit 发布；不得 parse/rewrite/re-serialize，缺失/FAIL/partial/poison 均拒绝。

该 commit 不得自证其 commit/tree/Gitlink/blob；仅更后的独立 reviewed P5 verifier revision才能写入 exact `AUTHORIZED_P4_V4_EVIDENCE`。record/refreeze 不授权 P5 export/compose。

## 5. 验收、范围与 verdict

本设计阶段只允许文本核验与 `git diff --check`。后续 static tooling 必用 stdlib fixtures覆盖 freeze fail-before-create、one-shot identity、dual PASS/FAIL/partial、raw-byte preservation、Git/current-byte/Gitlink drift和 authority separation。

请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_EXACT_REQUEST_RECORD_REFREEZE_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。即使批准，真实 preflight、record/refreeze、P5 authority/export、GPU 与 Local Memory/LIBERO 训练仍须各自独立三方审核与明确执行授权。
