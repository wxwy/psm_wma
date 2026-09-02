# R09-B2 P4-v4 Execution-Preflight Materialization 设计 v0.3

**状态**：draft，替代未批准 v0.2；仅申请 future CPU-only reservation tooling static implementation。公开 CLI 继续 hard-stop；不授权真实 request/preflight/materialize、P5、GPU 或训练。

## 1. 前置与不变范围

前置 full static closure：root=`baf8581`、implementation=`8535a8c`、ChatGPT=`fd00550`、Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。v0.2=`594923c` 的 ChatGPT review=`b7bd62f` 指出 B1--B3；本版只关闭这些设计缺口，不修改任何 closed nested/full request validator、P5 grammar、P3 snapshot 或 authority。

仅可修改 root `tools/g0/r09_b2_p4_v4_execution_preflight.py` 和其 stdlib test。`main()` 仍为 single-fd SHA binding → `load_execution_request(raw)` → unconditional hard-stop，永不调用 helper。

## 2. byte-bound admission capability 与一次性状态

private `_AdmittedRequest` 的 admission data 精确为 `raw: bytes` 与 `request_sha256: str`，由唯一 `_admit_execution_request(raw)` 在成功调用既有 `load_execution_request(raw)` 后构造。它不保存/信任该 mutable returned dict；helper 每次只验证 `sha256(raw)==request_sha256`，以 canonical JSON 从 `raw` 重派生 `run.<backend>.identity.root` 与 `run_token`。因此任何外部 dict/deepcopy/reparse 或事后对象 mutation均无法改变路径/token authority。

capability 另有 private per-instance one-shot latch，初值 `UNUSED`，唯一合法转移为 helper 入口的 `UNUSED -> CONSUMED`；随后永远拒绝。该 latch 不属于 admission data、不会写磁盘或全局 registry，且只防止同一 capability 二次 reservation；真实 cross-process identity persistence仍由后续 exact-request Gate另行冻结。helper 只接受 `_AdmittedRequest` instance，拒绝 bare raw/dict。

## 3. footprint、ancestor exception 与全量 precheck

每个固定 backend `recurrent` 后 `ttt_fast_weight` 的唯一 footprint 是：

```text
<run_root>/
<run_root>/import_staging/
<run_root>/import_staging/<run_token>/
```

同一 backend 内上述两个 strict ancestor relation 是**唯一允许且必需**的 overlap；除此之外 equality/alias、cross-backend overlap，以及同任何 source/candidate/frozen authority overlap均拒绝。每个 run root 须为明确测试 namespace direct child；namespace/现存 ancestor为 nofollow canonical directories，run roots 在开始时不存在。

任何 mkdir 前，对两个 footprints 全量检查：根/中间/leaf 不存在、现存 parent 无 symlink、run roots distinct、除该 required ancestor relation 外无 overlap。任一 precheck FAIL 时 latch 已消费但零路径创建，返回 `PRECHECK_REJECTED`；不得 retry。

## 4. 六步创建与精确 poison

全量 precheck 后唯一 mutation 序列为 recurrent root→middle→leaf，后接 TTT root→middle→leaf；每步一个无 `parents=True` 的 nofollow mkdir，随后立即 nofollow stat。成功 mkdir 后 stat 成功才将该 path 加入 `created_paths`。

任意 mkdir FAIL：返回 `POISONED`，`created_paths` 是此前确认的有序 prefix，failed path 为该 mkdir target；即第一 mkdir失败时 prefix 为空但 capability latch 已 `CONSUMED`，同一 capability 永久不可重试。任意 post-mkdir stat FAIL：返回 `POISONED`，`created_paths` 必包含刚成功创建的路径，随后 failed path 与原始失败类型；这是真实 filesystem partial footprint。任何 `POISONED` 禁 cleanup/repair/rename/reuse；成功返回 `RESERVED` 的 ordered six paths，二者都不代表 materialized/candidate/P5 evidence。

## 5. 禁止范围与 fixture

无 Git/subprocess/Python child/P5/static publication/网络/torch/GPU/模型数据 checkpoint I/O；无 copy、manifest、roster、payload、candidate、evidence。测试唯一 I/O 为显式临时 namespace 的上述 path/stat；CLI 永远零 I/O。

fixture 必覆盖 raw-byte derivation vs mutable dict、capability one-shot（包括 first mkdir zero-footprint failure）、required ancestor relation与所有 unexpected overlaps、六步顺序、precheck zero mkdir、六 mkdir与六 post-stat逐点 failure的 exact prefix、ambient/subprocess/P5/child零调用以及 `main()` hard-stop。验收仅 CPU unittest、py_compile、`git diff --check`。

本版请求 `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 file:line）。真实执行仍须另起 exact-request Gate 三方 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY`。
